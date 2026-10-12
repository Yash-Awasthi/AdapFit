"""Bring feature_state rows to the form app.core.durable reads.

Two older forms are rewritten: rows stored as pickle become JSON, and a shared
service's single row holding every user (key "_") is split into one row per
key of each state dict, under `namespace.attr`. Run before starting the server:
    python -m scripts.migrate_feature_state_json
Rows already in the current form are left alone, so running it twice is safe.
"""
import asyncio
import io
import os
import pathlib
import pickle
import sys

ENV_FILE = pathlib.Path(".env")
for line in (ENV_FILE.read_text(encoding="utf-8") if ENV_FILE.exists() else "").splitlines():
    if line.strip() and not line.startswith("#") and "=" in line:
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())
sys.path.insert(0, ".")

from app.core import crypto, durable  # noqa: E402

# The allowlist the old loader used: plain data and classes defined in this app.
_SAFE = {
    ("builtins", "set"), ("builtins", "frozenset"), ("builtins", "complex"), ("builtins", "bytearray"),
    ("datetime", "datetime"), ("datetime", "date"), ("datetime", "time"), ("datetime", "timedelta"),
    ("datetime", "timezone"), ("collections", "OrderedDict"), ("collections", "defaultdict"),
    ("collections", "deque"), ("copyreg", "_reconstructor"), ("builtins", "object"),
    ("builtins", "list"), ("builtins", "dict"), ("decimal", "Decimal"), ("uuid", "UUID"),
}


class _SafeUnpickler(pickle.Unpickler):
    def find_class(self, module: str, name: str):
        if (module, name) in _SAFE:
            return super().find_class(module, name)
        if module.startswith("app.") and "." not in name:
            obj = super().find_class(module, name)
            if isinstance(obj, type) and obj.__module__ == module:
                return obj
        raise pickle.UnpicklingError(f"refusing to load {module}.{name}")


def convert(blob: bytes) -> bytes:
    """A pickled row (a stored value, or an instance's attribute dict) as JSON."""
    return durable._dumps(_SafeUnpickler(io.BytesIO(blob)).load())


def split_shared(namespace: str, state: dict) -> list:
    """(namespace.attr, key, value) rows for a shared service's old all-users row."""
    out = []
    for attr, value in state.items():
        target = f"{namespace}.{attr}"
        if target not in durable._holders:
            continue  # reference data or a counter that is no longer stored
        if attr == "_audit_log" and isinstance(value, list):
            # The family sharing log moved from one list to one list per user it names.
            by_user: dict = {}
            for entry in value:
                for uid in {entry.actor_id, entry.target_id} - {""}:
                    by_user.setdefault(uid, []).append(entry)
            value = by_user
        out.extend((target, str(k), v) for k, v in value.items())
    return out


async def main() -> int:
    import app.main  # noqa: F401  registers every holder, so a shared row's new namespaces are known

    store = durable._store()
    rows, failed = [], 0
    for namespace, key, sealed, _seq in await store.load_all():
        if not sealed:
            continue
        aad = durable._aad(namespace, key)
        blob = crypto.open_sealed(sealed, aad)
        try:
            if blob[:1] == b"\x80":
                blob = convert(blob)
                if key != "_":
                    rows.append((namespace, key, crypto.seal(blob, aad)))
            if key == "_" and namespace not in durable._holders:
                for target, k, v in split_shared(namespace, durable._loads(blob)):
                    rows.append((target, k, crypto.seal(durable._dumps(v), durable._aad(target, k))))
                rows.append((namespace, key, b""))
        except Exception as exc:
            failed += 1
            print(f"not converted {namespace}/{key}: {exc}", file=sys.stderr)
    if failed:
        print(f"{failed} rows could not be converted; nothing was written", file=sys.stderr)
        return 1
    if rows:
        await store.put(rows)
    print(f"rewrote {len(rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

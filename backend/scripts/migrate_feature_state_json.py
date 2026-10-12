"""Rewrite feature_state rows stored as pickle into the JSON form app.core.durable reads.

Run once per database (or local SQLite store) before starting the new server:
    python -m scripts.migrate_feature_state_json
Rows already in JSON are left alone, so running it twice is safe.
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


async def main() -> int:
    store = durable._store()
    rows, failed = [], 0
    for namespace, key, sealed in await store.load_all():
        aad = durable._aad(namespace, key)
        blob = crypto.open_sealed(sealed, aad)
        if blob[:1] != b"\x80":
            continue
        try:
            value = convert(blob)
        except Exception as exc:
            failed += 1
            print(f"not converted {namespace}/{key}: {exc}", file=sys.stderr)
            continue
        rows.append((namespace, key, crypto.seal(value, aad)))
    if failed:
        print(f"{failed} rows could not be converted; nothing was written", file=sys.stderr)
        return 1
    if rows:
        await store.upsert(rows)
    print(f"converted {len(rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

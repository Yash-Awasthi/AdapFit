"""
Write-through persistence for feature state that lives in process memory.

Three kinds of holder register here: per-user service proxies (one row per
user), shared service singletons (one row), and module-level dicts (one row
per key). Everything loads once at startup; after each request the holders
it touched are snapshotted as tagged JSON and any that changed are written back.

This keeps the in-memory model, so the server must run one worker: two
processes would each hold their own copy.
ponytail: whole-state load at startup and a single worker; move to per-request
hydration by user (rows are already keyed by user) when memory or scale demands it.
"""
import asyncio
import base64
import enum
import hashlib
import importlib
import json
import logging
import os
import sqlite3
import threading
from collections import OrderedDict, defaultdict, deque
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel

from app.core import crypto

logger = logging.getLogger(__name__)

SHARED_KEY = "_"

# namespace -> (kind, holder)
_holders: Dict[str, Tuple[str, Any]] = {}
_touched: set = set()
_touched_lock = threading.Lock()
_saved_hash: Dict[Tuple[str, str], bytes] = {}
# Rows whose holder was not imported yet at load time; restored when it registers,
# so a lazily imported service never starts empty and saves over its stored state.
_pending: Dict[str, list] = {}
_loading = False


# ── Encoding ────────────────────────────────────────────────────────────────
# State is stored as tagged JSON, never pickle: decoding only rebuilds plain data,
# enums and classes defined in this app, so a tampered row cannot run code.

_TAG = "$t"
_FACTORIES = {"list": list, "dict": dict, "set": set, "int": int, "float": float, "str": str}


def _class_path(cls: type) -> Optional[str]:
    module = cls.__module__
    if module.startswith("app.") and "." not in cls.__qualname__:
        return f"{module}:{cls.__qualname__}"
    return None


def _class_at(path: str) -> type:
    module, _, name = path.partition(":")
    if not module.startswith("app.") or not name or "." in name:
        raise ValueError(f"refusing to load {path}")
    cls = getattr(importlib.import_module(module), name, None)
    if not isinstance(cls, type) or cls.__module__ != module:
        raise ValueError(f"refusing to load {path}")
    return cls


def _pairs(d: dict) -> list:
    return [[_encode(k), _encode(v)] for k, v in d.items()]


def _encode(value: Any) -> Any:
    """Tagged-JSON form of value; TypeError for anything that is not state (locks, clients)."""
    if isinstance(value, enum.Enum):
        path = _class_path(type(value))
        if path is None:
            raise TypeError(f"enum {type(value).__module__}.{type(value).__qualname__} is not this app's")
        return {_TAG: "enum", "c": path, "v": _encode(value.value)}
    t = type(value)
    if value is None or t in (bool, str, int, float):
        return value
    if t is list:
        return [_encode(v) for v in value]
    if t is dict:
        if all(type(k) is str for k in value) and _TAG not in value:
            return {k: _encode(v) for k, v in value.items()}
        return {_TAG: "dict", "v": _pairs(value)}
    if t is tuple:
        return {_TAG: "tuple", "v": [_encode(v) for v in value]}
    if t in (set, frozenset):
        return {_TAG: t.__name__, "v": [_encode(v) for v in value]}
    if t is OrderedDict:
        return {_TAG: "OrderedDict", "v": _pairs(value)}
    if t is defaultdict:
        factory = next((n for n, f in _FACTORIES.items() if f is value.default_factory), None)
        if factory is None and value.default_factory is not None:
            raise TypeError(f"defaultdict factory {value.default_factory!r} cannot be stored")
        return {_TAG: "defaultdict", "f": factory, "v": _pairs(value)}
    if t is deque:
        return {_TAG: "deque", "m": value.maxlen, "v": [_encode(v) for v in value]}
    if t is datetime:
        return {_TAG: "datetime", "v": value.isoformat()}
    if t is date:
        return {_TAG: "date", "v": value.isoformat()}
    if t is time:
        return {_TAG: "time", "v": value.isoformat()}
    if t is timedelta:
        return {_TAG: "timedelta", "v": [value.days, value.seconds, value.microseconds]}
    if t is timezone:
        return {_TAG: "timezone", "v": [value.utcoffset(None).total_seconds(), value.tzname(None)]}
    if t is Decimal:
        return {_TAG: "Decimal", "v": str(value)}
    if t is UUID:
        return {_TAG: "UUID", "v": str(value)}
    if t is complex:
        return {_TAG: "complex", "v": [value.real, value.imag]}
    if t in (bytes, bytearray):
        return {_TAG: t.__name__, "v": base64.b64encode(value).decode()}
    path = _class_path(t)
    if path is not None:
        if isinstance(value, BaseModel):
            return {_TAG: "model", "c": path, "set": sorted(value.model_fields_set),
                    "v": {k: _encode(v) for k, v in vars(value).items()}}
        if isinstance(value, tuple):
            return {_TAG: "obj", "c": path, "args": [_encode(v) for v in value]}
        if hasattr(value, "__dict__") and not hasattr(t, "__slots__"):
            return {_TAG: "obj", "c": path, "v": {k: _encode(v) for k, v in vars(value).items()}}
    raise TypeError(f"{t.__module__}.{t.__qualname__} cannot be stored")


def _decode(node: Any) -> Any:
    if isinstance(node, list):
        return [_decode(v) for v in node]
    if not isinstance(node, dict):
        return node
    tag = node.get(_TAG)
    if tag is None:
        return {k: _decode(v) for k, v in node.items()}
    v = node.get("v")
    if tag == "dict":
        return {_decode(k): _decode(x) for k, x in v}
    if tag == "OrderedDict":
        return OrderedDict((_decode(k), _decode(x)) for k, x in v)
    if tag == "defaultdict":
        return defaultdict(_FACTORIES[node["f"]] if node["f"] else None, ((_decode(k), _decode(x)) for k, x in v))
    if tag == "tuple":
        return tuple(_decode(x) for x in v)
    if tag == "set":
        return {_decode(x) for x in v}
    if tag == "frozenset":
        return frozenset(_decode(x) for x in v)
    if tag == "deque":
        return deque((_decode(x) for x in v), node["m"])
    if tag == "datetime":
        return datetime.fromisoformat(v)
    if tag == "date":
        return date.fromisoformat(v)
    if tag == "time":
        return time.fromisoformat(v)
    if tag == "timedelta":
        return timedelta(days=v[0], seconds=v[1], microseconds=v[2])
    if tag == "timezone":
        return timezone(timedelta(seconds=v[0]), v[1])
    if tag == "Decimal":
        return Decimal(v)
    if tag == "UUID":
        return UUID(v)
    if tag == "complex":
        return complex(*v)
    if tag in ("bytes", "bytearray"):
        raw = base64.b64decode(v)
        return raw if tag == "bytes" else bytearray(raw)
    if tag == "enum":
        cls = _class_at(node["c"])
        if not issubclass(cls, enum.Enum):
            raise ValueError(f"{node['c']} is not an enum")
        return cls(_decode(v))
    if tag == "model":
        cls = _class_at(node["c"])
        if not issubclass(cls, BaseModel):
            raise ValueError(f"{node['c']} is not a model")
        return cls.model_construct(set(node["set"]), **{k: _decode(x) for k, x in v.items()})
    if tag == "obj":
        cls = _class_at(node["c"])
        if "args" in node:
            return cls(*(_decode(x) for x in node["args"]))
        obj = cls.__new__(cls)
        vars(obj).update({k: _decode(x) for k, x in v.items()})
        return obj
    raise ValueError(f"unknown tag {tag!r}")


def _dumps(value: Any) -> bytes:
    return json.dumps(_encode(value), separators=(",", ":")).encode()


def _loads(blob: bytes) -> Any:
    return _decode(json.loads(blob))


# ── Storage backends ────────────────────────────────────────────────────────

class _SQLite:
    """Local file store for development and tests."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.execute("CREATE TABLE IF NOT EXISTS feature_state (namespace TEXT, key TEXT, payload BLOB, "
                         "updated_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (namespace, key))")
        self._lock = threading.Lock()

    async def load_all(self):
        with self._lock:
            return self._db.execute("SELECT namespace, key, payload FROM feature_state").fetchall()

    async def upsert(self, rows):
        with self._lock, self._db:
            self._db.executemany("INSERT INTO feature_state (namespace, key, payload) VALUES (?, ?, ?) "
                                 "ON CONFLICT(namespace, key) DO UPDATE SET payload = excluded.payload, "
                                 "updated_at = CURRENT_TIMESTAMP", rows)

    async def delete(self, pairs):
        with self._lock, self._db:
            self._db.executemany("DELETE FROM feature_state WHERE namespace = ? AND key = ?", pairs)

    async def delete_key(self, key: str):
        with self._lock, self._db:
            self._db.execute("DELETE FROM feature_state WHERE key = ?", (key,))


class _Postgres:
    async def _pool(self):
        from app.core.db import get_pool
        return await get_pool()

    async def load_all(self):
        pool = await self._pool()
        async with pool.acquire() as conn:
            return [(r["namespace"], r["key"], bytes(r["payload"]))
                    for r in await conn.fetch("SELECT namespace, key, payload FROM feature_state")]

    async def upsert(self, rows):
        pool = await self._pool()
        async with pool.acquire() as conn:
            await conn.executemany(
                "INSERT INTO feature_state (namespace, key, payload) VALUES ($1, $2, $3) "
                "ON CONFLICT (namespace, key) DO UPDATE SET payload = EXCLUDED.payload, updated_at = now()", rows)

    async def delete(self, pairs):
        pool = await self._pool()
        async with pool.acquire() as conn:
            await conn.executemany("DELETE FROM feature_state WHERE namespace = $1 AND key = $2", pairs)

    async def delete_key(self, key: str):
        pool = await self._pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM feature_state WHERE key = $1", key)


_backend = None


def _store():
    global _backend
    if _backend is None:
        from app.core.config import settings
        if settings.DATABASE_URL:
            _backend = _Postgres()
        else:
            from app.core.storage import DATA_DIR
            _backend = _SQLite(Path(os.getenv("ADAPFIT_DATA_DIR") or DATA_DIR) / "feature_state.sqlite3")
    return _backend


# ── Holders ─────────────────────────────────────────────────────────────────

def touch(namespace: str, key: str) -> None:
    if not _loading:
        with _touched_lock:
            _touched.add((namespace, key))


def _register(namespace: str, kind: str, holder: Any) -> None:
    global _loading
    _holders[namespace] = (kind, holder)
    rows = _pending.pop(namespace, [])
    if not rows:
        return
    was, _loading = _loading, True
    try:
        for key, blob in rows:
            try:
                _restore(namespace, key, _loads(blob))
                _saved_hash[(namespace, key)] = hashlib.sha256(blob).digest()
            except Exception as exc:
                logger.error("feature_state %s/%s not restored: %s", namespace, key, exc)
    finally:
        _loading = was


def track_per_user(namespace: str, proxy) -> None:
    _register(namespace, "per_user", proxy)


class SharedProxy:
    """A shared service whose every use marks it for saving."""

    def __init__(self, namespace: str, instance: Any):
        object.__setattr__(self, "_ns", namespace)
        object.__setattr__(self, "_instance", instance)

    def __getattr__(self, name):
        touch(object.__getattribute__(self, "_ns"), SHARED_KEY)
        return getattr(object.__getattribute__(self, "_instance"), name)

    def __setattr__(self, name, value):
        touch(object.__getattribute__(self, "_ns"), SHARED_KEY)
        setattr(object.__getattribute__(self, "_instance"), name, value)


def shared(namespace: str, instance: Any) -> Any:
    proxy = SharedProxy(namespace, instance)
    _register(namespace, "shared", proxy)
    return proxy


class DurableDict(dict):
    """A module-level dict whose entries persist, one row per key."""

    def __init__(self, namespace: str):
        super().__init__()
        self._ns = namespace
        _register(namespace, "dict", self)

    def _mark(self, key):
        touch(self._ns, str(key))

    def __getitem__(self, key):
        self._mark(key)
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        self._mark(key)
        super().__setitem__(key, value)

    def __delitem__(self, key):
        self._mark(key)
        super().__delitem__(key)

    def get(self, key, default=None):
        self._mark(key)
        return super().get(key, default)

    def setdefault(self, key, default=None):
        self._mark(key)
        return super().setdefault(key, default)

    def pop(self, key, *default):
        self._mark(key)
        return super().pop(key, *default)

    def values(self):
        # Iteration can mutate nested values without naming a key.
        for key in list(super().keys()):
            self._mark(key)
        return super().values()

    def items(self):
        for key in list(super().keys()):
            self._mark(key)
        return super().items()


def durable_dict(namespace: str) -> DurableDict:
    return DurableDict(namespace)


# ── Snapshots ───────────────────────────────────────────────────────────────

def _state_of(obj: Any) -> bytes:
    """Instance attributes that are data; locks, sockets and clients are skipped."""
    out = {}
    for name, value in vars(obj).items():
        try:
            out[name] = _encode(value)
        except TypeError:
            continue
    return json.dumps(out, separators=(",", ":")).encode()


def _snapshot(namespace: str, key: str) -> Optional[bytes]:
    kind, holder = _holders[namespace]
    if kind == "per_user":
        instances = object.__getattribute__(holder, "_instances")
        return _state_of(instances[key]) if key in instances else None
    if kind == "shared":
        return _state_of(object.__getattribute__(holder, "_instance"))
    if dict.__contains__(holder, key):
        return _dumps(dict.__getitem__(holder, key))
    return None


def _restore(namespace: str, key: str, value: Any) -> None:
    kind, holder = _holders[namespace]
    if kind == "per_user":
        vars(holder.instance_for(key)).update(value)
    elif kind == "shared":
        vars(object.__getattribute__(holder, "_instance")).update(value)
    else:
        dict.__setitem__(holder, key, value)


async def load_all() -> Dict[str, int]:
    """Restore every registered holder from the store; rows for holders not imported yet wait in _pending."""
    global _loading
    _loading = True
    loaded, skipped = 0, 0
    try:
        for namespace, key, sealed in await _store().load_all():
            # Outside the try: a missing key must stop startup, not restore empty state that is then saved.
            blob = crypto.open_sealed(sealed, _aad(namespace, key))
            if blob[:1] == b"\x80":
                raise RuntimeError("feature_state holds pickled rows; run python -m scripts.migrate_feature_state_json")
            if namespace not in _holders:
                _pending.setdefault(namespace, []).append((key, blob))
                skipped += 1
                continue
            try:
                _restore(namespace, key, _loads(blob))
                _saved_hash[(namespace, key)] = hashlib.sha256(blob).digest()
                loaded += 1
            except Exception as exc:
                skipped += 1
                logger.error("feature_state %s/%s not restored: %s", namespace, key, exc)
    finally:
        _loading = False
    return {"loaded": loaded, "skipped": skipped}


_flush_lock = asyncio.Lock()


async def flush() -> int:
    """Write back every touched holder whose snapshot changed. Returns rows written."""
    async with _flush_lock:
        with _touched_lock:
            pending = list(_touched)
            _touched.clear()
        upserts, deletes = [], []
        for namespace, key in pending:
            if namespace not in _holders:
                continue
            try:
                blob = _snapshot(namespace, key)
            except Exception as exc:
                logger.error("feature_state %s/%s not saved: %s", namespace, key, exc)
                continue
            if blob is None:
                if (namespace, key) in _saved_hash:
                    deletes.append((namespace, key))
                    _saved_hash.pop((namespace, key), None)
                continue
            digest = hashlib.sha256(blob).digest()
            if _saved_hash.get((namespace, key)) != digest:
                upserts.append((namespace, key, crypto.seal(blob, _aad(namespace, key))))
                _saved_hash[(namespace, key)] = digest
        if upserts:
            await _store().upsert(upserts)
        if deletes:
            await _store().delete(deletes)
        return len(upserts) + len(deletes)


# ── Erasure and export ──────────────────────────────────────────────────────
# Shared services keep every user's records in one object, keyed by user id or
# carrying it as a field. A record belongs to a user when it is keyed by their
# id or any of its string fields equals it; user ids are UUIDs, so a collision
# with reference data is not a practical concern.

def _fields(value: Any) -> Optional[dict]:
    if isinstance(value, dict):
        return value
    if type(value).__module__.startswith("app.") and hasattr(value, "__dict__"):
        return vars(value)
    return None


def _owned(value: Any, uid: str) -> bool:
    fields = _fields(value)
    return fields is not None and any(v == uid for v in fields.values() if isinstance(v, str))


def _record_ids(value: Any, ids: set, depth: int = 0) -> None:
    """Ids of records inside a removed value, so stores keyed by those ids can follow."""
    if depth > 4:
        return
    fields = _fields(value)
    if fields is not None:
        for k, v in fields.items():
            if k == "id" and isinstance(v, str):
                ids.add(v)
            elif isinstance(v, (dict, list)):
                _record_ids(v, ids, depth + 1)
    elif isinstance(value, list):
        for v in value:
            _record_ids(v, ids, depth + 1)


def _walk(node: Any, uid: str, remove: bool, found: list, ids: Optional[set], depth: int = 0) -> None:
    """Collect (and with remove, delete) everything in node keyed by or referring to uid."""
    if depth > 8:
        return
    if isinstance(node, dict):
        for key in list(dict.keys(node)):
            value = dict.__getitem__(node, key)
            if key == uid or _owned(value, uid) or (ids is not None and key in ids):
                found.append(value)
                if ids is not None:
                    _record_ids(value, ids)
                if remove:
                    dict.__delitem__(node, key)
            else:
                _walk(value, uid, remove, found, ids, depth + 1)
    elif isinstance(node, list):
        keep = []
        for value in node:
            if value == uid or _owned(value, uid):
                found.append(value)
            else:
                _walk(value, uid, remove, found, ids, depth + 1)
                keep.append(value)
        if remove:
            node[:] = keep
    elif isinstance(node, set):
        if uid in node:
            found.append(uid)
            if remove:
                node.discard(uid)
    else:
        fields = _fields(node)
        if fields is not None:
            _walk(fields, uid, remove, found, ids, depth + 1)


def _sweep(uid: str, remove: bool) -> Dict[str, list]:
    """Per holder, what the shared services and module stores hold for uid."""
    # Module stores are keyed by record id (goal_id, share_id), so a removed goal
    # takes its logs with it; a second pass catches stores walked before the owner.
    ids: set = set()
    out: Dict[str, list] = {}
    for _ in range(2):
        if not remove:
            out = {}
        for namespace, (kind, holder) in _holders.items():
            found: list = []
            if kind == "shared":
                for value in vars(object.__getattribute__(holder, "_instance")).values():
                    if isinstance(value, (dict, list, set)):
                        _walk(value, uid, remove, found, None)
            elif kind == "dict":
                _walk(holder, uid, remove, found, ids)
            elif remove:
                for other, instance in list(object.__getattribute__(holder, "_instances").items()):
                    if other != uid:
                        _walk(vars(instance), uid, True, found, None)
            if not found:
                continue
            out.setdefault(namespace, []).extend(found)
            if kind == "shared":
                touch(namespace, SHARED_KEY)
            elif kind == "dict":
                for key in set(dict.keys(holder)) | {k for n, k in _saved_hash if n == namespace}:
                    touch(namespace, str(key))
            else:
                for other in object.__getattribute__(holder, "_instances"):
                    touch(namespace, other)
    return out


def export_shared(user_id: str) -> Dict[str, Any]:
    """What shared services and module stores hold for one user, as plain data."""
    from app.core.per_user import _plain
    return {ns: _plain(items) for ns, items in _sweep(user_id, remove=False).items()}


def _aad(namespace: str, key: str) -> bytes:
    return f"feature_state/{namespace}/{key}".encode()


async def reseal_all() -> int:
    """Re-encrypt every stored row not already under the active key. Returns rows rewritten."""
    active = crypto.active_key_id()
    rows = []
    for namespace, key, sealed in await _store().load_all():
        if crypto.key_id_of(sealed) != active:
            aad = _aad(namespace, key)
            rows.append((namespace, key, crypto.seal(crypto.open_sealed(sealed, aad), aad)))
    if rows:
        await _store().upsert(rows)
    return len(rows)


async def erase_user(user_id: str) -> None:
    """Drop everything held for a user: their own state, and their records inside shared state."""
    for kind, holder in _holders.values():
        if kind == "per_user":
            holder.reset(user_id)
    _sweep(user_id, remove=True)
    await forget(user_id)
    await flush()


async def forget(user_id: str) -> None:
    """Remove every per-user and user-keyed row for an account."""
    await _store().delete_key(user_id)
    for pair in [p for p in _saved_hash if p[1] == user_id]:
        _saved_hash.pop(pair, None)


def _reset_for_tests() -> None:
    global _backend
    _backend = None
    _saved_hash.clear()
    _touched.clear()
    _pending.clear()

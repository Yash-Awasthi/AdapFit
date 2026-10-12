"""
Write-through persistence for feature state held in process memory.

Two kinds of holder register here: per-user service proxies (one row per user)
and durable dicts (one row per key; shared services keep each state dict as
one, so a user's records are rows keyed by that user). Rows load lazily: the
caller's rows when a request starts, any other row on first access, and a whole
namespace when it is iterated.

Several processes can serve one store. Before each request a process applies
the rows others changed since it last looked (every write takes a new sequence
number); after the request it writes back the rows that changed, each on the
condition that nobody wrote it since it was read. When somebody did, the two
versions are merged against the one both started from and the write retried.
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
import time as _time
from collections import OrderedDict, defaultdict, deque
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel

from app.core import crypto

logger = logging.getLogger(__name__)

# namespace -> (kind, holder)
_holders: Dict[str, Tuple[str, Any]] = {}
_touched: set = set()
_touched_lock = threading.Lock()


@dataclass
class _Row:
    """What this process last read or wrote for one row; tree is None when the row does not exist."""
    seq: Optional[int]
    tree: Any
    digest: Optional[bytes]


_rows: Dict[Tuple[str, str], _Row] = {}
_full: set = set()
# Rows another process changed while this one had them touched; settled at flush.
_deferred: Dict[Tuple[str, str], _Row] = {}
_seen_seq = 0
# Sequence numbers skipped so far; a slower transaction may still commit them.
_gaps: Dict[int, float] = {}
_GAP_SECONDS = 30.0
_restoring = False



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


def _bytes(tree: Any) -> bytes:
    return json.dumps(tree, separators=(",", ":")).encode()


def _digest(tree: Any) -> Optional[bytes]:
    return None if tree is None else hashlib.sha256(_bytes(tree)).digest()


# ── Three-way merge ─────────────────────────────────────────────────────────
# Works on the stored JSON trees, so it needs no knowledge of the classes inside.

_MISSING = object()


def _merge(base: Any, ours: Any, theirs: Any) -> Any:
    """Combine two edits of base. Where both changed the same scalar, ours wins."""
    if ours == theirs:
        return ours
    if ours == base:
        return theirs
    if theirs == base:
        return ours
    if isinstance(ours, dict) and isinstance(theirs, dict):
        base = base if isinstance(base, dict) else {}
        out = {}
        for key in list(theirs) + [k for k in ours if k not in theirs]:
            b, o, t = base.get(key, _MISSING), ours.get(key, _MISSING), theirs.get(key, _MISSING)
            if o is _MISSING:
                if t is not _MISSING and t != b:
                    out[key] = t
            elif t is _MISSING:
                if o != b:
                    out[key] = o
            else:
                out[key] = _merge(None if b is _MISSING else b, o, t)
        return out
    if isinstance(ours, list) and isinstance(theirs, list):
        base = base if isinstance(base, list) else []
        removed = [x for x in base if x not in ours]
        added = [x for x in ours if x not in base]
        return [x for x in theirs if x not in removed] + [x for x in added if x not in theirs]
    return ours


# ── Storage backends ────────────────────────────────────────────────────────
# A row is (namespace, key, sealed payload, seq). An empty payload is a deletion,
# kept so other processes learn of it; seq grows with every write.

_SQLITE_SCHEMA = ("CREATE TABLE IF NOT EXISTS feature_state (namespace TEXT, key TEXT, payload BLOB, "
                  "seq INTEGER NOT NULL DEFAULT 0, updated_at TEXT DEFAULT CURRENT_TIMESTAMP, "
                  "PRIMARY KEY (namespace, key))")


class _SQLite:
    """Local file store for development and tests; several processes may share the file."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), check_same_thread=False, timeout=30, isolation_level=None)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute(_SQLITE_SCHEMA)
        if "seq" not in [r[1] for r in self._db.execute("PRAGMA table_info(feature_state)")]:
            self._db.execute("ALTER TABLE feature_state ADD COLUMN seq INTEGER NOT NULL DEFAULT 0")
            self._db.execute("UPDATE feature_state SET seq = rowid")
        self._db.execute("CREATE INDEX IF NOT EXISTS feature_state_seq_idx ON feature_state (seq)")
        self._db.execute("CREATE INDEX IF NOT EXISTS feature_state_key_idx ON feature_state (key)")
        self._lock = threading.Lock()

    def _query(self, sql: str, args: tuple = ()) -> list:
        with self._lock:
            return self._db.execute(sql, args).fetchall()

    def _next_seq(self) -> int:
        return self._db.execute("SELECT COALESCE(MAX(seq), 0) + 1 FROM feature_state").fetchone()[0]

    def fetch_sync(self, ns: str, key: str):
        rows = self._query("SELECT payload, seq FROM feature_state WHERE namespace = ? AND key = ?", (ns, key))
        return (bytes(rows[0][0] or b""), rows[0][1]) if rows else None

    def fetch_namespace_sync(self, ns: str) -> list:
        return [(k, bytes(p or b""), s) for k, p, s in
                self._query("SELECT key, payload, seq FROM feature_state WHERE namespace = ?", (ns,))]

    async def fetch_key(self, key: str) -> list:
        return [(n, bytes(p or b""), s) for n, p, s in
                self._query("SELECT namespace, payload, seq FROM feature_state WHERE key = ?", (key,))]

    async def changes(self, after: int, gaps: List[int]) -> list:
        marks = ",".join("?" * len(gaps)) or "NULL"
        return [(n, k, bytes(p or b""), s) for n, k, p, s in self._query(
            f"SELECT namespace, key, payload, seq FROM feature_state WHERE seq > ? OR seq IN ({marks}) ORDER BY seq",
            (after, *gaps))]

    async def max_seq(self) -> int:
        return self._query("SELECT COALESCE(MAX(seq), 0) FROM feature_state")[0][0]

    async def load_all(self) -> list:
        return [(n, k, bytes(p or b""), s) for n, k, p, s in
                self._query("SELECT namespace, key, payload, seq FROM feature_state")]

    async def write(self, ns: str, key: str, payload: bytes, expected: Optional[int]):
        """New seq, or None and the row as it now stands when expected is out of date."""
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                row = self._db.execute("SELECT payload, seq FROM feature_state WHERE namespace = ? AND key = ?",
                                       (ns, key)).fetchone()
                if (row[1] if row else None) != expected:
                    self._db.execute("COMMIT")
                    return None, (bytes(row[0] or b""), row[1]) if row else (b"", None)
                seq = self._next_seq()
                self._db.execute(
                    "INSERT INTO feature_state (namespace, key, payload, seq) VALUES (?, ?, ?, ?) "
                    "ON CONFLICT(namespace, key) DO UPDATE SET payload = excluded.payload, seq = excluded.seq, "
                    "updated_at = CURRENT_TIMESTAMP", (ns, key, payload, seq))
                self._db.execute("COMMIT")
                return seq, None
            except BaseException:
                self._db.execute("ROLLBACK")
                raise

    async def put(self, rows: Iterable[Tuple[str, str, bytes]]) -> None:
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                for ns, key, payload in rows:
                    self._db.execute(
                        "INSERT INTO feature_state (namespace, key, payload, seq) VALUES (?, ?, ?, ?) "
                        "ON CONFLICT(namespace, key) DO UPDATE SET payload = excluded.payload, seq = excluded.seq, "
                        "updated_at = CURRENT_TIMESTAMP", (ns, key, payload, self._next_seq()))
                self._db.execute("COMMIT")
            except BaseException:
                self._db.execute("ROLLBACK")
                raise

    async def tombstone_key(self, key: str) -> list:
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            out = []
            for (ns,) in self._db.execute("SELECT namespace FROM feature_state WHERE key = ?", (key,)).fetchall():
                seq = self._next_seq()
                self._db.execute("UPDATE feature_state SET payload = ?, seq = ? WHERE namespace = ? AND key = ?",
                                 (b"", seq, ns, key))
                out.append((ns, seq))
            self._db.execute("COMMIT")
            return out


class _Postgres:
    async def _pool(self):
        from app.core.db import get_pool
        return await get_pool()

    async def _fetch(self, sql: str, *args) -> list:
        async with (await self._pool()).acquire() as conn:
            return await conn.fetch(sql, *args)

    def fetch_sync(self, ns: str, key: str):
        rows = _bridge.run(_bridge_fetch("SELECT payload, seq FROM feature_state WHERE namespace = $1 AND key = $2",
                                         ns, key))
        return (bytes(rows[0]["payload"] or b""), rows[0]["seq"]) if rows else None

    def fetch_namespace_sync(self, ns: str) -> list:
        rows = _bridge.run(_bridge_fetch("SELECT key, payload, seq FROM feature_state WHERE namespace = $1", ns))
        return [(r["key"], bytes(r["payload"] or b""), r["seq"]) for r in rows]

    async def fetch_key(self, key: str) -> list:
        rows = await self._fetch("SELECT namespace, payload, seq FROM feature_state WHERE key = $1", key)
        return [(r["namespace"], bytes(r["payload"] or b""), r["seq"]) for r in rows]

    async def changes(self, after: int, gaps: List[int]) -> list:
        rows = await self._fetch("SELECT namespace, key, payload, seq FROM feature_state "
                                 "WHERE seq > $1 OR seq = ANY($2::bigint[]) ORDER BY seq", after, gaps)
        return [(r["namespace"], r["key"], bytes(r["payload"] or b""), r["seq"]) for r in rows]

    async def max_seq(self) -> int:
        return (await self._fetch("SELECT COALESCE(MAX(seq), 0) AS m FROM feature_state"))[0]["m"]

    async def load_all(self) -> list:
        rows = await self._fetch("SELECT namespace, key, payload, seq FROM feature_state")
        return [(r["namespace"], r["key"], bytes(r["payload"] or b""), r["seq"]) for r in rows]

    async def write(self, ns: str, key: str, payload: bytes, expected: Optional[int]):
        async with (await self._pool()).acquire() as conn:
            async with conn.transaction():
                if expected is None:
                    seq = await conn.fetchval(
                        "INSERT INTO feature_state (namespace, key, payload) VALUES ($1, $2, $3) "
                        "ON CONFLICT (namespace, key) DO NOTHING RETURNING seq", ns, key, payload)
                else:
                    seq = await conn.fetchval(
                        "UPDATE feature_state SET payload = $3, seq = nextval('feature_state_seq'), updated_at = now() "
                        "WHERE namespace = $1 AND key = $2 AND seq = $4 RETURNING seq", ns, key, payload, expected)
                if seq is not None:
                    return seq, None
                row = await conn.fetchrow(
                    "SELECT payload, seq FROM feature_state WHERE namespace = $1 AND key = $2", ns, key)
                return None, (bytes(row["payload"] or b""), row["seq"]) if row else (b"", None)

    async def put(self, rows: Iterable[Tuple[str, str, bytes]]) -> None:
        async with (await self._pool()).acquire() as conn:
            await conn.executemany(
                "INSERT INTO feature_state (namespace, key, payload) VALUES ($1, $2, $3) "
                "ON CONFLICT (namespace, key) DO UPDATE SET payload = EXCLUDED.payload, "
                "seq = nextval('feature_state_seq'), updated_at = now()", list(rows))

    async def tombstone_key(self, key: str) -> list:
        rows = await self._fetch("UPDATE feature_state SET payload = '\\x'::bytea, seq = nextval('feature_state_seq'), "
                                 "updated_at = now() WHERE key = $1 RETURNING namespace, seq", key)
        return [(r["namespace"], r["seq"]) for r in rows]


class _Bridge:
    """Runs asyncpg calls for synchronous code (a first read of a row) on a thread with its own loop."""

    def __init__(self):
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._lock = threading.Lock()
        self.conn = None

    def run(self, coro):
        with self._lock:
            if self._loop is None:
                self._loop = asyncio.new_event_loop()
                threading.Thread(target=self._loop.run_forever, name="feature-state-bridge", daemon=True).start()
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result(timeout=30)


    def close(self) -> None:
        with self._lock:
            if self._loop is None:
                return
            if self.conn is not None:
                asyncio.run_coroutine_threadsafe(self.conn.close(), self._loop).result(timeout=10)
                self.conn = None
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._loop = None


_bridge = _Bridge()


def close() -> None:
    """Close the connection first reads use; the process is shutting down."""
    _bridge.close()


async def _bridge_fetch(sql: str, *args) -> list:
    import asyncpg
    from app.core.config import settings

    if _bridge.conn is None or _bridge.conn.is_closed():
        transaction_mode = ":6543" in settings.DATABASE_URL
        _bridge.conn = await asyncpg.connect(settings.DATABASE_URL,
                                             statement_cache_size=0 if transaction_mode else 100)
    return await _bridge.conn.fetch(sql, *args)


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
    if not _restoring:
        with _touched_lock:
            _touched.add((namespace, key))


def _register(namespace: str, kind: str, holder: Any) -> None:
    _holders[namespace] = (kind, holder)


def track_per_user(namespace: str, proxy) -> None:
    _register(namespace, "per_user", proxy)


class DurableDict(dict):
    """A dict whose entries persist, one row per key, read from the store on first use."""

    def __init__(self, namespace: str):
        super().__init__()
        self._ns = namespace
        _register(namespace, "dict", self)

    def _use(self, key) -> str:
        k = str(key)
        _ensure(self._ns, k)
        touch(self._ns, k)
        return k

    def __getitem__(self, key):
        self._use(key)
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        self._use(key)
        super().__setitem__(key, value)

    def __delitem__(self, key):
        self._use(key)
        super().__delitem__(key)

    def __contains__(self, key):
        _ensure(self._ns, str(key))
        return super().__contains__(key)

    def get(self, key, default=None):
        self._use(key)
        return super().get(key, default)

    def setdefault(self, key, default=None):
        self._use(key)
        return super().setdefault(key, default)

    def pop(self, key, *default):
        self._use(key)
        return super().pop(key, *default)

    def __iter__(self):
        _ensure_namespace(self._ns)
        return super().__iter__()

    def __len__(self):
        _ensure_namespace(self._ns)
        return super().__len__()

    def keys(self):
        _ensure_namespace(self._ns)
        return super().keys()

    def values(self):
        # Iteration can mutate nested values without naming a key.
        _ensure_namespace(self._ns)
        for key in list(super().keys()):
            touch(self._ns, str(key))
        return super().values()

    def items(self):
        _ensure_namespace(self._ns)
        for key in list(super().keys()):
            touch(self._ns, str(key))
        return super().items()

    # Reads that do not mark the row for writing back.
    def peek(self, key, default=None):
        _ensure(self._ns, str(key))
        return super().get(key, default)

    def peek_items(self):
        _ensure_namespace(self._ns)
        return list(super().items())


def durable_dict(namespace: str) -> DurableDict:
    return DurableDict(namespace)


def shared(namespace: str, instance: Any, state: Tuple[str, ...]) -> Any:
    """A service shared by every user: each dict named in state persists as `namespace.attr`, one row per key."""
    for attr in state:
        current = getattr(instance, attr)
        if not isinstance(current, dict):
            raise TypeError(f"{namespace}.{attr} must be a dict to persist")
        store = DurableDict(f"{namespace}.{attr}")
        dict.update(store, current)
        setattr(instance, attr, store)
    return instance


# ── Loading ─────────────────────────────────────────────────────────────────

def _open(namespace: str, key: str, payload: bytes) -> Any:
    if not payload:
        return None
    blob = crypto.open_sealed(payload, _aad(namespace, key))
    if blob[:1] == b"\x80":
        # Outside any fallback: decoding it as empty state would then be saved over it.
        raise RuntimeError("feature_state holds pickled rows; run python -m scripts.migrate_feature_state_json")
    return json.loads(blob)


def _state_tree(obj: Any) -> dict:
    """Instance attributes that are data; locks, sockets and clients are skipped."""
    out = {}
    for name, value in vars(obj).items():
        try:
            out[name] = _encode(value)
        except TypeError:
            continue
    return out


def _tree_of(namespace: str, key: str) -> Any:
    kind, holder = _holders[namespace]
    if kind == "per_user":
        instances = object.__getattribute__(holder, "_instances")
        return _state_tree(instances[key]) if key in instances else None
    if dict.__contains__(holder, key):
        return _encode(dict.__getitem__(holder, key))
    return None


def _apply(namespace: str, key: str, tree: Any) -> None:
    """Make memory hold tree for this row; None removes it."""
    global _restoring
    kind, holder = _holders[namespace]
    was, _restoring = _restoring, True
    try:
        if kind == "per_user":
            instances = object.__getattribute__(holder, "_instances")
            if tree is None:
                instances.pop(key, None)
            else:
                instance = object.__getattribute__(holder, "_factory")()
                vars(instance).update({k: _decode(v) for k, v in tree.items()})
                instances[key] = instance
        elif tree is None:
            dict.pop(holder, key, None)
        else:
            dict.__setitem__(holder, key, _decode(tree))
    finally:
        _restoring = was


def _install(namespace: str, key: str, payload: bytes, seq: Optional[int]) -> None:
    tree = _open(namespace, key, payload)
    _rows[(namespace, key)] = _Row(seq, tree, _digest(tree))
    if tree is not None:
        _apply(namespace, key, tree)


def _ensure(namespace: str, key: str) -> None:
    """Read a row this process has not seen yet."""
    if (namespace, key) in _rows or namespace in _full or namespace not in _holders:
        return
    found = _store().fetch_sync(namespace, key)
    if (namespace, key) not in _rows:
        _install(namespace, key, *(found or (b"", None)))


def _ensure_namespace(namespace: str) -> None:
    if namespace in _full or namespace not in _holders:
        return
    for key, payload, seq in _store().fetch_namespace_sync(namespace):
        if (namespace, key) not in _rows:
            _install(namespace, key, payload, seq)
    _full.add(namespace)


def ensure_user(namespace: str, user_id: str) -> None:
    """Called by a per-user proxy before it hands out a user's instance."""
    _ensure(namespace, user_id)


async def prefetch_user(user_id: str) -> None:
    """Read every row keyed by this user in one query, so the request finds them in memory."""
    if not user_id or all((ns, user_id) in _rows or ns in _full for ns in _holders):
        return
    found = {ns: (payload, seq) for ns, payload, seq in await _store().fetch_key(user_id)}
    for ns in list(_holders):
        if (ns, user_id) not in _rows and ns not in _full:
            _install(ns, user_id, *found.get(ns, (b"", None)))


async def _load_everything() -> None:
    """Every stored row of every registered holder; erasure and export walk all of it."""
    for ns, key, payload, seq in await _store().load_all():
        if ns in _holders and (ns, key) not in _rows and ns not in _full:
            _install(ns, key, payload, seq)
    _full.update(_holders)


async def sync() -> int:
    """Apply what other processes wrote since the last call. Returns rows applied."""
    global _seen_seq
    now = _time.monotonic()
    for seq in [s for s, t in _gaps.items() if now - t > _GAP_SECONDS]:
        del _gaps[seq]
    applied = 0
    for ns, key, payload, seq in await _store().changes(_seen_seq, sorted(_gaps)):
        _gaps.pop(seq, None)
        if seq > _seen_seq:
            for missing in range(_seen_seq + 1, seq):
                _gaps.setdefault(missing, now)
            _seen_seq = seq
        row = _rows.get((ns, key))
        if ns not in _holders or (row is None and ns not in _full):
            continue
        if row is not None and row.seq is not None and seq <= row.seq:
            continue
        tree = _open(ns, key, payload)
        fresh = _Row(seq, tree, _digest(tree))
        if (ns, key) in _touched:
            _deferred[(ns, key)] = fresh
            continue
        _rows[(ns, key)] = fresh
        if row is None or fresh.digest != row.digest:
            _apply(ns, key, tree)
        applied += 1
    return applied


async def start() -> None:
    """Begin following the store from its current end; rows load on demand from here on."""
    global _seen_seq
    _seen_seq = await _store().max_seq()


# ── Writing back ────────────────────────────────────────────────────────────

_flush_lock = asyncio.Lock()


async def _write(namespace: str, key: str, row: _Row, tree: Any) -> bool:
    """Store tree over row, merging with whatever another process wrote since. True if a write happened."""
    aad = _aad(namespace, key)
    base, expected = row.tree, row.seq
    for _ in range(10):
        payload = b"" if tree is None else crypto.seal(_bytes(tree), aad)
        seq, current = await _store().write(namespace, key, payload, expected)
        if seq is not None:
            _rows[(namespace, key)] = _Row(seq, tree, _digest(tree))
            return True
        their_payload, their_seq = current
        theirs = _open(namespace, key, their_payload)
        merged = _merge(base, tree, theirs)
        if merged != tree:
            _apply(namespace, key, merged)
        if merged == theirs:
            _rows[(namespace, key)] = _Row(their_seq, theirs, _digest(theirs))
            return False
        base, expected, tree = theirs, their_seq, merged
    raise RuntimeError(f"feature_state {namespace}/{key} kept changing under concurrent writes")


async def flush() -> int:
    """Write back every touched row whose content changed. Returns rows written."""
    async with _flush_lock:
        with _touched_lock:
            pending = list(_touched)
            _touched.clear()
        written = 0
        for namespace, key in pending:
            if namespace not in _holders:
                continue
            try:
                tree = _tree_of(namespace, key)
            except Exception as exc:
                logger.error("feature_state %s/%s not saved: %s", namespace, key, exc)
                continue
            row = _rows.get((namespace, key)) or _Row(None, None, None)
            remote = _deferred.pop((namespace, key), None)
            if _digest(tree) == row.digest:
                if remote is not None:
                    _rows[(namespace, key)] = remote
                    _apply(namespace, key, remote.tree)
                continue
            written += await _write(namespace, key, row, tree)
        return written


# ── Erasure and export ──────────────────────────────────────────────────────
# A record belongs to a user when it is keyed by their id or any of its string
# fields equals it; user ids are UUIDs, so a collision with reference data is
# not a practical concern.

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
    """Per holder, what the module and service stores (and, with remove, other users' state) hold for uid."""
    # Stores keyed by record id (goal_id, share_id) follow a removed record; a
    # second pass catches stores walked before the one holding the owner.
    ids: set = set()
    out: Dict[str, list] = {}
    for _ in range(2):
        if not remove:
            out = {}
        for namespace, (kind, holder) in _holders.items():
            found: list = []
            if kind == "dict":
                before = set(dict.keys(holder))
                _walk(holder, uid, remove, found, ids)
                for key in before:
                    touch(namespace, str(key))
            elif remove:
                for other, instance in list(object.__getattribute__(holder, "_instances").items()):
                    if other != uid:
                        before = len(found)
                        _walk(vars(instance), uid, True, found, None)
                        if len(found) > before:
                            touch(namespace, other)
            if found:
                out.setdefault(namespace, []).extend(found)
    return out


async def export_shared(user_id: str) -> Dict[str, Any]:
    """What the module and service stores hold for one user, as plain data."""
    from app.core.per_user import _plain
    await _load_everything()
    return {ns: _plain(items) for ns, items in _sweep(user_id, remove=False).items()}


def _aad(namespace: str, key: str) -> bytes:
    return f"feature_state/{namespace}/{key}".encode()


async def reseal_all() -> int:
    """Re-encrypt every stored row not already under the active key. Returns rows rewritten."""
    active = crypto.active_key_id()
    rows = []
    for namespace, key, sealed, _seq in await _store().load_all():
        if sealed and crypto.key_id_of(sealed) != active:
            aad = _aad(namespace, key)
            rows.append((namespace, key, crypto.seal(crypto.open_sealed(sealed, aad), aad)))
    if rows:
        await _store().put(rows)
    return len(rows)


async def erase_user(user_id: str) -> None:
    """Drop everything held for a user: their own rows, and their records inside everyone else's."""
    await _load_everything()
    for kind, holder in _holders.values():
        if kind == "per_user":
            holder.reset(user_id)
    _sweep(user_id, remove=True)
    await forget(user_id)
    await flush()


async def forget(user_id: str) -> None:
    """Delete every row keyed by this account, in every process."""
    for namespace, seq in await _store().tombstone_key(user_id):
        _rows[(namespace, user_id)] = _Row(seq, None, None)
        if namespace in _holders:
            _apply(namespace, user_id, None)


def _reset_for_tests() -> None:
    global _backend, _seen_seq
    _backend = None
    _seen_seq = 0
    _rows.clear()
    _full.clear()
    _deferred.clear()
    _gaps.clear()
    _touched.clear()

"""
Security audit log: sign-ins, session changes, exports, erasure, consent, admin
access to another user's records, sharing and vault use.

Durable (the `security_audit` table, or SQLite beside feature state) and kept
for 1 year, as the DPDP Rules and the privacy policy require. Entries carry
account ids, never health records; an email that matches no account is stored
only as a keyed hash so repeated attempts can still be grouped.
"""
import hashlib
import hmac
import json
import logging
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

RETENTION_SECONDS = 365 * 86400


def email_hash(email: str) -> str:
    from app.core.auth import SECRET_KEY

    return hmac.new(SECRET_KEY.encode(), email.strip().lower().encode(), hashlib.sha256).hexdigest()[:16]


class _SQLite:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.execute("CREATE TABLE IF NOT EXISTS security_audit (at REAL, event TEXT, user_id TEXT, "
                         "actor_id TEXT, ip TEXT, details TEXT)")
        self._db.execute("CREATE INDEX IF NOT EXISTS security_audit_user ON security_audit (user_id, at)")
        self._lock = threading.Lock()

    async def add(self, row):
        with self._lock, self._db:
            self._db.execute("INSERT INTO security_audit VALUES (?, ?, ?, ?, ?, ?)", row)

    async def query(self, user_id: Optional[str], limit: int):
        sql = "SELECT at, event, user_id, actor_id, ip, details FROM security_audit"
        args: list = []
        if user_id:
            sql += " WHERE user_id = ? OR actor_id = ?"
            args = [user_id, user_id]
        with self._lock:
            return self._db.execute(sql + " ORDER BY at DESC LIMIT ?", (*args, limit)).fetchall()

    async def purge(self, before: float) -> int:
        with self._lock, self._db:
            return self._db.execute("DELETE FROM security_audit WHERE at < ?", (before,)).rowcount


class _Postgres:
    async def _pool(self):
        from app.core.db import get_pool
        return await get_pool()

    async def add(self, row):
        pool = await self._pool()
        async with pool.acquire() as conn:
            await conn.execute("INSERT INTO security_audit (at, event, user_id, actor_id, ip, details) "
                               "VALUES (to_timestamp($1), $2, $3, $4, $5, $6)", *row)

    async def query(self, user_id: Optional[str], limit: int):
        pool = await self._pool()
        sql = "SELECT extract(epoch FROM at) AS at, event, user_id, actor_id, ip, details FROM security_audit"
        async with pool.acquire() as conn:
            if user_id:
                rows = await conn.fetch(sql + " WHERE user_id = $1 OR actor_id = $1 ORDER BY at DESC LIMIT $2",
                                        user_id, limit)
            else:
                rows = await conn.fetch(sql + " ORDER BY at DESC LIMIT $1", limit)
        return [tuple(r.values()) for r in rows]

    async def purge(self, before: float) -> int:
        pool = await self._pool()
        async with pool.acquire() as conn:
            status = await conn.execute("DELETE FROM security_audit WHERE at < to_timestamp($1)", before)
        return int(status.split()[-1])


_backend = None


def _store():
    global _backend
    if _backend is None:
        from app.core.config import settings
        if settings.DATABASE_URL:
            _backend = _Postgres()
        else:
            from app.core.storage import DATA_DIR
            _backend = _SQLite(Path(os.getenv("ADAPFIT_DATA_DIR") or DATA_DIR) / "security_audit.sqlite3")
    return _backend


async def record(event: str, user_id: str = "", actor_id: str = "", ip: str = "", **details) -> None:
    """Append one event. A failed write is logged, never raised: auditing must not break sign-in."""
    row = (time.time(), event, user_id or "", actor_id or user_id or "", ip or "", json.dumps(details, default=str))
    try:
        await _store().add(row)
    except Exception:
        logger.exception("security audit write failed: %s", event)


async def entries(user_id: Optional[str] = None, limit: int = 100) -> List[dict]:
    """Newest first; with a user id, events about that account or done by it."""
    limit = max(1, min(int(limit), 1000))
    return [{"at": float(at), "event": event, "user_id": uid, "actor_id": actor, "ip": ip,
             "details": json.loads(details or "{}")}
            for at, event, uid, actor, ip, details in await _store().query(user_id, limit)]


async def purge_expired(now: Optional[float] = None) -> int:
    return await _store().purge((now or time.time()) - RETENTION_SECONDS)


def _reset_for_tests() -> None:
    global _backend
    _backend = None

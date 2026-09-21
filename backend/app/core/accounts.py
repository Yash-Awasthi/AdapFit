"""
Durable account storage.

Registrations used to live only in the API process, so a restart deleted every
account. Accounts are written here on every change: to the `users` table when
a database is configured, and to a JSON file beside the in-memory store
otherwise, so local development survives a restart too.

Credentials are already hashed by the time they arrive; this layer never sees
a plaintext password.
"""
import json
import os
import stat
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings

ACCOUNTS_FILE = Path(__file__).resolve().parent.parent / "data" / "accounts.json"

# Columns on `users` that carry an account rather than a fitness profile.
_ACCOUNT_COLUMNS = (
    "id", "email", "username", "password_hash", "display_name", "avatar_url",
    "date_of_birth", "gender", "height_cm", "weight_kg", "units", "role",
    "is_active", "last_login",
)


def use_database() -> bool:
    return bool(settings.DATABASE_URL)


class AccountStore:
    """Load and persist account records. Postgres when configured, JSON file otherwise."""

    async def load_all(self) -> List[Dict[str, Any]]:
        if use_database():
            from app.core.db import get_pool

            pool = await get_pool()
            if pool is None:
                return self._read_file()
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    f"SELECT {', '.join(_ACCOUNT_COLUMNS)} FROM users WHERE password_hash IS NOT NULL"
                )
            return [_from_row(dict(r)) for r in rows]
        return self._read_file()

    async def save(self, account: Dict[str, Any]) -> None:
        if use_database():
            from app.core.db import get_pool

            pool = await get_pool()
            if pool is not None:
                await self._save_row(pool, account)
                return
        self._write_file_upsert(account)

    async def delete(self, user_id: str) -> None:
        if use_database():
            from app.core.db import get_pool

            pool = await get_pool()
            if pool is not None:
                async with pool.acquire() as conn:
                    await conn.execute("DELETE FROM users WHERE id = $1", _uuid(user_id))
                return
        rows = [a for a in self._read_file() if a.get("id") != user_id]
        self._write_file(rows)

    async def _save_row(self, pool, account: Dict[str, Any]) -> None:
        from app.core.repository import _to_pg

        data = _to_row(account)
        cols = [c for c in _ACCOUNT_COLUMNS if c in data]
        values = [_to_pg(c, data[c]) for c in cols]
        placeholders = ", ".join(f"${i + 1}" for i in range(len(cols)))
        updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c != "id")
        async with pool.acquire() as conn:
            await conn.execute(
                f"INSERT INTO users ({', '.join(cols)}) VALUES ({placeholders}) "
                f"ON CONFLICT (id) DO UPDATE SET {updates}",
                *values,
            )

    # ── JSON fallback ────────────────────────────────────────────────────
    def _read_file(self) -> List[Dict[str, Any]]:
        if not ACCOUNTS_FILE.exists():
            return []
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (ValueError, OSError):
            return []

    def _write_file(self, accounts: List[Dict[str, Any]]) -> None:
        ACCOUNTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = ACCOUNTS_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(accounts, f, indent=2)
        # Password hashes: readable by the owner only, and never world-readable
        # even for the moment between write and chmod.
        try:
            os.chmod(tmp, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass
        os.replace(tmp, ACCOUNTS_FILE)

    def _write_file_upsert(self, account: Dict[str, Any]) -> None:
        accounts = [a for a in self._read_file() if a.get("id") != account.get("id")]
        accounts.append(account)
        self._write_file(accounts)


def _uuid(value: str):
    import uuid

    try:
        return uuid.UUID(str(value))
    except ValueError:
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"adapfit.user.{value}")


def _to_row(account: Dict[str, Any]) -> Dict[str, Any]:
    """Account dict to database column names."""
    row = {k: v for k, v in account.items() if k in _ACCOUNT_COLUMNS}
    if "height" in account:
        row["height_cm"] = account["height"] or None
    if "weight" in account:
        row["weight_kg"] = account["weight"] or None
    if account.get("last_login"):
        from datetime import datetime, timezone

        row["last_login"] = datetime.fromtimestamp(float(account["last_login"]), tz=timezone.utc)
    else:
        row["last_login"] = None
    for key in ("avatar_url", "date_of_birth", "gender"):
        row.setdefault(key, account.get(key) or None)
    return row


def _from_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Database row to the account dict shape UserManager works in."""
    out = dict(row)
    out["id"] = str(out["id"])
    out["height"] = float(out.pop("height_cm") or 0)
    out["weight"] = float(out.pop("weight_kg") or 0)
    last_login = out.get("last_login")
    out["last_login"] = last_login.timestamp() if last_login else 0
    for key in ("email", "username", "display_name", "avatar_url", "date_of_birth", "gender", "units", "role"):
        out[key] = out.get(key) or ("metric" if key == "units" else "user" if key == "role" else "")
    out["is_active"] = bool(out.get("is_active", True))
    return out


class SessionStore:
    """
    The set of refresh tokens that are still valid.

    An allowlist rather than a denylist: a token that is not here is refused,
    so losing the store logs people out instead of resurrecting tokens someone
    has already signed out of. Only the SHA-256 of each token is kept.
    """

    async def load_all(self) -> Dict[str, float]:
        """token_hash -> expiry, with expired entries dropped."""
        now = _now()
        if use_database():
            from app.core.db import get_pool

            pool = await get_pool()
            if pool is not None:
                async with pool.acquire() as conn:
                    await conn.execute("DELETE FROM user_sessions WHERE expires_at < NOW()")
                    rows = await conn.fetch("SELECT token_hash, expires_at FROM user_sessions")
                return {r["token_hash"]: r["expires_at"].timestamp() for r in rows}
        return {h: e for h, e in _read_json(SESSIONS_FILE, {}).items() if e > now}

    async def add(self, token_hash: str, user_id: str, expires_at: float) -> None:
        if use_database():
            from app.core.db import get_pool
            from datetime import datetime, timezone

            pool = await get_pool()
            if pool is not None:
                async with pool.acquire() as conn:
                    await conn.execute(
                        "INSERT INTO user_sessions (token_hash, user_id, expires_at) VALUES ($1, $2, $3) "
                        "ON CONFLICT (token_hash) DO UPDATE SET expires_at = EXCLUDED.expires_at",
                        token_hash, _uuid(user_id), datetime.fromtimestamp(expires_at, tz=timezone.utc),
                    )
                return
        sessions = _read_json(SESSIONS_FILE, {})
        sessions[token_hash] = expires_at
        now = _now()
        _write_json(SESSIONS_FILE, {h: e for h, e in sessions.items() if e > now})

    async def remove(self, token_hash: str) -> None:
        if use_database():
            from app.core.db import get_pool

            pool = await get_pool()
            if pool is not None:
                async with pool.acquire() as conn:
                    await conn.execute("DELETE FROM user_sessions WHERE token_hash = $1", token_hash)
                return
        sessions = _read_json(SESSIONS_FILE, {})
        sessions.pop(token_hash, None)
        _write_json(SESSIONS_FILE, sessions)


SESSIONS_FILE = ACCOUNTS_FILE.with_name("sessions.json")


def _now() -> float:
    import time

    return time.time()


def _read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (ValueError, OSError):
        return default


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    try:
        os.chmod(tmp, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
    os.replace(tmp, path)


account_store = AccountStore()
session_store = SessionStore()


def reset_for_tests() -> None:
    """Drop the JSON fallback files. Used by tests that need a clean account set."""
    for path in (ACCOUNTS_FILE, SESSIONS_FILE):
        if path.exists():
            path.unlink()

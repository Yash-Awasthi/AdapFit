"""
Rate limiting: a token bucket per caller and route class, kept in the database.

The caller is the account when the request carries a valid token, otherwise the
client address. Behind a proxy the address is only right when uvicorn trusts the
proxy's X-Forwarded-For (FORWARDED_ALLOW_IPS); otherwise every client shares one bucket.

Buckets live in Postgres (or a SQLite file without DATABASE_URL) and each take
is one locked read-modify-write, so every worker draws from the same bucket and
a limit means the same with one worker or ten.
"""
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Optional

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.auth import decode_token

# (path prefixes, capacity, tokens per second, name[, methods]). First match wins.
# A prefix ending in "$" matches that path only.
RULES = (
    # Generous per address: carrier-grade NAT puts many phones behind one IP. The per-email
    # lockout in UserManager is what stops guessing one account's password.
    (("/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/forgot-password", "/api/v1/auth/reset-password",
      "/api/v1/privacy/guardian/"), 30, 30 / 300, "auth"),
    (("/api/v1/auth/change-password", "/api/v1/auth/delete-account"), 10, 10 / 300, "account"),
    (("/api/v1/chat", "/api/v1/ai-coach", "/api/v1/diet/photo-log", "/api/v1/voice-engine", "/api/v1/voice",
      "/api/v1/memory", "/api/v1/misinformation", "/api/v1/meal-photo"), 20, 20 / 300, "ai"),
    (("/api/v1/export", "/api/v1/encryption/key/rotate"), 5, 5 / 600, "export"),
    (("/api/v1/client-errors",), 10, 10 / 600, "crash"),
    (("/api/v1/mental-health$",), 20, 20 / 60, "mood", ("POST",)),
    (("/api/v1/trends/nlp/parse-goals",), 10, 10 / 60, "nlp-goals"),
    (("/api/v1/trends/nlp/sentiment",), 30, 30 / 60, "nlp-sentiment"),
    (("/api/v1/trends/nlp/feedback",), 30, 30 / 60, "nlp-feedback"),
    (("/api/v1/",), 180, 3.0, "api"),
    (("/health$",), 30, 30 / 60, "health"),
)
# Every rule refills completely well within this, so older rows are full buckets and can go.
_IDLE_SECONDS = 3600
_PRUNE_EVERY = 600


def _matches(path: str, prefix: str) -> bool:
    return path == prefix[:-1] if prefix.endswith("$") else path.startswith(prefix)


def _rule(path: str, method: str = "GET") -> Optional[tuple]:
    for prefixes, capacity, rate, name, *methods in RULES:
        if methods and method not in methods[0]:
            continue
        if any(_matches(path, p) for p in prefixes):
            return capacity, rate, name
    return None


def _refill(tokens: float, updated: float, capacity: int, rate: float, now: float) -> tuple[float, float]:
    """(tokens after this take, 0 when allowed or seconds to wait)."""
    tokens = min(capacity, tokens + max(0.0, now - updated) * rate)
    if tokens >= 1:
        return tokens - 1, 0.0
    return tokens, (1 - tokens) / rate


class _SQLiteBuckets:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), check_same_thread=False, timeout=30, isolation_level=None)
        self._db.execute("CREATE TABLE IF NOT EXISTS rate_limit_buckets "
                         "(key TEXT PRIMARY KEY, tokens REAL NOT NULL, updated_at REAL NOT NULL)")
        self._lock = threading.Lock()

    async def take(self, key: str, capacity: int, rate: float, now: float) -> float:
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                row = self._db.execute("SELECT tokens, updated_at FROM rate_limit_buckets WHERE key = ?",
                                       (key,)).fetchone()
                tokens, wait = _refill(*(row or (capacity, now)), capacity, rate, now)
                self._db.execute("INSERT INTO rate_limit_buckets (key, tokens, updated_at) VALUES (?, ?, ?) "
                                 "ON CONFLICT(key) DO UPDATE SET tokens = excluded.tokens, "
                                 "updated_at = excluded.updated_at", (key, tokens, now))
                self._db.execute("COMMIT")
            except BaseException:
                self._db.execute("ROLLBACK")
                raise
        return wait

    async def prune(self, before: float) -> None:
        with self._lock:
            self._db.execute("DELETE FROM rate_limit_buckets WHERE updated_at < ?", (before,))


class _PostgresBuckets:
    async def take(self, key: str, capacity: int, rate: float, now: float) -> float:
        from app.core.db import get_pool

        async with (await get_pool()).acquire() as conn:
            async with conn.transaction():
                await conn.execute("INSERT INTO rate_limit_buckets (key, tokens, updated_at) VALUES ($1, $2, $3) "
                                   "ON CONFLICT (key) DO NOTHING", key, float(capacity), now)
                row = await conn.fetchrow("SELECT tokens, updated_at FROM rate_limit_buckets WHERE key = $1 "
                                          "FOR UPDATE", key)
                tokens, wait = _refill(row["tokens"], row["updated_at"], capacity, rate, now)
                await conn.execute("UPDATE rate_limit_buckets SET tokens = $2, updated_at = $3 WHERE key = $1",
                                   key, tokens, now)
        return wait

    async def prune(self, before: float) -> None:
        from app.core.db import get_pool

        async with (await get_pool()).acquire() as conn:
            await conn.execute("DELETE FROM rate_limit_buckets WHERE updated_at < $1", before)


def _store():
    from app.core.config import settings

    if settings.DATABASE_URL:
        return _PostgresBuckets()
    from app.core.storage import DATA_DIR
    return _SQLiteBuckets(Path(os.getenv("ADAPFIT_DATA_DIR") or DATA_DIR) / "rate_limits.sqlite3")


def _caller(scope: Scope) -> str:
    for key, value in scope.get("headers", []):
        if key == b"authorization":
            raw = value.decode("latin-1")
            payload = decode_token(raw[7:]) if raw.startswith("Bearer ") else None
            if payload and payload.get("sub"):
                return "u:" + str(payload["sub"])
            break
    client = scope.get("client")
    return "ip:" + (client[0] if client else "unknown")


class RateLimitMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app
        self._buckets = None
        self._pruned = 0.0

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        rule = _rule(scope.get("path", ""), scope.get("method", "GET")) if scope["type"] == "http" else None
        if rule is None:
            await self.app(scope, receive, send)
            return
        capacity, rate, name = rule
        # Sign-in routes count by address even with a token, so a token cannot buy more guesses.
        who = _caller(scope) if name != "auth" else "ip:" + (scope.get("client") or ("unknown",))[0]
        if self._buckets is None:
            self._buckets = _store()
        now = time.time()
        wait = await self._buckets.take(f"{name}|{who}", capacity, rate, now)
        if now - self._pruned > _PRUNE_EVERY:
            self._pruned = now
            await self._buckets.prune(now - _IDLE_SECONDS)
        if wait:
            retry = str(max(1, int(wait + 0.999)))
            await JSONResponse(status_code=429, content={"detail": "Too many requests", "retry_after_seconds": int(retry)},
                               headers={"Retry-After": retry})(scope, receive, send)
            return
        await self.app(scope, receive, send)

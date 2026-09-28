"""
Rate limiting: a token bucket per caller and route class.

The caller is the account when the request carries a valid token, otherwise the
client address. Behind a proxy the address is only right when uvicorn trusts the
proxy's X-Forwarded-For (FORWARDED_ALLOW_IPS); otherwise every client shares one bucket.
"""
import time
from typing import Optional

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.auth import decode_token

# (path prefixes, capacity, tokens per second, name). First match wins.
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
    (("/api/v1/",), 180, 3.0, "api"),
)
MAX_BUCKETS = 50_000


class TokenBucket:
    __slots__ = ("capacity", "refill_rate", "tokens", "last_refill")

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()

    def consume(self) -> float:
        """0 when allowed, otherwise seconds until a token is available."""
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.last_refill) * self.refill_rate)
        self.last_refill = now
        if self.tokens >= 1:
            self.tokens -= 1
            return 0.0
        return (1 - self.tokens) / self.refill_rate


def _rule(path: str) -> Optional[tuple]:
    for prefixes, capacity, rate, name in RULES:
        if path.startswith(prefixes):
            return capacity, rate, name
    return None


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
        self._buckets: dict[tuple, TokenBucket] = {}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        rule = _rule(scope.get("path", "")) if scope["type"] == "http" else None
        if rule is None:
            await self.app(scope, receive, send)
            return
        capacity, rate, name = rule
        # Sign-in routes count by address even with a token, so a token cannot buy more guesses.
        who = _caller(scope) if name != "auth" else "ip:" + (scope.get("client") or ("unknown",))[0]
        key = (who, name)
        bucket = self._buckets.get(key)
        if bucket is None:
            if len(self._buckets) >= MAX_BUCKETS:
                self._prune()
            bucket = self._buckets[key] = TokenBucket(capacity, rate)
        wait = bucket.consume()
        if wait:
            retry = str(max(1, int(wait + 0.999)))
            await JSONResponse(status_code=429, content={"detail": "Too many requests", "retry_after_seconds": int(retry)},
                               headers={"Retry-After": retry})(scope, receive, send)
            return
        await self.app(scope, receive, send)

    def _prune(self) -> None:
        now = time.monotonic()
        self._buckets = {k: b for k, b in self._buckets.items()
                         if b.tokens + (now - b.last_refill) * b.refill_rate < b.capacity}
        if len(self._buckets) >= MAX_BUCKETS:
            self._buckets.clear()

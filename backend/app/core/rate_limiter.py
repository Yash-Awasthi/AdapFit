"""
Per-User Rate Limiter — Token Bucket Algorithm
"""
import time
from collections import defaultdict
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class TokenBucket:
    """Token bucket rate limiter per user."""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = capacity
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class PerUserRateLimiter(BaseHTTPMiddleware):
    """Rate limiter using token bucket algorithm, per IP."""

    # Endpoint-specific limits: (capacity, refill_rate)
    LIMITS = {
        "/api/v1/auth": (5, 0.1),        # 5 requests, refills ~1/10s
        "/api/v1/chat": (30, 0.5),       # 30 requests
        "/api/v1/camera": (60, 1.0),     # Camera needs high rate
        "/api/v1/location/point": (120, 2.0),  # GPS points need very high rate
        "/api/v1/summary": (10, 0.2),    # Dashboard endpoint
        "default": (60, 1.0),            # Default: 60 requests
    }

    def __init__(self, app):
        super().__init__(app)
        self._buckets: dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(60, 1.0)
        )

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        # Find matching rate limit
        limit_key = "default"
        for prefix, limits in self.LIMITS.items():
            if prefix != "default" and path.startswith(prefix):
                limit_key = prefix
                break

        bucket_key = f"{client_ip}:{limit_key}"
        capacity, refill = self.LIMITS.get(limit_key, self.LIMITS["default"])

        if bucket_key not in self._buckets:
            self._buckets[bucket_key] = TokenBucket(capacity, refill)

        bucket = self._buckets[bucket_key]
        if not bucket.consume():
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded", "retry_after_seconds": 1},
                headers={"Retry-After": "1"},
            )

        return await call_next(request)

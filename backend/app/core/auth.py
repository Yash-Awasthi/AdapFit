"""API key authentication with per-key rate limiting.

Supports:
- API key validation via X-API-Key header
- Per-key rate limiting (sliding window)
- Key rotation and revocation
- Optional JWT token support
"""

from __future__ import annotations
import time
import hashlib
import secrets
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional
from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass
class APIKey:
    key_hash: str
    name: str
    tier: str = "free"  # free, pro, enterprise
    rate_limit: int = 100  # requests per minute
    created_at: float = field(default_factory=time.time)
    last_used: float = 0.0
    is_active: bool = True


@dataclass
class SlidingWindowCounter:
    """Sliding window rate limiter per API key."""
    window_seconds: int = 60
    _requests: list[float] = field(default_factory=list)

    def is_allowed(self, max_requests: int) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds
        # Remove expired entries
        self._requests = [t for t in self._requests if t > cutoff]
        if len(self._requests) >= max_requests:
            return False
        self._requests.append(now)
        return True

    def current_usage(self) -> int:
        now = time.time()
        cutoff = now - self.window_seconds
        return len([t for t in self._requests if t > cutoff])


class APIKeyManager:
    """Manages API keys, validation, and rate limiting."""

    def __init__(self):
        self._keys: dict[str, APIKey] = {}
        self._windows: dict[str, SlidingWindowCounter] = defaultdict(SlidingWindowCounter)
        # Create default demo key
        self.create_key("demo", "free", 100)

    def create_key(self, name: str, tier: str = "free", rate_limit: int = 100) -> str:
        """Create a new API key and return the raw key."""
        raw_key = f"af_{secrets.token_hex(24)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        self._keys[key_hash] = APIKey(
            key_hash=key_hash,
            name=name,
            tier=tier,
            rate_limit=rate_limit,
        )
        return raw_key

    def validate_key(self, raw_key: str) -> Optional[APIKey]:
        """Validate an API key and check rate limits."""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key = self._keys.get(key_hash)

        if not key or not key.is_active:
            return None

        key.last_used = time.time()
        window = self._windows[key_hash]

        if not window.is_allowed(key.rate_limit):
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "tier": key.tier,
                    "limit": f"{key.rate_limit}/min",
                    "usage": window.current_usage(),
                    "retry_after": max(0, int(60 - (time.time() - (window._requests[0] if window._requests else 0)))),
                },
            )
        return key

    def revoke_key(self, raw_key: str) -> bool:
        """Revoke an API key."""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        if key_hash in self._keys:
            self._keys[key_hash].is_active = False
            return True
        return False

    def get_key_info(self, raw_key: str) -> Optional[dict]:
        """Get key info without exposing the hash."""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key = self._keys.get(key_hash)
        if not key:
            return None
        window = self._windows.get(key_hash)
        return {
            "name": key.name,
            "tier": key.tier,
            "rate_limit": key.rate_limit,
            "is_active": key.is_active,
            "current_usage": window.current_usage() if window else 0,
        }

    def list_keys(self) -> list[dict]:
        """List all keys (without hashes)."""
        return [
            {
                "name": k.name,
                "tier": k.tier,
                "rate_limit": k.rate_limit,
                "is_active": k.is_active,
                "last_used": k.last_used,
            }
            for k in self._keys.values()
        ]


# Global singleton
api_key_manager = APIKeyManager()


# ============================================================
# FastAPI Dependency
# ============================================================

async def require_api_key(
    request: Request,
    api_key: Optional[str] = Security(api_key_header),
) -> APIKey:
    """FastAPI dependency: require valid API key with rate limiting.

    Usage:
        @router.get("/endpoint")
        async def my_endpoint(key: APIKey = Depends(require_api_key)):
            ...
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-API-Key header. Get a key at /api/v1/auth/keys",
        )

    key_info = api_key_manager.validate_key(api_key)
    if not key_info:
        raise HTTPException(
            status_code=401,
            detail="Invalid or revoked API key",
        )
    return key_info

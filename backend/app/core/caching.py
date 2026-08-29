"""
TTL-Based In-Memory Cache for API Responses
"""
import time
from typing import Optional, Any
from functools import wraps


class TTLCache:
    """Simple TTL-based in-memory cache."""

    def __init__(self, default_ttl: int = 60):
        self._store: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        if key in self._store:
            value, expiry = self._store[key]
            if time.time() < expiry:
                self._hits += 1
                return value
            else:
                del self._store[key]
        self._misses += 1
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        ttl = ttl or self._default_ttl
        self._store[key] = (value, time.time() + ttl)

    def invalidate(self, key: str):
        self._store.pop(key, None)

    def clear(self):
        self._store.clear()

    def stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "entries": len(self._store),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / max(1, total) * 100, 1),
        }

    def cleanup(self):
        now = time.time()
        expired = [k for k, (_, exp) in self._store.items() if now >= exp]
        for k in expired:
            del self._store[k]


# Global cache instance
api_cache = TTLCache(default_ttl=60)

"""In-Memory Cache — LRU cache with TTL expiration for hot data.

Caches frequently accessed data like exercise catalogs, recommendations,
user profiles, and API responses. Reduces computation for repeated queries.

Ponytail: stdlib `functools.lru_cache` for simple cases, custom TTL dict for time-sensitive data.
"""

from __future__ import annotations
import time
import threading
from collections import OrderedDict
from typing import Optional, Any, Callable
from functools import wraps
import asyncio


class TTLCache:
    """Thread-safe LRU cache with per-entry TTL expiration."""

    def __init__(self, max_size: int = 256, default_ttl: float = 300.0):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                value, expires_at = self._cache[key]
                if expires_at > time.time():
                    self._cache.move_to_end(key)
                    self._hits += 1
                    return value
                else:
                    del self._cache[key]
            self._misses += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            elif len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
            self._cache[key] = (value, time.time() + (ttl or self.default_ttl))

    def delete(self, key: str):
        with self._lock:
            self._cache.pop(key, None)

    def clear(self):
        with self._lock:
            self._cache.clear()

    def cleanup(self):
        """Remove expired entries."""
        now = time.time()
        with self._lock:
            expired = [k for k, (_, exp) in self._cache.items() if exp <= now]
            for k in expired:
                del self._cache[k]

    @property
    def size(self) -> int:
        return len(self._cache)

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0

    def get_stats(self) -> dict:
        return {
            "size": self.size,
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self.hit_rate * 100, 1),
        }


# Global cache instances
exercises_cache = TTLCache(max_size=512, default_ttl=3600)  # Exercises change rarely
recommendations_cache = TTLCache(max_size=128, default_ttl=300)  # Recommendations refresh every 5min
user_profile_cache = TTLCache(max_size=256, default_ttl=600)  # User profiles 10min
api_response_cache = TTLCache(max_size=512, default_ttl=120)  # API responses 2min


def cached(ttl: float = 300, cache_key: str = ""):
    """Decorator: cache function result with TTL.

    Usage:
        @cached(ttl=600, cache_key="exercises:{category}")
        async def get_exercises(category: str):
            ...
    """
    def decorator(func):
        _cache = TTLCache(max_size=128, default_ttl=ttl)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Build cache key
            key = cache_key.format(**kwargs) if cache_key else f"{func.__name__}:{args}:{kwargs}"
            result = _cache.get(key)
            if result is not None:
                return result
            result = await func(*args, **kwargs)
            _cache.set(key, result)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            key = cache_key.format(**kwargs) if cache_key else f"{func.__name__}:{args}:{kwargs}"
            result = _cache.get(key)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            _cache.set(key, result)
            return result

        if asyncio.iscoroutinefunction(func):
            wrapper = async_wrapper
        else:
            wrapper = sync_wrapper

        wrapper.cache = _cache
        wrapper.invalidate = lambda: _cache.clear()
        return wrapper

    return decorator

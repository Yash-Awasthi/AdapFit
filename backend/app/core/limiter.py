"""
Shared rate limiter factory.

Returns a real slowapi Limiter when rate limiting is enabled,
or a no-op decorator passthrough when disabled (tests / dev).
"""
from app.core.config import settings


def make_limiter():
    """Create a rate limiter that respects the RATE_LIMITING_ENABLED config."""
    if not settings.RATE_LIMITING_ENABLED:
        class _NoopLimiter:
            def limit(self, *a, **kw):
                def decorator(fn):
                    return fn
                return decorator
        return _NoopLimiter()

    from slowapi import Limiter
    from slowapi.util import get_remote_address
    return Limiter(key_func=get_remote_address)

"""
Postgres connection pool (asyncpg), with pgvector codec registration.

When DATABASE_URL is unset, every function is a no-op returning None — the
in-memory store in app.core.database stays the working fallback.
"""
import logging

import asyncpg
from pgvector.asyncpg import register_vector

from app.core.config import settings

logger = logging.getLogger("adapfit.db")

_pool: asyncpg.Pool | None = None

# Flipped once on the first connection that cannot register the codec, so the
# warning is logged once rather than per connection.
_vector_available = True


async def _init_connection(conn: asyncpg.Connection) -> None:
    """
    Register the pgvector codec when the extension is present.

    Supabase and the pgvector image ship it; a stock Postgres does not, and
    there registration raises and every connection in the pool fails to open.
    Semantic exercise search falls back to its in-memory index without it,
    so the rest of the app stays usable.
    """
    try:
        await register_vector(conn)
    except Exception as exc:
        global _vector_available
        if _vector_available:
            logger.warning("pgvector not available (%s); vector columns are disabled.", exc)
        _vector_available = False


async def get_pool() -> asyncpg.Pool | None:
    """Return the shared connection pool, creating it lazily. None if DATABASE_URL is unset."""
    global _pool
    if not settings.DATABASE_URL:
        return None
    if _pool is None:
        # Supabase's session pooler allows 15 clients per project, shared across
        # every process pointing at it. asyncpg defaults to 10, so two processes
        # exhaust it. Transaction mode raises that ceiling but reuses server-side
        # connections between statements, which makes prepared statements unsafe.
        transaction_mode = ":6543" in settings.DATABASE_URL
        _pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            init=_init_connection,
            min_size=1,
            max_size=settings.DB_POOL_MAX_SIZE,
            statement_cache_size=0 if transaction_mode else 100,
        )
    return _pool


async def health_check() -> bool:
    """True if the database is reachable. False (never raises) if unset or unreachable."""
    if not settings.DATABASE_URL:
        return False
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception:
        return False


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None

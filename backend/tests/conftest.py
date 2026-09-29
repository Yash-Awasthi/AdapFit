"""
Test configuration — runs before any test module imports.

Sets env vars to:
  1. Disable rate limiting (avoids 429 during rapid test runs)
  2. Force in-memory storage (no DATABASE_URL / SUPABASE_URL)
  3. Disable auth middleware
  4. Keep every file the app writes inside a throwaway directory, so a run
     neither inherits a previous run's data nor edits the developer's own
"""
import asyncio
import os
import tempfile

# Must be set BEFORE any app module is imported — storage.py reads these
# at module level to decide postgres vs in-memory and where to write.
os.environ["DATABASE_URL"] = ""
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_KEY"] = ""
os.environ["RATE_LIMITING_ENABLED"] = "false"
os.environ["AUTH_DISABLED"] = "true"
os.environ["ADAPFIT_DATA_DIR"] = tempfile.mkdtemp(prefix="adapfit-test-data-")


def register_user(email: str, username: str, password: str = "Str0ngPassw0rd!", display_name: str = "") -> dict:
    """Register an account from synchronous test code."""
    from app.core.auth import user_manager

    consent = {"health_data": True, "ai": True, "sharing": True, "analytics": False}
    return asyncio.run(user_manager.register(email, username, password, display_name=display_name, birth_date="1990-01-01", consent=consent))


def iter_api_routes(app):
    """Flatten FastAPI's route tree to (path, methods, endpoint) triples.

    include_router no longer copies sub-routes into app.routes as flat APIRoutes;
    it mounts an _IncludedRouter wrapper, so a direct scan of app.routes misses
    almost everything. Recurse through each wrapper's included router, carrying
    the include prefix, to recover the real served paths.
    """
    from fastapi.routing import APIRoute

    def walk(routes, base=""):
        for r in routes:
            if isinstance(r, APIRoute):
                yield base + r.path, getattr(r, "methods", None) or set(), r.endpoint
            else:
                ctx = getattr(r, "include_context", None)
                if ctx is not None:
                    yield from walk(ctx.included_router.routes, base + (ctx.prefix or ""))

    yield from walk(app.routes)

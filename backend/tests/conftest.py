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


def register_user(email: str, username: str, password: str = "Str0ngPassw0rd!") -> dict:
    """Register an account from synchronous test code."""
    from app.core.auth import user_manager

    consent = {"health_data": True, "ai": True, "sharing": True, "analytics": False}
    return asyncio.run(user_manager.register(email, username, password, birth_date="1990-01-01", consent=consent))

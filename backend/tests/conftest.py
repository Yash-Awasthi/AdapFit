"""
Test configuration — runs before any test module imports.

Sets env vars to:
  1. Disable rate limiting (avoids 429 during rapid test runs)
  2. Force in-memory storage (no DATABASE_URL / SUPABASE_URL)
  3. Disable auth middleware
"""
import asyncio
import os
import tempfile
from pathlib import Path

# Must be set BEFORE any app module is imported — storage.py reads these
# at module level to decide postgres vs in-memory.
os.environ["DATABASE_URL"] = ""
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_KEY"] = ""
os.environ["RATE_LIMITING_ENABLED"] = "false"
os.environ["AUTH_DISABLED"] = "true"

import pytest

# Accounts persist to disk now. Point that file somewhere disposable so a test
# run neither inherits accounts from a previous run nor writes into app/data.
_ACCOUNTS_DIR = Path(tempfile.mkdtemp(prefix="adapfit-test-accounts-"))


@pytest.fixture(scope="session", autouse=True)
def _isolated_account_store():
    from app.core import accounts

    accounts.ACCOUNTS_FILE = _ACCOUNTS_DIR / "accounts.json"
    accounts.SESSIONS_FILE = _ACCOUNTS_DIR / "sessions.json"
    yield


def register_user(email: str, username: str, password: str = "Str0ngPassw0rd!") -> dict:
    """Register an account from synchronous test code."""
    from app.core.auth import user_manager

    return asyncio.run(user_manager.register(email, username, password))

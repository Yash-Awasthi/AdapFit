"""
Test configuration — runs before any test module imports.

Sets env vars to:
  1. Disable rate limiting (avoids 429 during rapid test runs)
  2. Force in-memory storage (no DATABASE_URL / SUPABASE_URL)
  3. Disable auth middleware
"""
import os

# Must be set BEFORE any app module is imported — storage.py reads these
# at module level to decide postgres vs in-memory.
os.environ["DATABASE_URL"] = ""
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_KEY"] = ""
os.environ["RATE_LIMITING_ENABLED"] = "false"
os.environ["AUTH_DISABLED"] = "true"

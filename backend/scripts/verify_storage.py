"""
Runnable check for the storage/repository rewrite (task W3).

With no DATABASE_URL and no SUPABASE_URL set, StorageEngine must stay on the
in-memory backend: write a recovery log and read it back unchanged, and confirm
get_stats reports the right backend label.

Run: python scripts/verify_storage.py
"""
import asyncio
import os
import sys
import uuid

# .env in this checkout sets SUPABASE_URL/KEY; pydantic-settings reads that file directly,
# so an empty string (not a pop) is what's needed to override it and force in-memory mode.
for _var in ("DATABASE_URL", "SUPABASE_URL", "SUPABASE_KEY"):
    os.environ[_var] = ""

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.storage import StorageEngine


async def main():
    storage = StorageEngine()
    # unique per run: the in-memory backend persists to store.json across runs,
    # and a fixed id would accumulate log entries from earlier invocations.
    user_id = f"verify-storage-{uuid.uuid4()}"

    log = {"hrv_rmssd": 55.5, "sleep_score": 82, "sleep_duration_hours": 7.5, "readiness_state": "OPTIMAL"}
    saved = await storage.add_recovery_log(user_id, dict(log))
    assert saved["hrv_rmssd"] == log["hrv_rmssd"]
    assert "id" in saved and "created_at" in saved

    fetched = await storage.get_recovery_logs(user_id, days=28)
    assert len(fetched) == 1
    assert fetched[0]["hrv_rmssd"] == log["hrv_rmssd"]
    assert fetched[0]["sleep_score"] == log["sleep_score"]

    sleep_logs = await storage.get_sleep_logs(user_id, days=28)
    assert len(sleep_logs) == 1
    assert sleep_logs[0]["sleep_score"] == log["sleep_score"]

    stats = await storage.get_stats()
    assert stats["backend"] == "in_memory", stats

    print("OK: recovery log round-trips through in-memory storage; backend =", stats["backend"])


if __name__ == "__main__":
    asyncio.run(main())

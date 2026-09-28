"""Training analytics count only sessions with a recorded RPE."""
import asyncio
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.core.storage import storage
from app.main import app

c = TestClient(app)


def _log(uid, days_ago, rpe, minutes):
    when = (datetime.now() - timedelta(days=days_ago)).isoformat()
    entry = {"completed_at": when, "actual_duration_minutes": minutes}
    if rpe is not None:
        entry["session_rpe"] = rpe
    asyncio.run(storage.add_workout_log(uid, entry))


def test_form_ignores_sessions_without_rpe():
    uid = "train-form"
    for d in range(20, 0, -2):
        _log(uid, d, 6, 50)
    _log(uid, 1, None, 60)
    r = c.get(f"/api/v1/training/form?user_id={uid}&days=30").json()
    assert r["sessions_used"] == 10 and r["sessions_without_rpe"] == 1
    assert r["today"]["fitness"] > 0 and "zone" in r["today"]


def test_intensity_split_by_rpe():
    uid = "train-tid"
    for d, rpe in ((1, 3), (2, 3), (3, 3), (4, 8)):
        _log(uid, d, rpe, 60)
    r = c.get(f"/api/v1/training/intensity?user_id={uid}").json()
    assert r["distribution"] == {"easy": 75.0, "moderate": 0.0, "hard": 25.0}


def test_no_sessions_means_no_curves():
    r = c.get("/api/v1/training/form?user_id=train-none").json()
    assert r["series"] == [] and r["today"] is None


def test_ride_fueling_plan():
    r = c.post("/api/v1/training/ride-fueling", json={"duration_hours": 3.5, "ride_type": "long_ride"}).json()
    assert r["carbs_per_hour_g"] >= 60 and r["gels"] > 0

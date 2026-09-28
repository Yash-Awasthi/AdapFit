"""Recorded routes: GPS noise and jumps do not add distance, and a finished run lands in history once."""
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)
T0 = datetime(2026, 9, 1, 6, 0, tzinfo=timezone.utc)


def _pt(sec, lat, lon, acc=5.0, alt=None):
    return {"lat": lat, "lon": lon, "accuracy_m": acc, "altitude": alt, "timestamp": (T0 + timedelta(seconds=sec)).isoformat()}


def test_a_run_ignores_bad_fixes_and_is_saved_once():
    rid = c.post("/api/v1/gps/start", json={"workout_type": "running"}).json()["route_id"]
    # ~1.11 km due north in 5 minutes, one 200 m-accuracy fix and one 5 km teleport in between.
    pts = [_pt(i * 30, 12.9700 + i * 0.001, 77.5900, alt=900 + i) for i in range(11)]
    pts.insert(3, _pt(65, 12.99, 77.60, acc=200))
    pts.insert(6, _pt(125, 13.02, 77.59))
    live = c.post(f"/api/v1/gps/{rid}/points", json={"coordinates": pts}).json()["live_stats"]
    assert 1080 < live["distance_m"] < 1140 and live["coordinates_used"] == 11
    assert live["elevation_gain_m"] == 9  # 10 m of 1 m steps, counted in 3 m steps
    done = c.post(f"/api/v1/gps/{rid}/finish").json()
    assert done["saved_to_history"] and done["stats"]["duration_seconds"] == 300
    assert c.post(f"/api/v1/gps/{rid}/finish").json()["saved_to_history"] is False
    assert c.post(f"/api/v1/gps/{rid}/points", json={"coordinates": pts[:1]}).json()["error"]


def test_standing_still_adds_no_distance():
    rid = c.post("/api/v1/gps/start", json={"workout_type": "running"}).json()["route_id"]
    jitter = [_pt(i * 5, 12.97 + (i % 2) * 0.0003, 77.59, acc=40) for i in range(20)]
    stats = c.post(f"/api/v1/gps/{rid}/points", json={"coordinates": jitter}).json()["live_stats"]
    assert stats["distance_m"] == 0

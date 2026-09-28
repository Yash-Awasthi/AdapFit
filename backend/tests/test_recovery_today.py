"""The recovery dashboard explains the check-in score; it does not compute another."""
from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)


def _checkin(uid, day, hrv):
    return c.post("/api/v1/recovery-logs", json={
        "user_id": uid, "log_date": f"2026-05-{day:02d}",
        "wearable_data": {"hrv_rmssd": hrv, "sleep_duration_hours": 7.5, "sleep_efficiency_pct": 90, "resting_heart_rate": 55},
        "subjective_checkin": {"soreness": 3, "fatigue": 3, "stress": 3},
    })


def test_no_checkin_means_no_score():
    today = c.get("/api/v1/recovery-logs/today?user_id=rt-empty").json()
    assert today["overall_score"] is None and today["domains"] == []


def test_dashboard_score_is_the_checkin_score():
    for day in range(1, 5):
        _checkin("rt-user", day, 50 + day)
    score = _checkin("rt-user", 5, 60).json()["recovery_score"]
    today = c.get("/api/v1/recovery-logs/today?user_id=rt-user").json()
    assert today["overall_score"] == score
    hrv = next(d for d in today["domains"] if d["name"] == "hrv")
    assert hrv["data_available"] and "your normal" in hrv["insight"]
    assert today["recommendations"][0]["category"] == "training"


def test_the_population_threshold_engine_is_gone():
    assert c.get("/api/v1/recovery-v2/quick").status_code == 404

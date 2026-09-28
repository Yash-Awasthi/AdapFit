"""The coach speaks from the user's records or says what is missing."""
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from tests.conftest import register_user

c = TestClient(app)


@pytest.fixture(autouse=True)
def _auth_enforced(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_DISABLED", False)


def _headers(name):
    result = register_user(f"{name}@example.com", name)
    return {"Authorization": f"Bearer {result['tokens']['access_token']}"}


def test_a_new_user_gets_no_invented_insights():
    h = _headers("coach-new")
    b = c.get("/api/v1/ai-coach/briefing", headers=h).json()
    assert b["today"] is None and b["insights"] == []
    assert any("check-in" in m for m in b["to_unlock"])
    assert c.get("/api/v1/ai-coach/weekly-report", headers=h).json()["status"] == "insufficient_data"


def test_a_checkin_produces_todays_call_with_its_score():
    h = _headers("coach-checkin")
    r = c.post("/api/v1/recovery-logs", headers=h, json={
        "user_id": "bound-by-server", "log_date": date.today().isoformat(),
        "wearable_data": {"hrv_rmssd": 60, "sleep_duration_hours": 7.5, "sleep_efficiency_pct": 90, "resting_heart_rate": 55},
        "subjective_checkin": {"soreness": 2, "fatigue": 2, "stress": 2},
    })
    assert r.status_code == 201, r.text
    score = r.json()["recovery_score"]
    b = c.get("/api/v1/ai-coach/briefing", headers=h).json()
    assert b["today"] is not None and str(score) in b["today"]["message"]
    report = c.get("/api/v1/ai-coach/weekly-report", headers=h).json()
    assert report["status"] == "ok" and report["figures"]["checkins"] == 1


def test_the_old_invented_routes_are_gone():
    h = _headers("coach-gone")
    for path in ("/api/v1/ai-coach/health-risks", "/api/v1/ai-coach/daily-insight", "/api/v1/ai-assistant/tips"):
        assert c.get(path, headers=h).status_code == 404


def test_personal_pattern_needs_a_real_difference():
    from app.services.ai_coach import personal_patterns

    nights = [{"date": f"2026-07-{d:02d}", "total_minutes": (480 if d % 2 else 360)} for d in range(1, 15)]
    moods = [{"mood": (8 if d % 2 else 5), "logged_at": f"2026-07-{d:02d}T20:00:00"} for d in range(1, 15)]
    found = personal_patterns([], moods, nights)
    assert found and "mood tracks your sleep" in found[0]["title"].lower()

    flat = [{"mood": 6, "logged_at": f"2026-07-{d:02d}T20:00:00"} for d in range(1, 15)]
    assert personal_patterns([], flat, nights) == []

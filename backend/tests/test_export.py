"""Exports contain the caller's real records, including per-user feature data."""
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from tests.conftest import register_user

c = TestClient(app)


@pytest.fixture(autouse=True)
def _auth_enforced(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_DISABLED", False)


def test_sleep_and_checkins_are_in_the_export():
    h = {"Authorization": f"Bearer {register_user('export@example.com', 'exporter')['tokens']['access_token']}"}
    c.post("/api/v1/sleep/logs", headers=h, json={"bedtime": "23:00", "wake_time": "06:30"})
    c.post("/api/v1/recovery-logs", headers=h, json={
        "user_id": "bound", "log_date": "2026-06-01",
        "wearable_data": {"hrv_rmssd": 55, "sleep_duration_hours": 7.5, "sleep_efficiency_pct": 90, "resting_heart_rate": 58},
        "subjective_checkin": {"soreness": 3, "fatigue": 3, "stress": 3},
    })
    everything = c.get("/api/v1/export/all", headers=h).json()["data"]
    assert len(everything["sleep"]) == 1 and len(everything["recovery"]) == 1
    assert "sleep_tracker.sleep_journal" in everything["feature_data"]
    csv = c.get("/api/v1/export/recovery?format=csv", headers=h).text
    assert "recovery_score" in csv.splitlines()[0]


def test_unknown_type_is_a_404():
    h = {"Authorization": f"Bearer {register_user('export2@example.com', 'exporter2')['tokens']['access_token']}"}
    assert c.get("/api/v1/export/nope", headers=h).status_code == 404

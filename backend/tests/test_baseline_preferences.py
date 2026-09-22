"""
Setting a sleep target must not wipe the measured parts of a baseline.

Onboarding asks for a sleep goal, which is what the sleep score is measured
against. The HRV mean, deviation and resting heart rate beside it are measured
from the user's own readings, so a preference write has to merge rather than
replace.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.personal_baseline import DEFAULTS

c = TestClient(app)


@pytest.fixture
def user_id():
    return "baseline-prefs-user"


def test_setting_a_sleep_target_keeps_the_measured_values(user_id):
    # Give the user a measured baseline first.
    for day in range(1, 8):
        assert c.post("/api/v1/recovery-logs", json={
            "user_id": user_id,
            "log_date": f"2026-06-{day:02d}",
            "wearable_data": {"hrv_rmssd": 91, "sleep_duration_hours": 8.0, "resting_heart_rate": 48},
            "subjective_checkin": {"soreness": 2, "fatigue": 2, "stress": 2},
        }).status_code == 201

    measured = c.get(f"/api/v1/users/{user_id}/baselines").json()
    assert measured["hrv_mean_rmssd"] > DEFAULTS["hrv_mean_rmssd"]

    saved = c.post(f"/api/v1/users/{user_id}/baselines", json={"sleep_target_hours": 9.0})
    assert saved.status_code == 200, saved.text

    after = c.get(f"/api/v1/users/{user_id}/baselines").json()
    assert after["sleep_target_hours"] == 9.0
    assert after["hrv_mean_rmssd"] == measured["hrv_mean_rmssd"], "a preference write overwrote a measurement"
    assert after["rhr_baseline"] == measured["rhr_baseline"]


def test_a_new_user_gets_the_defaults_plus_their_preference():
    response = c.post("/api/v1/users/baseline-fresh-user/baselines", json={"sleep_target_hours": 7.0})
    assert response.status_code == 200
    baselines = response.json()["baselines"]
    assert baselines["sleep_target_hours"] == 7.0
    assert baselines["hrv_mean_rmssd"] == DEFAULTS["hrv_mean_rmssd"]


def test_an_empty_update_is_refused():
    assert c.post("/api/v1/users/baseline-empty-user/baselines", json={}).status_code == 400


def test_an_implausible_sleep_target_is_refused():
    assert c.post("/api/v1/users/baseline-bad-user/baselines", json={"sleep_target_hours": 30}).status_code == 422

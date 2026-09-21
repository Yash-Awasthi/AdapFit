"""
The baseline is the user's own normal, and the recovery score depends on it.

These tests pin the two properties that make the score personal rather than
generic: the baseline moves toward the user's measured values as readings
accumulate, and two users with the same reading but different histories get
different scores.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import personal_baseline
from app.services.personal_baseline import DEFAULTS, FULL_CONFIDENCE_SAMPLES, MIN_HRV_STD, compute

c = TestClient(app)


def _logs(n, hrv, rhr=60, sleep=7.5):
    return [{"hrv_rmssd": hrv, "resting_heart_rate": rhr, "sleep_duration_hours": sleep} for _ in range(n)]


def test_no_history_gives_the_population_defaults():
    baseline = compute([])
    for key, value in DEFAULTS.items():
        assert baseline[key] == pytest.approx(value)
    assert baseline["confidence"] == 0


def test_one_reading_barely_moves_the_baseline():
    """A single night must not become the standard the next night is judged by."""
    baseline = compute(_logs(1, hrv=90))
    assert DEFAULTS["hrv_mean_rmssd"] < baseline["hrv_mean_rmssd"] < 60


def test_the_baseline_converges_on_the_measured_mean():
    baseline = compute(_logs(FULL_CONFIDENCE_SAMPLES, hrv=90))
    assert baseline["hrv_mean_rmssd"] == pytest.approx(90, abs=0.2)
    assert baseline["confidence"] == 1.0


def test_two_users_with_different_histories_get_different_baselines():
    high = compute(_logs(FULL_CONFIDENCE_SAMPLES, hrv=95, rhr=48))
    low = compute(_logs(FULL_CONFIDENCE_SAMPLES, hrv=32, rhr=72))
    assert high["hrv_mean_rmssd"] > low["hrv_mean_rmssd"]
    assert high["rhr_baseline"] < low["rhr_baseline"]


def test_identical_readings_do_not_collapse_the_deviation():
    """A zero standard deviation would make every z-score infinite."""
    assert compute(_logs(28, hrv=55))["hrv_std_rmssd"] >= MIN_HRV_STD


def test_missing_fields_are_skipped_rather_than_guessed():
    baseline = compute([{"sleep_duration_hours": 6.0}] * FULL_CONFIDENCE_SAMPLES)
    assert baseline["hrv_mean_rmssd"] == pytest.approx(DEFAULTS["hrv_mean_rmssd"])
    assert baseline["sleep_target_hours"] == pytest.approx(6.0, abs=0.1)


def test_unparseable_values_do_not_crash_the_baseline():
    assert compute([{"hrv_rmssd": "n/a"}, {"hrv_rmssd": None}])["hrv_mean_rmssd"] == pytest.approx(
        DEFAULTS["hrv_mean_rmssd"]
    )


def test_chronic_load_comes_from_the_workload_history():
    baseline = compute([], [{"chronic_load": 812.0}])
    assert baseline["chronic_load_28d"] == pytest.approx(812.0)


def test_the_same_hrv_scores_differently_against_different_baselines():
    """The end-to-end property: personal normal changes the verdict."""
    from app.models.schemas import SubjectiveCheckin, UserBaseline, WearableBiometrics
    from app.services.recovery_engine import RecoveryEngine

    reading = WearableBiometrics(hrv_rmssd=55, sleep_duration_hours=7.5, sleep_efficiency_pct=90)
    checkin = SubjectiveCheckin(soreness=3, fatigue=3, stress=3)

    # 55 is a good morning for someone whose normal is 40, and a poor one for
    # someone whose normal is 75.
    low_normal = RecoveryEngine.compute_daily_recovery(
        reading, checkin, UserBaseline(user_id="a", hrv_mean_rmssd=40, hrv_std_rmssd=8)
    )
    high_normal = RecoveryEngine.compute_daily_recovery(
        reading, checkin, UserBaseline(user_id="b", hrv_mean_rmssd=75, hrv_std_rmssd=8)
    )
    assert low_normal.recovery_score > high_normal.recovery_score


def test_logging_recovery_refreshes_the_stored_baseline():
    """A reading recorded today has to shape tomorrow's normal."""
    user_id = "baseline-refresh-user"
    before = c.get(f"/api/v1/users/{user_id}/baselines")

    for day in range(1, 8):
        r = c.post("/api/v1/recovery-logs", json={
            "user_id": user_id,
            "log_date": f"2026-03-0{day}",
            "wearable_data": {"hrv_rmssd": 95, "sleep_duration_hours": 8.0, "resting_heart_rate": 48},
            "subjective_checkin": {"soreness": 2, "fatigue": 2, "stress": 2},
        })
        assert r.status_code == 201, r.text

    after = c.get(f"/api/v1/users/{user_id}/baselines")
    assert after.status_code == 200
    assert after.json()["hrv_mean_rmssd"] > DEFAULTS["hrv_mean_rmssd"]
    if before.status_code == 200:
        assert after.json()["hrv_mean_rmssd"] > before.json()["hrv_mean_rmssd"]


@pytest.mark.anyio
async def test_refresh_stores_only_the_baseline_columns():
    """sample_counts and confidence describe the baseline; they are not part of it."""
    stored = await personal_baseline.refresh("baseline-columns-user")
    from app.core.storage import storage

    record = await storage.get_baseline("baseline-columns-user")
    assert set(record) >= set(DEFAULTS)
    assert "sample_counts" not in record
    assert "confidence" in stored

"""Tests for recovery detection service."""
import pytest
from app.services.recovery_detection import (
    DailyRecoveryData, compute_recovery_score, training_readiness,
    compute_acwr, full_recovery_assessment,
)


def _good_day(date: str) -> DailyRecoveryData:
    return DailyRecoveryData(
        date=date, hrv_rmssd=60.0, resting_hr=55,
        sleep_quality=85.0, sleep_hours=7.5,
        subjective_readiness=8, steps=8000,
        active_minutes=45, workout_strain=120.0,
    )


def _bad_day(date: str) -> DailyRecoveryData:
    return DailyRecoveryData(
        date=date, hrv_rmssd=30.0, resting_hr=70,
        sleep_quality=40.0, sleep_hours=5.0,
        subjective_readiness=3, steps=2000,
        active_minutes=10, workout_strain=300.0,
    )


class TestRecoveryScore:
    def test_empty_history(self):
        today = _good_day("2026-01-15")
        r = compute_recovery_score(today, [])
        assert "error" in r

    def test_good_recovery(self):
        history = [_good_day(f"2026-01-{i:02d}") for i in range(1, 8)]
        today = _good_day("2026-01-08")
        r = compute_recovery_score(today, history)
        assert r["recovery_score"] >= 50
        assert r["phase"] in ("recovered", "peaked", "recovering")

    def test_poor_recovery(self):
        history = [_good_day(f"2026-01-{i:02d}") for i in range(1, 8)]
        today = _bad_day("2026-01-08")
        r = compute_recovery_score(today, history)
        assert r["recovery_score"] < 50
        assert r["phase"] in ("overreaching", "detrained", "recovering")

    def test_breakdown_keys(self):
        history = [_good_day(f"2026-01-{i:02d}") for i in range(1, 8)]
        r = compute_recovery_score(_good_day("2026-01-08"), history)
        assert "breakdown" in r
        assert "hrv_trend" in r["breakdown"]
        assert "sleep_quality" in r["breakdown"]

    def test_missing_data_defaults_to_neutral(self):
        history = [_good_day(f"2026-01-{i:02d}") for i in range(1, 8)]
        # Today has no HRV or sleep data
        today = DailyRecoveryData(date="2026-01-08", subjective_readiness=5)
        r = compute_recovery_score(today, history)
        # Should be around 50 (neutral) since most signals default
        assert 30 <= r["recovery_score"] <= 70


class TestTrainingReadiness:
    def test_cardio_high_readiness(self):
        history = [_good_day(f"2026-01-{i:02d}") for i in range(1, 8)]
        today = _good_day("2026-01-08")
        r = training_readiness(today, history, "cardio")
        assert r["readiness_level"] in ("high", "moderate")
        assert r["sport"] == "cardio"
        assert "recommendation" in r

    def test_strength_low_readiness(self):
        history = [_good_day(f"2026-01-{i:02d}") for i in range(1, 8)]
        today = _bad_day("2026-01-08")
        r = training_readiness(today, history, "strength")
        assert r["readiness_level"] == "low"

    def test_unknown_sport_falls_back(self):
        history = [_good_day(f"2026-01-{i:02d}") for i in range(1, 8)]
        r = training_readiness(_good_day("2026-01-08"), history, "unknown")
        assert r["sport"] == "unknown"

    def test_hoit_requires_higher_readiness(self):
        history = [_good_day(f"2026-01-{i:02d}") for i in range(1, 8)]
        # HIIT has min_score_for_high = 75
        today_ok = _good_day("2026-01-08")
        r = training_readiness(today_ok, history, "hiit")
        # Good day should be high for HIIT
        assert r["readiness_level"] in ("high", "moderate")


class TestACWR:
    def test_insufficient_data(self):
        strain = [{"date": f"2026-01-{i:02d}", "strain": 100} for i in range(1, 5)]
        r = compute_acwr(strain, acute_window=7)
        assert "error" in r

    def test_sweet_spot(self):
        # Consistent load → ACWR ≈ 1.0
        strain = [{"date": f"2026-01-{i:02d}", "strain": 100.0} for i in range(1, 30)]
        r = compute_acwr(strain)
        assert 0.9 <= r["acwr"] <= 1.1
        assert r["zone"] == "sweet_spot"

    def test_danger_zone(self):
        # Last 7 days much higher than chronic
        chronic = [{"date": f"2026-01-{i:02d}", "strain": 100.0} for i in range(1, 22)]
        spike = [{"date": f"2026-01-{i:02d}", "strain": 200.0} for i in range(22, 29)]
        r = compute_acwr(chronic + spike)
        assert r["acwr"] > 1.5
        assert r["zone"] == "danger"
        assert r["injury_risk"] == "high"

    def test_detraining(self):
        # Last 7 days much lower than chronic
        chronic = [{"date": f"2026-01-{i:02d}", "strain": 150.0} for i in range(1, 22)]
        rest = [{"date": f"2026-01-{i:02d}", "strain": 50.0} for i in range(22, 29)]
        r = compute_acwr(chronic + rest)
        assert r["acwr"] < 0.8
        assert r["zone"] == "detraining"

    def test_zero_chronic(self):
        strain = [{"date": f"2026-01-{i:02d}", "strain": 0.0} for i in range(1, 30)]
        r = compute_acwr(strain)
        assert r["classification"] == "unmeasurable"


class TestFullAssessment:
    def test_comprehensive_output(self):
        history = [_good_day(f"2026-01-{i:02d}") for i in range(1, 8)]
        strain = [{"date": f"2026-01-{i:02d}", "strain": 100.0} for i in range(1, 29)]
        result = full_recovery_assessment(
            _good_day("2026-01-08"), history, "cardio", strain
        )
        assert "recovery" in result
        assert "training_readiness" in result
        assert "acwr" in result
        assert "final_recommendation" in result

    def test_without_strain_data(self):
        history = [_good_day(f"2026-01-{i:02d}") for i in range(1, 8)]
        result = full_recovery_assessment(_good_day("2026-01-08"), history)
        assert "acwr" not in result
        assert "final_recommendation" in result

    def test_poor_recovery_recommendation(self):
        history = [_good_day(f"2026-01-{i:02d}") for i in range(1, 8)]
        result = full_recovery_assessment(_bad_day("2026-01-08"), history, "cardio")
        assert result["final_recommendation"] != ""

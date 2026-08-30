"""Tests for health predictions engine."""
import pytest
from app.services.health_predictions import (
    DailyMetric, predict_sleep_score, predict_readiness,
    predict_activity, predict_hrv, detect_anomalies,
)


def _good_history(n=14):
    return [
        DailyMetric(
            date=f"2026-01-{i:02d}",
            sleep_score=80.0 + (i % 3),
            sleep_hours=7.5,
            readiness_score=75.0 + (i % 5),
            steps=8000 + (i % 4) * 500,
            hrv_rmssd=55.0 + (i % 3),
            resting_hr=58,
        )
        for i in range(1, n + 1)
    ]


class TestPredictSleepScore:
    def test_empty_history(self):
        assert "error" in predict_sleep_score([])

    def test_single_day(self):
        history = [DailyMetric(date="2026-01-01", sleep_score=80.0)]
        r = predict_sleep_score(history, days=3)
        assert len(r["predictions"]) == 3
        assert all("predicted_score" in p for p in r["predictions"])
        assert all("ci_lower" in p for p in r["predictions"])

    def test_14_day_history(self):
        r = predict_sleep_score(_good_history(), days=7)
        assert len(r["predictions"]) == 7
        assert r["data_points"] == 14
        assert r["trend"] in ("improving", "declining", "stable")

    def test_confidence_intervals_present(self):
        r = predict_sleep_score(_good_history(), days=7)
        for p in r["predictions"]:
            assert p["ci_lower"] <= p["predicted_score"] <= p["ci_upper"]

    def test_scores_clamped_0_100(self):
        r = predict_sleep_score(_good_history(), days=7)
        for p in r["predictions"]:
            assert 0 <= p["predicted_score"] <= 100


class TestPredictReadiness:
    def test_empty_history(self):
        assert "error" in predict_readiness([])

    def test_with_data(self):
        r = predict_readiness(_good_history(), days=3)
        assert len(r["predictions"]) == 3
        assert r["data_points"] >= 3

    def test_confidence_bounds(self):
        r = predict_readiness(_good_history(), days=3)
        for p in r["predictions"]:
            assert p["ci_lower"] <= p["predicted"] <= p["ci_upper"]


class TestPredictActivity:
    def test_empty_history(self):
        assert "error" in predict_activity([])

    def test_with_data(self):
        r = predict_activity(_good_history(), days=7)
        assert len(r["predictions"]) == 7
        assert "daily_averages" in r
        assert len(r["daily_averages"]) == 7  # Mon-Sun

    def test_has_dates(self):
        r = predict_activity(_good_history(), days=3)
        for p in r["predictions"]:
            assert "date" in p
            assert "day_of_week" in p
            assert p["predicted_steps"] >= 0


class TestPredictHRV:
    def test_empty_history(self):
        assert "error" in predict_hrv([])

    def test_with_data(self):
        r = predict_hrv(_good_history(), days=7)
        assert len(r["predictions"]) == 7
        assert r["data_points"] == 14

    def test_recovery_trajectory(self):
        r = predict_hrv(_good_history(), days=7)
        assert r["recovery_trajectory"] in ("improving", "declining", "stable")


class TestDetectAnomalies:
    def test_no_data(self):
        r = detect_anomalies([])
        assert r["anomaly_count"] == 0

    def test_normal_data_no_anomalies(self):
        r = detect_anomalies(_good_history())
        assert r["anomaly_count"] == 0

    def test_detects_spike(self):
        history = _good_history()
        # Add a spike: HRV drops to 10 (normally ~57)
        history.append(DailyMetric(date="2026-01-15", hrv_rmssd=10.0, sleep_score=30.0))
        r = detect_anomalies(history)
        metrics_flagged = [a["metric"] for a in r["anomalies"]]
        assert "hrv_rmssd" in metrics_flagged or "sleep_score" in metrics_flagged

    def test_anomaly_has_severity(self):
        history = _good_history()
        history.append(DailyMetric(date="2026-01-15", steps=500, resting_hr=95, sleep_score=20.0))
        r = detect_anomalies(history)
        for a in r["anomalies"]:
            assert a["severity"] in ("critical", "warning", "info")

    def test_sensitivity_affects_count(self):
        history = _good_history()
        history.append(DailyMetric(date="2026-01-15", hrv_rmssd=30.0))
        strict = detect_anomalies(history, sensitivity=1.0)
        loose = detect_anomalies(history, sensitivity=3.0)
        assert strict["anomaly_count"] >= loose["anomaly_count"]

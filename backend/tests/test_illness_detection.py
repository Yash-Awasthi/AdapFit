"""Tests for illness detection service."""
import pytest
from app.services.illness_detection import (
    DailyHealthSnapshot, compute_baselines, score_deviations,
    compute_illness_probability, detect_illness, detect_illness_trend,
)


def _healthy_day(date: str) -> DailyHealthSnapshot:
    return DailyHealthSnapshot(
        date=date, hrv_rmssd=60.0, resting_hr=58,
        body_temperature=36.5, sleep_quality_score=85.0,
        sleep_duration_hours=7.5, respiratory_rate=14.0, spo2=98.0,
    )


class TestComputeBaselines:
    def test_empty(self):
        assert compute_baselines([]) == {}

    def test_insufficient_data(self):
        history = [_healthy_day(f"2026-01-{i:02d}") for i in range(1, 3)]
        bl = compute_baselines(history)
        assert bl == {}  # Need ≥3 per metric

    def test_sufficient_data(self):
        history = [_healthy_day(f"2026-01-{i:02d}") for i in range(1, 15)]
        bl = compute_baselines(history)
        assert "hrv_rmssd" in bl
        assert bl["hrv_rmssd"]["mean"] == 60.0
        assert bl["resting_hr"]["mean"] == 58.0


class TestScoreDeviations:
    def test_normal_day_no_deviations(self):
        bl = {"hrv_rmssd": {"mean": 60.0, "std": 5.0, "count": 14},
              "resting_hr": {"mean": 58, "std": 3, "count": 14},
              "body_temperature": {"mean": 36.5, "std": 0.3, "count": 14}}
        today = _healthy_day("2026-01-15")
        devs = score_deviations(today, bl)
        assert not any(d["concerning"] for d in devs)

    def test_fever_detected(self):
        bl = {"body_temperature": {"mean": 36.5, "std": 0.3, "count": 14}}
        today = DailyHealthSnapshot(date="2026-01-15", body_temperature=38.5)
        devs = score_deviations(today, bl)
        fever = [d for d in devs if d["metric"] == "body_temperature"]
        assert len(fever) == 1
        assert fever[0]["concerning"] is True

    def test_low_hrv_detected(self):
        bl = {"hrv_rmssd": {"mean": 60.0, "std": 5.0, "count": 14}}
        # z = (40 - 60) / 5 = -4.0 → below -1.5 threshold
        today = DailyHealthSnapshot(date="2026-01-15", hrv_rmssd=40.0)
        devs = score_deviations(today, bl)
        hrv_dev = [d for d in devs if d["metric"] == "hrv_rmssd"]
        assert hrv_dev[0]["concerning"] is True

    def test_high_rhr_detected(self):
        bl = {"resting_hr": {"mean": 58, "std": 3, "count": 14}}
        # z = (70 - 58) / 3 = 4.0 → above 1.5 threshold
        today = DailyHealthSnapshot(date="2026-01-15", resting_hr=70)
        devs = score_deviations(today, bl)
        rhr_dev = [d for d in devs if d["metric"] == "resting_hr"]
        assert rhr_dev[0]["concerning"] is True


class TestComputeIllnessProbability:
    def test_no_deviations(self):
        r = compute_illness_probability([])
        assert r["severity"] == "none"
        assert r["probability"] == 0.0

    def test_single_mild_deviation(self):
        devs = [{"metric": "hrv_rmssd", "current": 45, "baseline_mean": 60,
                 "baseline_std": 5, "z_score": -3.0, "concerning": True, "direction": "below"}]
        r = compute_illness_probability(devs)
        assert r["probability"] > 0
        assert r["severity"] in ("low", "medium", "high", "critical")
        assert len(r["contributing_signals"]) == 1

    def test_multiple_critical_signals(self):
        devs = [
            {"metric": "hrv_rmssd", "current": 30, "baseline_mean": 60,
             "baseline_std": 5, "z_score": -6.0, "concerning": True, "direction": "below"},
            {"metric": "resting_hr", "current": 75, "baseline_mean": 58,
             "baseline_std": 3, "z_score": 5.67, "concerning": True, "direction": "above"},
            {"metric": "body_temperature", "current": 38.2, "baseline_mean": 36.5,
             "baseline_std": 0.3, "z_score": 5.67, "concerning": True, "direction": "above"},
        ]
        r = compute_illness_probability(devs)
        assert r["severity"] in ("high", "critical")
        assert r["probability"] > 0.4


class TestDetectIllness:
    def test_empty_history(self):
        assert "error" in detect_illness([])

    def test_healthy_baseline(self):
        history = [_healthy_day(f"2026-01-{i:02d}") for i in range(1, 15)]
        result = detect_illness(history)
        assert result["severity"] == "none"
        assert result["probability"] == 0.0

    def test_sick_today(self):
        history = [_healthy_day(f"2026-01-{i:02d}") for i in range(1, 15)]
        sick = DailyHealthSnapshot(
            date="2026-01-15", hrv_rmssd=35.0, resting_hr=72,
            body_temperature=38.6, sleep_quality_score=40.0,
            sleep_duration_hours=5.5, respiratory_rate=18.0, spo2=95.0,
        )
        result = detect_illness(history, today=sick)
        assert result["severity"] in ("medium", "high", "critical")
        assert result["probability"] > 0.3
        assert result["fever_alert"] is True

    def test_with_today_default(self):
        history = [_healthy_day(f"2026-01-{i:02d}") for i in range(1, 15)]
        result = detect_illness(history)
        # Today defaults to last history entry (healthy)
        assert result["severity"] == "none"


class TestIllnessTrend:
    def test_insufficient_data(self):
        assert "error" in detect_illness_trend([], window_days=7)

    def test_stable_trend(self):
        history = [_healthy_day(f"2026-01-{i:02d}") for i in range(1, 22)]
        result = detect_illness_trend(history)
        assert result["trend"] == "stable"

    def test_worsening_trend(self):
        history = [_healthy_day(f"2026-01-{i:02d}") for i in range(1, 15)]
        # Add 7 days of increasingly sick data
        for i in range(15, 22):
            severity = (i - 14) * 0.1
            history.append(DailyHealthSnapshot(
                date=f"2026-01-{i:02d}",
                hrv_rmssd=60.0 - severity * 30,
                resting_hr=58 + int(severity * 20),
                body_temperature=36.5 + severity * 1.5,
                sleep_quality_score=85 - severity * 50,
                spo2=98.0 - severity * 5,
            ))
        result = detect_illness_trend(history)
        assert result["trend"] in ("worsening", "stable")

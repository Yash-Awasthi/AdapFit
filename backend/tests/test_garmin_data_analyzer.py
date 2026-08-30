"""Tests for Garmin Data Analyzer Service."""
import pytest
from datetime import date, timedelta
from app.services.garmin_data_analyzer import (
    DailyMetrics, ReadinessLevel, TrainingIntensity, HRVStatus, SleepQuality,
    calculate_hrv_status, classify_sleep_quality, calculate_training_load,
    calculate_body_battery_trend, calculate_vo2max_trend, assess_readiness,
    calculate_fatigue_fitness_form, generate_daily_summary,
)


def make_daily(date_offset: int = 0, **kwargs) -> DailyMetrics:
    d = date(2025, 1, 1) + timedelta(days=date_offset)
    defaults = {
        "metric_date": d, "steps": 8000, "calories": 2000,
        "active_minutes": 60, "resting_heart_rate": 60,
        "hrv_sdnn": 50, "sleep_score": 75, "body_battery_max": 80,
        "body_battery_min": 20, "body_battery_charged": 60,
        "body_battery_drained": 40, "vo2_max": 45,
        "deep_sleep_minutes": 60, "total_sleep_minutes": 420,
    }
    defaults.update(kwargs)
    return DailyMetrics(**defaults)


class TestHRVStatus:
    def test_balanced(self):
        assert calculate_hrv_status(50, 50, 50) == HRVStatus.BALANCED

    def test_high(self):
        assert calculate_hrv_status(65, 50, 50) == HRVStatus.HIGH

    def test_low(self):
        assert calculate_hrv_status(30, 50, 50) == HRVStatus.LOW

    def test_unbalanced(self):
        assert calculate_hrv_status(40, 50, 50) == HRVStatus.UNBALANCED

    def test_none_values(self):
        assert calculate_hrv_status(None, 50, 50) == HRVStatus.UNBALANCED


class TestSleepQuality:
    def test_excellent(self):
        assert classify_sleep_quality(90, 0.2) == SleepQuality.EXCELLENT

    def test_good(self):
        assert classify_sleep_quality(75, 0.1) == SleepQuality.GOOD

    def test_fair(self):
        assert classify_sleep_quality(60, 0.05) == SleepQuality.FAIR

    def test_poor(self):
        assert classify_sleep_quality(40, 0.02) == SleepQuality.POOR

    def test_none(self):
        assert classify_sleep_quality(None) == SleepQuality.FAIR


class TestTrainingLoad:
    def test_basic(self):
        metrics = [make_daily(i, active_minutes=60, calories=2000) for i in range(30)]
        load = calculate_training_load(metrics)
        assert load.acute_load > 0
        assert load.acwr > 0

    def test_few_days(self):
        metrics = [make_daily(i) for i in range(5)]
        load = calculate_training_load(metrics)
        assert load.trend == "stable"

    def test_increasing_trend(self):
        metrics = [make_daily(i, active_minutes=30 + i * 5) for i in range(21)]
        load = calculate_training_load(metrics)
        assert load.trend in ("increasing", "stable")


class TestBodyBattery:
    def test_trend(self):
        metrics = [make_daily(i, body_battery_max=80, body_battery_min=20,
                              body_battery_charged=60, body_battery_drained=40) for i in range(7)]
        trend = calculate_body_battery_trend(metrics)
        assert trend["avg_max"] == 80
        assert trend["recovery_efficiency"] > 0


class TestVO2max:
    def test_improving(self):
        metrics = [make_daily(i, vo2_max=40 + i * 0.5) for i in range(10)]
        trend = calculate_vo2max_trend(metrics)
        assert trend["trend"] == "improving"

    def test_stable(self):
        metrics = [make_daily(i, vo2_max=45) for i in range(10)]
        trend = calculate_vo2max_trend(metrics)
        assert trend["trend"] == "stable"


class TestReadiness:
    def test_optimal(self):
        m = make_daily(0, hrv_sdnn=60, sleep_score=90, resting_heart_rate=55,
                       stress_score=20, body_battery_max=90)
        metrics_list = [make_daily(i) for i in range(7)]
        assessment = assess_readiness(m, metrics_list)
        assert assessment.level == ReadinessLevel.OPTIMAL

    def test_poor(self):
        m = make_daily(0, hrv_sdnn=20, sleep_score=30, resting_heart_rate=80,
                       stress_score=90, body_battery_max=20)
        metrics_list = [make_daily(i) for i in range(7)]
        assessment = assess_readiness(m, metrics_list)
        assert assessment.level in (ReadinessLevel.LOW, ReadinessLevel.POOR)

    def test_insights(self):
        m = make_daily(0, hrv_sdnn=60, sleep_score=90)
        metrics_list = [make_daily(i) for i in range(7)]
        assessment = assess_readiness(m, metrics_list)
        assert len(assessment.insights) > 0


class TestFatigueFitnessForm:
    def test_basic(self):
        metrics = [make_daily(i) for i in range(30)]
        ctl, atl, tsb = calculate_fatigue_fitness_form(metrics)
        assert isinstance(ctl, float)
        assert isinstance(atl, float)

    def test_few_days(self):
        metrics = [make_daily(i) for i in range(5)]
        ctl, atl, tsb = calculate_fatigue_fitness_form(metrics)
        assert ctl == 0


class TestDailySummary:
    def test_summary(self):
        metrics = [make_daily(i) for i in range(7)]
        summary = generate_daily_summary(metrics)
        assert "readiness" in summary
        assert "training_load" in summary

    def test_empty(self):
        assert "error" in generate_daily_summary([])

"""Tests for CGM Analyzer Service."""
import pytest
from datetime import datetime, timedelta
from app.services.cgm_analyzer import (
    GlucoseReading, GlucoseRange, RiskLevel,
    classify_glucose_range, calculate_time_in_range,
    calculate_glucose_variability, detect_episodes, calculate_gri,
    calculate_average_glucose, estimate_hba1c, calculate_mage,
    analyze_daily_patterns, generate_glucose_summary,
)


def make_readings(values: list[float], start_hour: int = 0) -> list[GlucoseReading]:
    base = datetime(2025, 1, 1, start_hour, 0, 0)
    return [GlucoseReading(timestamp=base + timedelta(minutes=i * 5), value=v) for i, v in enumerate(values)]


class TestClassify:
    def test_hypo(self):
        assert classify_glucose_range(50) == GlucoseRange.HYPO

    def test_target(self):
        assert classify_glucose_range(100) == GlucoseRange.TARGET

    def test_hyper(self):
        assert classify_glucose_range(200) == GlucoseRange.HYPER

    def test_boundary(self):
        assert classify_glucose_range(70) == GlucoseRange.LOW
        assert classify_glucose_range(180) == GlucoseRange.ELEVATED


class TestTimeInRange:
    def test_all_target(self):
        readings = make_readings([100] * 20)
        tir = calculate_time_in_range(readings)
        assert tir.percent_target == 100.0

    def test_mixed(self):
        readings = make_readings([100, 100, 60, 200, 100])
        tir = calculate_time_in_range(readings)
        assert tir.percent_target == 60.0
        assert tir.total_readings == 5

    def test_empty(self):
        tir = calculate_time_in_range([])
        assert tir.total_readings == 0


class TestVariability:
    def test_stable(self):
        readings = make_readings([100, 100, 100, 100])
        v = calculate_glucose_variability(readings)
        assert v.cv == 0.0

    def test_variable(self):
        readings = make_readings([50, 100, 150, 200])
        v = calculate_glucose_variability(readings)
        assert v.cv > 0

    def test_min_max(self):
        readings = make_readings([50, 100, 200])
        v = calculate_glucose_variability(readings)
        assert v.min_value == 50
        assert v.max_value == 200


class TestEpisodes:
    def test_no_episodes(self):
        readings = make_readings([100, 110, 120, 110, 100])
        episodes = detect_episodes(readings)
        assert len(episodes) == 0

    def test_hypo_episode(self):
        readings = make_readings([100, 60, 50, 60, 100])
        episodes = detect_episodes(readings)
        hypo = [e for e in episodes if e.episode_type == "hypo"]
        assert len(hypo) == 1

    def test_hyper_episode(self):
        readings = make_readings([100, 200, 250, 200, 100])
        episodes = detect_episodes(readings)
        hyper = [e for e in episodes if e.episode_type == "hyper"]
        assert len(hyper) == 1


class TestGRI:
    def test_all_target(self):
        readings = make_readings([100] * 20)
        gri = calculate_gri(readings)
        assert gri.gri < 20
        assert gri.risk_level == RiskLevel.LOW

    def test_high_risk(self):
        readings = make_readings([50] * 20)
        gri = calculate_gri(readings)
        assert gri.gri > 40


class TestHbA1c:
    def test_normal(self):
        hba1c = estimate_hba1c(100)
        assert 4.0 < hba1c < 7.0

    def test_high(self):
        hba1c = estimate_hba1c(200)
        assert hba1c > 8.0


class TestMAGE:
    def test_stable(self):
        readings = make_readings([100, 100, 100, 100])
        assert calculate_mage(readings) == 0.0

    def test_variable(self):
        readings = make_readings([100, 80, 120, 70, 130, 100])
        assert calculate_mage(readings) > 0


class TestDailyPatterns:
    def test_patterns(self):
        readings = make_readings([100, 120, 140], start_hour=6)
        patterns = analyze_daily_patterns(readings)
        assert "06:00" in patterns


class TestSummary:
    def test_summary(self):
        readings = make_readings([100, 110, 120, 100, 90, 80, 100, 110, 120, 130])
        summary = generate_glucose_summary(readings)
        assert "mean_glucose" in summary
        assert "gmi" in summary and "targets_met" in summary
        assert "time_in_range" in summary

    def test_empty(self):
        assert "error" in generate_glucose_summary([])

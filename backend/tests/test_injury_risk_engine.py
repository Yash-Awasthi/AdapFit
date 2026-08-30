"""Tests for injury_risk_engine.py — injury risk detection service."""

import pytest
from app.services.injury_risk_engine import (
    InjuryRiskEngine, DailyMetrics, RiskLevel, ACWRZone,
)


@pytest.fixture
def low_risk_metrics():
    return DailyMetrics(
        date=1.0,
        training_load=400,
        soreness=2.0,
        sleep_hours=8.0,
        resting_hr=58,
        baseline_hr=55,
        previous_injuries=0,
        days_since_injury=365,
    )


@pytest.fixture
def high_risk_metrics():
    return DailyMetrics(
        date=1.0,
        training_load=700,
        soreness=8.0,
        sleep_hours=5.0,
        resting_hr=75,
        baseline_hr=55,
        previous_injuries=3,
        days_since_injury=20,
        injury_prone=True,
    )


class TestACWR:
    def test_optimal_zone(self):
        loads = [400] * 30
        acute, chronic, acwr, zone = InjuryRiskEngine.calculate_acwr(loads)
        assert zone == ACWRZone.OPTIMAL
        assert 0.8 <= acwr <= 1.3

    def test_danger_zone(self):
        loads = [300] * 28 + [600] * 7
        acute, chronic, acwr, zone = InjuryRiskEngine.calculate_acwr(loads)
        assert zone == ACWRZone.DANGER
        assert acwr > 1.5

    def test_under_zone(self):
        loads = [500] * 28 + [200] * 7
        acute, chronic, acwr, zone = InjuryRiskEngine.calculate_acwr(loads)
        assert zone == ACWRZone.UNDER
        assert acwr < 0.8

    def test_elevated_zone(self):
        # Need enough data so acute > chronic by 30-50%
        loads = [300] * 28 + [450] * 7
        acute, chronic, acwr, zone = InjuryRiskEngine.calculate_acwr(loads)
        assert zone == ACWRZone.ELEVATED

    def test_short_history(self):
        loads = [400, 420, 380]
        acute, chronic, acwr, zone = InjuryRiskEngine.calculate_acwr(loads)
        assert acwr == 1.0  # fallback for short history

    def test_empty_loads(self):
        acute, chronic, acwr, zone = InjuryRiskEngine.calculate_acwr([])
        assert acwr == 1.0


class TestRollingFeatures:
    def test_rolling_mean_7d(self):
        values = list(range(1, 31))
        mean = InjuryRiskEngine.calculate_rolling_mean(values, 7)
        assert mean == pytest.approx(27.0, rel=0.01)

    def test_rolling_mean_short(self):
        values = [10, 20, 30]
        mean = InjuryRiskEngine.calculate_rolling_mean(values, 7)
        assert mean == 20.0

    def test_rolling_features(self):
        values = list(range(1, 31))
        features = InjuryRiskEngine.calculate_rolling_features(values)
        assert "7d" in features
        assert "14d" in features
        assert "28d" in features


class TestLoadTrend:
    def test_increasing_trend(self):
        loads = list(range(100, 110))
        trend = InjuryRiskEngine.calculate_load_trend(loads)
        assert trend > 0

    def test_decreasing_trend(self):
        loads = list(range(110, 100, -1))
        trend = InjuryRiskEngine.calculate_load_trend(loads)
        assert trend < 0

    def test_flat_trend(self):
        loads = [100] * 10
        trend = InjuryRiskEngine.calculate_load_trend(loads)
        assert trend == 0.0


class TestRiskFactors:
    def test_acwr_danger_factor(self, high_risk_metrics):
        factor = InjuryRiskEngine._acwr_factor(1.8)
        assert factor.contribution == 0.35
        assert factor.severity == "high"

    def test_soreness_factor(self):
        factor = InjuryRiskEngine._soreness_factor(8.0)
        assert factor.contribution > 0
        assert factor.severity == "high"

    def test_sleep_factor(self):
        factor = InjuryRiskEngine._sleep_factor(5.0)
        assert factor.contribution > 0

    def test_hr_factor(self):
        factor = InjuryRiskEngine._hr_factor(75, 55)
        assert factor.contribution > 0

    def test_injury_history_factor(self):
        factors = InjuryRiskEngine._injury_history_factor(3, 20)
        assert len(factors) == 2  # previous injuries + recent return

    def test_injury_prone_factor(self):
        factor = InjuryRiskEngine._injury_prone_factor(True)
        assert factor is not None
        assert factor.contribution == 0.10


class TestCompositeScore:
    def test_low_risk_score(self, low_risk_metrics):
        result = InjuryRiskEngine.analyze(low_risk_metrics)
        assert result.risk_score < 0.16
        assert result.risk_level == RiskLevel.LOW

    def test_high_risk_score(self, high_risk_metrics):
        result = InjuryRiskEngine.analyze(high_risk_metrics)
        assert result.risk_score > 0.27
        assert result.risk_level == RiskLevel.HIGH

    def test_moderate_risk(self):
        metrics = DailyMetrics(
            date=1.0, training_load=500, soreness=5.0,
            sleep_hours=6.5, resting_hr=68, baseline_hr=60,
            previous_injuries=1, days_since_injury=100,
        )
        result = InjuryRiskEngine.analyze(metrics)
        assert result.risk_level in (RiskLevel.LOW, RiskLevel.MODERATE)


class TestRecommendations:
    def test_high_risk_recommendations(self, high_risk_metrics):
        result = InjuryRiskEngine.analyze(high_risk_metrics)
        assert len(result.recommendations) > 0
        assert any("HIGH RISK" in r or "Reduce" in r or "monitor" in r.lower() for r in result.recommendations)

    def test_low_risk_recommendations(self, low_risk_metrics):
        result = InjuryRiskEngine.analyze(low_risk_metrics)
        assert len(result.recommendations) > 0
        assert result.risk_level == RiskLevel.LOW


class TestAnalyzeSeries:
    def test_series_analysis(self):
        metrics_list = [
            DailyMetrics(date=i, training_load=400 + i * 10, soreness=2.0,
                        sleep_hours=7.5, resting_hr=58, baseline_hr=55)
            for i in range(30)
        ]
        results = InjuryRiskEngine.analyze_series(metrics_list)
        assert len(results) == 30
        # Last result should have accumulated history
        assert results[-1].acute_load > 0
        assert results[-1].chronic_load > 0


class TestACWRZoneInfo:
    def test_zone_info(self):
        info = InjuryRiskEngine.get_acwr_zone_info()
        assert "zones" in info
        assert "optimal_range" in info
        assert info["danger_threshold"] == 1.5

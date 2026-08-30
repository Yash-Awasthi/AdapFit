"""Tests for Early Warning Score System."""
import pytest
from app.services.early_warning_score import (
    score_vital,
    calculate_news,
    calculate_cews,
    calculate_trend_score,
    calculate_aggregate_risk,
    generate_monitoring_recommendation,
    VitalSigns,
    EWSScore,
    NEWS_THRESHOLDS,
)


class TestScoreVital:
    def test_heart_rate_normal(self):
        score = score_vital(72, NEWS_THRESHOLDS["heart_rate"])
        assert score == 0

    def test_heart_rate_high(self):
        score = score_vital(120, NEWS_THRESHOLDS["heart_rate"])
        assert score == 2

    def test_heart_rate_dangerously_low(self):
        score = score_vital(35, NEWS_THRESHOLDS["heart_rate"])
        assert score == 3

    def test_temperature_normal(self):
        score = score_vital(36.5, NEWS_THRESHOLDS["temperature"])
        assert score == 0

    def test_temperature_hypothermia(self):
        score = score_vital(34.0, NEWS_THRESHOLDS["temperature"])
        assert score == 3

    def test_spo2_normal(self):
        score = score_vital(98, NEWS_THRESHOLDS["oxygen_saturation"])
        assert score == 0

    def test_spo2_critical(self):
        score = score_vital(88, NEWS_THRESHOLDS["oxygen_saturation"])
        assert score == 3


class TestCalculateNEWS:
    def test_normal_vitals(self):
        vitals = VitalSigns(
            heart_rate=72, respiratory_rate=14, temperature=36.5,
            oxygen_saturation=98, systolic_bp=120, avpu=0,
        )
        score = calculate_news(vitals)
        assert score.total_score == 0
        assert score.risk_level == "low"

    def test_elevated_heart_rate(self):
        vitals = VitalSigns(
            heart_rate=120, respiratory_rate=14, temperature=36.5,
            oxygen_saturation=98, systolic_bp=120, avpu=0,
        )
        score = calculate_news(vitals)
        assert score.total_score >= 2
        assert "heart_rate" in score.component_scores

    def test_critical_vitals(self):
        vitals = VitalSigns(
            heart_rate=35, respiratory_rate=8, temperature=34.0,
            oxygen_saturation=88, systolic_bp=80, avpu=3,
        )
        score = calculate_news(vitals)
        assert score.total_score >= 12
        assert score.risk_level == "high"

    def test_missing_vitals(self):
        vitals = VitalSigns(heart_rate=72)
        score = calculate_news(vitals)
        assert len(score.missing_vitals) > 0
        assert "respiratory_rate" in score.missing_vitals

    def test_supplemental_oxygen(self):
        vitals_o2 = VitalSigns(
            heart_rate=72, respiratory_rate=14, temperature=36.5,
            oxygen_saturation=98, systolic_bp=120, avpu=0,
            supplemental_oxygen=True,
        )
        score = calculate_news(vitals_o2)
        assert score.component_scores["supplemental_oxygen"] == 2

    def test_no_oxygen(self):
        vitals = VitalSigns(
            heart_rate=72, respiratory_rate=14, temperature=36.5,
            oxygen_saturation=98, systolic_bp=120, avpu=0,
            supplemental_oxygen=False,
        )
        score = calculate_news(vitals)
        assert score.component_scores["supplemental_oxygen"] == 0


class TestCalculateCEWS:
    def test_normal(self):
        vitals = VitalSigns(
            heart_rate=72, respiratory_rate=14, temperature=36.5,
            oxygen_saturation=98, systolic_bp=120,
        )
        score = calculate_cews(vitals)
        assert score.total_score == 0

    def test_elevated(self):
        vitals = VitalSigns(
            heart_rate=120, respiratory_rate=25, temperature=38.5,
            oxygen_saturation=92, systolic_bp=95,
        )
        score = calculate_cews(vitals)
        assert score.total_score >= 6
        assert score.risk_level == "high"

    def test_no_avpu_in_cews(self):
        vitals = VitalSigns(
            heart_rate=72, respiratory_rate=14, temperature=36.5,
            oxygen_saturation=98, systolic_bp=120, avpu=3,
        )
        score = calculate_cews(vitals)
        # CEWS doesn't include AVPU
        assert "avpu" not in score.component_scores


class TestTrendScore:
    def test_rising_trend(self):
        scores = [
            EWSScore(total_score=1),
            EWSScore(total_score=2),
            EWSScore(total_score=4),
            EWSScore(total_score=6),
        ]
        trend = calculate_trend_score(scores)
        assert trend["direction"] == "rising"
        assert trend["rate_of_change"] > 0

    def test_falling_trend(self):
        scores = [
            EWSScore(total_score=6),
            EWSScore(total_score=4),
            EWSScore(total_score=2),
        ]
        trend = calculate_trend_score(scores)
        assert trend["direction"] == "falling"

    def test_stable(self):
        scores = [
            EWSScore(total_score=2),
            EWSScore(total_score=2),
            EWSScore(total_score=2),
        ]
        trend = calculate_trend_score(scores)
        assert trend["direction"] == "stable"

    def test_insufficient_data(self):
        trend = calculate_trend_score([EWSScore(total_score=1)])
        assert trend["direction"] == "insufficient_data"


class TestAggregateRisk:
    def test_all_low(self):
        scores = [EWSScore(total_score=0, risk_level="low") for _ in range(10)]
        agg = calculate_aggregate_risk(scores)
        assert agg["risk_level"] == "low"

    def test_some_high(self):
        scores = [
            EWSScore(total_score=0, risk_level="low"),
            EWSScore(total_score=8, risk_level="high"),
        ]
        agg = calculate_aggregate_risk(scores)
        assert agg["risk_level"] == "high"

    def test_empty(self):
        agg = calculate_aggregate_risk([])
        assert agg["risk_level"] == "unknown"


class TestMonitoringRecommendation:
    def test_low_score(self):
        score = EWSScore(total_score=0)
        rec = generate_monitoring_recommendation(score)
        assert rec["frequency_hours"] == 12
        assert not rec["escalation"]

    def test_medium_score(self):
        score = EWSScore(total_score=5)
        rec = generate_monitoring_recommendation(score)
        assert rec["escalation"] is True
        assert rec["frequency_hours"] <= 1

    def test_critical_score(self):
        score = EWSScore(total_score=10)
        rec = generate_monitoring_recommendation(score)
        assert rec["frequency_hours"] == 0
        assert rec["escalation"] is True

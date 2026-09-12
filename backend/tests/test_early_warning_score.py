"""Tests for Early Warning Score System (NEWS2)."""
import pytest
from app.services.early_warning_score import (
    AlertLevel,
    VitalSigns,
    NEWSScore,
    _respiratory_rate_score,
    _oxygen_sat_score,
    _systolic_bp_score,
    _pulse_rate_score,
    _consciousness_score,
    _temperature_score,
    calculate_news2,
    news2_recommendation,
)


class TestIndividualScores:
    def test_respiratory_normal(self):
        assert _respiratory_rate_score(16) == 0

    def test_respiratory_low(self):
        assert _respiratory_rate_score(9) == 1

    def test_respiratory_critical(self):
        assert _respiratory_rate_score(7) == 3

    def test_respiratory_high(self):
        assert _respiratory_rate_score(22) == 2

    def test_spo2_normal(self):
        assert _oxygen_sat_score(98) == 0

    def test_spo2_low(self):
        assert _oxygen_sat_score(94) == 1

    def test_spo2_critical(self):
        assert _oxygen_sat_score(88) == 3

    def test_spo2_hypercapnic(self):
        assert _oxygen_sat_score(90, hypercapnic=True) == 0

    def test_systolic_normal(self):
        assert _systolic_bp_score(120) == 0

    def test_systolic_low(self):
        assert _systolic_bp_score(95) == 2

    def test_systolic_critical(self):
        assert _systolic_bp_score(85) == 3

    def test_pulse_normal(self):
        assert _pulse_rate_score(72) == 0

    def test_pulse_low(self):
        assert _pulse_rate_score(45) == 1

    def test_pulse_critical(self):
        assert _pulse_rate_score(35) == 3

    def test_consciousness_alert(self):
        assert _consciousness_score("alert") == 0

    def test_consciousness_voice(self):
        assert _consciousness_score("voice") == 3

    def test_consciousness_confusion(self):
        assert _consciousness_score("new confusion") == 3

    def test_temperature_normal(self):
        assert _temperature_score(36.5) == 0

    def test_temperature_hypothermia(self):
        assert _temperature_score(34.0) == 3

    def test_temperature_high(self):
        assert _temperature_score(39.5) == 2


class TestCalculateNEWS2:
    def test_normal_vitals(self):
        vitals = VitalSigns(
            respiratory_rate=16, oxygen_saturation=98,
            systolic_bp=120, pulse_rate=72,
            consciousness="alert", temperature=36.5,
        )
        score = calculate_news2(vitals)
        assert score.total == 0
        assert score.alert_level == AlertLevel.NONE
        assert score.trigger is None

    def test_elevated_score(self):
        vitals = VitalSigns(
            respiratory_rate=22, oxygen_saturation=93,
            systolic_bp=95, pulse_rate=115,
            consciousness="alert", temperature=38.5,
        )
        score = calculate_news2(vitals)
        assert score.total >= 5
        assert score.alert_level in (AlertLevel.MODERATE, AlertLevel.HIGH)

    def test_critical_score(self):
        vitals = VitalSigns(
            respiratory_rate=7, oxygen_saturation=85,
            systolic_bp=80, pulse_rate=35,
            consciousness="unresponsive", temperature=34.0,
        )
        score = calculate_news2(vitals)
        assert score.total >= 12
        assert score.alert_level == AlertLevel.HIGH
        assert score.trigger == "high"

    def test_supplemental_oxygen_adds_2(self):
        vitals_no_o2 = VitalSigns(
            respiratory_rate=16, oxygen_saturation=98,
            systolic_bp=120, pulse_rate=72,
            consciousness="alert", temperature=36.5,
            supplemental_oxygen=False,
        )
        vitals_o2 = VitalSigns(
            respiratory_rate=16, oxygen_saturation=98,
            systolic_bp=120, pulse_rate=72,
            consciousness="alert", temperature=36.5,
            supplemental_oxygen=True,
        )
        score_no = calculate_news2(vitals_no_o2)
        score_yes = calculate_news2(vitals_o2)
        assert score_yes.total == score_no.total + 2
        assert score_yes.supplemental_o2_score == 2


class TestNews2Recommendation:
    def test_no_concerns(self):
        score = NEWSScore(total=0, respiratory_score=0, oxygen_sat_score=0,
                          systolic_bp_score=0, pulse_score=0,
                          consciousness_score=0, temp_score=0,
                          supplemental_o2_score=0, alert_level=AlertLevel.NONE,
                          trigger=None)
        rec = news2_recommendation(score)
        assert "routine" in rec.lower()

    def test_low_risk(self):
        score = NEWSScore(total=2, respiratory_score=1, oxygen_sat_score=1,
                          systolic_bp_score=0, pulse_score=0,
                          consciousness_score=0, temp_score=0,
                          supplemental_o2_score=0, alert_level=AlertLevel.LOW,
                          trigger="low")
        rec = news2_recommendation(score)
        assert "monitor" in rec.lower()

    def test_moderate_risk(self):
        score = NEWSScore(total=6, respiratory_score=2, oxygen_sat_score=1,
                          systolic_bp_score=1, pulse_score=1,
                          consciousness_score=0, temp_score=1,
                          supplemental_o2_score=0, alert_level=AlertLevel.MODERATE,
                          trigger="medium")
        rec = news2_recommendation(score)
        assert "urgent" in rec.lower()

    def test_high_risk(self):
        score = NEWSScore(total=10, respiratory_score=3, oxygen_sat_score=3,
                          systolic_bp_score=3, pulse_score=1,
                          consciousness_score=0, temp_score=0,
                          supplemental_o2_score=0, alert_level=AlertLevel.HIGH,
                          trigger="high")
        rec = news2_recommendation(score)
        assert "emergency" in rec.lower()


class TestVitalSignsDefaults:
    def test_defaults(self):
        vitals = VitalSigns(respiratory_rate=16, oxygen_saturation=98,
                            systolic_bp=120, pulse_rate=72)
        assert vitals.consciousness == "alert"
        assert vitals.temperature == 37.0
        assert vitals.supplemental_oxygen is False
        assert vitals.hypercapnic_scale is False

    def test_frozen(self):
        vitals = VitalSigns(respiratory_rate=16, oxygen_saturation=98,
                            systolic_bp=120, pulse_rate=72)
        with pytest.raises(AttributeError):
            vitals.temperature = 38.0

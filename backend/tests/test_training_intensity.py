"""Tests for Training Intensity Distribution Analytics."""
import pytest
import math
from app.services.training_intensity import (
    polarization_index,
    treff_polarization_index,
    classify_distribution,
    compute_distribution_from_sessions,
    pmax_envelope,
    should_cap_rep,
    cap_rep_power,
    analyze_weekly_distribution,
)


class TestPolarizationIndex:
    def test_polarized(self):
        pi = polarization_index(80, 5, 15)
        assert pi is not None
        assert pi > 1.0  # log10(95/5) ≈ 1.28

    def test_pyramidal(self):
        pi = polarization_index(80, 15, 5)
        assert pi is not None
        assert pi > 0.5

    def test_inverted(self):
        pi = polarization_index(20, 60, 20)
        assert pi is not None
        assert pi < 0

    def test_near_zero_z3z4(self):
        pi = polarization_index(90, 0.05, 10)
        assert pi is None


class TestTreffPI:
    def test_polarized(self):
        pi = treff_polarization_index(80, 5, 15)
        assert pi is not None
        assert pi > 2.0  # log10(1200/5) ≈ 2.38

    def test_pyramidal(self):
        pi = treff_polarization_index(80, 15, 5)
        assert pi is not None
        assert 1.0 < pi < 2.0  # log10(400/15) ≈ 1.43

    def test_threshold(self):
        pi = treff_polarization_index(60, 30, 10)
        assert pi is not None
        # log10(600/30) = log10(20) ≈ 1.30

    def test_near_zero_z3z4(self):
        pi = treff_polarization_index(90, 0.05, 10)
        assert pi is None


class TestClassify:
    def test_polarized(self):
        result = classify_distribution(80, 5, 15)
        assert result.label == "polarized"
        assert result.confidence >= 0.5

    def test_pyramidal(self):
        result = classify_distribution(80, 15, 5)
        assert result.label == "pyramidal"

    def test_threshold(self):
        result = classify_distribution(60, 30, 10)
        assert result.label in ("threshold", "pyramidal")

    def test_hiit(self):
        result = classify_distribution(40, 25, 35)
        assert result.label == "hiit"

    def test_base(self):
        result = classify_distribution(95, 3, 2)
        assert result.label == "base"

    def test_has_pi_values(self):
        result = classify_distribution(80, 10, 10)
        assert result.pi_additive is not None
        assert result.pi_multiplicative is not None


class TestComputeDistribution:
    def test_basic(self):
        sessions = [
            {"tss": 100, "z1z2_pct": 80, "z3z4_pct": 10, "z5plus_pct": 10, "duration_hours": 1.0},
            {"tss": 200, "z1z2_pct": 60, "z3z4_pct": 20, "z5plus_pct": 20, "duration_hours": 2.0},
        ]
        dist = compute_distribution_from_sessions(sessions)
        assert dist.total_tss == 300
        assert dist.total_hours == 3.0
        # Weighted: z1z2 = (80*100 + 60*200)/300 = 66.7
        assert dist.z1z2_pct == pytest.approx(66.7, abs=1)

    def test_empty(self):
        dist = compute_distribution_from_sessions([])
        assert dist.total_tss == 0


class TestPMaxEnvelope:
    def test_at_zero(self):
        env = pmax_envelope(0, 200, 400)
        assert env == pytest.approx(400.0)

    def test_at_inf(self):
        env = pmax_envelope(10000, 200, 400)
        assert env == pytest.approx(200.0, abs=1)

    def test_midpoint(self):
        env = pmax_envelope(26, 200, 400)
        # exp(-1) ≈ 0.368, so env ≈ 200 + 200*0.368 = 273.6
        assert env == pytest.approx(273.6, abs=1)


class TestShouldCapRep:
    def test_qualifying_rep(self):
        assert should_cap_rep(1.3, 60, 200, 400) is True

    def test_low_ratio(self):
        assert should_cap_rep(1.0, 60, 200, 400) is False

    def test_long_duration(self):
        assert should_cap_rep(1.3, 200, 200, 400) is False

    def test_short_duration(self):
        assert should_cap_rep(1.5, 30, 200, 400) is True


class TestCapRepPower:
    def test_no_cap_needed(self):
        result = cap_rep_power(1.1, 60, 200, 400, 200)
        assert result is None

    def test_cap_applied(self):
        result = cap_rep_power(1.5, 30, 200, 400, 200)
        assert result is not None
        assert result < 1.5

    def test_vo2_floor(self):
        result = cap_rep_power(1.3, 30, 200, 400, 200)
        if result is not None:
            assert result >= 1.06  # VO2 floor


class TestWeeklyAnalysis:
    def test_basic(self):
        result = analyze_weekly_distribution(
            weekly_tss=[200, 250, 300, 280],
            weekly_z1z2=[80, 75, 70, 65],
            weekly_z3z4=[10, 15, 20, 25],
            weekly_z5plus=[10, 10, 10, 10],
        )
        assert result["weeks"] == 4
        assert result["avg_tss"] > 0
        assert "classification" in result

    def test_trend(self):
        result = analyze_weekly_distribution(
            weekly_tss=[200, 200, 200, 200, 200, 200],
            weekly_z1z2=[80, 75, 70, 65, 60, 55],
            weekly_z3z4=[10, 12, 14, 16, 18, 20],
            weekly_z5plus=[10, 13, 16, 19, 22, 25],
        )
        assert result["trend"] == "increasing_intensity"

    def test_empty(self):
        result = analyze_weekly_distribution([], [], [], [])
        assert result["weeks"] == 0

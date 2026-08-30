"""Tests for Endurance Coaching Analytics."""
import pytest
from app.services.endurance_coaching import (
    calculate_daily_tss,
    calculate_ctl_atl,
    classify_tsb,
    build_power_curve,
    estimate_ftp_from_curve,
    compute_power_zones,
    calculate_nutrition_for_session,
    generate_periodization,
    generate_daily_recommendation,
    DailyTrainingLoad,
    NutritionZone,
    TrainingPhase,
)


class TestTSS:
    def test_basic_tss(self):
        tss = calculate_daily_tss(60, 0.7)
        assert tss > 0
        assert tss < 200

    def test_tss_with_hr(self):
        tss = calculate_daily_tss(60, 0.7, hr_max=190, avg_hr=150)
        assert tss > 0

    def test_zero_duration(self):
        tss = calculate_daily_tss(0, 0.7)
        assert tss == 0.0


class TestCTLATL:
    def test_basic_calculation(self):
        loads = [
            DailyTrainingLoad(date=f"2024-01-{i:02d}", tss=200, duration_min=60)
            for i in range(1, 15)
        ]
        metrics = calculate_ctl_atl(loads)
        assert len(metrics) == 14
        assert metrics[-1].ctl > 0
        assert metrics[-1].atl > 0
        assert metrics[-1].tsb == pytest.approx(metrics[-1].ctl - metrics[-1].atl, abs=0.1)

    def test_empty_loads(self):
        assert calculate_ctl_atl([]) == []

    def test_ctl_lags_atl(self):
        loads = [
            DailyTrainingLoad(date=f"2024-01-{i:02d}", tss=300, duration_min=90)
            for i in range(1, 20)
        ]
        metrics = calculate_ctl_atl(loads)
        # ATL should respond faster than CTL
        assert metrics[2].atl > metrics[2].ctl


class TestTSBClassification:
    def test_very_fatigued(self):
        result = classify_tsb(-50)
        assert result["zone"] == "very_fatigued"

    def test_fresh(self):
        result = classify_tsb(5)
        assert result["zone"] == "fresh"

    def test_detrained(self):
        result = classify_tsb(30)
        assert result["zone"] == "detrained"


class TestPowerCurve:
    def test_build_curve(self):
        samples = [
            (1, 800), (1, 900), (5, 700), (5, 750),
            (60, 300), (60, 320), (1200, 250),
        ]
        curve = build_power_curve(samples)
        assert len(curve) >= 3
        assert curve[0].duration_sec < curve[-1].duration_sec

    def test_empty_samples(self):
        assert build_power_curve([]) == []

    def test_ftp_estimation(self):
        samples = [(1200, 250), (600, 300), (60, 400), (5, 700), (1, 900)]
        curve = build_power_curve(samples)
        ftp = estimate_ftp_from_curve(curve)
        assert ftp > 0
        assert ftp < 1000


class TestPowerZones:
    def test_zone_count(self):
        zones = compute_power_zones(200)
        assert len(zones) == 7

    def test_zone_values(self):
        zones = compute_power_zones(200)
        assert zones[0]["name"] == "Active Recovery"
        assert zones[3]["name"] == "Threshold"
        assert zones[3]["max_watts"] == 210  # 200 * 1.05

    def test_zero_ftp(self):
        zones = compute_power_zones(0)
        assert all(z["max_watts"] == 0 or z["zone"] == 7 for z in zones)


class TestNutrition:
    def test_recovery_zone(self):
        plan = calculate_nutrition_for_session(60, NutritionZone.RECOVERY)
        assert plan.carb_grams > 0
        assert plan.protein_grams > 0
        assert plan.calories > 0
        assert plan.hydration_liters > 0

    def test_vo2max_zone(self):
        plan = calculate_nutrition_for_session(60, NutritionZone.VO2MAX)
        assert plan.carb_grams > plan.protein_grams  # higher carb for VO2max

    def test_longer_session_more_calories(self):
        short = calculate_nutrition_for_session(30, NutritionZone.TEMPO)
        long = calculate_nutrition_for_session(120, NutritionZone.TEMPO)
        assert long.calories > short.calories

    def test_all_zones_have_guidance(self):
        for zone in NutritionZone:
            plan = calculate_nutrition_for_session(60, zone)
            assert plan.pre_workout_fuel
            assert plan.during_workout_fuel
            assert plan.post_workout_fuel


class TestPeriodization:
    def test_basic_plan(self):
        plan = generate_periodization(weeks=12, event_week=10)
        assert len(plan) == 12
        assert all("phase" in w for w in plan)
        assert all("target_tss" in w for w in plan)

    def test_taper_before_race(self):
        plan = generate_periodization(weeks=12, event_week=10)
        race_weeks = [w for w in plan if w["phase"] == TrainingPhase.RACE.value]
        assert len(race_weeks) > 0
        assert race_weeks[0]["tss_multiplier"] < 1.0

    def test_recovery_weeks(self):
        plan = generate_periodization(weeks=12, event_week=10)
        recovery = [w for w in plan if w["note"] == "recovery week"]
        assert len(recovery) >= 2  # at least weeks 4 and 8


class TestDailyRecommendation:
    def test_rest_when_fatigued(self):
        rec = generate_daily_recommendation(tsb=-50, sleep_quality=0.4, hrv_status="low")
        assert rec["intensity"] == "rest"

    def test_intervals_when_fresh(self):
        rec = generate_daily_recommendation(tsb=-10, sleep_quality=0.9, hrv_status="high")
        assert rec["intensity"] == "hard"

    def test_recovery_when_very_fresh(self):
        rec = generate_daily_recommendation(tsb=20, sleep_quality=0.9)
        assert rec["intensity"] == "recovery"

    def test_all_recommendations_have_activities(self):
        for tsb in [-50, -25, -10, 5, 20]:
            rec = generate_daily_recommendation(tsb=tsb)
            assert len(rec["activities"]) > 0

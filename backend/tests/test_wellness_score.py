"""Tests for wellness_score.py — unified wellness scoring."""

import pytest
from app.services.wellness_score import (
    score_sleep, score_recovery, score_activity, score_nutrition,
    score_stress, score_cardiovascular, calculate_wellness_score,
    generate_alerts, generate_recommendations, analyze_weekly_trend,
    generate_daily_report, ComponentScore, WellnessScore,
    AlertSeverity, TrendDirection,
)


class TestSleepScoring:
    def test_optimal_sleep(self):
        result = score_sleep(sleep_hours=8, sleep_quality=85, deep_sleep_pct=20, rem_pct=25)
        assert result.score >= 80
        assert result.status == "optimal"

    def test_poor_sleep(self):
        result = score_sleep(sleep_hours=4, sleep_quality=30, deep_sleep_pct=5, rem_pct=10)
        assert result.score < 50

    def test_sleep_debt_penalty(self):
        good = score_sleep(sleep_hours=8, sleep_quality=80, sleep_debt_hours=0)
        debt = score_sleep(sleep_hours=8, sleep_quality=80, sleep_debt_hours=5)
        assert debt.score < good.score

    def test_weight(self):
        result = score_sleep()
        assert result.weight == 0.25


class TestRecoveryScoring:
    def test_good_recovery(self):
        result = score_recovery(hrv_score=80, resting_hr_delta=0, readiness_score=85)
        assert result.score >= 70

    def test_poor_recovery(self):
        result = score_recovery(hrv_score=20, resting_hr_delta=15, readiness_score=30)
        assert result.score < 50


class TestActivityScoring:
    def test_meets_targets(self):
        result = score_activity(steps=10000, active_minutes=30, calories_burned=2500)
        assert result.score >= 90

    def test_below_targets(self):
        result = score_activity(steps=2000, active_minutes=5, calories_burned=1500)
        assert result.score < 50


class TestNutritionScoring:
    def test_balanced(self):
        result = score_nutrition(calorie_intake=2000, protein_g=50, water_ml=2500)
        assert result.score >= 80

    def test_dehydrated(self):
        result = score_nutrition(calorie_intake=2000, protein_g=50, water_ml=500)
        assert result.score < 80  # Hydration is 30% of nutrition score


class TestStressScoring:
    def test_low_stress(self):
        result = score_stress(hrv_rmssd=50, resting_hr=55, sleep_quality=80, activity_level=70)
        assert result.score >= 70

    def test_high_stress(self):
        result = score_stress(hrv_rmssd=15, resting_hr=85, sleep_quality=30, activity_level=20)
        assert result.score < 40


class TestCardiovascularScoring:
    def test_excellent(self):
        result = score_cardiovascular(resting_hr=60, hr_recovery_1min=20, blood_pressure_systolic=115, blood_pressure_diastolic=75)
        assert result.score >= 80

    def test_poor(self):
        result = score_cardiovascular(resting_hr=95, hr_recovery_1min=5, blood_pressure_systolic=150, blood_pressure_diastolic=95)
        assert result.score < 50


class TestUnifiedScore:
    def test_perfect_score(self):
        components = [
            ComponentScore(name="sleep", score=100, weight=0.25),
            ComponentScore(name="recovery", score=100, weight=0.20),
            ComponentScore(name="activity", score=100, weight=0.20),
            ComponentScore(name="nutrition", score=100, weight=0.15),
            ComponentScore(name="stress", score=100, weight=0.10),
            ComponentScore(name="cardiovascular", score=100, weight=0.10),
        ]
        result = calculate_wellness_score(components)
        assert result.overall == 100
        assert result.grade == "A+"

    def test_zero_score(self):
        components = [
            ComponentScore(name="sleep", score=0, weight=0.25),
            ComponentScore(name="recovery", score=0, weight=0.20),
        ]
        result = calculate_wellness_score(components)
        assert result.overall == 0
        assert result.grade == "F"

    def test_grade_mapping(self):
        for score, expected_grade in [(96, "A+"), (91, "A"), (86, "B+"), (81, "B"), (76, "C+"), (71, "C"), (65, "D"), (50, "F")]:
            components = [ComponentScore(name="sleep", score=score, weight=1.0)]
            result = calculate_wellness_score(components)
            assert result.grade == expected_grade, f"Score {score} should be {expected_grade}, got {result.grade}"


class TestAlerts:
    def test_critical_alert(self):
        components = [ComponentScore(name="sleep", score=20, weight=0.25)]
        alerts = generate_alerts(components, 25)
        assert any(a.severity == AlertSeverity.CRITICAL for a in alerts)

    def test_warning_alert(self):
        components = [ComponentScore(name="recovery", score=35, weight=0.20)]
        alerts = generate_alerts(components, 55)
        assert any(a.severity == AlertSeverity.WARNING for a in alerts)

    def test_no_alerts_for_good_scores(self):
        components = [
            ComponentScore(name="sleep", score=85, weight=0.25),
            ComponentScore(name="recovery", score=80, weight=0.20),
        ]
        alerts = generate_alerts(components, 82)
        assert len(alerts) == 0


class TestRecommendations:
    def test_low_score_generates_recommendation(self):
        components = [ComponentScore(name="sleep", score=35, weight=0.25)]
        recs = generate_recommendations(components)
        assert len(recs) > 0
        assert recs[0].category == "sleep"

    def test_high_score_positive_reinforcement(self):
        components = [
            ComponentScore(name="sleep", score=90, weight=0.25),
            ComponentScore(name="recovery", score=85, weight=0.20),
        ]
        recs = generate_recommendations(components)
        assert any("Great" in r.title for r in recs)


class TestTrends:
    def test_improving_trend(self):
        data = [{"date": f"2024-01-{i+1:02d}", "score": 50 + i * 5} for i in range(7)]
        trend = analyze_weekly_trend(data)
        assert trend.trend == TrendDirection.IMPROVING

    def test_declining_trend(self):
        data = [{"date": f"2024-01-{i+1:02d}", "score": 90 - i * 5} for i in range(7)]
        trend = analyze_weekly_trend(data)
        assert trend.trend == TrendDirection.DECLINING

    def test_empty_data(self):
        trend = analyze_weekly_trend([])
        assert trend.average_score == 0


class TestDailyReport:
    def test_full_report(self):
        report = generate_daily_report(date="2024-01-15")
        assert report.date == "2024-01-15"
        assert 0 <= report.score.overall <= 100
        assert len(report.score.components) == 6
        assert isinstance(report.alerts, list)
        assert isinstance(report.recommendations, list)
        assert isinstance(report.highlights, list)

    def test_report_with_previous(self):
        report = generate_daily_report(date="2024-01-15", prev_score=60)
        assert report.compare_to_yesterday != 0

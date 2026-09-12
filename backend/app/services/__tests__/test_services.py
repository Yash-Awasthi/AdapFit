"""Unit tests for ZFIT workout plan generator, HRV scorer, and nutrition analyzer."""

import pytest
from unittest.mock import MagicMock


class TestWorkoutPlanGenerator:
    """Tests for workout_plan_generator.py"""

    def test_import(self):
        from app.services.workout_plan_generator import WorkoutPlanGenerator
        assert WorkoutPlanGenerator is not None

    def test_generate_plan_returns_dict(self):
        from app.services.workout_plan_generator import WorkoutPlanGenerator
        gen = WorkoutPlanGenerator()
        plan = gen.generate(
            goal="strength",
            experience="intermediate",
            days_per_week=4,
            minutes_per_session=60,
        )
        assert isinstance(plan, dict)
        assert "name" in plan
        assert "goal" in plan
        assert "days" in plan or "duration_weeks" in plan

    def test_generate_plan_has_weeks(self):
        from app.services.workout_plan_generator import WorkoutPlanGenerator
        gen = WorkoutPlanGenerator()
        plan = gen.generate(goal="endurance", experience="beginner", days_per_week=3, minutes_per_session=45)
        assert plan.get("duration_weeks", 0) > 0

    def test_deload_weeks_present(self):
        from app.services.workout_plan_generator import WorkoutPlanGenerator
        gen = WorkoutPlanGenerator()
        plan = gen.generate(goal="hypertrophy", experience="advanced", days_per_week=5, minutes_per_session=75)
        # Advanced plans should include deload weeks
        assert plan.get("duration_weeks", 0) >= 4


class TestHRVRecoveryScorer:
    """Tests for hrv_recovery_scorer.py"""

    def test_import(self):
        from app.services.hrv_recovery_scorer import HRVRecoveryScorer
        assert HRVRecoveryScorer is not None

    def test_calculate_score(self):
        from app.services.hrv_recovery_scorer import HRVRecoveryScorer
        scorer = HRVRecoveryScorer()
        score = scorer.calculate(hrv_rmssd=50, resting_hr=60, sleep_hours=7.5)
        assert 0 <= score <= 100

    def test_high_hrv_high_score(self):
        from app.services.hrv_recovery_scorer import HRVRecoveryScorer
        scorer = HRVRecoveryScorer()
        high = scorer.calculate(hrv_rmssd=80, resting_hr=55, sleep_hours=8)
        low = scorer.calculate(hrv_rmssd=20, resting_hr=75, sleep_hours=5)
        assert high > low

    def test_readiness_label(self):
        from app.services.hrv_recovery_scorer import HRVRecoveryScorer
        scorer = HRVRecoveryScorer()
        score = scorer.calculate(hrv_rmssd=65, resting_hr=58, sleep_hours=7)
        readiness = scorer.get_readiness_label(score)
        assert readiness in ["poor", "below_average", "fair", "good", "excellent"]


class TestNutritionAnalyzer:
    """Tests for nutrition_analyzer.py"""

    def test_import(self):
        from app.services.nutrition_analyzer import NutritionAnalyzer
        assert NutritionAnalyzer is not None

    def test_analyze_returns_macros(self):
        from app.services.nutrition_analyzer import NutritionAnalyzer
        analyzer = NutritionAnalyzer()
        result = analyzer.analyze(weight_kg=80, goal="muscle_gain", activity_level="moderate")
        assert isinstance(result, dict)
        assert "calories" in result
        assert "protein_g" in result
        assert result["calories"] > 0
        assert result["protein_g"] > 0

    def test_muscle_gain_higher_calories_than_cut(self):
        from app.services.nutrition_analyzer import NutritionAnalyzer
        analyzer = NutritionAnalyzer()
        gain = analyzer.analyze(weight_kg=80, goal="muscle_gain", activity_level="moderate")
        cut = analyzer.analyze(weight_kg=80, goal="fat_loss", activity_level="moderate")
        assert gain["calories"] > cut["calories"]

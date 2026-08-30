"""Tests for fitness_planner.py — AI fitness planning service."""

import pytest
from app.services.fitness_planner import (
    FitnessPlanner, UserProfile, FitnessGoal, ActivityLevel,
    TrainingStyle, SplitType, FoodItem, MealType,
)


@pytest.fixture
def male_profile():
    return UserProfile(
        user_id="test_male",
        age=30,
        weight_kg=80,
        height_cm=180,
        sex="male",
        activity_level=ActivityLevel.MODERATE,
        fitness_goal=FitnessGoal.BULK,
        equipment_available=["barbell", "dumbbells", "bench", "cable_machine"],
        workout_frequency=4,
    )


@pytest.fixture
def female_profile():
    return UserProfile(
        user_id="test_female",
        age=25,
        weight_kg=60,
        height_cm=165,
        sex="female",
        activity_level=ActivityLevel.LIGHT,
        fitness_goal=FitnessGoal.CUT,
        equipment_available=["dumbbells", "bench"],
        workout_frequency=3,
    )


class TestBMR:
    def test_male_bmr(self):
        bmr = FitnessPlanner.calculate_bmr(80, 180, 30, "male")
        assert 1500 < bmr < 2000

    def test_female_bmr(self):
        bmr = FitnessPlanner.calculate_bmr(60, 165, 25, "female")
        assert 1200 < bmr < 1600

    def test_bmr_scales_with_weight(self):
        bmr_light = FitnessPlanner.calculate_bmr(60, 180, 30, "male")
        bmr_heavy = FitnessPlanner.calculate_bmr(100, 180, 30, "male")
        assert bmr_heavy > bmr_light


class TestTDEE:
    def test_sedentary_tdee(self):
        bmr = 1700
        tdee = FitnessPlanner.calculate_tdee(bmr, ActivityLevel.SEDENTARY)
        assert tdee == pytest.approx(1700 * 1.2, rel=0.01)

    def test_very_active_tdee(self):
        bmr = 1700
        tdee = FitnessPlanner.calculate_tdee(bmr, ActivityLevel.VERY_ACTIVE)
        assert tdee == pytest.approx(1700 * 1.9, rel=0.01)


class TestTargetCalories:
    def test_bulk_calories_above_tdee(self, male_profile):
        macros = FitnessPlanner.calculate_target_calories(male_profile)
        assert macros["calories"] > 2000
        assert macros["protein_g"] > 0
        assert macros["carbs_g"] > 0
        assert macros["fat_g"] > 0

    def test_cut_calories_below_tdee(self, female_profile):
        macros = FitnessPlanner.calculate_target_calories(female_profile)
        assert macros["calories"] < 2000

    def test_maintenance_equals_tdee(self):
        profile = UserProfile(
            user_id="test", age=30, weight_kg=75, height_cm=175,
            sex="male", activity_level=ActivityLevel.MODERATE,
            fitness_goal=FitnessGoal.MAINTENANCE,
        )
        macros = FitnessPlanner.calculate_target_calories(profile)
        bmr = FitnessPlanner.calculate_bmr(75, 175, 30, "male")
        tdee = FitnessPlanner.calculate_tdee(bmr, ActivityLevel.MODERATE)
        assert macros["calories"] == pytest.approx(tdee, rel=0.01)


class TestMealDistribution:
    def test_5_meal_distribution(self):
        dist = FitnessPlanner.distribute_meals(2500, 150, 300, 80, 5)
        assert len(dist) == 5
        total_cal = sum(m["calories"] for m in dist)
        assert total_cal == pytest.approx(2500, rel=0.05)

    def test_3_meal_distribution(self):
        dist = FitnessPlanner.distribute_meals(2000, 120, 250, 70, 3)
        assert len(dist) == 3
        total_cal = sum(m["calories"] for m in dist)
        assert total_cal == pytest.approx(2000, rel=0.05)


class TestFoodSearch:
    def test_create_search_text(self):
        food = FoodItem(
            name="Chicken Breast", serving_size=100, serving_unit="g",
            calories=165, protein_g=31, carbs_g=0, fat_g=3.6,
            tags=["lean", "protein"],
        )
        text = FitnessPlanner.create_food_search_text(food)
        assert "Chicken Breast" in text
        assert "165" in text
        assert "31" in text

    def test_score_food_match(self):
        food = FoodItem(
            name="Chicken", serving_size=100, serving_unit="g",
            calories=165, protein_g=31, carbs_g=0, fat_g=3.6,
            tags=["lean"],
        )
        score = FitnessPlanner.score_food_match(food, {"protein_g": 30}, [])
        assert score > 0

    def test_score_food_restriction(self):
        food = FoodItem(
            name="Beef", serving_size=100, serving_unit="g",
            calories=250, protein_g=26, carbs_g=0, fat_g=15,
            tags=["meat"],
        )
        score = FitnessPlanner.score_food_match(food, {}, ["meat"])
        assert score == 0.0


class TestWorkoutPlanning:
    def test_full_body_split(self):
        split = FitnessPlanner.generate_split(SplitType.FULL_BODY, 3, TrainingStyle.HYPERTROPHY)
        assert len(split) == 3
        assert all("muscles" in d for d in split)

    def test_upper_lower_split(self):
        split = FitnessPlanner.generate_split(SplitType.UPPER_LOWER, 4, TrainingStyle.HYPERTROPHY)
        assert len(split) == 4

    def test_ppl_split(self):
        split = FitnessPlanner.generate_split(SplitType.PUSH_PULL_LEGS, 6, TrainingStyle.HYPERTROPHY)
        assert len(split) == 6

    def test_select_exercises(self):
        exercises = FitnessPlanner.select_exercises(
            ["chest", "back"], ["barbell", "dumbbells"]
        )
        assert len(exercises) >= 4

    def test_reps_for_strength(self):
        reps = FitnessPlanner.get_reps_for_style(TrainingStyle.STRENGTH)
        assert "3" in reps or "5" in reps

    def test_reps_for_hypertrophy(self):
        reps = FitnessPlanner.get_reps_for_style(TrainingStyle.HYPERTROPHY)
        assert "8" in reps or "12" in reps

    def test_rest_for_strength(self):
        rest = FitnessPlanner.get_rest_for_style(TrainingStyle.STRENGTH)
        assert rest >= 120

    def test_rest_for_endurance(self):
        rest = FitnessPlanner.get_rest_for_style(TrainingStyle.ENDURANCE)
        assert rest <= 60


class TestCompletePlan:
    def test_generate_complete_plan(self, male_profile):
        plan = FitnessPlanner.generate_complete_plan(male_profile)
        assert plan.user_id == "test_male"
        assert plan.meal_plan is not None
        assert plan.workout_plan is not None
        assert len(plan.summary) > 0

    def test_plan_has_macros(self, male_profile):
        plan = FitnessPlanner.generate_complete_plan(male_profile)
        macros = plan.meal_plan["target_macros"]
        assert macros["calories"] > 0
        assert macros["protein_g"] > 0

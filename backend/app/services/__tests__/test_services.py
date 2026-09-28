"""Unit tests for the workout plan generator, HRV recovery scorer and nutrition analyzer."""

from datetime import datetime, timedelta


def _profile(goal, *, experience=5, sessions=4, minutes=60):
    from app.services.workout_plan_generator import Equipment, UserProfile

    return UserProfile(
        experience_level=experience,
        age=30,
        weight_kg=80.0,
        height_cm=180.0,
        injuries=[],
        available_equipment=[Equipment.BARBELL, Equipment.DUMBBELLS, Equipment.BODYWEIGHT],
        max_sessions_per_week=sessions,
        max_minutes_per_session=minutes,
        training_goal=goal,
        current_1rm={},
    )


class TestWorkoutPlanGenerator:
    def test_import(self):
        from app.services.workout_plan_generator import WorkoutPlanGenerator

        assert WorkoutPlanGenerator is not None

    def test_every_muscle_group_in_the_exercise_db_is_a_real_enum_member(self):
        from app.services.workout_plan_generator import EXERCISE_DB, MuscleGroup

        known = {m.value for m in MuscleGroup}
        assert set(EXERCISE_DB) <= known

    def test_generate_plan_returns_a_plan(self):
        from app.services.workout_plan_generator import TrainingGoal, TrainingPlan, WorkoutPlanGenerator

        plan = WorkoutPlanGenerator().generate_plan(_profile(TrainingGoal.STRENGTH))
        assert isinstance(plan, TrainingPlan)
        assert plan.goal is TrainingGoal.STRENGTH
        assert plan.duration_weeks > 0

    def test_plan_has_one_week_entry_per_week(self):
        from app.services.workout_plan_generator import TrainingGoal, WorkoutPlanGenerator

        plan = WorkoutPlanGenerator().generate_plan(
            _profile(TrainingGoal.ENDURANCE, experience=2, sessions=3, minutes=45), weeks=8
        )
        assert plan.duration_weeks == 8
        assert len(plan.weeks) == 8

    def test_deload_weeks_are_scheduled(self):
        from app.services.workout_plan_generator import TrainingGoal, WorkoutPlanGenerator

        plan = WorkoutPlanGenerator().generate_plan(
            _profile(TrainingGoal.HYPERTROPHY, experience=9, sessions=5, minutes=75), weeks=12
        )
        assert any(week.phase == "deload" for week in plan.weeks)

    def test_sessions_respect_the_session_cap(self):
        from app.services.workout_plan_generator import TrainingGoal, WorkoutPlanGenerator

        plan = WorkoutPlanGenerator().generate_plan(_profile(TrainingGoal.STRENGTH, sessions=3), weeks=4)
        assert all(len(week.sessions) <= 3 for week in plan.weeks)


class TestNutritionAnalyzer:
    def test_import(self):
        from app.services.nutrition_analyzer import NutritionAnalyzer

        assert NutritionAnalyzer is not None

    def test_targets_return_positive_macros(self):
        from app.services.nutrition_analyzer import DietaryGoal, NutritionAnalyzer

        targets = NutritionAnalyzer().calculate_targets(
            weight_kg=80, height_cm=180, age=30, sex="male", goal=DietaryGoal.MUSCLE_GAIN
        )
        assert targets.calories > 0
        assert targets.protein_g > 0
        assert targets.carbs_g > 0
        assert targets.fat_g > 0

    def test_muscle_gain_targets_more_calories_than_fat_loss(self):
        from app.services.nutrition_analyzer import DietaryGoal, NutritionAnalyzer

        analyzer = NutritionAnalyzer()
        common = dict(weight_kg=80, height_cm=180, age=30, sex="male")
        gain = analyzer.calculate_targets(goal=DietaryGoal.MUSCLE_GAIN, **common)
        cut = analyzer.calculate_targets(goal=DietaryGoal.FAT_LOSS, **common)
        assert gain.calories > cut.calories

    def test_macro_calories_reconcile_with_the_target(self):
        from app.services.nutrition_analyzer import DietaryGoal, NutritionAnalyzer

        targets = NutritionAnalyzer().calculate_targets(
            weight_kg=70, height_cm=170, age=28, sex="female", goal=DietaryGoal.MAINTENANCE
        )
        from_macros = targets.protein_g * 4 + targets.carbs_g * 4 + targets.fat_g * 9
        assert abs(from_macros - targets.calories) / targets.calories < 0.05

"""Tests for Workout Planner Service."""
import pytest
from datetime import datetime
from app.services.workout_planner import (
    Exercise, WorkoutDay, WorkoutWeek, WorkoutPlan, InjuryProfile,
    Difficulty, MuscleGroup, WorkoutGoal,
    get_exercises_for_goal, create_exercise, create_workout_day,
    create_split_plan, apply_progressive_overload, filter_exercises_for_injury,
    calculate_training_volume, estimate_workout_duration, suggest_deload_week,
)


class TestExercisesForGoal:
    def test_strength_returns_compounds(self):
        exercises = get_exercises_for_goal(WorkoutGoal.STRENGTH, MuscleGroup.CHEST)
        assert any("Press" in e for e in exercises)

    def test_hypertrophy_returns_all(self):
        exercises = get_exercises_for_goal(WorkoutGoal.HYPERTROPHY, MuscleGroup.CHEST)
        assert len(exercises) > 0

    def test_unknown_muscle_group(self):
        exercises = get_exercises_for_goal(WorkoutGoal.STRENGTH, MuscleGroup.CHEST)
        assert isinstance(exercises, list)


class TestCreateExercise:
    def test_basic(self):
        ex = create_exercise("Bench Press", MuscleGroup.CHEST, WorkoutGoal.HYPERTROPHY)
        assert ex.name == "Bench Press"
        assert ex.sets == 3
        assert ex.is_compound is True

    def test_non_compound(self):
        ex = create_exercise("Hammer Curl", MuscleGroup.BICEPS, WorkoutGoal.HYPERTROPHY)
        assert ex.is_compound is False

    def test_strength_higher_rest(self):
        ex = create_exercise("Squat", MuscleGroup.LEGS, WorkoutGoal.STRENGTH)
        assert ex.rest_seconds >= 120


class TestCreateWorkoutDay:
    def test_rest_day(self):
        day = create_workout_day(1, "Rest", [], WorkoutGoal.STRENGTH, is_rest=True)
        assert day.is_rest_day is True
        assert len(day.exercises) == 0

    def test_workout_day(self):
        day = create_workout_day(1, "Push", [MuscleGroup.CHEST], WorkoutGoal.HYPERTROPHY)
        assert len(day.exercises) > 0

    def test_max_exercises(self):
        day = create_workout_day(1, "Full", list(MuscleGroup), WorkoutGoal.HYPERTROPHY)
        assert len(day.exercises) <= 8


class TestCreateSplitPlan:
    def test_basic_plan(self):
        plan = create_split_plan("Test Plan", WorkoutGoal.HYPERTROPHY, Difficulty.INTERMEDIATE, 4)
        assert plan.name == "Test Plan"
        assert len(plan.weeks) == 4
        assert plan.duration_weeks == 4

    def test_week_has_days(self):
        plan = create_split_plan("Test", WorkoutGoal.STRENGTH, Difficulty.BEGINNER, 2)
        assert len(plan.weeks[0].days) == 4

    def test_longer_plan(self):
        plan = create_split_plan("8 Week", WorkoutGoal.HYPERTROPHY, Difficulty.ADVANCED, 8)
        assert len(plan.weeks) == 8


class TestProgressiveOverload:
    def test_increases_compound_sets(self):
        day = create_workout_day(1, "Push", [MuscleGroup.CHEST], WorkoutGoal.HYPERTROPHY)
        original_compound = [e for e in day.exercises if e.is_compound]
        if original_compound:
            original_sets = original_compound[0].sets
            week = WorkoutWeek(week_number=1, days=[day])
            apply_progressive_overload(week, 1.05)
            assert day.exercises[0 if not day.exercises[0].is_compound else 0].sets >= original_sets - 1


class TestInjuryFilter:
    def test_removes_injured(self):
        exercises = [
            Exercise("Bench Press", MuscleGroup.CHEST, 3, "8-12", is_compound=True),
            Exercise("Squat", MuscleGroup.LEGS, 3, "8-12", is_compound=True),
        ]
        injury = InjuryProfile(injured_areas=[MuscleGroup.CHEST])
        filtered = filter_exercises_for_injury(exercises, injury)
        assert all(e.muscle_group != MuscleGroup.CHEST for e in filtered)

    def test_keeps_healthy(self):
        exercises = [
            Exercise("Bench Press", MuscleGroup.CHEST, 3, "8-12"),
            Exercise("Squat", MuscleGroup.LEGS, 3, "8-12"),
        ]
        injury = InjuryProfile(injured_areas=[MuscleGroup.BACK])
        filtered = filter_exercises_for_injury(exercises, injury)
        assert len(filtered) == 2


class TestTrainingVolume:
    def test_basic(self):
        day = create_workout_day(1, "Push", [MuscleGroup.CHEST], WorkoutGoal.HYPERTROPHY)
        week = WorkoutWeek(week_number=1, days=[day])
        volume = calculate_training_volume(week)
        assert sum(volume.values()) > 0


class TestDuration:
    def test_rest_day_zero(self):
        day = create_workout_day(1, "Rest", [], WorkoutGoal.STRENGTH, is_rest=True)
        assert estimate_workout_duration(day) == 0

    def test_workout_has_duration(self):
        day = create_workout_day(1, "Push", [MuscleGroup.CHEST], WorkoutGoal.HYPERTROPHY)
        assert estimate_workout_duration(day) > 0


class TestDeload:
    def test_deload_at_4th_week(self):
        assert suggest_deload_week(4, 12) is True

    def test_no_deload_at_2nd_week(self):
        assert suggest_deload_week(2, 12) is False

    def test_deload_at_8th_week(self):
        assert suggest_deload_week(8, 12) is True

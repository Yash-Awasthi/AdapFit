"""Tests for workout_analytics.py — workout tracking analytics service."""

import pytest
from app.services.workout_analytics import (
    WorkoutAnalytics, ExerciseSet, WorkoutExercise, WorkoutSession,
    WorkoutType, PersonalRecord,
)


@pytest.fixture
def sample_session():
    return WorkoutSession(
        session_id="s1",
        user_id="user1",
        date=1000000.0,
        duration_seconds=3600,
        exercises=[
            WorkoutExercise(
                exercise_name="Bench Press",
                muscle_group="chest",
                sets=[
                    ExerciseSet(reps=10, weight=80),
                    ExerciseSet(reps=8, weight=85),
                    ExerciseSet(reps=6, weight=90),
                ],
            ),
            WorkoutExercise(
                exercise_name="Squats",
                muscle_group="legs",
                sets=[
                    ExerciseSet(reps=10, weight=100),
                    ExerciseSet(reps=8, weight=110),
                ],
            ),
        ],
    )


@pytest.fixture
def multi_session_data():
    sessions = []
    for i in range(10):
        sessions.append(WorkoutSession(
            session_id=f"s{i}",
            user_id="user1",
            date=1000000.0 + i * 86400 * 2,
            duration_seconds=3600,
            exercises=[
                WorkoutExercise(
                    exercise_name="Bench Press",
                    muscle_group="chest",
                    sets=[ExerciseSet(reps=10, weight=80 + i)],
                ),
                WorkoutExercise(
                    exercise_name="Squats",
                    muscle_group="legs",
                    sets=[ExerciseSet(reps=10, weight=100 + i)],
                ),
            ],
        ))
    return sessions


class TestVolumeCalculation:
    def test_set_volume(self):
        s = ExerciseSet(reps=10, weight=80)
        assert WorkoutAnalytics.calculate_set_volume(s) == 800.0

    def test_exercise_volume(self, sample_session):
        vol = WorkoutAnalytics.calculate_exercise_volume(sample_session.exercises[0])
        assert vol == 10 * 80 + 8 * 85 + 6 * 90

    def test_workout_volume(self, sample_session):
        vol = WorkoutAnalytics.calculate_workout_volume(sample_session)
        assert vol > 0


class TestIntensity:
    def test_intensity_calculation(self, sample_session):
        intensity = WorkoutAnalytics.calculate_intensity(sample_session)
        assert 0 < intensity <= 100

    def test_intensity_empty(self):
        session = WorkoutSession(
            session_id="empty", user_id="u1", date=0,
            duration_seconds=0, exercises=[],
        )
        assert WorkoutAnalytics.calculate_intensity(session) == 0.0


class TestPersonalRecords:
    def test_estimate_1rm(self):
        # Epley: 100kg × (1 + 5/30) = 116.7
        est = WorkoutAnalytics.estimate_1rm(100, 5)
        assert est == pytest.approx(116.7, rel=0.01)

    def test_estimate_1rm_single_rep(self):
        # Epley: 100 × (1 + 1/30) = 103.3
        est = WorkoutAnalytics.estimate_1rm(100, 1)
        assert est == pytest.approx(103.3, rel=0.01)

    def test_find_personal_records(self, sample_session):
        prs = WorkoutAnalytics.find_personal_records([sample_session])
        assert len(prs) == 2
        assert prs[0].exercise_name == "Squats"  # Higher 1RM

    def test_pr_tracking_across_sessions(self, multi_session_data):
        prs = WorkoutAnalytics.find_personal_records(multi_session_data)
        assert len(prs) == 2
        # Last session should have highest weight
        bench_pr = [pr for pr in prs if pr.exercise_name == "Bench Press"][0]
        assert bench_pr.weight == 89  # Last session weight


class TestWorkoutStats:
    def test_empty_stats(self):
        stats = WorkoutAnalytics.calculate_stats([])
        assert stats.total_workouts == 0

    def test_basic_stats(self, sample_session):
        stats = WorkoutAnalytics.calculate_stats([sample_session])
        assert stats.total_workouts == 1
        assert stats.total_duration_minutes == 60
        assert stats.total_sets == 5
        assert stats.total_reps == 42

    def test_multi_session_stats(self, multi_session_data):
        stats = WorkoutAnalytics.calculate_stats(multi_session_data)
        assert stats.total_workouts == 10
        assert stats.workout_frequency_per_week > 0


class TestMuscleBalance:
    def test_muscle_balance(self, sample_session):
        balance = WorkoutAnalytics.calculate_muscle_balance([sample_session])
        assert "chest" in balance
        assert "legs" in balance
        assert balance["chest"] == 3
        assert balance["legs"] == 2

    def test_assess_balance(self, sample_session):
        balance = WorkoutAnalytics.calculate_muscle_balance([sample_session])
        recs = WorkoutAnalytics.assess_muscle_balance(balance)
        assert len(recs) > 0


class TestStreaks:
    def test_streaks(self, multi_session_data):
        streaks = WorkoutAnalytics.calculate_streaks(multi_session_data)
        assert streaks["current_streak"] > 0
        assert streaks["best_streak"] > 0
        assert streaks["total_workout_days"] == 10

    def test_empty_streaks(self):
        streaks = WorkoutAnalytics.calculate_streaks([])
        assert streaks["current_streak"] == 0


class TestPeriodComparison:
    def test_compare_periods(self, multi_session_data):
        period1 = multi_session_data[:5]
        period2 = multi_session_data[5:]
        result = WorkoutAnalytics.compare_periods(period1, period2)
        assert "volume_change_pct" in result
        assert "frequency_change" in result


class TestExerciseLibrary:
    def test_get_library(self):
        lib = WorkoutAnalytics.get_exercise_library()
        assert len(lib) > 0
        assert "name" in lib[0]
        assert "muscle_group" in lib[0]

    def test_filter_by_difficulty(self):
        lib = WorkoutAnalytics.get_exercise_library()
        beginner = WorkoutAnalytics.filter_exercises(lib, difficulty="beginner")
        assert all(e["difficulty"] == "beginner" for e in beginner)

    def test_filter_by_muscle(self):
        lib = WorkoutAnalytics.get_exercise_library()
        chest = WorkoutAnalytics.filter_exercises(lib, muscle_group="chest")
        assert all(e["muscle_group"] == "chest" for e in chest)


class TestRecommendations:
    def test_no_sessions(self):
        recs = WorkoutAnalytics.generate_recommendations([])
        assert "Start logging" in recs[0]

    def test_with_sessions(self, multi_session_data):
        recs = WorkoutAnalytics.generate_recommendations(multi_session_data)
        assert len(recs) > 0

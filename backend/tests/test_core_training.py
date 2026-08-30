"""Tests for core_training.py — core training assessment service."""

import pytest
from app.services.core_training import (
    CoreTrainingAnalyzer, PullupRecord, GripType,
    WellnessEntry, BreathingExercise,
)


@pytest.fixture
def pullup_records():
    return [
        PullupRecord(date="2024-01-01", sets=5, max_reps=10, total_reps=40, grip_type=GripType.OVERHAND),
        PullupRecord(date="2024-01-08", sets=5, max_reps=12, total_reps=48, grip_type=GripType.OVERHAND),
        PullupRecord(date="2024-01-15", sets=5, max_reps=14, total_reps=55, grip_type=GripType.UNDERHAND),
        PullupRecord(date="2024-01-22", sets=5, max_reps=15, total_reps=60, grip_type=GripType.OVERHAND),
    ]


@pytest.fixture
def wellness_entry():
    return WellnessEntry(
        mood=7.0, energy=6.0, stress=4.0, sleep_hours=7.5,
        relationships=6.0, stress_management=7.0, self_confidence=7.0,
        emotional_balance=6.0, mental_resilience=6.0, focus_clarity=7.0,
    )


class TestValidation:
    def test_valid_record(self):
        r = PullupRecord(date="2024-01-01", sets=5, max_reps=10, total_reps=50)
        valid, errors = CoreTrainingAnalyzer.validate_record(r)
        assert valid
        assert errors == []

    def test_invalid_record(self):
        r = PullupRecord(date="2024-01-01", sets=0, max_reps=0, total_reps=0)
        valid, errors = CoreTrainingAnalyzer.validate_record(r)
        assert not valid
        assert len(errors) > 0


class TestPersonalBest:
    def test_new_pb(self, pullup_records):
        assert CoreTrainingAnalyzer.is_new_personal_best(20, pullup_records)

    def test_not_pb(self, pullup_records):
        assert not CoreTrainingAnalyzer.is_new_personal_best(10, pullup_records)

    def test_first_record(self):
        assert CoreTrainingAnalyzer.is_new_personal_best(5, [])


class TestVolume:
    def test_total_volume(self, pullup_records):
        vol = CoreTrainingAnalyzer.total_volume(pullup_records)
        assert vol == 40 + 48 + 55 + 60

    def test_avg_reps_per_set(self):
        r = PullupRecord(date="x", sets=5, max_reps=10, total_reps=50)
        assert CoreTrainingAnalyzer.avg_reps_per_set(r) == 10.0

    def test_total_sets(self, pullup_records):
        assert CoreTrainingAnalyzer.total_sets(pullup_records) == 20

    def test_volume_in_range(self, pullup_records):
        vol = CoreTrainingAnalyzer.volume_in_range(pullup_records, "2024-01-08", "2024-01-15")
        assert vol == 48 + 55


class TestOneRM:
    def test_1rm_estimation(self):
        # Epley: 10 × (1 + 10/30) = 13.3
        rm = CoreTrainingAnalyzer.estimate_1rm(10)
        assert rm == 13.3

    def test_1rm_single(self):
        rm = CoreTrainingAnalyzer.estimate_1rm(1)
        assert rm == 1.0


class TestProgression:
    def test_improving(self, pullup_records):
        rate = CoreTrainingAnalyzer.calculate_progression_rate(pullup_records)
        assert rate.trend == "improving"
        assert rate.reps_gained_per_week > 0

    def test_insufficient_data(self):
        rate = CoreTrainingAnalyzer.calculate_progression_rate([])
        assert rate.trend == "insufficient_data"


class TestGripDistribution:
    def test_distribution(self, pullup_records):
        dist = CoreTrainingAnalyzer.grip_distribution(pullup_records)
        assert len(dist) > 0
        assert sum(d["percent"] for d in dist) == pytest.approx(100, rel=0.1)


class TestRecommendations:
    def test_strength_recommendation(self):
        rec = CoreTrainingAnalyzer.recommend_next_session(15, "strength")
        assert rec["target_sets"] == 5
        assert rec["rest_seconds"] == 180

    def test_endurance_recommendation(self):
        rec = CoreTrainingAnalyzer.recommend_next_session(15, "endurance")
        assert rec["rest_seconds"] == 60


class TestWellness:
    def test_mental_score(self, wellness_entry):
        score = CoreTrainingAnalyzer.calculate_mental_score(wellness_entry)
        assert 5.0 <= score <= 8.0

    def test_wellness_score(self, wellness_entry):
        result = CoreTrainingAnalyzer.calculate_wellness_score(wellness_entry)
        assert 1.0 <= result.wellness_score <= 10.0
        assert result.mental_score > 0

    def test_low_wellness(self):
        entry = WellnessEntry(mood=2, energy=2, stress=9, sleep_hours=4,
                             relationships=2, stress_management=2, self_confidence=2,
                             emotional_balance=2, mental_resilience=2, focus_clarity=2)
        result = CoreTrainingAnalyzer.calculate_wellness_score(entry)
        assert result.wellness_score < 4

    def test_energy_level(self, wellness_entry):
        energy = CoreTrainingAnalyzer.calculate_energy_level(wellness_entry, 3)
        assert 1.0 <= energy <= 10.0


class TestBreathing:
    def test_exercises(self):
        exercises = CoreTrainingAnalyzer.get_breathing_exercises()
        assert len(exercises) >= 4
        assert all(isinstance(e, BreathingExercise) for e in exercises)

    def test_box_breathing(self):
        exercises = CoreTrainingAnalyzer.get_breathing_exercises()
        box = [e for e in exercises if e.name == "Box Breathing"][0]
        assert box.inhale_seconds == 4
        assert box.exhale_seconds == 4


class TestExerciseLibrary:
    def test_library(self):
        lib = CoreTrainingAnalyzer.get_exercise_library()
        assert len(lib) >= 8
        assert "muscle_group" in lib[0]

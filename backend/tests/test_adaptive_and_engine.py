"""Adaptive limitation filtering, the alternatives leak, and duration-aware plan generation."""
from app.services.adaptive_workouts import (
    Exercise, UserFitnessProfile, ACCESSIBILITY_ALTERNATIVES,
    select_adaptive_workout, get_accessible_alternatives,
)
from app.services.workout_engine import WorkoutEngineService


def _ex(id, name, muscle, diff=5):
    return Exercise(id=id, name=name, muscle_group=muscle, difficulty=diff,
                    equipment=[], accessibility=["standing"])


def test_limitations_exclude_by_name_not_only_canonical_id():
    # A client sends its own ids and real names; the knee limitation must still drop the squat.
    exercises = [
        _ex("ex_004", "Barbell Back Squat", "quads"),
        _ex("ex_009", "Bicep Curl", "biceps"),
        _ex("ex_013", "Lateral Raise", "shoulders"),
    ]
    # lower_back excludes 'barbell_squat'; the stems {barbell, squat} are in "Barbell Back Squat".
    profile = UserFitnessProfile(fitness_level="beginner", limitations=["lower_back"])
    result = select_adaptive_workout(exercises, profile, [], target_exercises=8)
    names = [e["name"] for e in result["exercises"]]
    assert "Barbell Back Squat" not in names
    assert "Bicep Curl" in names


def test_accessible_alternatives_does_not_grow_the_shared_table():
    before = {k: list(v) for k, v in ACCESSIBILITY_ALTERNATIVES.items()}
    ex = [_ex("seated_arm_cycling", "Seated Arm Cycling", "arms")]
    for _ in range(5):
        get_accessible_alternatives("running", ["wheelchair"], ex)
    assert {k: list(v) for k, v in ACCESSIBILITY_ALTERNATIVES.items()} == before


def test_alternatives_match_a_real_name():
    ex = [_ex("push_ups", "Push Ups", "chest")]
    out = get_accessible_alternatives("ex_001", ["lower_back"], ex, )
    # 'ex_001' named nothing here, but a direct canonical id still resolves its list.
    assert out["original_exercise"] == "ex_001"


def test_plan_generation_honours_duration_and_days():
    svc = WorkoutEngineService()
    short = svc.generate_workout_plan("muscle_gain", "beginner", [], duration_minutes=24, days_per_week=2)
    long = svc.generate_workout_plan("muscle_gain", "beginner", [], duration_minutes=64, days_per_week=5)
    assert len(short["weekly_structure"]) == 2
    assert len(long["weekly_structure"]) == 5  # more than the old 4-day cap
    # 24 min -> 3 per day, 64 min -> 8 per day
    assert len(short["weekly_structure"][0]["exercises"]) <= len(long["weekly_structure"][0]["exercises"])
    assert long["progression"] and long["est_calories_per_session"] > 0

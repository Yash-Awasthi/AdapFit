"""Fitness assessment: 1RM estimation, fitness tests, and bodyweight standards."""
from typing import Optional
from pydantic import BaseModel, Field


class OneRepMaxEstimate(BaseModel):
    exercise: str
    weight_kg: float
    reps: int
    estimated_1rm: float
    formula: str
    strength_level: str  # "beginner", "novice", "intermediate", "advanced", "elite"
    percent_of_1rm: float


class FitnessTest(BaseModel):
    test_name: str
    result: float
    unit: str
    percentile: float  # 0-100
    rating: str  # "poor", "below_average", "average", "above_average", "excellent"


# Strength standards (bodyweight multiples for bench press, approximate)
BENCH_STANDARDS = {
    "beginner": (0.0, 0.5),
    "novice": (0.5, 0.75),
    "intermediate": (0.75, 1.0),
    "advanced": (1.0, 1.5),
    "elite": (1.5, 2.5),
}

SQUAT_STANDARDS = {
    "beginner": (0.0, 0.75),
    "novice": (0.75, 1.0),
    "intermediate": (1.0, 1.5),
    "advanced": (1.5, 2.0),
    "elite": (2.0, 3.0),
}


def estimate_1rm(weight_kg: float, reps: int, exercise: str = "unknown") -> OneRepMaxEstimate:
    """
    Estimate 1RM using Epley formula: 1RM = weight * (1 + reps/30)
    Also Brzycki: 1RM = weight * (36 / (37 - reps)) for cross-check
    """
    if reps <= 0:
        reps = 1
    if reps == 1:
        return OneRepMaxEstimate(
            exercise=exercise, weight_kg=weight_kg, reps=1,
            estimated_1rm=weight_kg, formula="direct",
            strength_level="unknown", percent_of_1rm=100.0,
        )

    epley = weight_kg * (1 + reps / 30)
    brzycki = weight_kg * (36 / (37 - reps))
    avg_1rm = round((epley + brzycki) / 2, 1)

    return OneRepMaxEstimate(
        exercise=exercise,
        weight_kg=weight_kg,
        reps=reps,
        estimated_1rm=avg_1rm,
        formula="epley+brzycki average",
        strength_level="unknown",
        percent_of_1rm=round((weight_kg / avg_1rm) * 100, 1) if avg_1rm > 0 else 0,
    )


def assess_strength(exercise: str, weight_kg: float, reps: int, bodyweight_kg: float) -> OneRepMaxEstimate:
    """Estimate 1RM and classify strength level."""
    est = estimate_1rm(weight_kg, reps, exercise)

    standards = BENCH_STANDARDS if "bench" in exercise.lower() else SQUAT_STANDARDS
    ratio = est.estimated_1rm / bodyweight_kg if bodyweight_kg > 0 else 0

    level = "beginner"
    for name, (low, high) in standards.items():
        if low <= ratio < high:
            level = name
            break
    else:
        if ratio >= 2.0:
            level = "elite"

    est.strength_level = level
    return est


# Fitness test norms (percentile approximations)
FITNESS_TESTS = {
    "pushups_1min": {
        "name": "Push-ups in 1 minute",
        "unit": "reps",
        "norms": {"poor": 10, "below_average": 20, "average": 30, "above_average": 40, "excellent": 50},
    },
    "plank_hold": {
        "name": "Plank hold",
        "unit": "seconds",
        "norms": {"poor": 30, "below_average": 60, "average": 90, "above_average": 120, "excellent": 180},
    },
    "wall_sit": {
        "name": "Wall sit hold",
        "unit": "seconds",
        "norms": {"poor": 30, "below_average": 60, "average": 90, "above_average": 120, "excellent": 150},
    },
    "bodyweight_squats_1min": {
        "name": "Bodyweight squats in 1 minute",
        "unit": "reps",
        "norms": {"poor": 15, "below_average": 25, "average": 35, "above_average": 45, "excellent": 55},
    },
}


def assess_fitness_test(test_id: str, result: float) -> FitnessTest:
    """Assess a fitness test result against norms."""
    test = FITNESS_TESTS.get(test_id)
    if not test:
        return FitnessTest(
            test_name=test_id, result=result, unit="unknown",
            percentile=50, rating="average",
        )

    norms = test["norms"]
    # Calculate percentile
    if result >= norms["excellent"]:
        pct, rating = 95, "excellent"
    elif result >= norms["above_average"]:
        pct, rating = 80, "above_average"
    elif result >= norms["average"]:
        pct, rating = 60, "average"
    elif result >= norms["below_average"]:
        pct, rating = 40, "below_average"
    else:
        pct, rating = 20, "poor"

    return FitnessTest(
        test_name=test["name"], result=result,
        unit=test["unit"], percentile=pct, rating=rating,
    )


def available_tests() -> list:
    return [
        {"id": k, "name": v["name"], "unit": v["unit"]}
        for k, v in FITNESS_TESTS.items()
    ]

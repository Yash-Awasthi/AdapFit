"""Quick workout template engine.

Generates time-constrained workouts based on:
- Available time (15, 30, 45, 60 minutes)
- Equipment access
- Target muscles
- Workout type (strength, cardio, full body)
"""

from __future__ import annotations
import random
from dataclasses import dataclass


@dataclass
class QuickExercise:
    exercise_id: str
    name: str
    sets: int
    reps: str
    rest_seconds: int
    target_muscle: str
    equipment_needed: str
    rpe_target: float
    tempo: str


# ============================================================
# Exercise pools by equipment and muscle
# ============================================================

BODYWEIGHT_EXERCISES = [
    QuickExercise("pushups", "Push-Up", 3, "12-15", 45, "chest", "bodyweight", 6.0, "2-0-2"),
    QuickExercise("squats", "Bodyweight Squat", 3, "15-20", 45, "quadriceps", "bodyweight", 6.0, "2-1-2"),
    QuickExercise("lunges", "Walking Lunge", 3, "10/leg", 45, "quadriceps", "bodyweight", 6.5, "2-0-2"),
    QuickExercise("plank", "Plank Hold", 3, "45s", 30, "core", "bodyweight", 5.0, "iso"),
    QuickExercise("glute-bridge", "Glute Bridge", 3, "15", 30, "glutes", "bodyweight", 5.0, "2-2-2"),
    QuickExercise("mountain-climbers", "Mountain Climbers", 3, "20", 30, "core", "bodyweight", 7.0, "fast"),
    QuickExercise("burpees", "Burpees", 3, "10", 60, "full_body", "bodyweight", 8.0, "fast"),
    QuickExercise("diamond-pushup", "Diamond Push-Up", 3, "10", 45, "triceps", "bodyweight", 7.0, "2-0-2"),
    QuickExercise("jumping-jacks", "Jumping Jacks", 3, "30", 20, "cardio", "bodyweight", 5.5, "fast"),
    QuickExercise("step-ups", "Step-Up", 3, "12/leg", 45, "quadriceps", "bodyweight", 6.5, "2-0-1"),
    QuickExercise("calf-raises", "Calf Raise", 3, "20", 20, "calves", "bodyweight", 4.0, "2-1-2"),
    QuickExercise("superman", "Superman Hold", 3, "12", 30, "lower_back", "bodyweight", 5.0, "2-2-2"),
    QuickExercise("side-plank", "Side Plank", 3, "30s/side", 30, "core", "bodyweight", 5.5, "iso"),
    QuickExercise("high-knees", "High Knees", 3, "30s", 20, "cardio", "bodyweight", 7.0, "fast"),
]

DUMBBELL_EXERCISES = [
    QuickExercise("db-shoulder-press", "Dumbbell Shoulder Press", 3, "10", 60, "shoulders", "dumbbells", 7.0, "2-0-2"),
    QuickExercise("db-curl", "Dumbbell Bicep Curl", 3, "12", 45, "biceps", "dumbbells", 6.0, "2-1-2"),
    QuickExercise("db-row", "Dumbbell Row", 3, "10/arm", 45, "back", "dumbbells", 7.0, "2-1-2"),
    QuickExercise("db-squat", "Goblet Squat", 3, "12", 60, "quadriceps", "dumbbells", 7.0, "3-1-2"),
    QuickExercise("db-romanian-deadlift", "DB Romanian Deadlift", 3, "12", 60, "hamstrings", "dumbbells", 7.0, "3-1-2"),
    QuickExercise("db-chest-fly", "Dumbbell Chest Fly", 3, "12", 45, "chest", "dumbbells", 6.0, "2-2-2"),
    QuickExercise("db-lateral-raise", "Lateral Raise", 3, "12", 30, "shoulders", "dumbbells", 5.5, "2-1-2"),
    QuickExercise("db-tricep-extension", "Overhead Tricep Extension", 3, "12", 30, "triceps", "dumbbells", 6.0, "2-1-2"),
]

BARBELL_EXERCISES = [
    QuickExercise("bench-press", "Barbell Bench Press", 4, "8", 90, "chest", "barbell", 7.5, "3-1-2"),
    QuickExercise("barbell-squat", "Barbell Back Squat", 4, "8", 120, "quadriceps", "barbell", 8.0, "3-2-2"),
    QuickExercise("deadlift", "Conventional Deadlift", 4, "6", 120, "hamstrings", "barbell", 8.5, "2-1-3"),
    QuickExercise("overhead-press", "Barbell Overhead Press", 3, "8", 90, "shoulders", "barbell", 7.5, "2-0-2"),
    QuickExercise("barbell-row", "Barbell Row", 3, "8", 90, "back", "barbell", 7.5, "2-1-2"),
]


def _get_available_exercises(equipment: list[str]) -> list[QuickExercise]:
    """Filter exercises by available equipment."""
    available = list(BODYWEIGHT_EXERCISES)  # Always include bodyweight

    for ex in DUMBBELL_EXERCISES:
        if any(eq in equipment for eq in ["dumbbells", "dumbbells,bands"]):
            available.append(ex)

    for ex in BARBELL_EXERCISES:
        if any(eq in equipment for eq in ["barbell", "full_gym", "barbell,dumbbells"]):
            available.append(ex)

    return available


def _select_for_muscles(
    exercises: list[QuickExercise],
    target_muscles: list[str],
    count: int,
) -> list[QuickExercise]:
    """Select exercises targeting specific muscles."""
    if not target_muscles:
        return random.sample(exercises, min(count, len(exercises)))

    targeted = [e for e in exercises if e.target_muscle in target_muscles]
    general = [e for e in exercises if e.target_muscle not in target_muscles]

    selected = random.sample(targeted, min(count, len(targeted)))
    remaining = count - len(selected)
    if remaining > 0 and general:
        selected.extend(random.sample(general, min(remaining, len(general))))

    return selected


def generate_quick_workout(
    duration_minutes: int = 30,
    equipment: list[str] | None = None,
    target_muscles: list[str] | None = None,
    workout_type: str = "full_body",
) -> dict:
    """Generate a quick workout based on constraints.

    Args:
        duration_minutes: Available time (15, 30, 45, 60)
        equipment: Available equipment
        target_muscles: Preferred muscles to train
        workout_type: strength, cardio, full_body

    Returns:
        Complete workout plan
    """
    if equipment is None:
        equipment = ["bodyweight"]

    available = _get_available_exercises(equipment)

    # Calculate exercises based on time
    # ~3-4 min per exercise (sets * (reps_time + rest))
    exercises_per_session = max(3, min(8, duration_minutes // 4))

    if workout_type == "cardio":
        exercises_per_session = max(4, duration_minutes // 3)

    exercises = _select_for_muscles(available, target_muscles or [], exercises_per_session)

    # Adjust sets based on time
    if duration_minutes <= 15:
        for ex in exercises:
            ex.sets = 2
    elif duration_minutes <= 30:
        for ex in exercises:
            ex.sets = 3
    else:
        for ex in exercises:
            ex.sets = 4

    # Estimate total duration
    total_seconds = 0
    for ex in exercises:
        reps_num = 10  # default
        try:
            reps_str = ex.reps.split("-")[0].split("/")[0].replace("s", "")
            reps_num = int(reps_str)
        except (ValueError, IndexError):
            pass
        set_time = (reps_num * 3) + ex.rest_seconds  # ~3s per rep
        total_seconds += set_time * ex.sets

    actual_duration = round(total_seconds / 60, 1)

    return {
        "duration_minutes": duration_minutes,
        "estimated_duration_minutes": actual_duration,
        "workout_type": workout_type,
        "equipment_used": equipment,
        "target_muscles": target_muscles or ["full_body"],
        "exercise_count": len(exercises),
        "total_sets": sum(e.sets for e in exercises),
        "exercises": [
            {
                "exercise_id": e.exercise_id,
                "name": e.name,
                "sets": e.sets,
                "reps": e.reps,
                "rest_seconds": e.rest_seconds,
                "target_muscle": e.target_muscle,
                "rpe_target": e.rpe_target,
                "tempo": e.tempo,
            }
            for e in exercises
        ],
        "warmup_needed": duration_minutes > 20,
        "stretch_needed": duration_minutes > 30,
    }


# Pre-built quick templates
QUICK_TEMPLATES = {
    "15min_bodyweight": lambda: generate_quick_workout(15, ["bodyweight"], None, "full_body"),
    "15min_upper": lambda: generate_quick_workout(15, ["bodyweight"], ["chest", "back", "shoulders"], "strength"),
    "15min_lower": lambda: generate_quick_workout(15, ["bodyweight"], ["quadriceps", "hamstrings", "glutes"], "strength"),
    "15min_core": lambda: generate_quick_workout(15, ["bodyweight"], ["core"], "strength"),
    "15min_cardio": lambda: generate_quick_workout(15, ["bodyweight"], None, "cardio"),
    "30min_bodyweight": lambda: generate_quick_workout(30, ["bodyweight"], None, "full_body"),
    "30min_dumbbell": lambda: generate_quick_workout(30, ["bodyweight", "dumbbells"], None, "strength"),
    "30min_strength": lambda: generate_quick_workout(30, ["bodyweight", "dumbbells"], ["chest", "back", "quadriceps"], "strength"),
    "30min_hiit": lambda: generate_quick_workout(30, ["bodyweight"], None, "cardio"),
    "45min_gym": lambda: generate_quick_workout(45, ["bodyweight", "dumbbells", "barbell"], None, "strength"),
    "60min_full": lambda: generate_quick_workout(60, ["bodyweight", "dumbbells", "barbell"], None, "strength"),
}


quick_workout_engine = __import__(__name__)

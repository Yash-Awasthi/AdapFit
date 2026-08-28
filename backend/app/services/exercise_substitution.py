"""Exercise substitution engine.

Suggests alternative exercises based on:
- Same primary muscle group
- Available equipment
- Lower axial load rating (for fatigue management)
- Similar movement pattern
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class ExerciseVariant:
    exercise_id: str
    name: str
    primary_muscle: str
    equipment: str
    axial_load: int  # 1-5
    difficulty: str  # beginner, intermediate, advanced
    movement_pattern: str  # push, pull, squat, hinge, carry, isolation


# Substitution map: exercise_id -> list of alternatives
SUBSTITUTIONS: dict[str, list[ExerciseVariant]] = {
    "barbell-back-squat": [
        ExerciseVariant("leg-press", "Leg Press", "quadriceps", "machine", 2, "beginner", "squat"),
        ExerciseVariant("goblet-squat", "Goblet Squat", "quadriceps", "dumbbells", 2, "beginner", "squat"),
        ExerciseVariant("bulgarian-split-squat", "Bulgarian Split Squat", "quadriceps", "dumbbells", 3, "intermediate", "squat"),
        ExerciseVariant("hack-squat", "Hack Squat", "quadriceps", "machine", 2, "intermediate", "squat"),
        ExerciseVariant("front-squat", "Front Squat", "quadriceps", "barbell", 4, "advanced", "squat"),
    ],
    "conventional-deadlift": [
        ExerciseVariant("romanian-deadlift", "Romanian Deadlift", "hamstrings", "barbell", 3, "intermediate", "hinge"),
        ExerciseVariant("hip-thrust", "Hip Thrust", "glutes", "barbell", 2, "intermediate", "hinge"),
        ExerciseVariant("cable-pull-through", "Cable Pull Through", "hamstrings", "cable", 1, "beginner", "hinge"),
        ExerciseVariant("leg-curl", "Leg Curl", "hamstrings", "machine", 1, "beginner", "isolation"),
        ExerciseVariant("db-rdl", "DB Romanian Deadlift", "hamstrings", "dumbbells", 2, "beginner", "hinge"),
    ],
    "bench-press": [
        ExerciseVariant("dumbbell-bench-press", "Dumbbell Bench Press", "chest", "dumbbells", 2, "intermediate", "push"),
        ExerciseVariant("incline-dumbbell-press", "Incline DB Press", "chest", "dumbbells", 2, "intermediate", "push"),
        ExerciseVariant("chest-dip", "Chest Dip", "chest", "bodyweight", 2, "intermediate", "push"),
        ExerciseVariant("push-up", "Push-Up", "chest", "bodyweight", 1, "beginner", "push"),
        ExerciseVariant("machine-chest-press", "Machine Chest Press", "chest", "machine", 1, "beginner", "push"),
    ],
    "overhead-press": [
        ExerciseVariant("dumbbell-shoulder-press", "DB Shoulder Press", "shoulders", "dumbbells", 2, "intermediate", "push"),
        ExerciseVariant("lateral-raise", "Lateral Raise", "shoulders", "dumbbells", 1, "beginner", "isolation"),
        ExerciseVariant("arnold-press", "Arnold Press", "shoulders", "dumbbells", 2, "intermediate", "push"),
        ExerciseVariant("machine-press", "Machine Shoulder Press", "shoulders", "machine", 1, "beginner", "push"),
    ],
    "barbell-row": [
        ExerciseVariant("seated-cable-row", "Seated Cable Row", "back", "cable", 1, "beginner", "pull"),
        ExerciseVariant("dumbbell-row", "Dumbbell Row", "back", "dumbbells", 2, "beginner", "pull"),
        ExerciseVariant("machine-row", "Machine Row", "back", "machine", 1, "beginner", "pull"),
        ExerciseVariant("inverted-row", "Inverted Row", "back", "bodyweight", 1, "beginner", "pull"),
    ],
    "pull-up": [
        ExerciseVariant("lat-pulldown", "Lat Pulldown", "back", "cable", 1, "beginner", "pull"),
        ExerciseVariant("assisted-pull-up", "Assisted Pull-Up", "back", "machine", 2, "beginner", "pull"),
        ExerciseVariant("cable-pulldown", "Cable Pulldown", "back", "cable", 1, "beginner", "pull"),
        ExerciseVariant("chin-up", "Chin-Up", "back", "bodyweight", 2, "intermediate", "pull"),
    ],
    "barbell-curl": [
        ExerciseVariant("dumbbell-curl", "Dumbbell Curl", "biceps", "dumbbells", 1, "beginner", "isolation"),
        ExerciseVariant("hammer-curl", "Hammer Curl", "biceps", "dumbbells", 1, "beginner", "isolation"),
        ExerciseVariant("cable-curl", "Cable Curl", "biceps", "cable", 1, "beginner", "isolation"),
        ExerciseVariant("preacher-curl", "Preacher Curl", "biceps", "machine", 1, "beginner", "isolation"),
    ],
    "tricep-dip": [
        ExerciseVariant("tricep-pushdown", "Tricep Pushdown", "triceps", "cable", 1, "beginner", "isolation"),
        ExerciseVariant("overhead-tricep-extension", "Overhead Extension", "triceps", "dumbbells", 1, "beginner", "isolation"),
        ExerciseVariant("skull-crusher", "Skull Crusher", "triceps", "barbell", 2, "intermediate", "isolation"),
        ExerciseVariant("close-grip-bench", "Close-Grip Bench", "triceps", "barbell", 3, "intermediate", "push"),
    ],
}


def get_substitutions(
    exercise_id: str,
    equipment: list[str] | None = None,
    max_axial_load: int | None = None,
    difficulty: str | None = None,
) -> list[dict]:
    """Get substitution options for an exercise.

    Args:
        exercise_id: Current exercise to substitute
        equipment: Available equipment to filter by
        max_axial_load: Maximum acceptable axial load (1-5)
        difficulty: Preferred difficulty level

    Returns:
        List of substitution options with reasons
    """
    alternatives = SUBSTITUTIONS.get(exercise_id, [])

    # Apply filters
    filtered = alternatives
    if equipment:
        filtered = [a for a in filtered if a.equipment in equipment or a.equipment == "bodyweight"]
    if max_axial_load is not None:
        filtered = [a for a in filtered if a.axial_load <= max_axial_load]
    if difficulty:
        filtered = [a for a in filtered if a.difficulty == difficulty]

    # If no matches after filtering, return all (unfiltered)
    if not filtered:
        filtered = alternatives

    return [
        {
            "exercise_id": a.exercise_id,
            "name": a.name,
            "primary_muscle": a.primary_muscle,
            "equipment": a.equipment,
            "axial_load": a.axial_load,
            "difficulty": a.difficulty,
            "movement_pattern": a.movement_pattern,
            "reason": _get_reason(exercise_id, a),
        }
        for a in filtered
    ]


def _get_reason(original_id: str, alternative: ExerciseVariant) -> str:
    """Generate a human-readable reason for the substitution."""
    original_alts = SUBSTITUTIONS.get(original_id, [])
    original = next((a for a in original_alts if a.exercise_id == alternative.exercise_id), None)

    if original and alternative.axial_load < (original.axial_load if original else 5):
        return f"Lower axial load ({alternative.axial_load} vs {original.axial_load}) — reduces spinal stress"
    if alternative.equipment == "bodyweight":
        return "Bodyweight option — no equipment needed"
    if alternative.equipment == "machine":
        return "Machine variant — easier to control form when fatigued"
    return f"Same muscle ({alternative.primary_muscle}), similar movement pattern"


exercise_substitution_engine = __import__(__name__)

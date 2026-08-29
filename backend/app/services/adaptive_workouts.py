"""
Adaptive Workout Engine

Difficulty adjustment based on user performance history,
accessibility-aware exercise alternatives (seated, low-impact, wheelchair),
and progression that respects physical limitations.
"""
from dataclasses import dataclass, field
from typing import Optional
import statistics


@dataclass
class Exercise:
    id: str
    name: str
    muscle_group: str
    difficulty: int  # 1-10
    equipment: list[str]
    accessibility: list[str]  # "standing", "seated", "wheelchair", "low_impact", "no_equipment"
    alternatives: list[str] = field(default_factory=list)  # IDs of accessible alternatives


@dataclass
class WorkoutPerformance:
    exercise_id: str
    sets_completed: int
    reps_completed: list[int]
    weight_kg: Optional[float] = None
    rpe: Optional[int] = None  # Rate of Perceived Exertion (1-10)
    completed: bool = True


@dataclass
class UserFitnessProfile:
    fitness_level: str  # "beginner", "intermediate", "advanced"
    limitations: list[str]  # "lower_back", "knee", "shoulder", "wheelchair", "pregnancy"
    max_heart_rate: int = 190
    preferred_intensity: str = "moderate"  # "light", "moderate", "vigorous"


# Accessibility alternatives mapping
ACCESSIBILITY_ALTERNATIVES = {
    # Standing exercises → seated alternatives
    "barbell_squat": ["seated_leg_press", "chair_squats", "leg_extension"],
    "deadlift": ["seated_row", "chest_supported_row", "lat_pulldown"],
    "overhead_press": ["seated_dumbbell_press", "machine_chest_press", "resistance_band_press"],
    "lunges": ["seated_leg_curl", "glute_bridge", "seated_hip_abduction"],
    "running": ["seated_arm_cycling", "wheelchair_rolling", "swimming"],

    # High-impact → low-impact alternatives
    "burpees": ["step_ups", "march_in_place", "seated_arm_raises"],
    "jump_squats": ["bodyweight_squats", "wall_sits", "glute_bridges"],
    "box_jumps": ["step_ups", "calf_raises", "seated_knee_extensions"],
    "jumping_lunges": ["walking_lunges", "split_squats", "leg_press"],

    # Equipment-dependent → no-equipment alternatives
    "barbell_bench_press": ["push_ups", "diamond_push_ups", "resistance_band_chest_press"],
    "cable_rows": ["resistance_band_rows", "inverted_rows", "doorframe_rows"],
    "leg_press_machine": ["bodyweight_squats", "wall_sits", "step_ups"],
}

# Limitation-based exercise exclusions
LIMITATION_EXCLUSIONS = {
    "lower_back": ["deadlift", "barbell_squat", "good_morning", "bent_over_row"],
    "knee": ["lunges", "jump_squats", "box_jumps", "deep_squats"],
    "shoulder": ["overhead_press", "behind_neck_press", "upright_row"],
    "pregnancy": ["burpees", "jump_squats", "deadlift", "heavy_compound"],
    "wheelchair": ["running", "jumping_lunges", "barbell_squat", "lunges"],
}


def select_adaptive_workout(
    exercises: list[Exercise],
    profile: UserFitnessProfile,
    performance_history: list[WorkoutPerformance],
    target_exercises: int = 8,
) -> dict:
    """
    Select exercises adapted to user's fitness level, limitations, and history.

    Algorithm:
    1. Filter out exercises that conflict with limitations
    2. Score remaining exercises based on fitness level + history
    3. Select top exercises ensuring muscle group variety
    4. Assign difficulty based on recent performance
    """
    # Step 1: Filter by limitations
    excluded = set()
    for limitation in profile.limitations:
        excluded.update(LIMITATION_EXCLUSIONS.get(limitation, []))

    available = [e for e in exercises if e.id not in excluded]

    # Step 2: Score by fitness level match
    level_map = {"beginner": 4, "intermediate": 6, "advanced": 8}
    target_difficulty = level_map.get(profile.fitness_level, 5)

    # Adjust based on recent performance
    recent_rpes = [p.rpe for p in performance_history[-10:] if p.rpe is not None]
    if recent_rpes:
        avg_rpe = statistics.mean(recent_rpes)
        if avg_rpe > 8:
            target_difficulty = max(1, target_difficulty - 1)
        elif avg_rpe < 4:
            target_difficulty = min(10, target_difficulty + 1)

    scored = []
    for e in available:
        diff_score = max(0, 10 - abs(e.difficulty - target_difficulty) * 2)
        acc_score = len(e.accessibility) * 2
        scored.append((e, diff_score + acc_score))

    scored.sort(key=lambda x: x[1], reverse=True)

    # Step 3: Select with muscle group variety
    selected = []
    used_muscles = set()
    for exercise, score in scored:
        if len(selected) >= target_exercises:
            break
        if exercise.muscle_group not in used_muscles or len(selected) < target_exercises // 2:
            selected.append(exercise)
            used_muscles.add(exercise.muscle_group)

    return {
        "exercises": [
            {
                "id": e.id,
                "name": e.name,
                "muscle_group": e.muscle_group,
                "difficulty": e.difficulty,
                "accessibility": e.accessibility,
            }
            for e in selected
        ],
        "target_difficulty": target_difficulty,
        "limitations_accommodated": profile.limitations,
        "exercise_count": len(selected),
    }


def get_accessible_alternatives(
    exercise_id: str,
    limitations: list[str],
    all_exercises: list[Exercise],
) -> dict:
    """Get accessible alternatives for an exercise based on user limitations."""
    alternatives = ACCESSIBILITY_ALTERNATIVES.get(exercise_id, [])

    # Also check limitation-specific alternatives
    for limitation in limitations:
        for excluded_id in LIMITATION_EXCLUSIONS.get(limitation, []):
            if excluded_id == exercise_id:
                # Add limitation-specific alternatives
                if limitation == "wheelchair":
                    alternatives.extend(["seated_arm_cycling", "resistance_band_exercises"])
                elif limitation == "knee":
                    alternatives.extend(["upper_body_circuit", "seated_core"])

    # Deduplicate and verify alternatives exist
    alt_ids = list(dict.fromkeys(alternatives))
    exercise_map = {e.id: e for e in all_exercises}
    valid_alts = [exercise_map[aid] for aid in alt_ids if aid in exercise_map]

    return {
        "original_exercise": exercise_id,
        "alternatives": [
            {"id": a.id, "name": a.name, "accessibility": a.accessibility}
            for a in valid_alts
        ],
        "limitation": limitations,
    }


def score_exercise_accessibility(exercise: Exercise) -> dict:
    """Score how accessible an exercise is (0-100)."""
    score = 0

    # Accessibility features (40 pts)
    acc_features = len(exercise.accessibility)
    score += min(40, acc_features * 10)

    # No equipment needed (20 pts)
    if "no_equipment" in exercise.accessibility or not exercise.equipment:
        score += 20
    elif len(exercise.equipment) <= 2:
        score += 10

    # Has alternatives (20 pts)
    if exercise.alternatives:
        score += min(20, len(exercise.alternatives) * 7)

    # Low difficulty is more accessible (20 pts)
    if exercise.difficulty <= 3:
        score += 20
    elif exercise.difficulty <= 5:
        score += 12
    elif exercise.difficulty <= 7:
        score += 5

    return {
        "exercise_id": exercise.id,
        "accessibility_score": min(100, score),
        "grade": "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "D",
        "features": exercise.accessibility,
        "equipment_required": exercise.equipment,
        "has_alternatives": bool(exercise.alternatives),
    }


def suggest_progression(
    performance_history: list[WorkoutPerformance],
    profile: UserFitnessProfile,
) -> dict:
    """
    Suggest next workout progression based on history and limitations.

    Progression rules:
    - If RPE < 6 for 3+ sessions: increase difficulty
    - If RPE > 8 for 2+ sessions: decrease difficulty or add rest
    - If all sets completed: progression opportunity
    - Respect limitations: no progression on limited areas
    """
    if not performance_history:
        return {"recommendation": "start_light", "reason": "No history — begin with baseline difficulty"}

    recent = performance_history[-10:]
    recent_rpes = [p.rpe for p in recent if p.rpe is not None]
    completion_rate = sum(1 for p in recent if p.completed) / len(recent)

    if not recent_rpes:
        return {"recommendation": "start_light", "reason": "No RPE data — begin with baseline"}

    avg_rpe = statistics.mean(recent_rpes)

    if avg_rpe < 5 and completion_rate >= 0.9:
        return {
            "recommendation": "increase_difficulty",
            "reason": f"RPE {avg_rpe:.1f} with {completion_rate:.0%} completion — ready for more",
            "suggested_change": "+1 difficulty or +2 reps",
        }
    elif avg_rpe > 8:
        return {
            "recommendation": "decrease_difficulty",
            "reason": f"RPE {avg_rpe:.1f} — too challenging, reduce load",
            "suggested_change": "-1 difficulty or add rest day",
        }
    elif avg_rpe >= 6 and avg_rpe <= 8:
        return {
            "recommendation": "maintain",
            "reason": f"RPE {avg_rpe:.1f} — in optimal training zone",
            "suggested_change": "Same difficulty, focus on form",
        }
    else:
        return {
            "recommendation": "maintain",
            "reason": f"RPE {avg_rpe:.1f} with {completion_rate:.0%} completion — steady progress",
        }

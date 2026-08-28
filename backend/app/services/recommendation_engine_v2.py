"""
Smart Workout Recommendation Engine v2.
Suggests workouts based on recovery score, training history, goals,
muscle fatigue, ACWR, and periodization phase.
"""
from typing import Optional
from pydantic import BaseModel, Field
from statistics import mean


class WorkoutRecommendation(BaseModel):
    workout_type: str  # "strength", "hypertrophy", "endurance", "mobility", "rest"
    focus_muscles: list[str]
    intensity: str  # "low", "moderate", "high", "very_high"
    volume_level: str  # "low", "moderate", "high"
    duration_minutes: int
    exercises: list[dict]
    rationale: str
    confidence: float  # 0-1
    alternatives: list[str]


class UserProfile(BaseModel):
    recovery_score: int = 50
    readiness_state: str = "MODERATE"
    fitness_level: str = "intermediate"
    primary_goal: str = "hypertrophy"
    preferred_days_per_week: int = 4
    recent_workouts: list[dict] = []
    sore_muscles: list[str] = []
    acwr: float = 1.0
    sleep_score: float = 80
    days_since_last_workout: int = 1
    equipment_access: list[str] = ["bodyweight", "dumbbells", "barbell"]
    training_history: dict = {}  # muscle -> {volume_7d, sessions_14d}


# Muscle recovery times (hours after adequate training)
MUSCLE_RECOVERY_HOURS = {
    "chest": 48, "back": 48, "shoulders": 36,
    "biceps": 24, "triceps": 36,
    "quadriceps": 72, "hamstrings": 72, "glutes": 48,
    "calves": 24, "core": 24,
}


def _get_readiness_modifier(readiness: str) -> float:
    return {"OPTIMAL": 1.0, "MODERATE": 0.85, "REDUCED": 0.65, "DEPLETED": 0.4}.get(readiness, 0.85)


def _get_fatigued_muscles(history: dict, sore: list[str]) -> list[str]:
    """Identify muscles that need more recovery time."""
    fatigued = set(sore)
    for muscle, data in history.items():
        vol_7d = data.get("volume_7d", 0)
        sessions = data.get("sessions_14d", 0)
        avg_vol_per_session = vol_7d / max(sessions, 1)
        if avg_vol_per_session > 2000 or sessions >= 4:
            fatigued.add(muscle)
    return list(fatigued)


def _select_muscles(goal: str, fatigued: list[str], available: list[str]) -> list[str]:
    """Select muscles to train based on goal and fatigue status."""
    muscle_groups = {
        "push": ["chest", "shoulders", "triceps"],
        "pull": ["back", "biceps"],
        "legs": ["quadriceps", "hamstrings", "glutes", "calves"],
        "upper": ["chest", "back", "shoulders", "biceps", "triceps"],
        "lower": ["quadriceps", "hamstrings", "glutes", "calves"],
        "full_body": ["chest", "back", "shoulders", "quadriceps", "hamstrings"],
    }

    # Prefer muscles not in fatigue list
    all_muscles = []
    for group in muscle_groups.values():
        all_muscles.extend(group)

    trainable = [m for m in all_muscles if m not in fatigued]

    if goal == "hypertrophy":
        return trainable[:4] if len(trainable) >= 4 else trainable
    elif goal == "strength":
        return trainable[:3] if len(trainable) >= 3 else trainable
    elif goal == "endurance":
        return trainable[:5] if len(trainable) >= 5 else trainable
    else:
        return trainable[:4] if len(trainable) >= 4 else trainable


def _get_intensity(recovery: int, acwr: float, readiness_modifier: float) -> str:
    """Determine intensity based on recovery and load status."""
    effective = recovery * readiness_modifier

    if acwr > 1.3:
        return "low"  # Overreaching
    elif acwr > 1.1:
        return "moderate"  # Sweet spot upper
    elif effective >= 80:
        return "high"
    elif effective >= 60:
        return "moderate"
    else:
        return "low"


def _get_volume(intensity: str, goal: str, fatigue_count: int) -> str:
    """Determine volume level."""
    if fatigue_count > 3:
        return "low"
    if intensity == "low":
        return "low"
    if goal == "hypertrophy":
        return "high" if intensity in ("high", "moderate") else "moderate"
    elif goal == "strength":
        return "moderate"
    elif goal == "endurance":
        return "high"
    return "moderate"


def _get_duration(intensity: str, volume: str, goal: str) -> int:
    """Estimate workout duration."""
    base = 45
    if intensity == "low":
        base = 30
    elif intensity == "high":
        base = 55
    if volume == "high":
        base += 10
    elif volume == "low":
        base -= 10
    return max(20, min(90, base))


EXERCISE_DB = {
    "chest": [
        {"id": "barbell-bench-press", "name": "Barbell Bench Press", "type": "compound"},
        {"id": "dumbbell-incline-press", "name": "Incline Dumbbell Press", "type": "compound"},
        {"id": "pushups", "name": "Push-ups", "type": "compound"},
    ],
    "back": [
        {"id": "barbell-bent-over-row", "name": "Barbell Row", "type": "compound"},
        {"id": "pullups", "name": "Pull-ups", "type": "compound"},
    ],
    "shoulders": [
        {"id": "overhead-press", "name": "Overhead Press", "type": "compound"},
    ],
    "biceps": [
        {"id": "barbell-curl", "name": "Barbell Curl", "type": "isolation"},
    ],
    "triceps": [
        {"id": "tricep-pushdown", "name": "Tricep Pushdown", "type": "isolation"},
    ],
    "quadriceps": [
        {"id": "barbell-squat", "name": "Barbell Squat", "type": "compound"},
        {"id": "leg-press", "name": "Leg Press", "type": "compound"},
    ],
    "hamstrings": [
        {"id": "romanian-deadlift", "name": "Romanian Deadlift", "type": "compound"},
    ],
    "glutes": [
        {"id": "hip-thrust", "name": "Hip Thrust", "type": "compound"},
    ],
    "calves": [
        {"id": "calf-raise", "name": "Calf Raise", "type": "isolation"},
    ],
    "core": [
        {"id": "plank", "name": "Plank", "type": "isolation"},
    ],
}


def _select_exercises(muscles: list[str], intensity: str) -> list[dict]:
    """Select specific exercises for the target muscles."""
    exercises = []
    reps_map = {
        "low": "12-15", "moderate": "8-12", "high": "6-8", "very_high": "3-5"
    }
    sets_map = {"low": 2, "moderate": 3, "high": 4, "very_high": 5}
    rpe_map = {"low": 6, "moderate": 7, "high": 8, "very_high": 9}

    for muscle in muscles:
        db_exercises = EXERCISE_DB.get(muscle, [])
        if db_exercises:
            ex = db_exercises[0]  # Pick first available
            exercises.append({
                "exercise_id": ex["id"],
                "name": ex["name"],
                "target_muscle": muscle,
                "sets": sets_map.get(intensity, 3),
                "target_reps": reps_map.get(intensity, "8-12"),
                "target_rpe": rpe_map.get(intensity, 7),
                "rest_seconds": 60 if intensity == "low" else 90,
            })
    return exercises


def recommend_workout(profile: UserProfile) -> WorkoutRecommendation:
    """Generate a smart workout recommendation."""
    readiness_mod = _get_readiness_modifier(profile.readiness_state)
    fatigued = _get_fatigued_muscles(profile.training_history, profile.sore_muscles)

    # If very fatigued or depleted, suggest rest or mobility
    if profile.readiness_state == "DEPLETED" or profile.recovery_score < 30:
        return WorkoutRecommendation(
            workout_type="rest",
            focus_muscles=[],
            intensity="low",
            volume_level="low",
            duration_minutes=0,
            exercises=[],
            rationale=f"Recovery score is {profile.recovery_score}/100 ({profile.readiness_state}). "
                      f"Rest day recommended to prevent overtraining.",
            confidence=0.95,
            alternatives=["Light yoga", "Walking", "Foam rolling", "Stretching"],
        )

    if profile.readiness_state == "REDUCED" or profile.recovery_score < 50:
        muscles = _select_muscles("mobility", fatigued, profile.equipment_access)
        return WorkoutRecommendation(
            workout_type="mobility",
            focus_muscles=muscles[:2],
            intensity="low",
            volume_level="low",
            duration_minutes=25,
            exercises=_select_exercises(muscles[:2], "low"),
            rationale=f"Recovery is reduced ({profile.recovery_score}/100). "
                      f"Light mobility work to maintain movement quality without adding fatigue.",
            confidence=0.85,
            alternatives=["Rest day", "Light walking"],
        )

    # Determine workout type based on ACWR and goal
    if profile.acwr > 1.3:
        workout_type = "endurance"
        goal_mod = "endurance"
    elif profile.acwr < 0.7:
        workout_type = "strength"
        goal_mod = "strength"
    else:
        workout_type = profile.primary_goal
        goal_mod = profile.primary_goal

    muscles = _select_muscles(goal_mod, fatigued, profile.equipment_access)
    intensity = _get_intensity(profile.recovery_score, profile.acwr, readiness_mod)
    volume = _get_volume(intensity, goal_mod, len(fatigued))
    duration = _get_duration(intensity, volume, goal_mod)
    exercises = _select_exercises(muscles, intensity)

    # Build rationale
    reasons = []
    if fatigued:
        reasons.append(f"Avoiding {', '.join(fatigued[:2])} (fatigued)")
    if profile.acwr > 1.1:
        reasons.append(f"ACWR {profile.acwr:.2f} — reducing intensity")
    elif profile.acwr < 0.8:
        reasons.append(f"ACWR {profile.acwr:.2f} — room to push harder")
    reasons.append(f"Recovery {profile.recovery_score}/100 supports {intensity} intensity")

    alternatives = ["Active recovery", "Cardio session", "Yoga"]
    if workout_type != "strength":
        alternatives.insert(0, "Strength training")
    if workout_type != "endurance":
        alternatives.insert(0, "Endurance work")

    return WorkoutRecommendation(
        workout_type=workout_type,
        focus_muscles=muscles,
        intensity=intensity,
        volume_level=volume,
        duration_minutes=duration,
        exercises=exercises,
        rationale=". ".join(reasons),
        confidence=0.8 if profile.recovery_score > 60 else 0.6,
        alternatives=alternatives[:3],
    )

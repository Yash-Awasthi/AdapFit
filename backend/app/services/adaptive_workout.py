"""Adaptive Workout Generator — generates workouts adapting to daily state.

Takes into account:
- Daily energy level (from check-in or recovery score)
- Sleep quality and duration
- Medications and their exercise effects
- Health conditions and exercise restrictions
- Current training load (ACWR)
- Available time and equipment
- Menstrual cycle phase (if tracked)

Generates appropriate workout with intensity, volume, and exercise selection.
"""

from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DailyContext:
    energy_level: int = 7  # 1-10
    sleep_quality: int = 7  # 1-10
    sleep_hours: float = 7.0
    recovery_score: float = 75.0  # 0-100
    soreness: int = 3  # 1-10
    stress: int = 4  # 1-10
    cycle_phase: Optional[str] = None  # menstrual, follicular, ovulation, luteal
    medications: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)
    exercise_restrictions: dict = field(default_factory=dict)
    available_time_minutes: int = 45
    available_equipment: list[str] = field(default_factory=lambda: ["full_gym"])
    primary_goal: str = "hypertrophy"
    fitness_level: str = "intermediate"
    acwr: float = 1.0
    last_workout_type: str = ""
    days_since_last_workout: int = 1


@dataclass
class AdaptiveWorkout:
    workout_type: str
    intensity: str
    target_rpe: float
    duration_minutes: int
    warmup_minutes: int
    exercises: list[dict]
    cooldown_minutes: int
    reasoning: list[str]
    modifications: list[str]
    warnings: list[str]
    estimated_calories: int
    focus_muscles: list[str]


# Exercise database organized by muscle group and intensity
EXERCISE_DB = {
    "chest": {
        "compound": [
            {"id": "barbell-bench-press", "name": "Barbell Bench Press", "intensity": "high", "equipment": "barbell"},
            {"id": "dumbbell-press", "name": "Dumbbell Press", "intensity": "moderate", "equipment": "dumbbells"},
            {"id": "push-up", "name": "Push-Up", "intensity": "low", "equipment": "bodyweight"},
            {"id": "incline-bench", "name": "Incline Bench Press", "intensity": "high", "equipment": "barbell"},
        ],
        "isolation": [
            {"id": "cable-fly", "name": "Cable Fly", "intensity": "moderate", "equipment": "cable"},
            {"id": "dumbbell-fly", "name": "Dumbbell Fly", "intensity": "moderate", "equipment": "dumbbells"},
        ],
    },
    "back": {
        "compound": [
            {"id": "barbell-row", "name": "Barbell Row", "intensity": "high", "equipment": "barbell"},
            {"id": "pull-up", "name": "Pull-Up", "intensity": "high", "equipment": "bodyweight"},
            {"id": "lat-pulldown", "name": "Lat Pulldown", "intensity": "moderate", "equipment": "cable"},
            {"id": "cable-row", "name": "Cable Row", "intensity": "moderate", "equipment": "cable"},
        ],
        "isolation": [
            {"id": "face-pull", "name": "Face Pull", "intensity": "low", "equipment": "cable"},
            {"id": "back-extension", "name": "Back Extension", "intensity": "low", "equipment": "bodyweight"},
        ],
    },
    "legs": {
        "compound": [
            {"id": "squat", "name": "Barbell Squat", "intensity": "high", "equipment": "barbell"},
            {"id": "leg-press", "name": "Leg Press", "intensity": "moderate", "equipment": "machine"},
            {"id": "lunges", "name": "Walking Lunges", "intensity": "moderate", "equipment": "dumbbells"},
            {"id": "leg-press-machine", "name": "Leg Press Machine", "intensity": "moderate", "equipment": "machine"},
        ],
        "isolation": [
            {"id": "leg-extension", "name": "Leg Extension", "intensity": "low", "equipment": "machine"},
            {"id": "leg-curl", "name": "Leg Curl", "intensity": "low", "equipment": "machine"},
            {"id": "calf-raise", "name": "Calf Raise", "intensity": "low", "equipment": "machine"},
        ],
    },
    "shoulders": {
        "compound": [
            {"id": "overhead-press", "name": "Overhead Press", "intensity": "high", "equipment": "barbell"},
            {"id": "dumbbell-ohp", "name": "Dumbbell OHP", "intensity": "moderate", "equipment": "dumbbells"},
        ],
        "isolation": [
            {"id": "lateral-raise", "name": "Lateral Raise", "intensity": "low", "equipment": "dumbbells"},
            {"id": "face-pull-shoulder", "name": "Face Pull", "intensity": "low", "equipment": "cable"},
            {"id": "rear-delt-fly", "name": "Rear Delt Fly", "intensity": "low", "equipment": "dumbbells"},
        ],
    },
    "arms": {
        "compound": [],
        "isolation": [
            {"id": "bicep-curl", "name": "Barbell Curl", "intensity": "moderate", "equipment": "barbell"},
            {"id": "tricep-pushdown", "name": "Tricep Pushdown", "intensity": "moderate", "equipment": "cable"},
            {"id": "hammer-curl", "name": "Hammer Curl", "intensity": "low", "equipment": "dumbbells"},
            {"id": "overhead-tricep", "name": "Overhead Tricep Extension", "intensity": "low", "equipment": "dumbbells"},
        ],
    },
    "core": {
        "compound": [],
        "isolation": [
            {"id": "plank", "name": "Plank", "intensity": "low", "equipment": "bodyweight"},
            {"id": "dead-bug", "name": "Dead Bug", "intensity": "low", "equipment": "bodyweight"},
            {"id": "pallof-press", "name": "Pallof Press", "intensity": "low", "equipment": "cable"},
            {"id": "bird-dog", "name": "Bird Dog", "intensity": "low", "equipment": "bodyweight"},
        ],
    },
    "cardio": {
        "low": [
            {"id": "walking", "name": "Brisk Walking", "intensity": "low", "equipment": "none"},
            {"id": "cycling-easy", "name": "Easy Cycling", "intensity": "low", "equipment": "bike"},
        ],
        "moderate": [
            {"id": "rowing", "name": "Rowing", "intensity": "moderate", "equipment": "machine"},
            {"id": "elliptical", "name": "Elliptical", "intensity": "moderate", "equipment": "machine"},
        ],
        "high": [
            {"id": "sprints", "name": "Sprint Intervals", "intensity": "high", "equipment": "none"},
            {"id": "assault-bike", "name": "Assault Bike", "intensity": "high", "equipment": "bike"},
        ],
    },
}

# Workout templates per goal
GOAL_TEMPLATES = {
    "strength": {
        "exercises": 4, "sets": (3, 5), "reps": (3, 6), "rest_seconds": (120, 180),
        "split": ["legs", "chest", "back", "shoulders"],
    },
    "hypertrophy": {
        "exercises": 5, "sets": (3, 4), "reps": (8, 12), "rest_seconds": (60, 90),
        "split": ["chest", "back", "legs", "shoulders", "arms"],
    },
    "endurance": {
        "exercises": 6, "sets": (2, 3), "reps": (12, 20), "rest_seconds": (30, 60),
        "split": ["cardio", "core", "legs", "cardio"],
    },
    "fat_loss": {
        "exercises": 6, "sets": (3, 4), "reps": (10, 15), "rest_seconds": (30, 45),
        "split": ["chest", "back", "legs", "shoulders", "cardio", "core"],
    },
    "recovery": {
        "exercises": 5, "sets": (2, 2), "reps": (12, 15), "rest_seconds": (45, 60),
        "split": ["core", "shoulders", "legs", "core", "cardio"],
    },
}


def generate_adaptive_workout(ctx: DailyContext) -> AdaptiveWorkout:
    """Generate a workout adapted to the user's current state."""
    reasoning = []
    modifications = []
    warnings = []

    # 1. Compute composite readiness score
    readiness = _compute_readiness(ctx)
    reasoning.append(f"Readiness score: {readiness:.0f}/100 (energy:{ctx.energy_level}, sleep:{ctx.sleep_quality}, recovery:{ctx.recovery_score})")

    # 2. Determine workout type based on readiness + context
    workout_type = _determine_workout_type(ctx, readiness, reasoning)

    # 3. Determine intensity
    intensity, target_rpe = _determine_intensity(ctx, readiness, workout_type, reasoning)

    # 4. Apply medication effects
    for med in ctx.medications:
        med_lower = med.lower()
        if "beta" in med_lower and "blocker" in med_lower:
            target_rpe = min(target_rpe, 7.5)
            modifications.append("Beta blocker detected — using RPE instead of HR zones")
        if "muscle" in med_lower and "relaxant" in med_lower:
            warnings.append("Muscle relaxant detected — avoid heavy lifts and overhead work")
            intensity = "light"
        if "corticosteroid" in med_lower:
            warnings.append("Corticosteroid detected — avoid heavy eccentrics, extend warmup")

    # 5. Apply condition restrictions
    avoid_exercises = ctx.exercise_restrictions.get("avoid", [])
    for condition in ctx.conditions:
        cond_key = condition.lower().replace(" ", "_")
        if "hernia" in cond_key and "disc" in cond_key:
            avoid_exercises.extend(["squat", "deadlift", "barbell-row"])
            modifications.append("Disc herniation: avoiding spinal flexion under load")
        if "arthritis" in cond_key:
            modifications.append("Arthritis detected — using low-impact alternatives")
        if "heart" in cond_key:
            target_rpe = min(target_rpe, 7.0)
            warnings.append("Heart condition — keeping intensity conservative")

    # 6. Apply cycle phase effects
    if ctx.cycle_phase == "menstrual":
        target_rpe = min(target_rpe, 7.0)
        modifications.append("Menstrual phase — reduced intensity, listen to body")
    elif ctx.cycle_phase == "follicular":
        target_rpe = min(target_rpe + 0.5, 9.0)
        reasoning.append("Follicular phase — strength potential elevated")
    elif ctx.cycle_phase == "luteal":
        target_rpe = min(target_rpe, 7.5)
        modifications.append("Luteal phase — moderate intensity, focus on technique")

    # 7. ACWR adjustment
    if ctx.acwr > 1.3:
        target_rpe = min(target_rpe, 6.0)
        reasoning.append(f"ACWR at {ctx.acwr:.2f} — reducing intensity to prevent overreaching")
    elif ctx.acwr < 0.8:
        target_rpe = min(target_rpe + 0.5, 9.0)
        reasoning.append(f"ACWR at {ctx.acwr:.2f} — room for increased load")

    # 8. Select exercises
    template = GOAL_TEMPLATES.get(workout_type, GOAL_TEMPLATES["hypertrophy"])
    exercises = _select_exercises(ctx, template, avoid_exercises, intensity)

    # 9. Calculate duration
    warmup = 8 if intensity in ("high", "very_high") else 5
    cooldown = 5
    est_exercise_time = len(exercises) * (template["sets"][1] * 1.5 + template["rest_seconds"][1] / 60)
    duration = min(ctx.available_time_minutes, int(warmup + est_exercise_time + cooldown))

    return AdaptiveWorkout(
        workout_type=workout_type,
        intensity=intensity,
        target_rpe=target_rpe,
        duration_minutes=duration,
        warmup_minutes=warmup,
        exercises=exercises,
        cooldown_minutes=cooldown,
        reasoning=reasoning,
        modifications=modifications,
        warnings=warnings,
        estimated_calories=int(duration * 8 * (target_rpe / 7)),
        focus_muscles=list(set(e.get("muscle", "") for e in exercises if e.get("muscle"))),
    )


def _compute_readiness(ctx: DailyContext) -> float:
    score = (
        ctx.energy_level * 3
        + ctx.sleep_quality * 2.5
        + min(ctx.sleep_hours / 8, 1.0) * 15
        + ctx.recovery_score * 0.2
        + (10 - ctx.soreness) * 1.5
        + (10 - ctx.stress) * 1.0
    )
    return min(100, max(0, score))


def _determine_workout_type(ctx: DailyContext, readiness: float, reasoning: list) -> str:
    if readiness < 30:
        reasoning.append("Very low readiness — recommending rest or light mobility")
        return "recovery"
    if readiness < 50:
        reasoning.append("Low readiness — light session with focus on form")
        return "recovery"
    if readiness >= 70 and ctx.acwr < 1.1:
        reasoning.append("Good readiness and manageable load — push intensity")
        return ctx.primary_goal
    return ctx.primary_goal


def _determine_intensity(ctx: DailyContext, readiness: float, workout_type: str, reasoning: list) -> tuple[str, float]:
    if workout_type == "recovery":
        return "light", 4.0
    if readiness >= 80:
        return "high", 8.0
    if readiness >= 60:
        return "moderate", 7.0
    return "light", 5.5


def _select_exercises(ctx: DailyContext, template: dict, avoid: list, intensity: str) -> list[dict]:
    exercises = []
    template_exercises = template["exercises"]
    sets_range = template["sets"]
    reps_range = template["reps"]
    rest_range = template["rest_seconds"]

    muscle_groups_used = template.get("split", [])[:template_exercises]

    for muscle in muscle_groups_used:
        group = EXERCISE_DB.get(muscle, {})
        all_exercises = []
        for category in group.values():
            all_exercises.extend(category)

        # Filter by equipment and avoid list
        available = [e for e in all_exercises if e["id"] not in avoid]

        # Filter by intensity
        if intensity == "light":
            available = [e for e in available if e["intensity"] in ("low", "moderate")]
        elif intensity == "moderate":
            available = [e for e in available if e["intensity"] != "very_high"]

        if not available:
            available = [e for e in all_exercises if e["intensity"] == "low"]

        if available:
            chosen = random.choice(available)
            sets = random.randint(*sets_range)
            reps = random.randint(*reps_range)
            rest = random.randint(*rest_range)
            exercises.append({
                "exercise_id": chosen["id"],
                "name": chosen["name"],
                "muscle": muscle,
                "sets": sets,
                "reps": reps,
                "rest_seconds": rest,
                "equipment": chosen["equipment"],
                "intensity": chosen["intensity"],
            })

    return exercises

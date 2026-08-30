"""Workout Planning Service.

Extracted from fitness-coach (inspiration).
Structured workout plans with weeks, days, exercises,
progressive overload, and injury-aware scheduling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Difficulty(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class MuscleGroup(Enum):
    CHEST = "chest"
    BACK = "back"
    SHOULDERS = "shoulders"
    BICEPS = "biceps"
    TRICEPS = "triceps"
    LEGS = "legs"
    GLUTES = "glutes"
    CORE = "core"
    FULL_BODY = "full_body"


class WorkoutGoal(Enum):
    STRENGTH = "strength"
    HYPERTROPHY = "hypertrophy"
    ENDURANCE = "endurance"
    WEIGHT_LOSS = "weight_loss"
    MAINTENANCE = "maintenance"


@dataclass
class Exercise:
    name: str
    muscle_group: MuscleGroup
    sets: int
    reps: str
    weight: str = "bodyweight"
    rest_seconds: int = 90
    order_index: int = 0
    alternatives: list[str] = field(default_factory=list)
    is_compound: bool = False


@dataclass
class WorkoutDay:
    day_number: int
    name: str
    exercises: list[Exercise] = field(default_factory=list)
    target_muscles: list[MuscleGroup] = field(default_factory=list)
    is_rest_day: bool = False
    notes: str = ""


@dataclass
class WorkoutWeek:
    week_number: int
    days: list[WorkoutDay] = field(default_factory=list)
    focus: str = ""
    progression: float = 1.0


@dataclass
class WorkoutPlan:
    name: str
    goal: WorkoutGoal
    difficulty: Difficulty
    weeks: list[WorkoutWeek] = field(default_factory=list)
    duration_weeks: int = 8
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class InjuryProfile:
    injured_areas: list[MuscleGroup] = field(default_factory=list)
    recovery_date: datetime | None = None
    severity: str = "mild"


MUSCLE_GROUP_EXERCISES = {
    MuscleGroup.CHEST: [
        "Bench Press", "Incline Press", "Dumbbell Fly", "Push-ups", "Cable Crossover"
    ],
    MuscleGroup.BACK: [
        "Deadlift", "Barbell Row", "Pull-ups", "Lat Pulldown", "T-Bar Row"
    ],
    MuscleGroup.SHOULDERS: [
        "Overhead Press", "Lateral Raise", "Front Raise", "Rear Delt Fly"
    ],
    MuscleGroup.BICEPS: ["Barbell Curl", "Hammer Curl", "Preacher Curl"],
    MuscleGroup.TRICEPS: ["Tricep Pushdown", "Skull Crushers", "Dips"],
    MuscleGroup.LEGS: [
        "Squat", "Leg Press", "Romanian Deadlift", "Leg Curl", "Leg Extension"
    ],
    MuscleGroup.GLUTES: ["Hip Thrust", "Bulgarian Split Squat", "Cable Pull-through"],
    MuscleGroup.CORE: ["Plank", "Crunches", "Russian Twist", "Hanging Leg Raise"],
    MuscleGroup.FULL_BODY: ["Clean & Jerk", "Burpees", "Thrusters"],
}

REPS_RANGES = {
    WorkoutGoal.STRENGTH: ("1-5", 180),
    WorkoutGoal.HYPERTROPHY: ("8-12", 90),
    WorkoutGoal.ENDURANCE: ("15-25", 45),
    WorkoutGoal.WEIGHT_LOSS: ("12-20", 60),
    WorkoutGoal.MAINTENANCE: ("8-12", 90),
}

SETS_RANGES = {
    WorkoutGoal.STRENGTH: (3, 5),
    WorkoutGoal.HYPERTROPHY: (3, 4),
    WorkoutGoal.ENDURANCE: (2, 3),
    WorkoutGoal.WEIGHT_LOSS: (3, 4),
    WorkoutGoal.MAINTENANCE: (3, 3),
}


def get_exercises_for_goal(goal: WorkoutGoal, muscle_group: MuscleGroup) -> list[str]:
    """Get recommended exercises for a goal and muscle group."""
    exercises = MUSCLE_GROUP_EXERCISES.get(muscle_group, [])
    if goal == WorkoutGoal.STRENGTH:
        compound = [e for e in exercises if "Press" in e or "Deadlift" in e or "Squat" in e or "Row" in e]
        return compound if compound else exercises[:3]
    return exercises


def create_exercise(
    name: str, muscle_group: MuscleGroup, goal: WorkoutGoal,
    order_index: int = 0,
) -> Exercise:
    """Create an exercise with goal-appropriate parameters."""
    reps_range, rest = REPS_RANGES[goal]
    sets_range = SETS_RANGES[goal]
    sets = sets_range[0] + (sets_range[1] - sets_range[0]) // 2
    compound = any(kw in name for kw in ["Press", "Squat", "Deadlift", "Row", "Clean", "Jerk"])
    return Exercise(
        name=name, muscle_group=muscle_group, sets=sets,
        reps=reps_range, rest_seconds=rest,
        order_index=order_index, is_compound=compound,
    )


def create_workout_day(
    day_number: int, name: str, muscle_groups: list[MuscleGroup],
    goal: WorkoutGoal, is_rest: bool = False,
) -> WorkoutDay:
    """Create a workout day targeting specific muscle groups."""
    if is_rest:
        return WorkoutDay(day_number=day_number, name="Rest Day", is_rest_day=True)
    exercises = []
    idx = 0
    for mg in muscle_groups:
        for ex_name in get_exercises_for_goal(goal, mg):
            exercises.append(create_exercise(ex_name, mg, goal, idx))
            idx += 1
            if idx >= 8:
                return WorkoutDay(day_number=day_number, name=name, exercises=exercises, target_muscles=muscle_groups)
    return WorkoutDay(
        day_number=day_number, name=name,
        exercises=exercises, target_muscles=muscle_groups,
    )


def create_split_plan(
    name: str, goal: WorkoutGoal, difficulty: Difficulty,
    duration_weeks: int = 8,
) -> WorkoutPlan:
    """Create a standard push/pull/legs split plan."""
    splits = [
        ([MuscleGroup.CHEST, MuscleGroup.SHOULDERS, MuscleGroup.TRICEPS], "Push Day"),
        ([MuscleGroup.BACK, MuscleGroup.BICEPS], "Pull Day"),
        ([MuscleGroup.LEGS, MuscleGroup.GLUTES, MuscleGroup.CORE], "Leg Day"),
    ]
    weeks = []
    progression = 1.0 + (duration_weeks * 0.02)
    for w in range(duration_weeks):
        week_num = w + 1
        days = []
        for day_idx, (muscles, day_name) in enumerate(splits):                days.append(create_workout_day(day_number=day_idx + 1, name=day_name, muscle_groups=muscles, goal=goal))
        days.append(create_workout_day(day_number=4, name="Active Recovery", muscle_groups=[], goal=goal, is_rest=True))
        weeks.append(WorkoutWeek(week_number=week_num, days=days, progression=progression))
    return WorkoutPlan(
        name=name, goal=goal, difficulty=difficulty,
        weeks=weeks, duration_weeks=duration_weeks,
    )


def apply_progressive_overload(week: WorkoutWeek, factor: float = 1.05) -> WorkoutWeek:
    """Apply progressive overload to a week's exercises."""
    for day in week.days:
        for exercise in day.exercises:
            if exercise.is_compound:
                exercise.sets = min(exercise.sets + 1, 8)
            exercise.rest_seconds = max(exercise.rest_seconds - 10, 30)
    week.progression = factor
    return week


def filter_exercises_for_injury(
    exercises: list[Exercise], injury: InjuryProfile,
) -> list[Exercise]:
    """Remove or replace exercises targeting injured areas."""
    filtered = []
    for ex in exercises:
        if ex.muscle_group in injury.injured_areas:
            if ex.alternatives:
                safe = Exercise(
                    name=ex.alternatives[0], muscle_group=ex.muscle_group,
                    sets=2, reps="10-12", weight="bodyweight",
                    rest_seconds=120, order_index=ex.order_index,
                )
                filtered.append(safe)
        else:
            filtered.append(ex)
    return filtered


def calculate_training_volume(week: WorkoutWeek) -> dict[str, int]:
    """Calculate total training volume per muscle group."""
    volume: dict[str, int] = {}
    for day in week.days:
        for exercise in day.exercises:
            mg = exercise.muscle_group.value
            volume[mg] = volume.get(mg, 0) + exercise.sets
    return volume


def estimate_workout_duration(day: WorkoutDay) -> int:
    """Estimate workout duration in minutes."""
    if day.is_rest_day:
        return 0
    total_sets = sum(ex.sets for ex in day.exercises)
    total_rest = sum(ex.rest_seconds * (ex.sets - 1) for ex in day.exercises)
    work_time = total_sets * 45
    return (work_time + total_rest) // 60


def suggest_deload_week(current_week: int, total_weeks: int) -> bool:
    """Suggest deload every 4th week."""
    return current_week > 0 and current_week % 4 == 0

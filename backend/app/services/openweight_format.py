"""OpenWeight format — vendor-neutral JSON schema for strength training data.

Extracted from inspiration/ZFIT/openweight.
Pattern: standardized export/import format so training data isn't locked to one app.
Schemas: WorkoutLog, WorkoutTemplate, Program, LifterProfile.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any
import json


@dataclass
class SetLog:
    """A single completed set."""
    reps: int
    weight: float  # kg
    rpe: float | None = None  # Rate of Perceived Exertion 1-10
    completed: bool = True
    rest_seconds: int | None = None
    notes: str = ""


@dataclass
class ExerciseLog:
    """A completed exercise within a workout."""
    name: str
    sets: list[SetLog] = field(default_factory=list)
    exercise_id: str | None = None
    notes: str = ""


@dataclass
class WorkoutLog:
    """A completed workout session."""
    date: str  # ISO 8601
    name: str
    exercises: list[ExerciseLog] = field(default_factory=list)
    duration_seconds: int | None = None
    bodyweight: float | None = None  # kg
    notes: str = ""


@dataclass
class SetTarget:
    """A planned set."""
    reps: int | None = None
    weight: float | None = None  # kg or percentage of 1RM
    weight_type: str = "absolute"  # "absolute" or "percentage"
    rpe_target: float | None = None
    rest_seconds: int | None = None


@dataclass
class ExerciseTemplate:
    """A planned exercise within a template."""
    name: str
    sets: list[SetTarget] = field(default_factory=list)
    exercise_id: str | None = None
    notes: str = ""


@dataclass
class WorkoutTemplate:
    """A planned workout."""
    name: str
    exercises: list[ExerciseTemplate] = field(default_factory=list)
    notes: str = ""


@dataclass
class Program:
    """A multi-week training program."""
    name: str
    weeks: list[list[str]] = field(default_factory=list)  # each week = list of template names
    duration_weeks: int = 0
    notes: str = ""


@dataclass
class OneRepMax:
    exercise: str
    weight: float  # kg
    date: str  # ISO 8601
    estimated: bool = False


@dataclass
class LifterProfile:
    """Athlete data."""
    name: str
    height_cm: float | None = None
    bodyweight_history: list[dict] = field(default_factory=list)  # [{date, weight}]
    prs: list[OneRepMax] = field(default_factory=list)
    training_age_years: int | None = None


def workout_to_json(workout: WorkoutLog) -> str:
    """Serialize a workout log to OpenWeight JSON."""
    return json.dumps(asdict(workout), indent=2)


def workout_from_json(data: str) -> WorkoutLog:
    """Deserialize a workout log from OpenWeight JSON."""
    d = json.loads(data)
    exercises = [
        ExerciseLog(
            name=e["name"],
            sets=[SetLog(**s) for s in e.get("sets", [])],
            exercise_id=e.get("exercise_id"),
            notes=e.get("notes", ""),
        )
        for e in d.get("exercises", [])
    ]
    return WorkoutLog(
        date=d["date"],
        name=d["name"],
        exercises=exercises,
        duration_seconds=d.get("duration_seconds"),
        bodyweight=d.get("bodyweight"),
        notes=d.get("notes", ""),
    )


def estimate_1rm(weight: float, reps: int, formula: str = "epley") -> float:
    """Estimate 1-rep max from a set.

    Epley: 1RM = weight × (1 + reps/30)
    Brzycki: 1RM = weight × 36 / (37 - reps)
    Lombardi: 1RM = weight × reps^0.10
    """
    if reps == 1:
        return weight

    if formula == "epley":
        return weight * (1 + reps / 30)
    elif formula == "brzycki":
        return weight * 36 / (37 - reps)
    elif formula == "lombardi":
        return weight * (reps ** 0.10)
    return weight * (1 + reps / 30)


def calculate_training_volume(workout: WorkoutLog) -> float:
    """Total training volume (sum of reps × weight)."""
    total = 0.0
    for ex in workout.exercises:
        for s in ex.sets:
            if s.completed and s.reps and s.weight:
                total += s.reps * s.weight
    return total


def calculate_relative_intensity(workout: WorkoutLog, one_rm: dict[str, float]) -> float:
    """Average relative intensity (% of 1RM) across all sets."""
    intensities = []
    for ex in workout.exercises:
        for s in ex.sets:
            if s.completed and ex.name in one_rm and one_rm[ex.name] > 0:
                intensities.append(s.weight / one_rm[ex.name] * 100)
    return sum(intensities) / len(intensities) if intensities else 0

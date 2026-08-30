"""Fitdown markup parser — structured data from weightlifting workout logs.

Extracted from inspiration/ZFIT/fitdown.
Pattern: Markdown superset for fitness logs. Parses workout dates, exercises, sets, reps, weights.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class WorkoutSet:
    reps: int | None = None
    weight: float | None = None
    notes: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class Exercise:
    name: str
    sets: list[WorkoutSet] = field(default_factory=list)
    notes: str = ""


@dataclass
class Workout:
    date: datetime | None = None
    name: str | None = None
    exercises: list[Exercise] = field(default_factory=list)
    raw_text: str = ""


def parse_workout_date(line: str) -> datetime | None:
    """Parse 'Workout September 16, 2020' format."""
    m = re.match(r'^Workout\s+(.+)', line, re.IGNORECASE)
    if not m:
        return None
    date_str = m.group(1).strip()
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def parse_set(line: str) -> WorkoutSet | None:
    """Parse a set line like '3x5@165', '5@255 TOUGH', '3x5', '5@185'."""
    line = line.strip()
    if not line:
        return None

    # Tags (uppercase words at end)
    tags = re.findall(r'\b([A-Z]{3,})\b', line)
    for tag in tags:
        line = line.replace(tag, "").strip()

    # 3x5@165 — sets x reps @ weight
    m = re.match(r'^(\d+)\s*x\s*(\d+)\s*@\s*([\d.]+)', line)
    if m:
        return WorkoutSet(
            reps=int(m.group(2)),
            weight=float(m.group(3)),
            tags=tags,
        )

    # 3x5 — sets x reps (no weight)
    m = re.match(r'^(\d+)\s*x\s*(\d+)', line)
    if m:
        return WorkoutSet(reps=int(m.group(2)), tags=tags)

    # 5@185 — reps @ weight
    m = re.match(r'^(\d+)\s*@\s*([\d.]+)', line)
    if m:
        return WorkoutSet(
            reps=int(m.group(1)),
            weight=float(m.group(2)),
            tags=tags,
        )

    # Just a number — reps with no weight
    m = re.match(r'^(\d+)$', line)
    if m:
        return WorkoutSet(reps=int(m.group(1)), tags=tags)

    # "Up to 145lb" — progressive
    m = re.match(r'^up to\s+([\d.]+)', line, re.IGNORECASE)
    if m:
        return WorkoutSet(
            weight=float(m.group(1)),
            notes="progressive",
            tags=tags,
        )

    # Notes line
    return WorkoutSet(notes=line, tags=tags)


def parse_fitdown(text: str) -> Workout:
    """Parse a Fitdown workout log.

    Format:
        Workout September 16, 2020

        Snatch
        Up to technique bar + 35lb each side

        Clean and Jerk
        Up to 145lb

        Squat
        3x5@165

        Bench
        3x5@170

        Deadlift
        5@185
        5@255 TOUGH
    """
    lines = text.strip().split('\n')
    workout = Workout(raw_text=text)

    current_exercise: Exercise | None = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Workout date header
        if stripped.lower().startswith("workout"):
            workout.date = parse_workout_date(stripped)
            continue

        # Check if this is an exercise name (capitalized words, no set pattern)
        is_set = bool(re.match(r'^[\dx@.]', stripped) or stripped.lower().startswith("up to"))
        if not is_set and not stripped.startswith("#"):
            # New exercise
            if current_exercise:
                workout.exercises.append(current_exercise)
            current_exercise = Exercise(name=stripped)
            continue

        # Parse as set
        if current_exercise is None:
            current_exercise = Exercise(name="Unknown")

        s = parse_set(stripped)
        if s:
            current_exercise.sets.append(s)

    if current_exercise:
        workout.exercises.append(current_exercise)

    return workout


def workout_to_dict(workout: Workout) -> dict:
    """Convert workout to JSON-serializable dict."""
    return {
        "date": workout.date.isoformat() if workout.date else None,
        "name": workout.name,
        "exercises": [
            {
                "name": ex.name,
                "notes": ex.notes,
                "sets": [
                    {
                        "reps": s.reps,
                        "weight": s.weight,
                        "notes": s.notes,
                        "tags": s.tags,
                    }
                    for s in ex.sets
                ],
            }
            for ex in workout.exercises
        ],
    }


def calculate_volume(workout: Workout) -> float:
    """Calculate total training volume (sum of reps × weight)."""
    total = 0.0
    for ex in workout.exercises:
        for s in ex.sets:
            if s.reps and s.weight:
                total += s.reps * s.weight
    return total

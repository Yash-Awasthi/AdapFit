"""
Workout String Parser for ZFIT
Extracted from: caber (string parsing library for logging workouts)
Patterns: Natural language workout parsing, set/rep/weight extraction,
          exercise name recognition, date parsing, unit conversion
"""
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class ExerciseSet:
    weight: Optional[float] = None
    reps: Optional[int] = None
    duration: Optional[str] = None  # "1:30:00" format
    distance: Optional[float] = None
    distance_unit: str = "miles"
    rpe: Optional[float] = None  # Rate of Perceived Exertion
    notes: str = ""


@dataclass
class Exercise:
    name: str
    sets: list[ExerciseSet] = field(default_factory=list)
    category: str = "unknown"  # strength, cardio, flexibility


@dataclass
class Workout:
    name: str = ""
    date: Optional[datetime] = None
    exercises: list[Exercise] = field(default_factory=list)
    notes: str = ""
    total_duration: Optional[str] = None
    raw_text: str = ""


# ─── Exercise Database ─────────────────────────────────────────────────

EXERCISE_CATEGORIES = {
    "squat": "strength",
    "bench": "strength",
    "deadlift": "strength",
    "press": "strength",
    "curl": "strength",
    "row": "strength",
    "pull": "strength",
    "chin": "strength",
    "dip": "strength",
    "lunge": "strength",
    "plank": "strength",
    "run": "cardio",
    "jog": "cardio",
    "cycling": "cardio",
    "bike": "cardio",
    "swim": "cardio",
    "walk": "cardio",
    "rowing": "cardio",
    "elliptical": "cardio",
    "jump rope": "cardio",
    "yoga": "flexibility",
    "stretch": "flexibility",
    "foam roll": "flexibility",
}

DAYS_OF_WEEK = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}


# ─── Parsing Functions ─────────────────────────────────────────────────

def parse_workout(text: str, default_weight_unit: str = "lbs") -> Workout:
    """Parse a workout string into structured data."""
    lines = text.strip().split("\n")
    workout = Workout(raw_text=text)

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if line is a workout name/date header
        date = _parse_date(line)
        if date:
            workout.date = date
            continue

        if _is_exercise_line(line):
            exercise = _parse_exercise_line(line, default_weight_unit)
            workout.exercises.append(exercise)
        elif workout.exercises:
            # Append to last exercise as notes
            workout.exercises[-1].notes += " " + line

    if not workout.name and workout.exercises:
        workout.name = f"Workout ({len(workout.exercises)} exercises)"

    return workout


def _parse_date(text: str) -> Optional[datetime]:
    """Try to parse a date from text."""
    text_lower = text.lower().strip()
    today = datetime.now()

    # Day names
    for day_name, day_num in DAYS_OF_WEEK.items():
        if day_name in text_lower:
            today_num = today.weekday()
            diff = (day_num - today_num) % 7
            if diff == 0:
                diff = 7
            return today - timedelta(days=7 - diff)

    # "Leg Day", "Upper Body", etc. are workout names, not dates
    return None


def _is_exercise_line(line: str) -> bool:
    """Check if a line describes an exercise."""
    # Lines with sets like "135x5" or "3x10" or "1:30:00"
    if re.search(r'\d+\s*x\s*\d+', line):
        return True
    # Lines starting with known exercise names
    first_word = line.split()[0].lower() if line.split() else ""
    return first_word in EXERCISE_CATEGORIES


def _parse_exercise_line(line: str, default_unit: str = "lbs") -> Exercise:
    """Parse a line describing an exercise with sets."""
    # Extract exercise name (before first number or parenthetical)
    name_match = re.match(r'^([a-zA-Z\s\-]+?)(?:\s*\(|\s*\d)', line)
    name = name_match.group(1).strip() if name_match else line.split()[0]
    name = name.title()

    category = "unknown"
    for keyword, cat in EXERCISE_CATEGORIES.items():
        if keyword in name.lower():
            category = cat
            break

    exercise = Exercise(name=name, category=category)

    # Parse sets: "135x5, 200x3, 225x4"
    set_pattern = re.findall(r'(\d+(?:\.\d+)?)\s*x\s*(\d+)', line)
    for weight, reps in set_pattern:
        exercise.sets.append(ExerciseSet(
            weight=float(weight),
            reps=int(reps),
        ))

    # Parse duration: "1:30:00" or "45:00"
    duration_match = re.search(r'(\d+:\d+(?::\d+)?)', line)
    if duration_match:
        exercise.sets.append(ExerciseSet(duration=duration_match.group(1)))

    # Parse distance: "15 miles" or "5km"
    dist_match = re.search(r'(\d+(?:\.\d+)?)\s*(miles?|km|m|feet|ft)', line)
    if dist_match:
        exercise.sets.append(ExerciseSet(
            distance=float(dist_match.group(1)),
            distance_unit=dist_match.group(2),
        ))

    # Parse RPE: "RPE 8" or "(8)"
    rpe_match = re.search(r'rpe\s*(\d+(?:\.\d+)?)', line, re.IGNORECASE)
    if not rpe_match:
        rpe_match = re.search(r'\((\d+(?:\.\d+)?)\)\s*$', line)
    if rpe_match:
        rpe = float(rpe_match.group(1))
        if 1 <= rpe <= 10:
            exercise.sets.append(ExerciseSet(rpe=rpe))

    # Parse weight unit
    if "kg" in line.lower():
        for s in exercise.sets:
            if s.weight:
                s.notes = "kg"

    return exercise


# ─── Workout Summaries ─────────────────────────────────────────────────

def summarize_workout(workout: Workout) -> dict:
    """Generate a summary of a parsed workout."""
    total_sets = sum(len(e.sets) for e in workout.exercises)
    total_volume = 0
    total_reps = 0

    for exercise in workout.exercises:
        for s in exercise.sets:
            if s.weight and s.reps:
                total_volume += s.weight * s.reps
                total_reps += s.reps

    return {
        "name": workout.name,
        "date": workout.date.isoformat() if workout.date else None,
        "exercises": len(workout.exercises),
        "total_sets": total_sets,
        "total_reps": total_reps,
        "total_volume": round(total_volume, 1),
        "exercise_details": [
            {
                "name": e.name,
                "category": e.category,
                "sets": len(e.sets),
                "volume": round(sum((s.weight or 0) * (s.reps or 0) for s in e.sets), 1),
            }
            for e in workout.exercises
        ],
    }


def batch_parse(workouts: list[str], default_unit: str = "lbs") -> list[Workout]:
    """Parse multiple workout strings."""
    return [parse_workout(w, default_unit) for w in workouts]

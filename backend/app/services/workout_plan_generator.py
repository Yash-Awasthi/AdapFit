"""
AI Workout Plan Generator — Personalized multi-week training programs.

Combines:
- Fitness assessment data
- Recovery status (HRV, sleep, readiness)
- Exercise database with muscle group targeting
- Progressive overload algorithms
- Periodization principles (linear, undulating, block)
- Deload scheduling
- Equipment constraints
- Time constraints per session
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Tuple
import json


class TrainingGoal(Enum):
    STRENGTH = "strength"
    HYPERTROPHY = "hypertrophy"
    ENDURANCE = "endurance"
    POWER = "power"
    FAT_LOSS = "fat_loss"
    MAINTENANCE = "maintenance"
    SPORT_SPECIFIC = "sport_specific"


class PeriodizationType(Enum):
    LINEAR = "linear"           # gradually increase intensity
    UNDULATING = "undulating"   # vary intensity within week
    BLOCK = "block"             # focus on one quality per block
    DUP = "dup"                 # daily undulating periodization


class MuscleGroup(Enum):
    CHEST = "chest"
    BACK = "back"
    SHOULDERS = "shoulders"
    BICEPS = "biceps"
    TRICEPS = "triceps"
    LEGS = "legs"
    QUADS = "quads"
    HAMSTRINGS = "hamstrings"
    GLUTES = "glutes"
    CALVES = "calves"
    CORE = "core"
    FULL_BODY = "full_body"


class Equipment(Enum):
    BODYWEIGHT = "bodyweight"
    DUMBBELLS = "dumbbells"
    BARBELL = "barbell"
    CABLES = "cables"
    RESISTANCE_BANDS = "resistance_bands"
    KETTLEBELL = "kettlebell"
    MACHINE = "machine"
    PULL_UP_BAR = "pull_up_bar"


@dataclass
class Exercise:
    name: str
    muscle_groups: List[MuscleGroup]
    equipment: List[Equipment]
    difficulty: int  # 1-10
    sets: int = 3
    reps: str = "8-12"  # can be "5", "8-12", "30s", "AMRAP"
    rest_seconds: int = 90
    notes: str = ""


@dataclass
class WorkoutSession:
    name: str
    day_of_week: int  # 0=Monday
    exercises: List[Exercise]
    estimated_minutes: int
    target_muscles: List[MuscleGroup]
    intensity: float  # 0-1 (RPE)
    volume: int  # total sets
    notes: str = ""


@dataclass
class TrainingWeek:
    week_number: int
    sessions: List[WorkoutSession]
    phase: str  # "accumulation", "intensification", "realization", "deload"
    target_volume: int  # total sets across all sessions
    target_intensity: float  # average RPE


@dataclass
class TrainingPlan:
    name: str
    goal: TrainingGoal
    duration_weeks: int
    sessions_per_week: int
    periodization: PeriodizationType
    weeks: List[TrainingWeek]
    deload_frequency: int  # every N weeks
    available_equipment: List[Equipment]
    max_session_minutes: int
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class UserProfile:
    experience_level: int  # 1 (beginner) to 10 (advanced)
    age: int
    weight_kg: float
    height_cm: float
    injuries: List[str]
    available_equipment: List[Equipment]
    max_sessions_per_week: int
    max_minutes_per_session: int
    training_goal: TrainingGoal
    current_1rm: Dict[str, float]  # exercise -> 1RM in kg


# ── Default Exercise Database ────────────────────────────────────────────────

EXERCISE_DB: Dict[str, List[Exercise]] = {
    MuscleGroup.CHEST.value: [
        Exercise("Barbell Bench Press", [MuscleGroup.CHEST, MuscleGroup.TRICEPS], [Equipment.BARBELL], 6, 4, "5-8", 180),
        Exercise("Dumbbell Incline Press", [MuscleGroup.CHEST, MuscleGroup.SHOULDERS], [Equipment.DUMBBELLS], 5, 3, "8-12", 120),
        Exercise("Cable Flyes", [MuscleGroup.CHEST], [Equipment.CABLES], 3, 3, "12-15", 60),
        Exercise("Push-ups", [MuscleGroup.CHEST, MuscleGroup.TRICEPS], [Equipment.BODYWEIGHT], 3, 3, "15-20", 60),
        Exercise("Dips", [MuscleGroup.CHEST, MuscleGroup.TRICEPS, MuscleGroup.SHOULDERS], [Equipment.PULL_UP_BAR], 5, 3, "8-12", 120),
    ],
    MuscleGroup.BACK.value: [
        Exercise("Barbell Deadlift", [MuscleGroup.BACK, MuscleGroup.HAMSTRINGS, MuscleGroup.GLUTES], [Equipment.BARBELL], 8, 4, "3-5", 240),
        Exercise("Pull-ups", [MuscleGroup.BACK, MuscleGroup.BICEPS], [Equipment.PULL_UP_BAR], 5, 4, "6-10", 120),
        Exercise("Barbell Row", [MuscleGroup.BACK, MuscleGroup.BICEPS], [Equipment.BARBELL], 5, 4, "6-10", 120),
        Exercise("Cable Pulldown", [MuscleGroup.BACK], [Equipment.CABLES], 3, 3, "10-15", 90),
        Exercise("Dumbbell Single-Arm Row", [MuscleGroup.BACK], [Equipment.DUMBBELLS], 4, 3, "8-12", 90),
    ],
    MuscleGroup.LEGS.value: [
        Exercise("Barbell Back Squat", [MuscleGroup.QUADS, MuscleGroup.GLUTES], [Equipment.BARBELL], 7, 4, "5-8", 180),
        Exercise("Romanian Deadlift", [MuscleGroup.HAMSTRINGS, MuscleGroup.GLUTES], [Equipment.BARBELL], 5, 3, "8-12", 120),
        Exercise("Leg Press", [MuscleGroup.QUADS, MuscleGroup.GLUTES], [Equipment.MACHINE], 4, 3, "10-15", 90),
        Exercise("Walking Lunges", [MuscleGroup.QUADS, MuscleGroup.GLUTES], [Equipment.DUMBBELLS], 4, 3, "12 each", 90),
        Exercise("Leg Curl", [MuscleGroup.HAMSTRINGS], [Equipment.MACHINE], 3, 3, "12-15", 60),
    ],
}


class WorkoutPlanGenerator:
    """AI-powered workout plan generator."""

    def __init__(self):
        self.exercises = EXERCISE_DB

    def generate_plan(self, user: UserProfile, weeks: int = 12) -> TrainingPlan:
        """Generate a complete multi-week training plan."""
        sessions_per_week = min(user.max_sessions_per_week, self._optimal_frequency(user))
        periodization = self._select_periodization(user)

        training_weeks = []
        for w in range(1, weeks + 1):
            is_deload = w % 4 == 0  # deload every 4th week
            phase = self._get_phase(w, weeks, is_deload)

            week = TrainingWeek(
                week_number=w,
                sessions=self._generate_week_sessions(
                    user, sessions_per_week, w, weeks, phase, is_deload
                ),
                phase=phase,
                target_volume=self._target_volume(user, w, weeks, is_deload),
                target_intensity=self._target_intensity(user, w, weeks, is_deload),
            )
            training_weeks.append(week)

        return TrainingPlan(
            name=f"{user.training_goal.value.title()} Program — {weeks} Weeks",
            goal=user.training_goal,
            duration_weeks=weeks,
            sessions_per_week=sessions_per_week,
            periodization=periodization,
            weeks=training_weeks,
            deload_frequency=4,
            available_equipment=user.available_equipment,
            max_session_minutes=user.max_minutes_per_session,
        )

    def _optimal_frequency(self, user: UserProfile) -> int:
        if user.experience_level <= 3:
            return 3  # beginner: 3x/week
        elif user.experience_level <= 6:
            return 4  # intermediate: 4x/week
        else:
            return 5  # advanced: 5x/week

    def _select_periodization(self, user: UserProfile) -> PeriodizationType:
        if user.training_goal == TrainingGoal.STRENGTH:
            return PeriodizationType.LINEAR
        elif user.training_goal == TrainingGoal.HYPERTROPHY:
            return PeriodizationType.UNDULATING
        elif user.experience_level >= 7:
            return PeriodizationType.DUP
        return PeriodizationType.LINEAR

    def _get_phase(self, week: int, total_weeks: int, is_deload: bool) -> str:
        if is_deload:
            return "deload"
        progress = week / total_weeks
        if progress <= 0.4:
            return "accumulation"
        elif progress <= 0.7:
            return "intensification"
        else:
            return "realization"

    def _target_volume(self, user: UserProfile, week: int, total: int, is_deload: bool) -> int:
        if is_deload:
            return 12  # low volume deload
        base = 15 + user.experience_level
        progression = (week / total) * 10
        return int(base + progression)

    def _target_intensity(self, user: UserProfile, week: int, total: int, is_deload: bool) -> float:
        if is_deload:
            return 0.5
        base = 0.5 + (user.experience_level * 0.03)
        progression = (week / total) * 0.2
        return min(0.95, base + progression)

    def _generate_week_sessions(
        self,
        user: UserProfile,
        sessions_per_week: int,
        week_num: int,
        total_weeks: int,
        phase: str,
        is_deload: bool,
    ) -> List[WorkoutSession]:
        """Generate training sessions for a single week."""
        templates = self._get_split_template(sessions_per_week)
        sessions = []

        for i, template in enumerate(templates):
            exercises = []
            for muscle_group in template["muscles"]:
                available = self._filter_exercises(muscle_group, user.available_equipment)
                if available:
                    count = 2 if phase == "accumulation" else 1
                    exercises.extend(available[:count])

            # Apply phase modifiers
            if is_deload:
                for ex in exercises:
                    ex.sets = max(2, ex.sets - 1)
                    ex.reps = self._deload_reps(ex.reps)
                    ex.rest_seconds = max(60, ex.rest_seconds - 30)

            session = WorkoutSession(
                name=template["name"],
                day_of_week=i * (7 // sessions_per_week),
                exercises=exercises,
                estimated_minutes=min(user.max_minutes_per_session, template.get("est_minutes", 60)),
                target_muscles=template["muscles"],
                intensity=self._target_intensity(user, week_num, total_weeks, is_deload),
                volume=sum(e.sets for e in exercises),
            )
            sessions.append(session)

        return sessions

    def _get_split_template(self, sessions: int) -> List[Dict]:
        templates = {
            3: [
                {"name": "Full Body A", "muscles": [MuscleGroup.CHEST, MuscleGroup.BACK, MuscleGroup.LEGS], "est_minutes": 60},
                {"name": "Full Body B", "muscles": [MuscleGroup.SHOULDERS, MuscleGroup.BACK, MuscleGroup.LEGS], "est_minutes": 60},
                {"name": "Full Body C", "muscles": [MuscleGroup.CHEST, MuscleGroup.BACK, MuscleGroup.LEGS], "est_minutes": 60},
            ],
            4: [
                {"name": "Upper A", "muscles": [MuscleGroup.CHEST, MuscleGroup.BACK], "est_minutes": 50},
                {"name": "Lower A", "muscles": [MuscleGroup.LEGS], "est_minutes": 55},
                {"name": "Upper B", "muscles": [MuscleGroup.SHOULDERS, MuscleGroup.BACK], "est_minutes": 50},
                {"name": "Lower B", "muscles": [MuscleGroup.LEGS], "est_minutes": 55},
            ],
            5: [
                {"name": "Push", "muscles": [MuscleGroup.CHEST, MuscleGroup.SHOULDERS], "est_minutes": 50},
                {"name": "Pull", "muscles": [MuscleGroup.BACK], "est_minutes": 50},
                {"name": "Legs", "muscles": [MuscleGroup.LEGS], "est_minutes": 55},
                {"name": "Upper", "muscles": [MuscleGroup.CHEST, MuscleGroup.BACK], "est_minutes": 50},
                {"name": "Lower", "muscles": [MuscleGroup.LEGS], "est_minutes": 55},
            ],
        }
        return templates.get(sessions, templates[3])

    def _filter_exercises(
        self, muscle_group: MuscleGroup, equipment: List[Equipment]
    ) -> List[Exercise]:
        available_equipment = set(equipment)
        exercises = []
        for group_name, group_exercises in self.exercises.items():
            for ex in group_exercises:
                if muscle_group in ex.muscle_groups or muscle_group.value in group_name:
                    if any(e in available_equipment for e in ex.equipment) or Equipment.BODYWEIGHT in ex.equipment:
                        exercises.append(ex)
        return exercises

    def _deload_reps(self, reps: str) -> str:
        """Reduce reps for deload weeks."""
        if "-" in reps:
            parts = reps.split("-")
            try:
                low, high = int(parts[0]), int(parts[1])
                return f"{max(1, low - 2)}-{max(2, high - 2)}"
            except ValueError:
                return reps
        try:
            val = int(reps)
            return str(max(1, val - 3))
        except ValueError:
            return reps

"""
AI Fitness Plan Generator — creates personalized workout and nutrition plans.
Adapts to user profile, goals, equipment, and recovery state.

Inspired by: ai-fitness-planner (LangGraph fitness planner)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class FitnessGoal(Enum):
    CUT = "cut"
    BULK = "bulk"
    MAINTENANCE = "maintenance"
    RECOMP = "recomp"
    STRENGTH = "strength"
    ENDURANCE = "endurance"


class TrainingStyle(Enum):
    HYPERTROPHY = "hypertrophy"
    STRENGTH = "strength"
    ENDURANCE = "endurance"
    POWER = "power"
    GENERAL = "general"


class SplitType(Enum):
    FULL_BODY = "full_body"
    UPPER_LOWER = "upper_lower"
    PUSH_PULL_LEGS = "push_pull_legs"
    BRO_SPLIT = "bro_split"
    PPL_UPPER_LOWER = "ppl_upper_lower"


class ActivityLevel(Enum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"


# Activity level multipliers for TDEE
ACTIVITY_MULTIPLIERS: dict[ActivityLevel, float] = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHT: 1.375,
    ActivityLevel.MODERATE: 1.55,
    ActivityLevel.ACTIVE: 1.725,
    ActivityLevel.VERY_ACTIVE: 1.9,
}


@dataclass
class UserProfile:
    """User profile for plan generation."""
    user_id: str
    age: int = 30
    weight_kg: float = 70.0
    height_cm: float = 170.0
    sex: str = "male"  # male, female
    activity_level: ActivityLevel = ActivityLevel.MODERATE
    fitness_goal: FitnessGoal = FitnessGoal.MAINTENANCE
    workout_frequency: int = 3  # days per week
    workout_duration_min: int = 60
    equipment: list[str] = field(default_factory=lambda: [
        "barbell", "dumbbells", "pull_up_bar", "bench",
    ])
    allergies: list[str] = field(default_factory=list)
    dietary_preferences: list[str] = field(default_factory=list)
    injuries: list[str] = field(default_factory=list)
    experience_level: str = "intermediate"  # beginner, intermediate, advanced


@dataclass
class Exercise:
    """A single exercise in a workout."""
    name: str
    sets: int
    reps: str  # "8-10" or "5" or "AMRAP"
    rest_seconds: int = 90
    tempo: str = ""
    notes: str = ""
    category: str = ""  # compound, isolation
    muscles: list[str] = field(default_factory=list)


@dataclass
class WorkoutDay:
    """A single workout day."""
    name: str
    exercises: list[Exercise]
    duration_min: int = 60
    focus: str = ""
    warmup: list[str] = field(default_factory=list)
    cooldown: list[str] = field(default_factory=list)


@dataclass
class NutritionPlan:
    """Daily nutrition targets."""
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    water_ml: int
    meals: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class WeeklyPlan:
    """Complete weekly fitness plan."""
    user_id: str
    generated_at: datetime
    workouts: list[WorkoutDay]
    nutrition: NutritionPlan
    notes: list[str] = field(default_factory=list)
    deload_week: bool = False


class FitnessPlanGenerator:
    """Generates personalized fitness plans based on user profile."""

    # Exercise database (simplified)
    EXERCISE_DB: dict[str, dict[str, Any]] = {
        "squat": {"muscles": ["quads", "glutes", "core"], "type": "compound", "equipment": ["barbell"]},
        "deadlift": {"muscles": ["hamstrings", "glutes", "back"], "type": "compound", "equipment": ["barbell"]},
        "bench_press": {"muscles": ["chest", "triceps", "shoulders"], "type": "compound", "equipment": ["barbell", "bench"]},
        "overhead_press": {"muscles": ["shoulders", "triceps", "core"], "type": "compound", "equipment": ["barbell"]},
        "barbell_row": {"muscles": ["back", "biceps"], "type": "compound", "equipment": ["barbell"]},
        "pull_up": {"muscles": ["back", "biceps"], "type": "compound", "equipment": ["pull_up_bar"]},
        "dumbbell_curl": {"muscles": ["biceps"], "type": "isolation", "equipment": ["dumbbells"]},
        "tricep_pushdown": {"muscles": ["triceps"], "type": "isolation", "equipment": ["cable"]},
        "lateral_raise": {"muscles": ["shoulders"], "type": "isolation", "equipment": ["dumbbells"]},
        "leg_press": {"muscles": ["quads", "glutes"], "type": "compound", "equipment": ["leg_press"]},
        "romanian_deadlift": {"muscles": ["hamstrings", "glutes"], "type": "compound", "equipment": ["barbell"]},
        "hip_thrust": {"muscles": ["glutes", "hamstrings"], "type": "compound", "equipment": ["barbell", "bench"]},
        "plank": {"muscles": ["core"], "type": "isolation", "equipment": []},
        "lat_pulldown": {"muscles": ["back", "biceps"], "type": "compound", "equipment": ["cable"]},
        "cable_fly": {"muscles": ["chest"], "type": "isolation", "equipment": ["cable"]},
        "face_pull": {"muscles": ["rear_delts", "rotator_cuff"], "type": "isolation", "equipment": ["cable"]},
        "lunges": {"muscles": ["quads", "glutes"], "type": "compound", "equipment": ["dumbbells"]},
        "bulgarian_split_squat": {"muscles": ["quads", "glutes"], "type": "compound", "equipment": ["dumbbells", "bench"]},
        "hammer_curl": {"muscles": ["biceps", "forearms"], "type": "isolation", "equipment": ["dumbbells"]},
        "leg_curl": {"muscles": ["hamstrings"], "type": "isolation", "equipment": ["machine"]},
        "leg_extension": {"muscles": ["quads"], "type": "isolation", "equipment": ["machine"]},
        "calf_raise": {"muscles": ["calves"], "type": "isolation", "equipment": ["machine"]},
        "dumbbell_shoulder_press": {"muscles": ["shoulders", "triceps"], "type": "compound", "equipment": ["dumbbells"]},
        "chest_fly": {"muscles": ["chest"], "type": "isolation", "equipment": ["dumbbells", "bench"]},
        "russian_twist": {"muscles": ["obliques", "core"], "type": "isolation", "equipment": []},
    }

    def calculate_tdee(self, profile: UserProfile) -> float:
        """Calculate Total Daily Energy Expenditure using Mifflin-St Jeor."""
        if profile.sex == "male":
            bmr = 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age + 5
        else:
            bmr = 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age - 161

        return bmr * ACTIVITY_MULTIPLIERS.get(profile.activity_level, 1.55)

    def calculate_macros(self, profile: UserProfile) -> NutritionPlan:
        """Calculate daily macro targets based on goal."""
        tdee = self.calculate_tdee(profile)

        # Adjust calories based on goal
        goal_adjustments: dict[FitnessGoal, tuple[float, float, float]] = {
            FitnessGoal.CUT: (-500, 0.1, 0.3),
            FitnessGoal.BULK: (+400, 0.1, 0.3),
            FitnessGoal.MAINTENANCE: (0, 0.1, 0.3),
            FitnessGoal.RECOMP: (-200, 0.1, 0.3),
            FitnessGoal.STRENGTH: (+200, 0.1, 0.25),
            FitnessGoal.ENDURANCE: (+100, 0.08, 0.4),
        }

        cal_adj, pro_pct, fat_pct = goal_adjustments.get(
            profile.fitness_goal, (0, 0.1, 0.3)
        )
        calories = int(tdee + cal_adj)

        # Protein: 1.8-2.2 g/kg
        protein_g = round(profile.weight_kg * 2.0, 1)
        protein_cal = protein_g * 4

        # Fat: percentage of calories
        fat_cal = calories * fat_pct
        fat_g = round(fat_cal / 9, 1)

        # Carbs: remaining calories
        carbs_cal = calories - protein_cal - fat_cal
        carbs_g = round(max(carbs_cal / 4, 50), 1)

        return NutritionPlan(
            calories=calories,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fat_g=fat_g,
            fiber_g=round(calories / 1000 * 14, 1),  # 14g per 1000 cal
            water_ml=int(profile.weight_kg * 35),  # 35ml per kg
        )

    def _filter_exercises(self, profile: UserProfile) -> dict[str, dict[str, Any]]:
        """Filter exercises based on equipment and injuries."""
        available = set(profile.equipment)
        injury_muscles = set()
        for injury in profile.injuries:
            injury_muscles.update(injury.lower().split())

        filtered = {}
        for name, info in self.EXERCISE_DB.items():
            required = set(info.get("equipment", []))
            if required and not required.issubset(available):
                continue
            muscles = set(info.get("muscles", []))
            if muscles & injury_muscles:
                continue
            filtered[name] = info
        return filtered

    def _create_full_body_day(
        self, exercises: dict[str, dict[str, Any]], style: TrainingStyle
    ) -> WorkoutDay:
        """Create a full-body workout day."""
        workout_exercises = []

        # Compounds first
        compounds = [n for n, e in exercises.items() if e["type"] == "compound"]
        for name in compounds[:5]:
            e = exercises[name]
            sets, reps = self._get_sets_reps(style)
            workout_exercises.append(Exercise(
                name=name.replace("_", " ").title(),
                sets=sets,
                reps=reps,
                category="compound",
                muscles=e["muscles"],
            ))

        # Add isolation if room
        isolations = [n for n, e in exercises.items() if e["type"] == "isolation"]
        for name in isolations[:3]:
            e = exercises[name]
            workout_exercises.append(Exercise(
                name=name.replace("_", " ").title(),
                sets=3,
                reps="10-12",
                category="isolation",
                muscles=e["muscles"],
            ))

        return WorkoutDay(
            name="Full Body",
            exercises=workout_exercises,
            focus="Full Body Strength & Hypertrophy",
        )

    def _create_upper_lower_day(
        self, exercises: dict[str, dict[str, Any]], style: TrainingStyle, is_upper: bool
    ) -> WorkoutDay:
        """Create an upper or lower body workout day."""
        workout_exercises = []
        target_muscles = {
            True: {"chest", "back", "shoulders", "biceps", "triceps", "rear_delts", "rotator_cuff", "forearms"},
            False: {"quads", "hamstrings", "glutes", "calves", "core", "obliques"},
        }[is_upper]

        for name, info in exercises.items():
            muscles = set(info.get("muscles", []))
            if muscles & target_muscles:
                sets, reps = self._get_sets_reps(style)
                workout_exercises.append(Exercise(
                    name=name.replace("_", " ").title(),
                    sets=sets,
                    reps=reps,
                    category=info["type"],
                    muscles=info["muscles"],
                ))

        return WorkoutDay(
            name="Upper Body" if is_upper else "Lower Body",
            exercises=workout_exercises[:8],  # Cap at 8 exercises
            focus="Upper Body" if is_upper else "Lower Body",
        )

    def _get_sets_reps(self, style: TrainingStyle) -> tuple[int, str]:
        """Get set/rep scheme based on training style."""
        schemes: dict[TrainingStyle, tuple[int, str]] = {
            TrainingStyle.HYPERTROPHY: (4, "8-12"),
            TrainingStyle.STRENGTH: (5, "3-5"),
            TrainingStyle.ENDURANCE: (3, "15-20"),
            TrainingStyle.POWER: (5, "2-3"),
            TrainingStyle.GENERAL: (3, "8-10"),
        }
        return schemes.get(style, (3, "8-10"))

    def generate_weekly_plan(self, profile: UserProfile) -> WeeklyPlan:
        """Generate a complete weekly fitness plan."""
        exercises = self._filter_exercises(profile)
        style = TrainingStyle.GENERAL  # Could be inferred from goal

        if profile.fitness_goal in (FitnessGoal.STRENGTH,):
            style = TrainingStyle.STRENGTH
        elif profile.fitness_goal in (FitnessGoal.CUT, FitnessGoal.RECOMP):
            style = TrainingStyle.HYPERTROPHY
        elif profile.fitness_goal == FitnessGoal.ENDURANCE:
            style = TrainingStyle.ENDURANCE

        workouts: list[WorkoutDay] = []
        freq = min(profile.workout_frequency, 6)

        if profile.fitness_goal in (FitnessGoal.BULK, FitnessGoal.STRENGTH):
            style = TrainingStyle.STRENGTH if profile.fitness_goal == FitnessGoal.STRENGTH else TrainingStyle.HYPERTROPHY
        elif profile.fitness_goal in (FitnessGoal.CUT, FitnessGoal.RECOMP):
            style = TrainingStyle.HYPERTROPHY

        if freq <= 3:
            for _ in range(freq):
                workouts.append(self._create_full_body_day(exercises, style))
        elif freq == 4:
            for day_type in [True, False, True, False]:
                workouts.append(self._create_upper_lower_day(exercises, style, day_type))
        else:
            # 5-6 days: push/pull/legs or upper/lower
            for i in range(freq):
                is_upper = i % 2 == 0
                workouts.append(self._create_upper_lower_day(exercises, style, is_upper))

        nutrition = self.calculate_macros(profile)

        notes = []
        if profile.experience_level == "beginner":
            notes.append("As a beginner, focus on form over weight. Consider adding 2.5kg per session for compounds.")
        if profile.fitness_goal == FitnessGoal.CUT:
            notes.append("During a caloric deficit, prioritize protein intake and keep intensity high while reducing volume slightly.")

        return WeeklyPlan(
            user_id=profile.user_id,
            generated_at=datetime.utcnow(),
            workouts=workouts,
            nutrition=nutrition,
            notes=notes,
        )

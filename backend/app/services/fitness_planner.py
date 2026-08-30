"""
AI Fitness Planner Service — Personalized meal and workout planning
Inspired by ai-fitness-planner: LangGraph workflows, USDA nutrition data, goal-specific plans

Patterns extracted:
- User profile model with fitness goals (cut/bulk/maintenance/recomp)
- Goal-specific calorie and macro calculation
- Meal plan generation with macro targets
- Workout plan generation with split types and training styles
- Food text representation for search
- Comprehensive plan summary
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class FitnessGoal(Enum):
    CUT = "cut"
    BULK = "bulk"
    MAINTENANCE = "maintenance"
    RECOMP = "recomp"


class ActivityLevel(Enum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"


class TrainingStyle(Enum):
    STRENGTH = "strength"
    HYPERTROPHY = "hypertrophy"
    ENDURANCE = "endurance"
    POWER = "power"


class SplitType(Enum):
    FULL_BODY = "full_body"
    UPPER_LOWER = "upper_lower"
    PUSH_PULL_LEGS = "push_pull_legs"
    BRO_SPLIT = "bro_split"
    PPL_TWICE = "ppl_twice"


class MealType(Enum):
    BREAKFAST = "breakfast"
    MORNING_SNACK = "morning_snack"
    LUNCH = "lunch"
    AFTERNOON_SNACK = "afternoon_snack"
    DINNER = "dinner"


@dataclass
class UserProfile:
    user_id: str
    age: int
    weight_kg: float
    height_cm: float
    sex: str  # male, female
    activity_level: ActivityLevel
    fitness_goal: FitnessGoal
    target_calories: Optional[int] = None
    target_protein_g: Optional[float] = None
    target_carbs_g: Optional[float] = None
    target_fat_g: Optional[float] = None
    dietary_restrictions: List[str] = field(default_factory=list)
    allergies: List[str] = field(default_factory=list)
    equipment_available: List[str] = field(default_factory=list)
    workout_frequency: int = 3
    workout_duration_minutes: int = 60
    experience_level: str = "intermediate"  # beginner, intermediate, advanced


@dataclass
class FoodItem:
    name: str
    serving_size: float
    serving_unit: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float = 0.0
    tags: List[str] = field(default_factory=list)


@dataclass
class MealFood:
    food_name: str
    portion: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


@dataclass
class Meal:
    meal_type: MealType
    foods: List[MealFood]
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    preparation_notes: str = ""


@dataclass
class DailyMealPlan:
    day: int
    day_name: str
    meals: List[Meal]
    daily_calories: float
    daily_protein_g: float
    daily_carbs_g: float
    daily_fat_g: float


@dataclass
class Exercise:
    name: str
    sets: int
    reps: str
    rest_seconds: int
    muscle_group: str
    notes: str = ""


@dataclass
class WorkoutDay:
    day: int
    day_name: str
    focus: str
    exercises: List[Exercise]
    estimated_duration: int
    warm_up: List[str] = field(default_factory=list)
    cool_down: List[str] = field(default_factory=list)


@dataclass
class WorkoutPlan:
    plan_name: str
    split_type: SplitType
    training_style: TrainingStyle
    weekly_schedule: List[WorkoutDay]
    progression_strategy: str
    equipment_needed: List[str]
    key_principles: List[str]


@dataclass
class FitnessPlan:
    user_id: str
    meal_plan: Optional[Dict] = None
    workout_plan: Optional[Dict] = None
    summary: str = ""
    generated_at: float = 0.0


# ── Activity Multipliers ──────────────────────────────────────────────────

ACTIVITY_MULTIPLIERS = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHT: 1.375,
    ActivityLevel.MODERATE: 1.55,
    ActivityLevel.ACTIVE: 1.725,
    ActivityLevel.VERY_ACTIVE: 1.9,
}

# ── Goal Adjustments ──────────────────────────────────────────────────────

GOAL_ADJUSTMENTS = {
    FitnessGoal.CUT: {"calorie_delta": -500, "protein_modifier": 1.3, "carb_modifier": 0.8, "fat_modifier": 0.9},
    FitnessGoal.BULK: {"calorie_delta": 300, "protein_modifier": 1.1, "carb_modifier": 1.2, "fat_modifier": 1.0},
    FitnessGoal.MAINTENANCE: {"calorie_delta": 0, "protein_modifier": 1.0, "carb_modifier": 1.0, "fat_modifier": 1.0},
    FitnessGoal.RECOMP: {"calorie_delta": -100, "protein_modifier": 1.4, "carb_modifier": 0.9, "fat_modifier": 0.9},
}

# ── Exercise Database ─────────────────────────────────────────────────────

EXERCISE_DATABASE = {
    "chest": [
        {"name": "Barbell Bench Press", "equipment": ["barbell", "bench"]},
        {"name": "Dumbbell Incline Press", "equipment": ["dumbbells", "bench"]},
        {"name": "Push-ups", "equipment": ["none"]},
        {"name": "Cable Flyes", "equipment": ["cable_machine"]},
        {"name": "Dumbbell Flyes", "equipment": ["dumbbells", "bench"]},
    ],
    "back": [
        {"name": "Barbell Row", "equipment": ["barbell"]},
        {"name": "Pull-ups", "equipment": ["pull_up_bar"]},
        {"name": "Lat Pulldown", "equipment": ["cable_machine"]},
        {"name": "Seated Cable Row", "equipment": ["cable_machine"]},
        {"name": "Dumbbell Row", "equipment": ["dumbbells", "bench"]},
    ],
    "shoulders": [
        {"name": "Overhead Press", "equipment": ["barbell"]},
        {"name": "Dumbbell Lateral Raise", "equipment": ["dumbbells"]},
        {"name": "Face Pulls", "equipment": ["cable_machine"]},
        {"name": "Arnold Press", "equipment": ["dumbbells"]},
        {"name": "Rear Delt Flyes", "equipment": ["dumbbells"]},
    ],
    "legs": [
        {"name": "Barbell Squat", "equipment": ["barbell", "squat_rack"]},
        {"name": "Romanian Deadlift", "equipment": ["barbell"]},
        {"name": "Leg Press", "equipment": ["leg_press_machine"]},
        {"name": "Walking Lunges", "equipment": ["dumbbells"]},
        {"name": "Leg Curl", "equipment": ["machine"]},
        {"name": "Leg Extension", "equipment": ["machine"]},
        {"name": "Calf Raises", "equipment": ["machine"]},
    ],
    "arms": [
        {"name": "Barbell Curl", "equipment": ["barbell"]},
        {"name": "Tricep Pushdown", "equipment": ["cable_machine"]},
        {"name": "Dumbbell Curl", "equipment": ["dumbbells"]},
        {"name": "Skull Crushers", "equipment": ["barbell", "bench"]},
        {"name": "Hammer Curl", "equipment": ["dumbbells"]},
    ],
    "core": [
        {"name": "Plank", "equipment": ["none"]},
        {"name": "Cable Crunch", "equipment": ["cable_machine"]},
        {"name": "Hanging Leg Raise", "equipment": ["pull_up_bar"]},
        {"name": "Ab Wheel Rollout", "equipment": ["ab_wheel"]},
        {"name": "Russian Twists", "equipment": ["none"]},
    ],
}


class FitnessPlanner:
    """Pure function fitness planner — meal and workout generation."""

    # ── Calorie Calculation ───────────────────────────────────────────────

    @staticmethod
    def calculate_bmr(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
        """Mifflin-St Jeor equation for Basal Metabolic Rate."""
        if sex.lower() == "male":
            return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        else:
            return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    @staticmethod
    def calculate_tdee(bmr: float, activity_level: ActivityLevel) -> float:
        """Total Daily Energy Expenditure."""
        return bmr * ACTIVITY_MULTIPLIERS[activity_level]

    @classmethod
    def calculate_target_calories(cls, profile: UserProfile) -> Dict:
        """Calculate target calories and macros based on user profile and goal."""
        bmr = cls.calculate_bmr(profile.weight_kg, profile.height_cm, profile.age, profile.sex)
        tdee = cls.calculate_tdee(bmr, profile.activity_level)
        adjustment = GOAL_ADJUSTMENTS[profile.fitness_goal]
        target_calories = tdee + adjustment["calorie_delta"]

        # Protein: 1.6-2.2g per kg bodyweight (adjusted by goal)
        base_protein = profile.weight_kg * 1.8
        target_protein = base_protein * adjustment["protein_modifier"]

        # Fat: 25-35% of calories
        fat_calories = target_calories * 0.30
        target_fat = fat_calories / 9

        # Carbs: remaining calories
        protein_calories = target_protein * 4
        fat_calories_actual = target_fat * 9
        target_carbs = (target_calories - protein_calories - fat_calories_actual) / 4

        return {
            "calories": round(target_calories),
            "protein_g": round(target_protein, 1),
            "carbs_g": round(max(0, target_carbs), 1),
            "fat_g": round(target_fat, 1),
            "bmr": round(bmr),
            "tdee": round(tdee),
            "goal": profile.fitness_goal.value,
        }

    # ── Meal Planning ─────────────────────────────────────────────────────

    @staticmethod
    def distribute_meals(target_calories: float, target_protein: float,
                         target_carbs: float, target_fat: float,
                         meal_count: int = 5) -> List[Dict]:
        """Distribute macros across meals with appropriate ratios."""
        meal_ratios = {
            3: [0.30, 0.35, 0.35],
            4: [0.25, 0.15, 0.35, 0.25],
            5: [0.25, 0.10, 0.30, 0.10, 0.25],
            6: [0.20, 0.10, 0.25, 0.10, 0.25, 0.10],
        }
        ratios = meal_ratios.get(meal_count, meal_ratios[5])
        meals = []
        for ratio in ratios:
            meals.append({
                "calories": round(target_calories * ratio),
                "protein_g": round(target_protein * ratio, 1),
                "carbs_g": round(target_carbs * ratio, 1),
                "fat_g": round(target_fat * ratio, 1),
            })
        return meals

    @staticmethod
    def create_food_search_text(food: FoodItem) -> str:
        """Create searchable text representation of a food item."""
        parts = [f"Food: {food.name}"]
        parts.append(f"Calories: {food.calories} per {food.serving_size}{food.serving_unit}")
        parts.append(f"Protein: {food.protein_g}g, Carbs: {food.carbs_g}g, Fat: {food.fat_g}g")
        if food.fiber_g > 0:
            parts.append(f"Fiber: {food.fiber_g}g")
        if food.tags:
            parts.append(f"Tags: {', '.join(food.tags)}")
        return " | ".join(parts)

    @staticmethod
    def score_food_match(food: FoodItem, target_macros: Dict, restrictions: List[str]) -> float:
        """Score how well a food matches target macros and restrictions."""
        score = 1.0

        # Check restrictions
        for restriction in restrictions:
            if restriction in food.tags:
                score *= 0.0  # Disqualify if matches restriction

        # Protein density score
        if target_macros.get("protein_g", 0) > 0:
            protein_density = food.protein_g / max(food.calories, 1) * 100
            score *= min(1.0, protein_density / 30)  # 30% protein density is ideal

        return score

    # ── Workout Planning ──────────────────────────────────────────────────

    @staticmethod
    def generate_split(split_type: SplitType, days_per_week: int,
                       training_style: TrainingStyle) -> List[Dict]:
        """Generate workout split based on type and frequency."""
        splits = {
            SplitType.FULL_BODY: [
                {"day": 1, "focus": "Full Body A", "muscles": ["chest", "back", "legs", "shoulders", "arms", "core"]},
                {"day": 2, "focus": "Full Body B", "muscles": ["chest", "back", "legs", "shoulders", "arms", "core"]},
                {"day": 3, "focus": "Full Body C", "muscles": ["chest", "back", "legs", "shoulders", "arms", "core"]},
            ],
            SplitType.UPPER_LOWER: [
                {"day": 1, "focus": "Upper Body", "muscles": ["chest", "back", "shoulders", "arms"]},
                {"day": 2, "focus": "Lower Body", "muscles": ["legs", "core"]},
                {"day": 3, "focus": "Upper Body", "muscles": ["chest", "back", "shoulders", "arms"]},
                {"day": 4, "focus": "Lower Body", "muscles": ["legs", "core"]},
            ],
            SplitType.PUSH_PULL_LEGS: [
                {"day": 1, "focus": "Push", "muscles": ["chest", "shoulders"]},
                {"day": 2, "focus": "Pull", "muscles": ["back", "arms"]},
                {"day": 3, "focus": "Legs", "muscles": ["legs", "core"]},
                {"day": 4, "focus": "Push", "muscles": ["chest", "shoulders"]},
                {"day": 5, "focus": "Pull", "muscles": ["back", "arms"]},
                {"day": 6, "focus": "Legs", "muscles": ["legs", "core"]},
            ],
        }
        template = splits.get(split_type, splits[SplitType.FULL_BODY])
        return template[:days_per_week]

    @staticmethod
    def select_exercises(muscles: List[str], equipment: List[str],
                         exercises_per_muscle: int = 2) -> List[Dict]:
        """Select exercises based on available equipment."""
        selected = []
        for muscle in muscles:
            available = EXERCISE_DATABASE.get(muscle, [])
            # Filter by equipment
            usable = [e for e in available
                     if any(eq in equipment for eq in e["equipment"]) or "none" in e["equipment"]]
            if not usable:
                usable = available[:exercises_per_muscle]  # Fallback to any
            selected.extend(usable[:exercises_per_muscle])
        return selected

    @staticmethod
    def get_reps_for_style(style: TrainingStyle) -> str:
        """Get rep range based on training style."""
        rep_ranges = {
            TrainingStyle.STRENGTH: "3-5",
            TrainingStyle.HYPERTROPHY: "8-12",
            TrainingStyle.ENDURANCE: "15-20",
            TrainingStyle.POWER: "3-6",
        }
        return rep_ranges[style]

    @staticmethod
    def get_rest_for_style(style: TrainingStyle) -> int:
        """Get rest period based on training style."""
        rest_periods = {
            TrainingStyle.STRENGTH: 180,
            TrainingStyle.HYPERTROPHY: 90,
            TrainingStyle.ENDURANCE: 45,
            TrainingStyle.POWER: 180,
        }
        return rest_periods[style]

    # ── Plan Generation ───────────────────────────────────────────────────

    @classmethod
    def generate_complete_plan(cls, profile: UserProfile) -> FitnessPlan:
        """Generate a complete fitness plan with meals and workouts."""
        macros = cls.calculate_target_calories(profile)
        meal_distribution = cls.distribute_meals(
            macros["calories"], macros["protein_g"],
            macros["carbs_g"], macros["fat_g"], 5
        )
        split = cls.generate_split(
            SplitType.PUSH_PULL_LEGS if profile.workout_frequency >= 5
            else SplitType.UPPER_LOWER if profile.workout_frequency >= 4
            else SplitType.FULL_BODY,
            profile.workout_frequency,
            TrainingStyle.HYPERTROPHY
        )
        equipment = profile.equipment_available or ["none", "dumbbells", "barbell"]
        workout_days = []
        for day_info in split:
            exercises = cls.select_exercises(day_info["muscles"], equipment)
            workout_day = WorkoutDay(
                day=day_info["day"],
                day_name=f"Day {day_info['day']}",
                focus=day_info["focus"],
                exercises=[
                    Exercise(
                        name=e["name"],
                        sets=4 if profile.experience_level == "advanced" else 3,
                        reps=cls.get_reps_for_style(TrainingStyle.HYPERTROPHY),
                        rest_seconds=cls.get_rest_for_style(TrainingStyle.HYPERTROPHY),
                        muscle_group=day_info["focus"],
                    )
                    for e in exercises
                ],
                estimated_duration=profile.workout_duration_minutes,
                warm_up=["5 min light cardio", "Dynamic stretching"],
                cool_down=["Static stretching", "Foam rolling"],
            )
            workout_days.append(workout_day)
        workout_plan = WorkoutPlan(
            plan_name=f"{profile.fitness_goal.value.title()} Plan - {profile.experience_level.title()}",
            split_type=SplitType.PUSH_PULL_LEGS,
            training_style=TrainingStyle.HYPERTROPHY,
            weekly_schedule=workout_days,
            progression_strategy="Increase weight by 2.5-5% when you can complete all sets with good form",
            equipment_needed=equipment,
            key_principles=[
                "Progressive overload is key to adaptation",
                "Prioritize compound movements",
                "Allow 48 hours between training same muscle groups",
                "Track your workouts for progressive overload",
            ],
        )
        summary = cls._generate_summary(profile, macros, workout_plan)
        return FitnessPlan(
            user_id=profile.user_id,
            meal_plan={
                "target_macros": macros,
                "meal_distribution": meal_distribution,
                "meal_count": 5,
            },
            workout_plan={
                "plan_name": workout_plan.plan_name,
                "split_type": workout_plan.split_type.value,
                "training_style": workout_plan.training_style.value,
                "days": len(workout_plan.weekly_schedule),
                "progression": workout_plan.progression_strategy,
            },
            summary=summary,
        )

    @staticmethod
    def _generate_summary(profile: UserProfile, macros: Dict, plan: WorkoutPlan) -> str:
        """Generate a human-readable summary of the fitness plan."""
        goal_text = {
            FitnessGoal.CUT: "fat loss while preserving muscle",
            FitnessGoal.BULK: "muscle gain with controlled fat",
            FitnessGoal.MAINTENANCE: "maintaining current physique",
            FitnessGoal.RECOMP: "body recomposition (simultaneous fat loss and muscle gain)",
        }
        return (
            f"Your {profile.fitness_goal.value} plan targets {macros['calories']} calories/day "
            f"with {macros['protein_g']}g protein, {macros['carbs_g']}g carbs, and "
            f"{macros['fat_g']}g fat. Training {profile.workout_frequency}x/week with "
            f"{plan.split_type.value.replace('_', ' ')} split focused on {goal_text.get(profile.fitness_goal, 'fitness')}. "
            f"Progression: {plan.progression_strategy}."
        )

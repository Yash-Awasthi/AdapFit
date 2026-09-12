"""
Nutrition Tracking Service — Macro/micronutrient analysis, meal tracking, dietary restrictions
Inspired by ai-fitness-planner, athlete-training-load-prediction
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field

from app.services.fitness_planner import FitnessPlanner, ActivityLevel


class DietaryRestriction(Enum):
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    KETO = "keto"
    PALEO = "paleo"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    HALAL = "halal"
    KOSHER = "kosher"
    LOW_CARB = "low_carb"
    LOW_FAT = "low_fat"


class MealType(Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


@dataclass
class Nutrient:
    name: str
    amount: float
    unit: str
    daily_value_percent: float = 0.0


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
    sugar_g: float = 0.0
    sodium_mg: float = 0.0
    cholesterol_mg: float = 0.0
    vitamins: Dict[str, float] = field(default_factory=dict)
    minerals: Dict[str, float] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class Meal:
    meal_type: MealType
    foods: List[FoodItem]
    timestamp: float
    notes: str = ""


@dataclass
class DailyNutrition:
    date: str
    total_calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    sugar_g: float
    sodium_mg: float
    meals: List[Meal]
    macro_split: Dict[str, float]
    hydration_ml: float = 0.0


@dataclass
class NutritionGoal:
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    restrictions: List[DietaryRestriction] = field(default_factory=list)


class NutritionTracker:
    """Pure function nutrition analysis and tracking."""

    # Daily recommended values
    DV = {
        "calories": 2000,
        "protein_g": 50,
        "carbs_g": 275,
        "fat_g": 78,
        "fiber_g": 28,
        "sugar_g": 50,
        "sodium_mg": 2300,
        "cholesterol_mg": 300,
        "vitamin_a": 900,
        "vitamin_c": 90,
        "vitamin_d": 20,
        "calcium": 1300,
        "iron": 18,
        "potassium": 4700,
    }

    @staticmethod
    def calculate_macro_split(foods: List[FoodItem]) -> Dict[str, float]:
        total_protein = sum(f.protein_g for f in foods)
        total_carbs = sum(f.carbs_g for f in foods)
        total_fat = sum(f.fat_g for f in foods)
        total_calories = (total_protein * 4 + total_carbs * 4 + total_fat * 9)
        if total_calories == 0:
            return {"protein": 0, "carbs": 0, "fat": 0}
        return {
            "protein": round(total_protein * 4 / total_calories * 100, 1),
            "carbs": round(total_carbs * 4 / total_calories * 100, 1),
            "fat": round(total_fat * 9 / total_calories * 100, 1),
        }

    @staticmethod
    def calculate_meal_totals(foods: List[FoodItem]) -> Dict:
        return {
            "calories": sum(f.calories for f in foods),
            "protein_g": sum(f.protein_g for f in foods),
            "carbs_g": sum(f.carbs_g for f in foods),
            "fat_g": sum(f.fat_g for f in foods),
            "fiber_g": sum(f.fiber_g for f in foods),
            "sugar_g": sum(f.sugar_g for f in foods),
            "sodium_mg": sum(f.sodium_mg for f in foods),
        }

    @classmethod
    def calculate_daily_totals(cls, meals: List[Meal]) -> DailyNutrition:
        all_foods = []
        for meal in meals:
            all_foods.extend(meal.foods)
        totals = cls.calculate_meal_totals(all_foods)
        macro_split = cls.calculate_macro_split(all_foods)
        return DailyNutrition(
            date="",
            total_calories=totals["calories"],
            protein_g=totals["protein_g"],
            carbs_g=totals["carbs_g"],
            fat_g=totals["fat_g"],
            fiber_g=totals["fiber_g"],
            sugar_g=totals["sugar_g"],
            sodium_mg=totals["sodium_mg"],
            meals=meals,
            macro_split=macro_split,
        )

    @staticmethod
    def check_dietary_compliance(foods: List[FoodItem],
                                  restrictions: List[DietaryRestriction]) -> Dict:
        violations = []
        for food in foods:
            for restriction in restrictions:
                if restriction == DietaryRestriction.VEGETARIAN:
                    if "meat" in food.tags or "fish" in food.tags:
                        violations.append(f"{food.name} contains meat/fish")
                elif restriction == DietaryRestriction.VEGAN:
                    if any(t in food.tags for t in ["meat", "fish", "dairy", "eggs"]):
                        violations.append(f"{food.name} contains animal products")
                elif restriction == DietaryRestriction.KETO:
                    if food.carbs_g > 10:
                        violations.append(f"{food.name} too high in carbs for keto")
                elif restriction == DietaryRestriction.GLUTEN_FREE:
                    if "gluten" in food.tags:
                        violations.append(f"{food.name} contains gluten")
                elif restriction == DietaryRestriction.DAIRY_FREE:
                    if "dairy" in food.tags:
                        violations.append(f"{food.name} contains dairy")
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "violation_count": len(violations),
        }

    @staticmethod
    def score_nutrition_quality(daily: DailyNutrition, goal: NutritionGoal) -> float:
        scores = []
        if goal.calories > 0:
            cal_ratio = daily.total_calories / goal.calories
            cal_score = max(0, 1 - abs(1 - cal_ratio))
            scores.append(("calories", cal_score, 0.3))
        if goal.protein_g > 0:
            protein_ratio = daily.protein_g / goal.protein_g
            protein_score = max(0, min(1, protein_ratio))
            scores.append(("protein", protein_score, 0.25))
        if goal.fat_g > 0:
            fat_ratio = daily.fat_g / goal.fat_g
            fat_score = max(0, 1 - abs(1 - fat_ratio))
            scores.append(("fat", fat_score, 0.2))
        if goal.carbs_g > 0:
            carbs_ratio = daily.carbs_g / goal.carbs_g
            carbs_score = max(0, 1 - abs(1 - carbs_ratio))
            scores.append(("carbs", carbs_score, 0.15))
        fiber_score = min(1.0, daily.fiber_g / 28)
        scores.append(("fiber", fiber_score, 0.1))
        if not scores:
            return 0.0
        total = sum(score * weight for _, score, weight in scores)
        total_weight = sum(weight for _, _, weight in scores)
        return round(total / total_weight * 100, 1) if total_weight > 0 else 0.0

    @staticmethod
    def generate_recommendations(daily: DailyNutrition, goal: NutritionGoal) -> List[str]:
        recommendations = []
        cal_diff = goal.calories - daily.total_calories
        if cal_diff > 200:
            recommendations.append(f"You need {int(cal_diff)} more calories today")
        elif cal_diff < -200:
            recommendations.append(f"You've exceeded your calorie goal by {int(abs(cal_diff))}")
        if daily.protein_g < goal.protein_g * 0.8:
            recommendations.append("Consider adding more protein-rich foods")
        if daily.fiber_g < 20:
            recommendations.append("Add more fiber-rich foods (vegetables, whole grains)")
        if daily.sodium_mg > 2300:
            recommendations.append("Sodium intake is high — reduce processed foods")
        if daily.sugar_g > 50:
            recommendations.append("Sugar intake is above recommended limit")
        if daily.hydration_ml < 2000:
            recommendations.append("Drink more water — aim for 2-3 liters daily")
        return recommendations

    @classmethod
    def estimate_portion(cls, food: FoodItem, portion_grams: float) -> FoodItem:
        factor = portion_grams / food.serving_size
        return FoodItem(
            name=food.name,
            serving_size=portion_grams,
            serving_unit="g",
            calories=round(food.calories * factor, 1),
            protein_g=round(food.protein_g * factor, 1),
            carbs_g=round(food.carbs_g * factor, 1),
            fat_g=round(food.fat_g * factor, 1),
            fiber_g=round(food.fiber_g * factor, 1),
            sugar_g=round(food.sugar_g * factor, 1),
            sodium_mg=round(food.sodium_mg * factor, 1),
            tags=food.tags,
        )

    @staticmethod
    def calculate_water_score(hydration_ml: float, weight_kg: float,
                              exercise_minutes: int, temperature_c: float) -> float:
        base_need = weight_kg * 30
        exercise_add = exercise_minutes * 0.5
        heat_add = max(0, (temperature_c - 25)) * 200
        total_need = base_need + exercise_add + heat_add
        if total_need <= 0:
            return 100.0
        return min(100.0, round(hydration_ml / total_need * 100, 1))


# ── Endpoint-facing API ─────────────────────────────────────────────────────
# The endpoints post flat macro figures, while the tracker works in FoodItem
# and DailyNutrition. These models are the wire format and the functions below
# convert one into the other and return JSON-ready dicts.

class MacroNutrients(BaseModel):
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0
    fiber_g: float = 0.0

    @property
    def calories(self) -> float:
        """Energy from the macros: 4 kcal/g protein and carbs, 9 kcal/g fat."""
        return self.protein_g * 4 + self.carbs_g * 4 + self.fat_g * 9


class MicroNutrients(BaseModel):
    """Optional micronutrient detail, keyed by nutrient name."""
    vitamins: Dict[str, float] = Field(default_factory=dict)
    minerals: Dict[str, float] = Field(default_factory=dict)


class MealEntry(BaseModel):
    name: str
    calories: float = 0.0
    macros: MacroNutrients = Field(default_factory=MacroNutrients)
    meal_type: str = "snack"


class DailyIntake(BaseModel):
    meals: List[MealEntry] = Field(default_factory=list)
    water_ml: float = 0.0
    target_calories: float = 2000.0
    target_protein_g: float = 150.0
    target_water_ml: float = 3000.0


# Dietary profiles as name → macro shape and ceiling. Values stay plain so the
# restriction listing can be serialised directly.
DIETARY_PROFILES: Dict[str, Dict] = {
    "standard": {
        "name": "Standard",
        "description": "Balanced mixed diet with no restrictions",
        "protein_pct": 20, "carbs_pct": 50, "fat_pct": 30,
        "max_carbs_g": None, "max_fat_pct": None, "exclude_tags": [],
    },
    "vegetarian": {
        "name": "Vegetarian",
        "description": "No meat or fish; dairy and eggs allowed",
        "protein_pct": 20, "carbs_pct": 50, "fat_pct": 30,
        "max_carbs_g": None, "max_fat_pct": None, "exclude_tags": ["meat", "fish"],
    },
    "vegan": {
        "name": "Vegan",
        "description": "No animal products of any kind",
        "protein_pct": 20, "carbs_pct": 52, "fat_pct": 28,
        "max_carbs_g": None, "max_fat_pct": None,
        "exclude_tags": ["meat", "fish", "dairy", "eggs"],
    },
    "keto": {
        "name": "Ketogenic",
        "description": "Very low carbohydrate, high fat",
        "protein_pct": 25, "carbs_pct": 5, "fat_pct": 70,
        "max_carbs_g": 30, "max_fat_pct": None, "exclude_tags": [],
    },
    "low_carb": {
        "name": "Low carbohydrate",
        "description": "Reduced carbohydrate, higher protein and fat",
        "protein_pct": 30, "carbs_pct": 25, "fat_pct": 45,
        "max_carbs_g": 130, "max_fat_pct": None, "exclude_tags": [],
    },
    "low_fat": {
        "name": "Low fat",
        "description": "Fat held below a quarter of daily energy",
        "protein_pct": 25, "carbs_pct": 55, "fat_pct": 20,
        "max_carbs_g": None, "max_fat_pct": 25, "exclude_tags": [],
    },
    "paleo": {
        "name": "Paleo",
        "description": "Whole foods; no grains, legumes or dairy",
        "protein_pct": 30, "carbs_pct": 30, "fat_pct": 40,
        "max_carbs_g": None, "max_fat_pct": None,
        "exclude_tags": ["grains", "legumes", "dairy"],
    },
    "gluten_free": {
        "name": "Gluten free",
        "description": "No wheat, barley, rye or their derivatives",
        "protein_pct": 20, "carbs_pct": 50, "fat_pct": 30,
        "max_carbs_g": None, "max_fat_pct": None, "exclude_tags": ["gluten"],
    },
    "dairy_free": {
        "name": "Dairy free",
        "description": "No milk, cheese, butter or whey",
        "protein_pct": 20, "carbs_pct": 50, "fat_pct": 30,
        "max_carbs_g": None, "max_fat_pct": None, "exclude_tags": ["dairy"],
    },
    "halal": {
        "name": "Halal",
        "description": "No pork or alcohol",
        "protein_pct": 20, "carbs_pct": 50, "fat_pct": 30,
        "max_carbs_g": None, "max_fat_pct": None, "exclude_tags": ["pork", "alcohol"],
    },
    "kosher": {
        "name": "Kosher",
        "description": "No pork or shellfish; meat and dairy kept separate",
        "protein_pct": 20, "carbs_pct": 50, "fat_pct": 30,
        "max_carbs_g": None, "max_fat_pct": None,
        "exclude_tags": ["pork", "shellfish"],
    },
}

DIET_RESTRICTIONS = {
    "vegetarian": DietaryRestriction.VEGETARIAN,
    "vegan": DietaryRestriction.VEGAN,
    "keto": DietaryRestriction.KETO,
    "paleo": DietaryRestriction.PALEO,
    "gluten_free": DietaryRestriction.GLUTEN_FREE,
    "dairy_free": DietaryRestriction.DAIRY_FREE,
    "halal": DietaryRestriction.HALAL,
    "kosher": DietaryRestriction.KOSHER,
    "low_carb": DietaryRestriction.LOW_CARB,
    "low_fat": DietaryRestriction.LOW_FAT,
}


def _meal_type(value: str) -> MealType:
    try:
        return MealType(value.strip().lower())
    except ValueError:
        return MealType.SNACK


def _to_service_meal(entry: MealEntry) -> Meal:
    macros = entry.macros
    food = FoodItem(
        name=entry.name,
        serving_size=1.0,
        serving_unit="serving",
        calories=entry.calories,
        protein_g=macros.protein_g,
        carbs_g=macros.carbs_g,
        fat_g=macros.fat_g,
        fiber_g=macros.fiber_g,
    )
    return Meal(meal_type=_meal_type(entry.meal_type), foods=[food], timestamp=0.0)


def _goal_for(intake: DailyIntake, diet: str) -> NutritionGoal:
    """Build the tracker's goal shape from the intake's targets and diet."""
    profile = DIETARY_PROFILES.get(diet, DIETARY_PROFILES["standard"])
    remaining = max(0.0, intake.target_calories - intake.target_protein_g * 4)
    return NutritionGoal(
        calories=intake.target_calories,
        protein_g=intake.target_protein_g,
        carbs_g=remaining * profile["carbs_pct"] / max(1, profile["carbs_pct"] + profile["fat_pct"]) / 4,
        fat_g=remaining * profile["fat_pct"] / max(1, profile["carbs_pct"] + profile["fat_pct"]) / 9,
        restrictions=[DIET_RESTRICTIONS[diet]] if diet in DIET_RESTRICTIONS else [],
    )


def analyze_daily_intake(intake: DailyIntake, diet: str = "standard") -> Dict:
    """Analyse a day of meals against its calorie, macro and water targets."""
    key = diet.strip().lower()
    profile = DIETARY_PROFILES.get(key)
    if profile is None:
        raise KeyError(diet)

    meals = [_to_service_meal(m) for m in intake.meals]
    daily = NutritionTracker.calculate_daily_totals(meals)
    daily.hydration_ml = intake.water_ml
    goal = _goal_for(intake, key)

    foods = [food for meal in meals for food in meal.foods]
    compliance = NutritionTracker.check_dietary_compliance(
        foods, goal.restrictions
    )

    # Ceilings that the tag-based check cannot see, because meals arrive as
    # aggregate macros rather than tagged ingredients.
    if profile["max_carbs_g"] is not None and daily.carbs_g > profile["max_carbs_g"]:
        compliance["compliant"] = False
        compliance["violations"].append(
            f"Total carbohydrate {daily.carbs_g:.0f}g exceeds the {profile['max_carbs_g']}g "
            f"ceiling for {profile['name']}"
        )
    if profile["max_fat_pct"] is not None and daily.total_calories > 0:
        fat_pct = daily.fat_g * 9 / daily.total_calories * 100
        if fat_pct > profile["max_fat_pct"]:
            compliance["compliant"] = False
            compliance["violations"].append(
                f"Fat is {fat_pct:.0f}% of energy, above the {profile['max_fat_pct']}% "
                f"ceiling for {profile['name']}"
            )
    compliance["violation_count"] = len(compliance["violations"])

    quality = NutritionTracker.score_nutrition_quality(daily, goal)
    water_target = intake.target_water_ml or 1
    water_pct = min(100.0, round(intake.water_ml / water_target * 100, 1))

    return {
        "diet": diet.strip().lower(),
        "diet_name": profile["name"],
        "meal_count": len(intake.meals),
        "totals": {
            "calories": round(daily.total_calories, 1),
            "protein_g": round(daily.protein_g, 1),
            "carbs_g": round(daily.carbs_g, 1),
            "fat_g": round(daily.fat_g, 1),
            "fiber_g": round(daily.fiber_g, 1),
        },
        "targets": {
            "calories": intake.target_calories,
            "protein_g": intake.target_protein_g,
            "water_ml": intake.target_water_ml,
        },
        "remaining": {
            "calories": round(intake.target_calories - daily.total_calories, 1),
            "protein_g": round(intake.target_protein_g - daily.protein_g, 1),
        },
        "macro_split_pct": daily.macro_split,
        "quality_score": quality,
        "water_ml": intake.water_ml,
        "water_target_pct": water_pct,
        "compliance": compliance,
        "recommendations": NutritionTracker.generate_recommendations(daily, goal),
    }


def calculate_tdee(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: str,
    activity_level: str = "moderate",
) -> Dict:
    """Total daily energy expenditure from Mifflin-St Jeor and an activity factor."""
    try:
        level = ActivityLevel(activity_level.strip().lower())
    except ValueError:
        level = ActivityLevel.MODERATE

    bmr = FitnessPlanner.calculate_bmr(weight_kg, height_cm, age, sex)
    tdee = FitnessPlanner.calculate_tdee(bmr, level)

    return {
        "bmr": round(bmr, 1),
        "tdee": round(tdee, 1),
        "activity_level": level.value,
        "activity_multiplier": round(tdee / bmr, 3) if bmr > 0 else 0.0,
        "method": "Mifflin-St Jeor",
        "goal_calories": {
            "cut": round(tdee - 500, 1),
            "maintain": round(tdee, 1),
            "bulk": round(tdee + 300, 1),
        },
    }


def score_meal_quality(meal: MealEntry) -> Dict:
    """Score a single meal on macro balance, protein density and fiber."""
    macros = meal.macros
    service_meal = _to_service_meal(meal)
    daily = NutritionTracker.calculate_daily_totals([service_meal])

    # Balance is scored against the plate's own energy, so the calorie term
    # saturates and the remaining terms describe the composition.
    energy = max(macros.calories, meal.calories, 1.0)
    balance_goal = NutritionGoal(
        calories=energy,
        protein_g=energy * 0.30 / 4,
        carbs_g=energy * 0.40 / 4,
        fat_g=energy * 0.30 / 9,
    )
    score = NutritionTracker.score_nutrition_quality(daily, balance_goal)

    if score >= 80:
        label = "excellent"
    elif score >= 65:
        label = "good"
    elif score >= 50:
        label = "fair"
    else:
        label = "poor"

    notes = []
    protein_pct = macros.protein_g * 4 / energy * 100
    fat_pct = macros.fat_g * 9 / energy * 100
    if protein_pct < 15:
        notes.append("Low in protein for a meal — add a lean protein source.")
    if protein_pct > 40:
        notes.append("Very high protein share — pair with carbohydrate for training days.")
    if fat_pct > 45:
        notes.append("Fat provides a large share of this meal's energy.")
    if macros.fiber_g < 5:
        notes.append("Low in fiber — add vegetables, fruit or whole grains.")

    return {
        "name": meal.name,
        "meal_type": meal.meal_type,
        "calories": round(meal.calories, 1),
        "macros": {
            "protein_g": macros.protein_g,
            "carbs_g": macros.carbs_g,
            "fat_g": macros.fat_g,
            "fiber_g": macros.fiber_g,
        },
        "protein_pct": round(protein_pct, 1),
        "fat_pct": round(fat_pct, 1),
        "quality_score": score,
        "label": label,
        "notes": notes,
    }

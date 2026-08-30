"""
Nutrition Tracking Service — Macro/micronutrient analysis, meal tracking, dietary restrictions
Inspired by ai-fitness-planner, athlete-training-load-prediction
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


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

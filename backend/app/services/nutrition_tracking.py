"""
Nutrition Tracking Engine

Macro/micronutrient analysis, hydration tracking, dietary restriction support,
and meal quality scoring.
"""
from dataclasses import dataclass, field
from typing import Optional
import statistics


# Dietary restriction profiles
DIETARY_PROFILES = {
    "standard":    {"protein_g_per_kg": 1.6, "fat_pct": (25, 35), "carb_pct": (40, 55)},
    "vegan":       {"protein_g_per_kg": 1.8, "fat_pct": (20, 35), "carb_pct": (45, 60), "supplements": ["B12", "iron", "omega-3"]},
    "vegetarian":  {"protein_g_per_kg": 1.6, "fat_pct": (25, 35), "carb_pct": (40, 55)},
    "keto":        {"protein_g_per_kg": 1.8, "fat_pct": (70, 80), "carb_pct": (5, 10)},
    "paleo":       {"protein_g_per_kg": 1.8, "fat_pct": (30, 40), "carb_pct": (20, 35)},
    "halal":       {"protein_g_per_kg": 1.6, "fat_pct": (25, 35), "carb_pct": (40, 55), "restrictions": ["pork", "alcohol"]},
    "kosher":      {"protein_g_per_kg": 1.6, "fat_pct": (25, 35), "carb_pct": (40, 55), "restrictions": ["pork", "shellfish", "mixing dairy meat"]},
    "gluten_free": {"protein_g_per_kg": 1.6, "fat_pct": (25, 35), "carb_pct": (40, 55), "restrictions": ["wheat", "barley", "rye"]},
    "mediterranean": {"protein_g_per_kg": 1.6, "fat_pct": (35, 40), "carb_pct": (40, 50), "focus": "olive oil, fish, vegetables"},
}


@dataclass
class MacroNutrients:
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float = 0

    @property
    def total_calories(self) -> float:
        return self.protein_g * 4 + self.carbs_g * 4 + self.fat_g * 9

    @property
    def protein_pct(self) -> float:
        cal = self.total_calories
        return (self.protein_g * 4 / cal * 100) if cal > 0 else 0

    @property
    def carb_pct(self) -> float:
        cal = self.total_calories
        return (self.carbs_g * 4 / cal * 100) if cal > 0 else 0

    @property
    def fat_pct(self) -> float:
        cal = self.total_calories
        return (self.fat_g * 9 / cal * 100) if cal > 0 else 0


@dataclass
class MicroNutrients:
    vitamin_a_mcg: float = 0
    vitamin_c_mg: float = 0
    vitamin_d_mcg: float = 0
    vitamin_b12_mcg: float = 0
    calcium_mg: float = 0
    iron_mg: float = 0
    potassium_mg: float = 0
    sodium_mg: float = 0
    zinc_mg: float = 0
    omega_3_g: float = 0


@dataclass
class MealEntry:
    name: str
    calories: float
    macros: MacroNutrients
    micros: Optional[MicroNutrients] = None
    meal_type: str = "snack"  # "breakfast", "lunch", "dinner", "snack"
    restrictions_check: Optional[dict] = None


@dataclass
class DailyIntake:
    meals: list[MealEntry]
    water_ml: float = 0
    target_calories: float = 2000
    target_protein_g: float = 150
    target_water_ml: float = 3000


def analyze_daily_intake(intake: DailyIntake, diet: str = "standard") -> dict:
    """Analyze daily nutritional intake against targets."""
    total_cal = sum(m.calories for m in intake.meals)
    total_protein = sum(m.macros.protein_g for m in intake.meals)
    total_carbs = sum(m.macros.carbs_g for m in intake.meals)
    total_fat = sum(m.macros.fat_g for m in intake.meals)
    total_fiber = sum(m.macros.fiber_g for m in intake.meals)

    combined = MacroNutrients(total_protein, total_carbs, total_fat, total_fiber)

    # Calorie target adherence
    calorie_adherence = (total_cal / intake.target_calories * 100) if intake.target_calories > 0 else 0
    protein_adherence = (total_protein / intake.target_protein_g * 100) if intake.target_protein_g > 0 else 0

    # Meal distribution
    meal_types = {}
    for m in intake.meals:
        meal_types[m.meal_type] = meal_types.get(m.meal_type, 0) + m.calories

    # Diet-specific check
    profile = DIETARY_PROFILES.get(diet, DIETARY_PROFILES["standard"])
    macro_check = _check_macro_ranges(combined, profile)

    # Water intake
    water_pct = (intake.water_ml / intake.target_water_ml * 100) if intake.target_water_ml > 0 else 0

    return {
        "total_calories": round(total_cal),
        "total_protein_g": round(total_protein, 1),
        "total_carbs_g": round(total_carbs, 1),
        "total_fat_g": round(total_fat, 1),
        "total_fiber_g": round(total_fiber, 1),
        "macro_breakdown": {
            "protein_pct": round(combined.protein_pct, 1),
            "carb_pct": round(combined.carb_pct, 1),
            "fat_pct": round(combined.fat_pct, 1),
        },
        "calorie_adherence_pct": round(calorie_adherence, 1),
        "protein_adherence_pct": round(protein_adherence, 1),
        "meal_distribution": meal_types,
        "diet": diet,
        "macro_in_range": macro_check,
        "water_ml": intake.water_ml,
        "water_adherence_pct": round(water_pct, 1),
        "meal_count": len(intake.meals),
    }


def _check_macro_ranges(macros: MacroNutrients, profile: dict) -> dict:
    """Check if macros fall within the diet profile's recommended ranges."""
    fat_lo, fat_hi = profile.get("fat_pct", (25, 35))
    carb_lo, carb_hi = profile.get("carb_pct", (40, 55))

    return {
        "protein_in_range": macros.protein_pct >= 15,
        "fat_in_range": fat_lo <= macros.fat_pct <= fat_hi,
        "carb_in_range": carb_lo <= macros.carb_pct <= carb_hi,
    }


def calculate_tdee(weight_kg: float, height_cm: float, age: int, sex: str, activity_level: str) -> dict:
    """Calculate Total Daily Energy Expenditure (Mifflin-St Jeor)."""
    if sex == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }
    multiplier = multipliers.get(activity_level, 1.55)
    tdee = bmr * multiplier

    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "activity_level": activity_level,
        "maintenance_calories": round(tdee),
        "deficit_500": round(tdee - 500),
        "surplus_300": round(tdee + 300),
    }


def score_meal_quality(meal: MealEntry) -> dict:
    """Score a meal's nutritional quality (0-100)."""
    score = 0

    # Protein quality (25 pts)
    if meal.macros.protein_g >= 25:
        score += 25
    elif meal.macros.protein_g >= 15:
        score += 15
    elif meal.macros.protein_g >= 8:
        score += 8

    # Fiber (20 pts)
    if meal.macros.fiber_g >= 8:
        score += 20
    elif meal.macros.fiber_g >= 4:
        score += 12

    # Calorie density (20 pts) — lower is better for most meals
    if meal.calories > 0:
        cal_per_gram = meal.calories / max(1, sum([meal.macros.protein_g, meal.macros.carbs_g, meal.macros.fat_g]))
        if cal_per_gram <= 4:
            score += 20
        elif cal_per_gram <= 5:
            score += 12

    # Macro balance (20 pts)
    if 15 <= meal.macros.protein_pct <= 40:
        score += 10
    if meal.macros.fat_pct <= 35:
        score += 10

    # Micronutrient presence (15 pts)
    if meal.micros:
        micro_count = sum(1 for v in [
            meal.micros.vitamin_c_mg, meal.micros.iron_mg,
            meal.micros.potassium_mg, meal.micros.calcium_mg
        ] if v > 0)
        score += min(15, micro_count * 4)

    return {
        "quality_score": min(100, score),
        "grade": "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "D",
    }

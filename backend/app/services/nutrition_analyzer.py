"""
AI Nutrition Analyzer — analyzes meals, tracks macros, and generates plans.

Features:
- Food recognition from descriptions
- Macro/micronutrient calculation
- Meal plan generation based on goals
- Allergen detection and substitution
- Meal timing optimization (pre/post workout)
- Weekly nutrition reports
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import List, Dict, Optional, Tuple


class DietaryGoal(Enum):
    FAT_LOSS = "fat_loss"
    MUSCLE_GAIN = "muscle_gain"
    MAINTENANCE = "maintenance"
    PERFORMANCE = "performance"
    HEALTH = "health"
    KETO = "keto"
    VEGAN = "vegan"


class MealType(Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    PRE_WORKOUT = "pre_workout"
    POST_WORKOUT = "post_workout"


@dataclass
class NutrientProfile:
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float = 0
    sugar_g: float = 0
    sodium_mg: float = 0
    potassium_mg: float = 0
    vitamin_a_iu: float = 0
    vitamin_c_mg: float = 0
    calcium_mg: float = 0
    iron_mg: float = 0
    omega_3_g: float = 0


@dataclass
class FoodItem:
    name: str
    serving_size: str
    nutrients: NutrientProfile
    allergens: List[str] = field(default_factory=list)
    category: str = ""


@dataclass
class Meal:
    meal_type: MealType
    foods: List[Tuple[FoodItem, float]]  # food, multiplier
    time: str = ""
    notes: str = ""

    @property
    def total_nutrients(self) -> NutrientProfile:
        total = NutrientProfile(0, 0, 0, 0)
        for food, multiplier in self.foods:
            total.calories += food.nutrients.calories * multiplier
            total.protein_g += food.nutrients.protein_g * multiplier
            total.carbs_g += food.nutrients.carbs_g * multiplier
            total.fat_g += food.nutrients.fat_g * multiplier
            total.fiber_g += food.nutrients.fiber_g * multiplier
        return total


@dataclass
class DailyPlan:
    date: str
    meals: List[Meal]
    target_nutrients: NutrientProfile
    water_ml: int = 3000
    notes: List[str] = field(default_factory=list)


@dataclass
class NutritionReport:
    period: str
    avg_daily_calories: float
    avg_daily_protein: float
    avg_daily_carbs: float
    avg_daily_fat: float
    adherence_pct: float
    top_foods: List[Tuple[str, int]]
    deficiencies: List[str]
    recommendations: List[str]


# ── Food Database (common foods) ─────────────────────────────────────────────

FOOD_DATABASE: Dict[str, FoodItem] = {
    "chicken_breast": FoodItem(
        name="Chicken Breast (grilled)", serving_size="100g",
        nutrients=NutrientProfile(165, 31, 0, 3.6, 0),
        allergens=[], category="protein",
    ),
    "salmon": FoodItem(
        name="Salmon (baked)", serving_size="100g",
        nutrients=NutrientProfile(208, 20, 0, 13, 0, omega_3_g=2.3),
        allergens=["fish"], category="protein",
    ),
    "brown_rice": FoodItem(
        name="Brown Rice (cooked)", serving_size="100g",
        nutrients=NutrientProfile(123, 2.7, 26, 1, 1.8),
        allergens=[], category="carbs",
    ),
    "egg": FoodItem(
        name="Egg (whole, boiled)", serving_size="1 large",
        nutrients=NutrientProfile(78, 6.3, 0.6, 5.3, 0),
        allergens=["eggs"], category="protein",
    ),
    "broccoli": FoodItem(
        name="Broccoli (steamed)", serving_size="100g",
        nutrients=NutrientProfile(35, 2.8, 7.2, 0.4, 3.3),
        allergens=[], category="vegetable",
    ),
    "sweet_potato": FoodItem(
        name="Sweet Potato (baked)", serving_size="100g",
        nutrients=NutrientProfile(90, 2, 21, 0.1, 3.3),
        allergens=[], category="carbs",
    ),
    "oatmeal": FoodItem(
        name="Oatmeal (cooked)", serving_size="100g",
        nutrients=NutrientProfile(68, 2.4, 12, 1.4, 1.7),
        allergens=["gluten"], category="carbs",
    ),
    "banana": FoodItem(
        name="Banana", serving_size="1 medium",
        nutrients=NutrientProfile(105, 1.3, 27, 0.4, 3.1),
        allergens=[], category="fruit",
    ),
    "greek_yogurt": FoodItem(
        name="Greek Yogurt (plain)", serving_size="100g",
        nutrients=NutrientProfile(59, 10, 3.6, 0.7, 0),
        allergens=["dairy"], category="dairy",
    ),
    "almonds": FoodItem(
        name="Almonds (raw)", serving_size="30g",
        nutrients=NutrientProfile(173, 6.3, 6.1, 15, 3.5),
        allergens=["tree nuts"], category="nuts",
    ),
    "whey_protein": FoodItem(
        name="Whey Protein Shake", serving_size="1 scoop (30g)",
        nutrients=NutrientProfile(120, 25, 3, 1, 0),
        allergens=["dairy"], category="supplement",
    ),
    "olive_oil": FoodItem(
        name="Extra Virgin Olive Oil", serving_size="1 tbsp",
        nutrients=NutrientProfile(119, 0, 0, 13.5, 0),
        allergens=[], category="fat",
    ),
}


class NutritionAnalyzer:
    """AI-powered nutrition analysis and meal planning."""

    # Calorie targets by goal
    CALORIE_TARGETS = {
        DietaryGoal.FAT_LOSS: (-500, -300),   # deficit
        DietaryGoal.MUSCLE_GAIN: (300, 500),   # surplus
        DietaryGoal.MAINTENANCE: (-100, 100),
        DietaryGoal.PERFORMANCE: (100, 300),
        DietaryGoal.HEALTH: (-200, 100),
    }

    # Macro ratios by goal (protein, carbs, fat) as % of calories
    MACRO_RATIOS = {
        DietaryGoal.FAT_LOSS: (0.40, 0.30, 0.30),
        DietaryGoal.MUSCLE_GAIN: (0.35, 0.45, 0.20),
        DietaryGoal.MAINTENANCE: (0.30, 0.40, 0.30),
        DietaryGoal.PERFORMANCE: (0.30, 0.50, 0.20),
        DietaryGoal.HEALTH: (0.25, 0.45, 0.30),
        DietaryGoal.KETO: (0.25, 0.05, 0.70),
    }

    def calculate_bmr(self, weight_kg: float, height_cm: float, age: int, sex: str) -> float:
        """Mifflin-St Jeor BMR equation."""
        if sex.lower() == "male":
            return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        else:
            return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    def calculate_tdee(self, bmr: float, activity_level: float) -> float:
        """Calculate Total Daily Energy Expenditure."""
        return bmr * activity_level

    def calculate_targets(
        self, weight_kg: float, height_cm: float, age: int, sex: str,
        goal: DietaryGoal, activity_level: float = 1.55,
    ) -> NutrientProfile:
        """Calculate daily nutrient targets."""
        bmr = self.calculate_bmr(weight_kg, height_cm, age, sex)
        tdee = self.calculate_tdee(bmr, activity_level)

        cal_range = self.CALORIE_TARGETS.get(goal, (-100, 100))
        target_calories = tdee + (cal_range[0] + cal_range[1]) / 2

        protein_ratio, carb_ratio, fat_ratio = self.MACRO_RATIOS.get(goal, (0.3, 0.4, 0.3))

        return NutrientProfile(
            calories=round(target_calories),
            protein_g=round(target_calories * protein_ratio / 4),
            carbs_g=round(target_calories * carb_ratio / 4),
            fat_g=round(target_calories * fat_ratio / 9),
            fiber_g=25 if goal != DietaryGoal.KETO else 15,
        )

    def generate_meal_plan(
        self, targets: NutrientProfile, goal: DietaryGoal,
        allergies: List[str] = None, meals_per_day: int = 4,
    ) -> List[DailyPlan]:
        """Generate a week of meal plans."""
        allergies = allergies or []
        plans = []

        # Distribute calories across meals
        meal_distribution = {
            MealType.BREAKFAST: 0.25,
            MealType.LUNCH: 0.35,
            MealType.DINNER: 0.30,
            MealType.SNACK: 0.10,
        }

        available_foods = [
            food for food in FOOD_DATABASE.values()
            if not any(a in food.allergens for a in allergies)
        ]

        for day in range(7):
            meals = []
            for meal_type in list(MealType)[:meals_per_day]:
                ratio = meal_distribution.get(meal_type, 0.15)
                meal_calories = targets.calories * ratio

                # Select foods for this meal
                selected = self._select_foods_for_meal(
                    available_foods, meal_calories, meal_type, targets
                )
                meals.append(Meal(
                    meal_type=meal_type,
                    foods=selected,
                    time=self._get_meal_time(meal_type),
                ))

            plans.append(DailyPlan(
                date=f"Day {day + 1}",
                meals=meals,
                target_nutrients=targets,
            ))

        return plans

    def analyze_meal(self, foods: List[Tuple[FoodItem, float]]) -> NutrientProfile:
        """Analyze a single meal's nutritional content."""
        total = NutrientProfile(0, 0, 0, 0)
        for food, multiplier in foods:
            total.calories += food.nutrients.calories * multiplier
            total.protein_g += food.nutrients.protein_g * multiplier
            total.carbs_g += food.nutrients.carbs_g * multiplier
            total.fat_g += food.nutrients.fat_g * multiplier
            total.fiber_g += food.nutrients.fiber_g * multiplier
        return total

    def get_substitutes(self, food_name: str, allergies: List[str]) -> List[FoodItem]:
        """Suggest food substitutes avoiding allergens."""
        original = FOOD_DATABASE.get(food_name)
        if not original:
            return []

        return [
            f for f in FOOD_DATABASE.values()
            if f.name != original.name
            and f.category == original.category
            and not any(a in f.allergens for a in allergies)
        ][:3]

    def generate_report(
        self, daily_logs: List[Dict], targets: NutrientProfile
    ) -> NutritionReport:
        """Generate a weekly nutrition report."""
        if not daily_logs:
            return NutritionReport(
                period="No data", avg_daily_calories=0, avg_daily_protein=0,
                avg_daily_carbs=0, avg_daily_fat=0, adherence_pct=0,
                top_foods=[], deficiencies=[], recommendations=["Start logging meals"],
            )

        total_cal = sum(d.get("calories", 0) for d in daily_logs)
        total_protein = sum(d.get("protein", 0) for d in daily_logs)
        total_carbs = sum(d.get("carbs", 0) for d in daily_logs)
        total_fat = sum(d.get("fat", 0) for d in daily_logs)
        days = len(daily_logs)

        # Adherence
        cal_diff = abs((total_cal / days) - targets.calories)
        adherence = max(0, 100 - (cal_diff / targets.calories * 100))

        recommendations = []
        if total_protein / days < targets.protein_g * 0.8:
            recommendations.append("Increase protein intake — aim for lean meats or supplements")
        if total_fat / days < targets.fat_g * 0.7:
            recommendations.append("Healthy fats are low — add nuts, olive oil, or avocado")

        return NutritionReport(
            period=f"Last {days} days",
            avg_daily_calories=round(total_cal / days),
            avg_daily_protein=round(total_protein / days),
            avg_daily_carbs=round(total_carbs / days),
            avg_daily_fat=round(total_fat / days),
            adherence_pct=round(adherence),
            top_foods=[],
            deficiencies=[],
            recommendations=recommendations,
        )

    def _select_foods_for_meal(
        self, foods: List[FoodItem], target_calories: float,
        meal_type: MealType, targets: NutrientProfile,
    ) -> List[Tuple[FoodItem, float]]:
        """Select foods and portions to hit calorie target."""
        selected = []
        remaining_calories = target_calories

        # Prioritize protein for post-workout
        if meal_type == MealType.POST_WORKOUT:
            protein_foods = [f for f in foods if f.nutrients.protein_g > 15]
            if protein_foods:
                food = protein_foods[0]
                multiplier = min(2.0, remaining_calories / food.nutrients.calories)
                selected.append((food, multiplier))
                remaining_calories -= food.nutrients.calories * multiplier

        # Fill remaining with balanced choices
        for food in foods[:4]:
            if remaining_calories <= 0:
                break
            if food in [s[0] for s in selected]:
                continue
            multiplier = min(2.0, remaining_calories / max(food.nutrients.calories, 1))
            if multiplier > 0.3:
                selected.append((food, round(multiplier, 1)))
                remaining_calories -= food.nutrients.calories * multiplier

        return selected

    def _get_meal_time(self, meal_type: MealType) -> str:
        times = {
            MealType.BREAKFAST: "07:00",
            MealType.LUNCH: "12:30",
            MealType.DINNER: "19:00",
            MealType.SNACK: "15:30",
            MealType.PRE_WORKOUT: "17:00",
            MealType.POST_WORKOUT: "18:30",
        }
        return times.get(meal_type, "12:00")

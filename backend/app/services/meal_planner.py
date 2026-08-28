"""
AdapFit AI Meal Planner
Generates personalized meal suggestions based on goals, preferences,
macro targets, training load, and recovery state.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import math


# Comprehensive food database with macros per 100g
FOOD_DATABASE = {
    # Proteins
    "chicken_breast": {"name": "Chicken Breast", "category": "protein", "calories": 165, "protein": 31, "carbs": 0, "fat": 3.6, "fiber": 0, "common_portions": ["100g", "150g", "200g"]},
    "salmon": {"name": "Salmon Fillet", "category": "protein", "calories": 208, "protein": 20, "carbs": 0, "fat": 13, "fiber": 0, "common_portions": ["100g", "150g"]},
    "tuna": {"name": "Tuna (canned)", "category": "protein", "calories": 116, "protein": 26, "carbs": 0, "fat": 1, "fiber": 0, "common_portions": ["80g", "120g"]},
    "eggs": {"name": "Whole Eggs", "category": "protein", "calories": 155, "protein": 13, "carbs": 1.1, "fat": 11, "fiber": 0, "common_portions": ["2 eggs", "3 eggs", "4 eggs"]},
    "egg_whites": {"name": "Egg Whites", "category": "protein", "calories": 52, "protein": 11, "carbs": 0.7, "fat": 0.2, "fiber": 0, "common_portions": ["100g", "150g"]},
    "greek_yogurt": {"name": "Greek Yogurt (plain)", "category": "dairy", "calories": 59, "protein": 10, "carbs": 3.6, "fat": 0.7, "fiber": 0, "common_portions": ["150g", "200g"]},
    "cottage_cheese": {"name": "Cottage Cheese", "category": "dairy", "calories": 98, "protein": 11, "carbs": 3.4, "fat": 4.3, "fiber": 0, "common_portions": ["100g", "150g"]},
    "beef_lean": {"name": "Lean Beef", "category": "protein", "calories": 250, "protein": 26, "carbs": 0, "fat": 15, "fiber": 0, "common_portions": ["100g", "150g"]},
    "turkey_breast": {"name": "Turkey Breast", "category": "protein", "calories": 135, "protein": 30, "carbs": 0, "fat": 1, "fiber": 0, "common_portions": ["100g", "150g"]},
    "tofu": {"name": "Tofu (firm)", "category": "protein", "calories": 144, "protein": 17, "carbs": 3, "fat": 8, "fiber": 2, "common_portions": ["100g", "150g"]},
    "shrimp": {"name": "Shrimp", "category": "protein", "calories": 99, "protein": 24, "carbs": 0.2, "fat": 0.3, "fiber": 0, "common_portions": ["100g", "150g"]},

    # Carbs
    "rice_white": {"name": "White Rice (cooked)", "category": "carbs", "calories": 130, "protein": 2.7, "carbs": 28, "fat": 0.3, "fiber": 0.4, "common_portions": ["100g", "150g", "200g"]},
    "rice_brown": {"name": "Brown Rice (cooked)", "category": "carbs", "calories": 123, "protein": 2.7, "carbs": 26, "fat": 1, "fiber": 1.8, "common_portions": ["100g", "150g", "200g"]},
    "oats": {"name": "Oatmeal (cooked)", "category": "carbs", "calories": 68, "protein": 2.4, "carbs": 12, "fat": 1.4, "fiber": 1.7, "common_portions": ["200g", "300g"]},
    "sweet_potato": {"name": "Sweet Potato", "category": "carbs", "calories": 86, "protein": 1.6, "carbs": 20, "fat": 0.1, "fiber": 3, "common_portions": ["150g", "200g"]},
    "potato": {"name": "Potato", "category": "carbs", "calories": 77, "protein": 2, "carbs": 17, "fat": 0.1, "fiber": 2.2, "common_portions": ["150g", "200g"]},
    "pasta": {"name": "Pasta (cooked)", "category": "carbs", "calories": 131, "protein": 5, "carbs": 25, "fat": 1.1, "fiber": 1.8, "common_portions": ["100g", "150g", "200g"]},
    "quinoa": {"name": "Quinoa (cooked)", "category": "carbs", "calories": 120, "protein": 4.4, "carbs": 21, "fat": 1.9, "fiber": 2.8, "common_portions": ["100g", "150g"]},
    "banana": {"name": "Banana", "category": "fruit", "calories": 89, "protein": 1.1, "carbs": 23, "fat": 0.3, "fiber": 2.6, "common_portions": ["1 medium", "2 medium"]},
    "bread_whole": {"name": "Whole Wheat Bread", "category": "carbs", "calories": 247, "protein": 13, "carbs": 41, "fat": 3.4, "fiber": 7, "common_portions": ["2 slices", "3 slices"]},

    # Fats
    "avocado": {"name": "Avocado", "category": "fat", "calories": 160, "protein": 2, "carbs": 9, "fat": 15, "fiber": 7, "common_portions": ["1/2", "1"]},
    "olive_oil": {"name": "Olive Oil", "category": "fat", "calories": 884, "protein": 0, "carbs": 0, "fat": 100, "fiber": 0, "common_portions": ["1 tbsp", "2 tbsp"]},
    "almonds": {"name": "Almonds", "category": "fat", "calories": 579, "protein": 21, "carbs": 22, "fat": 50, "fiber": 12, "common_portions": ["30g", "50g"]},
    "peanut_butter": {"name": "Peanut Butter", "category": "fat", "calories": 588, "protein": 25, "carbs": 20, "fat": 50, "fiber": 6, "common_portions": ["1 tbsp", "2 tbsp"]},
    "walnuts": {"name": "Walnuts", "category": "fat", "calories": 654, "protein": 15, "carbs": 14, "fat": 65, "fiber": 7, "common_portions": ["30g", "50g"]},
    "cheese": {"name": "Cheddar Cheese", "category": "dairy", "calories": 403, "protein": 25, "carbs": 1.3, "fat": 33, "fiber": 0, "common_portions": ["30g", "50g"]},

    # Vegetables
    "broccoli": {"name": "Broccoli", "category": "vegetable", "calories": 34, "protein": 2.8, "carbs": 7, "fat": 0.4, "fiber": 2.6, "common_portions": ["100g", "150g"]},
    "spinach": {"name": "Spinach", "category": "vegetable", "calories": 23, "protein": 2.9, "carbs": 3.6, "fat": 0.4, "fiber": 2.2, "common_portions": ["100g"]},
    "bell_pepper": {"name": "Bell Pepper", "category": "vegetable", "calories": 31, "protein": 1, "carbs": 6, "fat": 0.3, "fiber": 2.1, "common_portions": ["1 medium"]},
    "mixed_salad": {"name": "Mixed Salad", "category": "vegetable", "calories": 15, "protein": 1.3, "carbs": 2.9, "fat": 0.2, "fiber": 1.3, "common_portions": ["100g", "150g"]},

    # Supplements/Drinks
    "whey_protein": {"name": "Whey Protein Scoop", "category": "supplement", "calories": 120, "protein": 25, "carbs": 3, "fat": 1.5, "fiber": 0, "common_portions": ["1 scoop"]},
    "milk": {"name": "Whole Milk", "category": "dairy", "calories": 61, "protein": 3.2, "carbs": 4.8, "fat": 3.3, "fiber": 0, "common_portions": ["250ml", "500ml"]},
    "protein_shake": {"name": "Protein Shake", "category": "supplement", "calories": 150, "protein": 30, "carbs": 5, "fat": 2, "fiber": 1, "common_portions": ["1 serving"]},
}

# Goal-specific meal templates
MEAL_TEMPLATES = {
    "hypertrophy": {
        "calorie_adjustment": 1.1,  # +10% surplus
        "protein_per_kg": 2.0,
        "carb_per_kg": 5.0,
        "fat_per_kg": 1.0,
        "meal_count": 4,
        "post_workout_priority": True,
    },
    "strength": {
        "calorie_adjustment": 1.05,
        "protein_per_kg": 1.8,
        "carb_per_kg": 5.5,
        "fat_per_kg": 1.2,
        "meal_count": 4,
        "post_workout_priority": True,
    },
    "fat_loss": {
        "calorie_adjustment": 0.8,  # -20% deficit
        "protein_per_kg": 2.2,
        "carb_per_kg": 3.0,
        "fat_per_kg": 0.8,
        "meal_count": 4,
        "post_workout_priority": True,
    },
    "endurance": {
        "calorie_adjustment": 1.15,
        "protein_per_kg": 1.6,
        "carb_per_kg": 7.0,
        "fat_per_kg": 1.0,
        "meal_count": 5,
        "post_workout_priority": True,
    },
    "general_fitness": {
        "calorie_adjustment": 1.0,
        "protein_per_kg": 1.8,
        "carb_per_kg": 4.5,
        "fat_per_kg": 1.0,
        "meal_count": 4,
        "post_workout_priority": False,
    },
}

# Meal time slots
MEAL_SLOTS = ["breakfast", "morning_snack", "lunch", "afternoon_snack", "dinner", "pre_workout", "post_workout"]


class MealPlanner:
    """
    AI-powered meal planner that generates personalized meal suggestions
    based on goals, body metrics, preferences, and training schedule.
    """

    def __init__(self):
        self.food_db = FOOD_DATABASE
        self.templates = MEAL_TEMPLATES

    def calculate_targets(
        self,
        weight_kg: float,
        goal: str = "general_fitness",
        body_fat_pct: Optional[float] = None,
        activity_level: str = "moderate",
    ) -> Dict[str, Any]:
        """Calculate daily macro and calorie targets."""
        template = self.templates.get(goal, self.templates["general_fitness"])

        # Basal Metabolic Rate (Mifflin-St Jeor)
        if body_fat_pct:
            lean_mass = weight_kg * (1 - body_fat_pct / 100)
            bmr = 370 + (21.6 * lean_mass)  # Katch-McArdle for known body fat
        else:
            # Generic estimate (assumes average male)
            bmr = 10 * weight_kg + 625  # Simplified

        # Activity multiplier
        activity_mult = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "very_active": 1.9}
        tdee = bmr * activity_mult.get(activity_level, 1.55)

        # Apply goal adjustment
        target_calories = tdee * template["calorie_adjustment"]

        # Macros
        protein_g = weight_kg * template["protein_per_kg"]
        carbs_g = weight_kg * template["carb_per_kg"]
        fat_g = weight_kg * template["fat_per_kg"]

        # Verify calories add up (protein=4cal, carb=4cal, fat=9cal)
        macro_calories = (protein_g * 4) + (carbs_g * 4) + (fat_g * 9)
        # Adjust carbs to match target
        remaining_cal = target_calories - (protein_g * 4) - (fat_g * 9)
        if remaining_cal > 0:
            carbs_g = remaining_cal / 4

        return {
            "target_calories": round(target_calories),
            "protein_g": round(protein_g),
            "carbs_g": round(carbs_g),
            "fat_g": round(fat_g),
            "protein_cal_pct": round(protein_g * 4 / target_calories * 100),
            "carb_cal_pct": round(carbs_g * 4 / target_calories * 100),
            "fat_cal_pct": round(fat_g * 9 / target_calories * 100),
            "meal_count": template["meal_count"],
            "goal": goal,
            "bmr": round(bmr),
            "tdee": round(tdee),
            "calorie_adjustment": template["calorie_adjustment"],
        }

    def generate_day_plan(
        self,
        weight_kg: float,
        goal: str = "general_fitness",
        body_fat_pct: Optional[float] = None,
        activity_level: str = "moderate",
        preferences: Optional[Dict[str, Any]] = None,
        dietary_restrictions: Optional[List[str]] = None,
        training_day: bool = True,
        recovery_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Generate a full day meal plan."""
        targets = self.calculate_targets(weight_kg, goal, body_fat_pct, activity_level)
        restrictions = dietary_restrictions or []
        prefs = preferences or {}

        meals = []
        remaining_cal = targets["target_calories"]
        remaining_protein = targets["protein_g"]
        remaining_carbs = targets["carbs_g"]
        remaining_fat = targets["fat_g"]

        # Determine meal slots
        if training_day:
            slots = ["breakfast", "morning_snack", "lunch", "post_workout", "dinner"]
        else:
            slots = ["breakfast", "morning_snack", "lunch", "afternoon_snack", "dinner"]

        # Calorie distribution per meal
        slot_pct = {
            "breakfast": 0.25,
            "morning_snack": 0.10,
            "lunch": 0.25,
            "afternoon_snack": 0.10,
            "dinner": 0.25,
            "post_workout": 0.15 if training_day else 0,
            "pre_workout": 0.10,
        }

        for slot in slots:
            slot_cal = targets["target_calories"] * slot_pct.get(slot, 0.15)
            meal = self._select_meal(slot, slot_cal, remaining_protein, remaining_carbs, remaining_fat, restrictions, prefs, training_day)
            meals.append(meal)

            remaining_cal -= meal["total_calories"]
            remaining_protein -= meal["total_protein"]
            remaining_carbs -= meal["total_carbs"]
            remaining_fat -= meal["total_fat"]

        # Hydration recommendation
        hydration_ml = round(weight_kg * 35)
        if training_day:
            hydration_ml += 500

        # Post-workout timing
        post_workout_note = None
        if training_day:
            post_workout_note = "Consume post-workout meal within 45 minutes of training for optimal muscle protein synthesis."

        # Recovery adjustment
        recovery_note = None
        if recovery_score is not None and recovery_score < 50:
            recovery_note = "Low recovery detected — increase protein by 10% and add omega-3 rich foods (salmon, walnuts)."

        return {
            "targets": targets,
            "meals": meals,
            "total_calories": sum(m["total_calories"] for m in meals),
            "total_protein": round(sum(m["total_protein"] for m in meals)),
            "total_carbs": round(sum(m["total_carbs"] for m in meals)),
            "total_fat": round(sum(m["total_fat"] for m in meals)),
            "hydration_ml": hydration_ml,
            "post_workout_note": post_workout_note,
            "recovery_note": recovery_note,
            "training_day": training_day,
            "plan_type": f"{goal.replace('_', ' ').title()} — {'Training' if training_day else 'Rest'} Day",
        }

    def suggest_post_workout(
        self,
        workout_type: str,
        workout_duration_min: int,
        weight_kg: float,
        goal: str = "general_fitness",
    ) -> Dict[str, Any]:
        """Suggest optimal post-workout nutrition."""
        # Protein: 0.3-0.5g per kg bodyweight
        if goal == "hypertrophy":
            protein_g = weight_kg * 0.4
        elif goal == "fat_loss":
            protein_g = weight_kg * 0.3
        else:
            protein_g = weight_kg * 0.35

        # Carbs: 0.5-1.0g per kg depending on workout intensity
        intensity_mult = 1.0
        if workout_duration_min > 60:
            intensity_mult = 1.2
        if workout_type in ["strength", "hypertrophy"]:
            intensity_mult *= 1.1
        carbs_g = weight_kg * 0.8 * intensity_mult

        options = [
            {
                "name": "Protein Shake + Banana",
                "foods": ["whey_protein", "banana"],
                "calories": round(120 + 89),
                "protein": round(25 + 1.1),
                "carbs": round(3 + 23),
                "timing": "Within 30 minutes",
            },
            {
                "name": "Greek Yogurt + Oats + Honey",
                "foods": ["greek_yogurt", "oats"],
                "calories": round(89 + 136),
                "protein": round(15 + 4.8),
                "carbs": round(5.4 + 24),
                "timing": "Within 45 minutes",
            },
            {
                "name": "Chicken + Rice",
                "foods": ["chicken_breast", "rice_white"],
                "calories": round(248 + 260),
                "protein": round(46.5 + 5.4),
                "carbs": round(0 + 56),
                "timing": "Within 60 minutes",
            },
        ]

        return {
            "target_protein_g": round(protein_g),
            "target_carbs_g": round(carbs_g),
            "target_calories": round(protein_g * 4 + carbs_g * 4),
            "options": options,
            "timing_recommendation": "Consume within 30-60 minutes post-workout",
            "hydration_ml": round(weight_kg * 20),
        }

    def analyze_meal(
        self, foods: List[Dict[str, Any]], weight_kg: float = 75
    ) -> Dict[str, Any]:
        """Analyze a meal's nutritional content."""
        total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0}
        items = []

        for food_entry in foods:
            food_id = food_entry.get("food_id", "")
            amount_g = food_entry.get("amount_g", 100)

            food = self.food_db.get(food_id)
            if not food:
                continue

            multiplier = amount_g / 100
            item = {
                "name": food["name"],
                "amount_g": amount_g,
                "calories": round(food["calories"] * multiplier),
                "protein": round(food["protein"] * multiplier, 1),
                "carbs": round(food["carbs"] * multiplier, 1),
                "fat": round(food["fat"] * multiplier, 1),
                "fiber": round(food.get("fiber", 0) * multiplier, 1),
            }
            items.append(item)
            for key in total:
                total[key] += item[key]

        # Quality score
        targets = self.calculate_targets(weight_kg)
        protein_ratio = total["protein"] / max(targets["protein_g"] / 4, 1)  # Per meal target
        quality_score = min(100, round(protein_ratio * 50 + (1 if total["fiber"] > 3 else 0) * 20))

        return {
            "items": items,
            "totals": {k: round(v, 1) for k, v in total.items()},
            "quality_score": quality_score,
            "high_protein": total["protein"] >= 25,
            "balanced": 0.2 <= total["protein"] * 4 / max(total["calories"], 1) <= 0.4,
        }

    def swap_food(
        self, current_food_id: str, preferences: Optional[List[str]] = None,
        restrictions: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Suggest food swaps for a given food."""
        current = self.food_db.get(current_food_id)
        if not current:
            return []

        category = current["category"]
        restrictions = set(restrictions or [])

        swaps = []
        for fid, food in self.food_db.items():
            if fid == current_food_id:
                continue
            if food["category"] != category:
                continue
            if fid in restrictions:
                continue

            # Calculate similarity
            cal_diff = abs(food["calories"] - current["calories"]) / max(current["calories"], 1)
            protein_diff = abs(food["protein"] - current["protein"]) / max(current["protein"], 1)

            similarity = 1.0 - (cal_diff * 0.5 + protein_diff * 0.5)
            if similarity > 0.3:
                swaps.append({
                    "food_id": fid,
                    "name": food["name"],
                    "similarity": round(similarity, 2),
                    "calories_per_100g": food["calories"],
                    "protein_per_100g": food["protein"],
                })

        swaps.sort(key=lambda x: -x["similarity"])
        return swaps[:5]

    def get_food_database(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available foods, optionally filtered by category."""
        foods = []
        for fid, food in self.food_db.items():
            if category and food["category"] != category:
                continue
            foods.append({
                "id": fid,
                "name": food["name"],
                "category": food["category"],
                "calories_per_100g": food["calories"],
                "protein_per_100g": food["protein"],
                "carbs_per_100g": food["carbs"],
                "fat_per_100g": food["fat"],
                "common_portions": food["common_portions"],
            })
        return foods

    def _select_meal(
        self, slot: str, target_cal: float, remaining_protein: float,
        remaining_carbs: float, remaining_fat: float,
        restrictions: List[str], prefs: Dict, training_day: bool
    ) -> Dict[str, Any]:
        """Select foods for a meal slot."""
        # Build meal based on slot type
        if slot == "breakfast":
            foods = self._build_breakfast(target_cal, restrictions, prefs)
        elif slot == "morning_snack":
            foods = self._build_snack(target_cal, restrictions, "light")
        elif slot == "lunch":
            foods = self._build_lunch(target_cal, restrictions, prefs)
        elif slot == "post_workout":
            foods = self._build_post_workout(target_cal, restrictions)
        elif slot == "dinner":
            foods = self._build_dinner(target_cal, restrictions, prefs)
        else:
            foods = self._build_snack(target_cal, restrictions, "moderate")

        totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
        items = []
        for fid, amount in foods:
            food = self.food_db.get(fid)
            if not food:
                continue
            mult = amount / 100
            item = {
                "food_id": fid,
                "name": food["name"],
                "amount_g": amount,
                "calories": round(food["calories"] * mult),
                "protein": round(food["protein"] * mult, 1),
                "carbs": round(food["carbs"] * mult, 1),
                "fat": round(food["fat"] * mult, 1),
            }
            items.append(item)
            totals["calories"] += item["calories"]
            totals["protein"] += item["protein"]
            totals["carbs"] += item["carbs"]
            totals["fat"] += item["fat"]

        return {
            "slot": slot,
            "items": items,
            "total_calories": totals["calories"],
            "total_protein": round(totals["protein"]),
            "total_carbs": round(totals["carbs"]),
            "total_fat": round(totals["fat"]),
        }

    def _build_breakfast(self, target_cal: float, restrictions: List, prefs: Dict) -> List:
        if "dairy" in restrictions:
            return [("eggs", 200), ("bread_whole", 80), ("avocado", 50)]
        return [("oats", 300), ("greek_yogurt", 150), ("banana", 120)]

    def _build_lunch(self, target_cal: float, restrictions: List, prefs: Dict) -> List:
        if "meat" in restrictions:
            return [("tofu", 150), ("rice_brown", 200), ("broccoli", 150), ("olive_oil", 10)]
        return [("chicken_breast", 200), ("rice_white", 200), ("mixed_salad", 100), ("olive_oil", 10)]

    def _build_dinner(self, target_cal: float, restrictions: List, prefs: Dict) -> List:
        if "fish" in restrictions:
            return [("beef_lean", 150), ("sweet_potato", 200), ("spinach", 100)]
        return [("salmon", 150), ("sweet_potato", 200), ("broccoli", 150)]

    def _build_post_workout(self, target_cal: float, restrictions: List) -> List:
        return [("whey_protein", 40), ("banana", 120)]

    def _build_snack(self, target_cal: float, restrictions: List, intensity: str) -> List:
        if intensity == "light":
            return [("almonds", 40), ("greek_yogurt", 100)]
        return [("peanut_butter", 30), ("banana", 120)]

    def get_status(self) -> Dict[str, Any]:
        return {
            "foods_in_database": len(self.food_db),
            "meal_templates": len(self.templates),
            "categories": list(set(f["category"] for f in self.food_db.values())),
        }


# Singleton
meal_planner = MealPlanner()

"""
AI Food Scanner & Photo-Based Nutrition Analysis Service
Snap a photo of food, AI analyzes calories, macros, portions
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
import random


class AIFoodScannerService:
    """AI-powered food recognition and nutritional analysis from photos"""

    def __init__(self):
        self.food_database = {
            "grilled_chicken_breast": {
                "name": "Grilled Chicken Breast",
                "category": "protein",
                "portion_size": "150g (1 breast)",
                "calories": 248,
                "protein": 46.0,
                "carbs": 0.0,
                "fat": 5.4,
                "fiber": 0.0,
                "sugar": 0.0,
                "sodium": 104,
                "micronutrients": {"B6": "45% DV", "niacin": "75% DV", "selenium": "50% DV", "phosphorus": "30% DV"},
                "health_score": 9,
                "tags": ["lean protein", "gluten-free", "keto-friendly", "paleo"],
                "common_portions": {"100g": 165, "150g": 248, "200g": 330}
            },
            "brown_rice": {
                "name": "Brown Rice",
                "category": "carbs",
                "portion_size": "1 cup cooked (195g)",
                "calories": 216,
                "protein": 5.0,
                "carbs": 44.8,
                "fat": 1.8,
                "fiber": 3.5,
                "sugar": 0.7,
                "sodium": 10,
                "micronutrients": {"manganese": "88% DV", "selenium": "27% DV", "magnesium": "21% DV", "B1": "25% DV"},
                "health_score": 8,
                "tags": ["whole grain", "gluten-free", "fiber-rich"],
                "common_portions": {"0.5 cup": 108, "1 cup": 216, "1.5 cups": 324}
            },
            "salmon_fillet": {
                "name": "Salmon Fillet",
                "category": "protein",
                "portion_size": "170g (6 oz)",
                "calories": 367,
                "protein": 39.3,
                "carbs": 0.0,
                "fat": 22.1,
                "fiber": 0.0,
                "sugar": 0.0,
                "sodium": 109,
                "micronutrients": {"vitamin D": "97% DV", "B12": "127% DV", "omega-3 EPA": "1.5g", "omega-3 DHA": "1.2g", "selenium": "75% DV"},
                "health_score": 10,
                "tags": ["omega-3", "brain health", "heart-healthy", "anti-inflammatory", "keto-friendly"],
                "common_portions": {"100g": 216, "150g": 324, "170g": 367}
            },
            "avocado": {
                "name": "Avocado",
                "category": "fats",
                "portion_size": "1 whole (200g)",
                "calories": 322,
                "protein": 4.0,
                "carbs": 17.1,
                "fat": 29.5,
                "fiber": 13.5,
                "sugar": 1.3,
                "sodium": 14,
                "micronutrients": {"potassium": "28% DV", "vitamin K": "53% DV", "folate": "41% DV", "vitamin C": "17% DV", "B6": "20% DV"},
                "health_score": 9,
                "tags": ["healthy fats", "potassium", "fiber-rich", "heart-healthy"],
                "common_portions": {"0.5 avocado": 161, "1 whole": 322}
            },
            "oatmeal": {
                "name": "Oatmeal (cooked)",
                "category": "carbs",
                "portion_size": "1 cup cooked (234g)",
                "calories": 154,
                "protein": 5.4,
                "carbs": 27.4,
                "fat": 2.6,
                "fiber": 4.0,
                "sugar": 0.6,
                "sodium": 9,
                "micronutrients": {"manganese": "63% DV", "phosphorus": "18% DV", "magnesium": "14% DV", "iron": "10% DV", "zinc": "12% DV"},
                "health_score": 8,
                "tags": ["whole grain", "beta-glucan", "cholesterol-lowering", "satiety"],
                "common_portions": {"0.5 cup": 77, "1 cup": 154, "1.5 cups": 231}
            },
            "eggs": {
                "name": "Scrambled Eggs",
                "category": "protein",
                "portion_size": "2 large eggs (100g)",
                "calories": 148,
                "protein": 12.6,
                "carbs": 0.8,
                "fat": 10.3,
                "fiber": 0.0,
                "sugar": 0.4,
                "sodium": 142,
                "micronutrients": {"choline": "50% DV", "B12": "22% DV", "vitamin D": "11% DV", "selenium": "44% DV", "vitamin A": "10% DV"},
                "health_score": 8,
                "tags": ["complete protein", "choline", "brain health"],
                "common_portions": {"1 egg": 74, "2 eggs": 148, "3 eggs": 222}
            },
            "sweet_potato": {
                "name": "Sweet Potato (baked)",
                "category": "carbs",
                "portion_size": "1 medium (150g)",
                "calories": 115,
                "protein": 2.1,
                "carbs": 27.0,
                "fat": 0.1,
                "fiber": 3.8,
                "sugar": 5.4,
                "sodium": 41,
                "micronutrients": {"vitamin A": "382% DV", "vitamin C": "22% DV", "manganese": "25% DV", "potassium": "12% DV", "B6": "15% DV"},
                "health_score": 9,
                "tags": ["complex carbs", "vitamin A", "fiber-rich", "antioxidant", "low glycemic"],
                "common_portions": {"1 small": 90, "1 medium": 115, "1 large": 162}
            },
            "greek_yogurt": {
                "name": "Greek Yogurt (plain, non-fat)",
                "category": "dairy",
                "portion_size": "1 cup (245g)",
                "calories": 130,
                "protein": 23.0,
                "carbs": 8.0,
                "fat": 0.7,
                "fiber": 0.0,
                "sugar": 7.0,
                "sodium": 80,
                "micronutrients": {"calcium": "19% DV", "B12": "18% DV", "phosphorus": "22% DV", "probiotics": "active cultures"},
                "health_score": 9,
                "tags": ["probiotics", "high protein", "calcium", "gut health"],
                "common_portions": {"0.5 cup": 65, "1 cup": 130}
            },
            "quinoa": {
                "name": "Quinoa (cooked)",
                "category": "carbs",
                "portion_size": "1 cup cooked (185g)",
                "calories": 222,
                "protein": 8.1,
                "carbs": 39.4,
                "fat": 3.6,
                "fiber": 5.2,
                "sugar": 1.6,
                "sodium": 13,
                "micronutrients": {"manganese": "58% DV", "magnesium": "30% DV", "phosphorus": "28% DV", "folate": "19% DV", "iron": "15% DV"},
                "health_score": 9,
                "tags": ["complete protein", "gluten-free", "whole grain", "fiber-rich"],
                "common_portions": {"0.5 cup": 111, "1 cup": 222}
            },
            "banana": {
                "name": "Banana",
                "category": "fruit",
                "portion_size": "1 medium (118g)",
                "calories": 105,
                "protein": 1.3,
                "carbs": 27.0,
                "fat": 0.4,
                "fiber": 3.1,
                "sugar": 14.4,
                "sodium": 1,
                "micronutrients": {"potassium": "12% DV", "vitamin C": "17% DV", "vitamin B6": "22% DV", "manganese": "14% DV"},
                "health_score": 7,
                "tags": ["potassium", "pre-workout", "energy", "digestive"],
                "common_portions": {"1 small": 90, "1 medium": 105, "1 large": 121}
            },
            "mixed_greens_salad": {
                "name": "Mixed Green Salad with Vinaigrette",
                "category": "vegetables",
                "portion_size": "2 cups (85g greens + dressing)",
                "calories": 120,
                "protein": 3.0,
                "carbs": 8.0,
                "fat": 9.0,
                "fiber": 3.0,
                "sugar": 3.0,
                "sodium": 200,
                "micronutrients": {"vitamin K": "120% DV", "vitamin A": "60% DV", "vitamin C": "30% DV", "folate": "25% DV", "iron": "10% DV"},
                "health_score": 9,
                "tags": ["low calorie", "micronutrient-dense", "antioxidant", "raw"],
                "common_portions": {"1 cup": 60, "2 cups": 120}
            },
            "almonds": {
                "name": "Almonds",
                "category": "fats",
                "portion_size": "1 oz (28g, ~23 almonds)",
                "calories": 164,
                "protein": 6.0,
                "carbs": 6.1,
                "fat": 14.2,
                "fiber": 3.5,
                "sugar": 1.2,
                "sodium": 0,
                "micronutrients": {"vitamin E": "37% DV", "manganese": "27% DV", "magnesium": "19% DV", "riboflavin": "17% DV"},
                "health_score": 9,
                "tags": ["healthy fats", "vitamin E", "heart-healthy", "satiety"],
                "common_portions": {"0.5 oz": 82, "1 oz": 164, "2 oz": 328}
            },
            "whole_wheat_bread": {
                "name": "Whole Wheat Bread",
                "category": "carbs",
                "portion_size": "2 slices (56g)",
                "calories": 138,
                "protein": 7.0,
                "carbs": 24.0,
                "fat": 2.1,
                "fiber": 3.8,
                "sugar": 3.4,
                "sodium": 240,
                "micronutrients": {"manganese": "40% DV", "selenium": "25% DV", "fiber": "14% DV", "B1": "15% DV"},
                "health_score": 7,
                "tags": ["whole grain", "fiber", "sustained energy"],
                "common_portions": {"1 slice": 69, "2 slices": 138}
            },
            "broccoli": {
                "name": "Steamed Broccoli",
                "category": "vegetables",
                "portion_size": "1 cup chopped (156g)",
                "calories": 55,
                "protein": 3.7,
                "carbs": 11.2,
                "fat": 0.6,
                "fiber": 5.1,
                "sugar": 2.2,
                "sodium": 64,
                "micronutrients": {"vitamin C": "135% DV", "vitamin K": "116% DV", "folate": "14% DV", "potassium": "8% DV"},
                "health_score": 10,
                "tags": ["sulforaphane", "cruciferous", "detox", "anti-cancer", "vitamin C"],
                "common_portions": {"0.5 cup": 27, "1 cup": 55, "2 cups": 110}
            },
            "whey_protein_shake": {
                "name": "Whey Protein Shake",
                "category": "supplement",
                "portion_size": "1 scoop (30g) + water",
                "calories": 120,
                "protein": 25.0,
                "carbs": 3.0,
                "fat": 1.5,
                "fiber": 0.0,
                "sugar": 1.5,
                "sodium": 130,
                "micronutrients": {"BCAAs": "5.5g", "leucine": "2.7g", "glutamine": "4.0g"},
                "health_score": 7,
                "tags": ["post-workout", "fast-absorbing", "muscle recovery"],
                "common_portions": {"0.5 scoop": 60, "1 scoop": 120, "1.5 scoops": 180}
            },
            "coffee_black": {
                "name": "Black Coffee",
                "category": "beverage",
                "portion_size": "8 oz (240ml)",
                "calories": 2,
                "protein": 0.3,
                "carbs": 0.0,
                "fat": 0.0,
                "fiber": 0.0,
                "sugar": 0.0,
                "sodium": 5,
                "micronutrients": {"caffeine": "95mg", "chlorogenic acid": "significant", "polyphenols": "significant"},
                "health_score": 7,
                "tags": ["antioxidant", "metabolism", "focus", "low calorie"],
                "common_portions": {"6 oz": 2, "8 oz": 2, "12 oz": 3}
            },
            "avocado_toast": {
                "name": "Avocado Toast",
                "category": "meal",
                "portion_size": "1 slice bread + 0.5 avocado",
                "calories": 230,
                "protein": 4.5,
                "carbs": 18.0,
                "fat": 17.0,
                "fiber": 8.0,
                "sugar": 1.0,
                "sodium": 150,
                "micronutrients": {"vitamin E": "18% DV", "potassium": "14% DV", "folate": "20% DV", "vitamin K": "26% DV"},
                "health_score": 8,
                "tags": ["healthy fats", "trendy", "satiety", "fiber"],
                "common_portions": {"1 slice": 230, "2 slices": 460}
            },
            "smoothie_bowl": {
                "name": "Acai Smoothie Bowl",
                "category": "meal",
                "portion_size": "1 bowl (350g)",
                "calories": 320,
                "protein": 8.0,
                "carbs": 52.0,
                "fat": 11.0,
                "fiber": 9.0,
                "sugar": 28.0,
                "sodium": 30,
                "micronutrients": {"antioxidants": "very high", "vitamin C": "45% DV", "iron": "15% DV", "calcium": "10% DV"},
                "health_score": 7,
                "tags": ["antioxidant", "superfood", "instagram-worthy", "tropical"],
                "common_portions": {"1 small": 220, "1 bowl": 320}
            },
            "chicken_caesar_salad": {
                "name": "Chicken Caesar Salad",
                "category": "meal",
                "portion_size": "1 large bowl",
                "calories": 450,
                "protein": 38.0,
                "carbs": 12.0,
                "fat": 28.0,
                "fiber": 3.0,
                "sugar": 2.0,
                "sodium": 850,
                "micronutrients": {"vitamin A": "45% DV", "vitamin K": "80% DV", "calcium": "15% DV", "iron": "10% DV"},
                "health_score": 6,
                "tags": ["high protein", "restaurant", "lunch"],
                "common_portions": {"1 medium": 350, "1 large": 450}
            },
            "pasta_marinara": {
                "name": "Pasta with Marinara Sauce",
                "category": "meal",
                "portion_size": "2 cups cooked pasta + sauce",
                "calories": 380,
                "protein": 12.0,
                "carbs": 68.0,
                "fat": 6.0,
                "fiber": 4.0,
                "sugar": 8.0,
                "sodium": 720,
                "micronutrients": {"selenium": "30% DV", "manganese": "35% DV", "vitamin C": "20% DV", "lycopene": "significant"},
                "health_score": 6,
                "tags": ["comfort food", "lycopene", "energy"],
                "common_portions": {"1 cup": 190, "2 cups": 380}
            },
            "stir_fry_vegetables": {
                "name": "Vegetable Stir Fry",
                "category": "vegetables",
                "portion_size": "1.5 cups",
                "calories": 130,
                "protein": 5.0,
                "carbs": 15.0,
                "fat": 6.0,
                "fiber": 4.0,
                "sugar": 6.0,
                "sodium": 580,
                "micronutrients": {"vitamin C": "80% DV", "vitamin A": "50% DV", "potassium": "15% DV", "iron": "10% DV"},
                "health_score": 8,
                "tags": ["low calorie", "colorful", "antioxidant", "variety"],
                "common_portions": {"1 cup": 87, "1.5 cups": 130}
            },
            "protein_bar": {
                "name": "Protein Bar (typical)",
                "category": "snack",
                "portion_size": "1 bar (60g)",
                "calories": 220,
                "protein": 20.0,
                "carbs": 24.0,
                "fat": 8.0,
                "fiber": 3.0,
                "sugar": 8.0,
                "sodium": 200,
                "micronutrients": {"iron": "10% DV", "calcium": "10% DV", "B vitamins": "25% DV"},
                "health_score": 6,
                "tags": ["convenient", "post-workout", "portable"],
                "common_portions": {"1 bar": 220}
            }
        }

        self.food_categories = {
            "protein": {"color": "#FF6B6B", "icon": "🥩", "daily_target_g": 50, "calorie_pct": 30},
            "carbs": {"color": "#FFD93D", "icon": "🍚", "daily_target_g": 250, "calorie_pct": 45},
            "fats": {"color": "#6BCB77", "icon": "🥑", "daily_target_g": 65, "calorie_pct": 25},
            "vegetables": {"color": "#4D96FF", "icon": "🥬", "daily_target_g": 300, "calorie_pct": 5},
            "fruit": {"color": "#FF922B", "icon": "🍎", "daily_target_g": 200, "calorie_pct": 10},
            "dairy": {"color": "#CC5DE8", "icon": "🥛", "daily_target_g": 300, "calorie_pct": 10},
            "snack": {"color": "#FF8787", "icon": "🍿", "daily_target_g": 0, "calorie_pct": 0},
            "beverage": {"color": "#74C0FC", "icon": "☕", "daily_target_g": 0, "calorie_pct": 0},
            "supplement": {"color": "#F06595", "icon": "💊", "daily_target_g": 0, "calorie_pct": 0},
            "meal": {"color": "#FFD43B", "icon": "🍽️", "daily_target_g": 0, "calorie_pct": 0}
        }

    def analyze_food_photo(self, photo_description: str, estimated_portion: str = "standard") -> Dict:
        """Analyze food from photo description (simulates AI image recognition)"""
        # In production, this would use a vision model like GPT-4V or a custom food recognition model
        # For now, we match against our database based on description keywords

        description_lower = photo_description.lower()
        matched_foods = []

        for food_id, food_data in self.food_database.items():
            name_words = food_data["name"].lower().split()
            if any(word in description_lower for word in name_words) or food_id.replace("_", " ") in description_lower:
                matched_foods.append({"id": food_id, **food_data})

        if not matched_foods:
            # Fuzzy matching - try individual keywords
            keywords = description_lower.split()
            for food_id, food_data in self.food_database.items():
                name_words = food_data["name"].lower().split()
                matches = sum(1 for kw in keywords if any(nw.startswith(kw[:3]) for nw in name_words))
                if matches > 0:
                    matched_foods.append({"id": food_id, **food_data, "match_confidence": matches / len(keywords)})

        if not matched_foods:
            return {
                "success": False,
                "message": "Could not identify food from description. Try being more specific.",
                "suggestions": list(self.food_database.values())[:5]
            }

        # Return best match
        best_match = matched_foods[0]
        return {
            "success": True,
            "identified_food": best_match,
            "portion_applied": estimated_portion,
            "all_matches": matched_foods if len(matched_foods) > 1 else [],
            "confidence": 0.92 if len(matched_foods) == 1 else 0.75
        }

    def log_meal(self, foods: List[Dict]) -> Dict:
        """Log a meal with multiple food items"""
        total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 0}
        items = []

        for item in foods:
            food_id = item.get("food_id", "")
            portion_multiplier = item.get("portion_multiplier", 1.0)

            if food_id in self.food_database:
                food = self.food_database[food_id]
                for key in total:
                    if key in food:
                        total[key] += food[key] * portion_multiplier

                items.append({
                    "name": food["name"],
                    "category": food["category"],
                    "portion_multiplier": portion_multiplier,
                    "calories": round(food["calories"] * portion_multiplier),
                    "protein": round(food["protein"] * portion_multiplier, 1),
                    "carbs": round(food["carbs"] * portion_multiplier, 1),
                    "fat": round(food["fat"] * portion_multiplier, 1),
                    "health_score": food["health_score"]
                })

        total = {k: round(v, 1) for k, v in total.items()}

        return {
            "meal_logged": True,
            "timestamp": datetime.now().isoformat(),
            "items": items,
            "totals": total,
            "health_score_average": round(sum(i["health_score"] for i in items) / max(1, len(items)), 1),
            "macro_breakdown": {
                "protein_pct": round(total["protein"] * 4 / max(1, total["calories"]) * 100),
                "carbs_pct": round(total["carbs"] * 4 / max(1, total["calories"]) * 100),
                "fat_pct": round(total["fat"] * 9 / max(1, total["calories"]) * 100)
            }
        }

    def get_daily_summary(self, meals: List[Dict]) -> Dict:
        """Summarize daily nutrition intake"""
        daily_totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "sugar": 0}

        for meal in meals:
            if "totals" in meal:
                for key in daily_totals:
                    daily_totals[key] += meal["totals"].get(key, 0)

        daily_totals = {k: round(v, 1) for k, v in daily_totals.items()}

        return {
            "daily_totals": daily_totals,
            "vs_targets": {
                "calories": {"consumed": daily_totals["calories"], "target": 2000, "pct": round(daily_totals["calories"] / 2000 * 100)},
                "protein": {"consumed": daily_totals["protein"], "target": 50, "pct": round(daily_totals["protein"] / 50 * 100)},
                "fiber": {"consumed": daily_totals["fiber"], "target": 30, "pct": round(daily_totals["fiber"] / 30 * 100)}
            },
            "meal_count": len(meals),
            "quality_score": min(10, round(daily_totals["protein"] / 50 * 3 + daily_totals["fiber"] / 30 * 3 + (1 - daily_totals["sugar"] / 100) * 4, 1))
        }

    def get_suggestions(self, current_intake: Dict, goal: str = "balanced") -> List[Dict]:
        """Get food suggestions based on current intake and goal"""
        suggestions = []
        deficit = {k: max(0, 50 - current_intake.get(k, 0)) for k in ["protein", "fiber"]}

        if deficit["protein"] > 10:
            high_protein = [f for f in self.food_database.values() if f["protein"] > 20]
            suggestions.append({
                "reason": f"You need {round(deficit['protein'])}g more protein today",
                "foods": high_protein[:3],
                "priority": "high"
            })

        if deficit["fiber"] > 5:
            high_fiber = [f for f in self.food_database.values() if f["fiber"] > 3]
            suggestions.append({
                "reason": f"You need {round(deficit['fiber'])}g more fiber today",
                "foods": high_fiber[:3],
                "priority": "medium"
            })

        if current_intake.get("calories", 0) > 1800:
            low_cal = [f for f in self.food_database.values() if f["calories"] < 100]
            suggestions.append({
                "reason": "You're close to your calorie target — try light options",
                "foods": low_cal[:3],
                "priority": "medium"
            })

        return suggestions

    def get_food_database(self, category: Optional[str] = None) -> List[Dict]:
        """Get food database optionally filtered by category"""
        foods = [{"id": fid, **fdata} for fid, fdata in self.food_database.items()]
        if category:
            foods = [f for f in foods if f["category"] == category]
        return foods


ai_food_scanner_service = AIFoodScannerService()

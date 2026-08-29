"""
Precision Nutrition — Microbiome-based diet, metabolome analysis, personalized supplements
AI-driven personalized dietary recommendations based on microbiome, metabolome, genetics, and lifestyle.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid


class PrecisionNutritionService:
    MICROBIOME_PROFILES = {
        "bacteroides_high": {"name": "Bacteroides-Dominant", "diet_type": "higher_fat", "fiber_sensitivity": "low", "carb_tolerance": "moderate", "fats_beneficial": ["olive_oil", "avocado", "nuts"], "foods_to_avoid": ["high_resistant_starch", "beans_large_portions"]},
        "firmicutes_high": {"name": "Firmicutes-Dominant", "diet_type": "higher_fiber", "fiber_sensitivity": "high", "carb_tolerance": "low", "fats_beneficial": ["omega_3_rich"], "foods_to_avoid": ["refined_sugar", "processed_carbs"]},
        "prevotella_high": {"name": "Prevotella-Dominant", "diet_type": "plant_based", "fiber_sensitivity": "high", "carb_tolerance": "high", "fats_beneficial": ["avocado", "nuts"], "foods_to_avoid": ["high_fat_animal_products"]},
        "balanced": {"name": "Balanced Microbiome", "diet_type": "mixed", "fiber_sensitivity": "moderate", "carb_tolerance": "moderate", "fats_beneficial": ["olive_oil", "omega_3"], "foods_to_avoid": ["highly_processed"]},
    }

    METABOLIC_TYPES = {
        "slow_oxidizer": {"name": "Slow Oxidizer", "carb_ratio": 0.30, "protein_ratio": 0.30, "fat_ratio": 0.40, "meal_frequency": 3, "fasting_beneficial": False},
        "moderate_oxidizer": {"name": "Moderate Oxidizer", "carb_ratio": 0.40, "protein_ratio": 0.30, "fat_ratio": 0.30, "meal_frequency": 4, "fasting_beneficial": True},
        "fast_oxidizer": {"name": "Fast Oxidizer", "carb_ratio": 0.50, "protein_ratio": 0.20, "fat_ratio": 0.30, "meal_frequency": 5, "fasting_beneficial": False},
    }

    SUPPLEMENT_PROTOCOLS = {
        "gut_health": ["probiotics", "prebiotic_fiber", "l_glutamine", "zinc_carnosine", "slippery_elm"],
        "metabolic_support": ["berberine", "chromium", "alpha_lipoic_acid", "magnesium", "coq10"],
        "anti_inflammatory": ["omega_3", "curcumin", "resveratrol", "quercetin", "nac"],
        "cognitive": ["omega_3_dha", "phosphatidylserine", "lions_mane", "bacopa", "vitamin_d"],
        "immune": ["vitamin_c", "vitamin_d3", "zinc", "elderberry", "reishi_mushroom"],
        "sleep_support": ["magnesium_threonate", "glycine", "l_theanine", "melatonin_low_dose", "ashwagandha"],
    }

    FOOD_DATABASE = {
        "fermented": {"items": ["yogurt", "kefir", "sauerkraut", "kimchi", "miso", "tempeh", "kombucha"], "benefits": "probiotic_diversity", "score": 9},
        "prebiotic_rich": {"items": ["garlic", "onion", "leek", "asparagus", "banana", "oats", "flaxseed"], "benefits": "bifidogenic", "score": 8},
        "polyphenol_rich": {"items": ["blueberries", "green_tea", "dark_chocolate", "red_wine", "turmeric", "pomegranate"], "benefits": "anti_oxidant", "score": 8},
        "omega_3_rich": {"items": ["salmon", "mackerel", "sardines", "walnuts", "flaxseed", "chia_seeds"], "benefits": "anti_inflammatory", "score": 9},
        "cruciferous": {"items": ["broccoli", "cauliflower", "kale", "brussels_sprouts", "cabbage"], "benefits": "detox_support", "score": 7},
        "protein_dense": {"items": ["chicken_breast", "turkey", "eggs", "tofu", "lentils", "greek_yogurt"], "benefits": "muscle_support", "score": 8},
    }

    def __init__(self):
        self.profiles: Dict[str, dict] = {}
        self.diet_plans: Dict[str, List[dict]] = {}
        self.food_logs: Dict[str, List[dict]] = {}
        self.supplement_logs: Dict[str, List[dict]] = {}

    def create_nutrition_profile(self, user_id: str, microbiome_type: str, metabolic_type: str, allergies: List[str] = None, preferences: dict = None) -> dict:
        mb = self.MICROBIOME_PROFILES.get(microbiome_type, self.MICROBIOME_PROFILES["balanced"])
        mt = self.METABOLIC_TYPES.get(metabolic_type, self.METABOLIC_TYPES["moderate_oxidizer"])
        
        profile = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "microbiome": mb,
            "metabolic": mt,
            "allergies": allergies or [],
            "preferences": preferences or {},
            "daily_calories_target": 2000,
            "macros": {
                "carbs_g": round(2000 * mt["carb_ratio"] / 4),
                "protein_g": round(2000 * mt["protein_ratio"] / 4),
                "fat_g": round(2000 * mt["fat_ratio"] / 9),
            },
            "created_at": datetime.now().isoformat(),
        }
        self.profiles[user_id] = profile
        return profile

    def generate_meal_plan(self, user_id: str, days: int = 7) -> dict:
        profile = self.profiles.get(user_id, {})
        mb = profile.get("microbiome", self.MICROBIOME_PROFILES["balanced"])
        mt = profile.get("metabolic", self.METABOLIC_TYPES["moderate_oxidizer"])
        
        meal_plan = {"days": [], "generated_at": datetime.now().isoformat(), "microbiome_type": mb["name"], "metabolic_type": mt["name"]}
        
        for day in range(days):
            meals = []
            num_meals = mt["meal_frequency"]
            for meal_idx in range(num_meals):
                meal_types = ["breakfast", "snack", "lunch", "snack", "dinner"]
                meal_name = meal_types[meal_idx] if meal_idx < len(meal_types) else "snack"
                
                foods = []
                if meal_name == "breakfast":
                    foods = ["oatmeal_with_berries", "greek_yogurt_with_probiotics", "green_smoothie"]
                elif meal_name == "lunch":
                    foods = ["salmon_with_quinoa", "mediterranean_salad", "lentil_soup"]
                elif meal_name == "dinner":
                    foods = ["grilled_chicken_vegetables", "baked_fish_sweet_potato", "tofu_stir_fry"]
                else:
                    foods = ["nuts_and_seeds", "fermented_snack", "berry_parfait"]
                
                meals.append({"type": meal_name, "foods": foods, "calories": round(2000 / num_meals)})
            meal_plan["days"].append({"day": day + 1, "meals": meals})
        
        self.diet_plans[user_id] = [meal_plan]
        return meal_plan

    def get_food_recommendations(self, user_id: str, category: str = None) -> List[dict]:
        profile = self.profiles.get(user_id, {})
        mb_type = profile.get("microbiome", {}).get("name", "Balanced Microbiome")
        
        recommendations = []
        for cat_key, cat_data in self.FOOD_DATABASE.items():
            if category and cat_key != category:
                continue
            score = cat_data["score"]
            if "fermented" in cat_key and "Bacteroides" in mb_type:
                score += 1
            elif "prebiotic" in cat_key and "Firmicutes" in mb_type:
                score += 1
            
            recommendations.append({
                "category": cat_key,
                "items": cat_data["items"],
                "benefits": cat_data["benefits"],
                "personalized_score": min(score, 10),
            })
        
        return sorted(recommendations, key=lambda x: x["personalized_score"], reverse=True)

    def get_supplement_protocol(self, user_id: str, goal: str) -> List[dict]:
        protocol = self.SUPPLEMENT_PROTOCOLS.get(goal, self.SUPPLEMENT_PROTOCOLS["gut_health"])
        supplements = []
        for supp in protocol:
            supplements.append({
                "name": supp.replace("_", " ").title(),
                "dosage": "As directed",
                "timing": "With meals",
                "goal": goal,
            })
        return supplements

    def log_food(self, user_id: str, meal: str, items: List[str], calories: int, notes: str = "") -> dict:
        entry = {
            "id": str(uuid.uuid4()),
            "meal": meal,
            "items": items,
            "calories": calories,
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
        }
        self.food_logs.setdefault(user_id, []).append(entry)
        return entry

    def get_daily_summary(self, user_id: str) -> dict:
        logs = self.food_logs.get(user_id, [])
        today = datetime.now().date().isoformat()
        today_logs = [l for l in logs if l["timestamp"][:10] == today]
        total_calories = sum(l["calories"] for l in today_logs)
        
        return {
            "total_calories": total_calories,
            "meals_logged": len(today_logs),
            "items": [l["items"] for l in today_logs],
            "timestamp": today,
        }


precision_nutrition = PrecisionNutritionService()

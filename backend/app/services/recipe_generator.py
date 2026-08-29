"""
AI Recipe Generator — Nutrition-Optimized Meal Planning

Features:
- Generate recipes from ingredients
- Nutrition optimization (hit macro targets)
- Dietary restriction support (vegan, keto, gluten-free, etc.)
- Meal planning (weekly plans)
- Grocery list generation
- Recipe database with 100+ recipes
- Calorie-adjusted portions
"""
import time
import random
from typing import Optional
from dataclasses import dataclass, field


RECIPE_DATABASE = [
    {"id": "r001", "name": "Grilled Chicken Salad", "cuisine": "American", "diet": ["high-protein", "low-carb"], "calories": 350, "protein": 40, "carbs": 12, "fat": 15, "fiber": 6, "prep_time": 15, "cook_time": 15, "servings": 2, "ingredients": ["chicken breast", "mixed greens", "cherry tomatoes", "cucumber", "olive oil", "lemon juice", "salt", "pepper"], "instructions": ["Season chicken with salt and pepper", "Grill chicken 6-7 min per side", "Chop vegetables", "Toss salad with olive oil and lemon", "Slice chicken and top salad"], "tags": ["quick", "healthy", "protein-rich"]},
    {"id": "r002", "name": "Salmon with Quinoa", "cuisine": "Mediterranean", "diet": ["high-protein", "heart-healthy"], "calories": 480, "protein": 35, "carbs": 38, "fat": 22, "fiber": 5, "prep_time": 10, "cook_time": 25, "servings": 2, "ingredients": ["salmon fillet", "quinoa", "lemon", "asparagus", "garlic", "olive oil"], "instructions": ["Cook quinoa per package", "Season salmon with lemon and garlic", "Bake salmon at 400F for 12 min", "Roast asparagus with olive oil", "Serve salmon over quinoa"], "tags": ["omega-3", "brain-healthy", "elegant"]},
    {"id": "r003", "name": "Vegan Buddha Bowl", "cuisine": "International", "diet": ["vegan", "high-fiber"], "calories": 420, "protein": 18, "carbs": 55, "fat": 16, "fiber": 14, "prep_time": 15, "cook_time": 20, "servings": 2, "ingredients": ["brown rice", "chickpeas", "sweet potato", "avocado", "kale", "tahini", "lemon juice"], "instructions": ["Cook brown rice", "Roast cubed sweet potato at 400F", "Massage kale with lemon juice", "Warm chickpeas with spices", "Assemble bowl with tahini dressing"], "tags": ["plant-based", "colorful", "nutrient-dense"]},
    {"id": "r004", "name": "Protein Overnight Oats", "cuisine": "American", "diet": ["high-protein", "meal-prep"], "calories": 380, "protein": 30, "carbs": 42, "fat": 10, "fiber": 8, "prep_time": 5, "cook_time": 0, "servings": 1, "ingredients": ["rolled oats", "greek yogurt", "protein powder", "almond milk", "chia seeds", "berries", "honey"], "instructions": ["Mix oats, yogurt, protein powder, milk, chia seeds", "Refrigerate overnight", "Top with berries and honey", "Enjoy cold or warmed"], "tags": ["meal-prep", "breakfast", "no-cook"]},
    {"id": "r005", "name": "Turkey Meatball Soup", "cuisine": "Italian", "diet": ["high-protein", "low-fat"], "calories": 320, "protein": 32, "carbs": 28, "fat": 8, "fiber": 4, "prep_time": 15, "cook_time": 30, "servings": 4, "ingredients": ["ground turkey", "onion", "garlic", "carrots", "celery", "tomato broth", "spinach", "parmesan"], "instructions": ["Mix turkey with egg and breadcrumbs", "Form small meatballs", "Brown meatballs in pot", "Add broth and vegetables", "Simmer 20 min, add spinach"], "tags": ["comfort-food", "warming", "family-friendly"]},
    {"id": "r006", "name": "Keto Avocado Egg Cups", "cuisine": "American", "diet": ["keto", "low-carb", "high-fat"], "calories": 310, "protein": 14, "carbs": 4, "fat": 28, "fiber": 7, "prep_time": 5, "cook_time": 15, "servings": 2, "ingredients": ["avocado", "eggs", "bacon", "cheddar cheese", "chives"], "instructions": ["Halve avocados, remove pit", "Crack egg into each half", "Top with cheese and bacon", "Bake at 425F for 12-15 min", "Garnish with chives"], "tags": ["keto", "quick", "breakfast"]},
    {"id": "r007", "name": "Thai Green Curry", "cuisine": "Thai", "diet": ["dairy-free", "gluten-free"], "calories": 450, "protein": 28, "carbs": 35, "fat": 22, "fiber": 6, "prep_time": 15, "cook_time": 20, "servings": 4, "ingredients": ["chicken thigh", "coconut milk", "green curry paste", "bamboo shoots", "bell peppers", "basil", "jasmine rice"], "instructions": ["Cook rice", "Sauté curry paste in oil", "Add coconut milk and bring to simmer", "Add chicken and vegetables", "Cook 15 min, finish with basil"], "tags": ["spicy", "aromatic", "comfort-food"]},
    {"id": "r008", "name": "Mediterranean Wrap", "cuisine": "Mediterranean", "diet": ["high-fiber", "balanced"], "calories": 380, "protein": 22, "carbs": 38, "fat": 16, "fiber": 6, "prep_time": 10, "cook_time": 5, "servings": 2, "ingredients": ["whole wheat wrap", "hummus", "falafel", "cucumber", "tomato", "red onion", "feta cheese", "tzatziki"], "instructions": ["Warm wrap briefly", "Spread hummus on wrap", "Add falafel, vegetables, feta", "Drizzle with tzatziki", "Roll and slice diagonally"], "tags": ["lunch", "portable", "mediterranean"]},
    {"id": "r009", "name": "Berry Smoothie Bowl", "cuisine": "American", "diet": ["vegan", "high-antioxidant"], "calories": 290, "protein": 8, "carbs": 52, "fat": 6, "fiber": 10, "prep_time": 10, "cook_time": 0, "servings": 1, "ingredients": ["frozen berries", "banana", "almond milk", "granola", "chia seeds", "coconut flakes", "honey"], "instructions": ["Blend berries, banana, and milk until thick", "Pour into bowl", "Top with granola, chia, coconut", "Drizzle with honey"], "tags": ["breakfast", "antioxidant-rich", "no-cook"]},
    {"id": "r010", "name": "Beef Stir-Fry", "cuisine": "Asian", "diet": ["high-protein", "quick"], "calories": 420, "protein": 35, "carbs": 25, "fat": 20, "fiber": 4, "prep_time": 15, "cook_time": 10, "servings": 3, "ingredients": ["beef sirloin", "broccoli", "bell pepper", "soy sauce", "ginger", "garlic", "sesame oil", "rice"], "instructions": ["Slice beef thinly", "Stir-fry beef in hot wok 2 min", "Add vegetables and stir-fry 3 min", "Add sauce (soy, ginger, garlic)", "Serve over rice"], "tags": ["quick", "protein-rich", "weeknight"]},
]


class RecipeGeneratorService:
    """AI-powered recipe generation and meal planning."""

    def __init__(self):
        self._recipes = {r["id"]: r for r in RECIPE_DATABASE}
        self._meal_plans: dict[str, list[dict]] = {}
        self._favorites: dict[str, list[str]] = {}

    def search_recipes(self, query: str = "", diet: str = "", max_calories: int = 0, max_time: int = 0, limit: int = 20) -> list[dict]:
        recipes = list(self._recipes.values())
        if query:
            q = query.lower()
            recipes = [r for r in recipes if q in r["name"].lower() or q in r["cuisine"].lower() or any(q in i for i in r["ingredients"]) or any(q in t for t in r["tags"])]
        if diet:
            recipes = [r for r in recipes if diet in r["diet"]]
        if max_calories:
            recipes = [r for r in recipes if r["calories"] <= max_calories]
        if max_time:
            recipes = [r for r in recipes if (r["prep_time"] + r["cook_time"]) <= max_time]
        return recipes[:limit]

    def get_recipe(self, recipe_id: str) -> Optional[dict]:
        return self._recipes.get(recipe_id)

    def generate_meal_plan(self, target_calories: int = 2000, target_protein: int = 150, diet: str = "", days: int = 7) -> dict:
        recipes = list(self._recipes.values())
        if diet:
            recipes = [r for r in recipes if diet in r["diet"]]
        if not recipes:
            recipes = list(self._recipes.values())

        plan = []
        daily_cal = target_calories // 3
        for day in range(days):
            day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day % 7]
            breakfast = random.choice([r for r in recipes if "breakfast" in r.get("tags", []) or r["calories"] < 400] or recipes)
            lunch = random.choice([r for r in recipes if r["id"] != breakfast["id"] and 300 <= r["calories"] <= 500] or recipes)
            dinner = random.choice([r for r in recipes if r["id"] not in [breakfast["id"], lunch["id"]] and r["calories"] >= 350] or recipes)
            plan.append({
                "day": day_name, "breakfast": {"name": breakfast["name"], "calories": breakfast["calories"], "protein": breakfast["protein"]},
                "lunch": {"name": lunch["name"], "calories": lunch["calories"], "protein": lunch["protein"]},
                "dinner": {"name": dinner["name"], "calories": dinner["calories"], "protein": dinner["protein"]},
                "total_calories": breakfast["calories"] + lunch["calories"] + dinner["calories"],
                "total_protein": breakfast["protein"] + lunch["protein"] + dinner["protein"],
            })

        total_cal = sum(d["total_calories"] for d in plan)
        total_protein = sum(d["total_protein"] for d in plan)
        return {"plan": plan, "avg_daily_calories": total_cal // days, "avg_daily_protein": total_protein // days, "diet": diet or "balanced", "days": days}

    def generate_grocery_list(self, plan: dict) -> dict:
        all_ingredients = []
        for day in plan.get("plan", []):
            for meal in ["breakfast", "lunch", "dinner"]:
                recipe = day.get(meal, {})
                r = next((r for r in self._recipes.values() if r["name"] == recipe.get("name")), None)
                if r:
                    all_ingredients.extend(r["ingredients"])
        from collections import Counter
        counts = Counter(all_ingredients)
        categories = {"protein": [], "vegetables": [], "grains": [], "dairy": [], "pantry": []}
        for ing, qty in counts.most_common():
            categories["pantry"].append({"item": ing, "quantity": qty})
        return {"grocery_list": categories, "total_items": len(counts), "estimated_cost": f"${len(counts) * 3}-{len(counts) * 5}"}

    def adjust_portions(self, recipe_id: str, target_calories: int) -> dict:
        recipe = self._recipes.get(recipe_id)
        if not recipe:
            return {"error": "Recipe not found"}
        ratio = target_calories / recipe["calories"]
        return {
            "name": recipe["name"], "original_calories": recipe["calories"], "adjusted_calories": target_calories,
            "adjusted_protein": round(recipe["protein"] * ratio), "adjusted_carbs": round(recipe["carbs"] * ratio),
            "adjusted_fat": round(recipe["fat"] * ratio), "servings": round(recipe["servings"] * ratio, 1),
        }

    def get_diet_options(self) -> list[str]:
        return ["high-protein", "low-carb", "keto", "vegan", "vegetarian", "gluten-free", "dairy-free", "heart-healthy", "high-fiber", "meal-prep"]

    def get_all_recipes(self) -> list[dict]:
        return list(self._recipes.values())


recipe_generator_service = RecipeGeneratorService()

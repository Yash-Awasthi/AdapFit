"""Meal Delivery & Grocery Integration Service.

Based on 2025 Instacart/meal planning research:
- Healthy restaurant discovery with nutrition data
- Grocery list generation from meal plans
- Dietary filter (keto, vegan, gluten-free, etc.)
- Calorie and macro matching
- Order tracking
- Meal prep suggestions
"""

import time
import random
from typing import Dict, List, Any


class MealDeliveryService:
    """Healthy meal ordering and grocery delivery integration."""

    def __init__(self):
        self.restaurants = self._init_restaurants()
        self.grocery_items = self._init_grocery()

    def _init_restaurants(self) -> List[Dict]:
        return [
            {"id": "r1", "name": "Sweetgreen", "cuisine": "salad", "rating": 4.5, "delivery_time_min": 25, "dietary": ["vegetarian", "vegan", "gluten_free"], "popular_items": [{"name": "Harvest Bowl", "calories": 550, "protein": 32, "carbs": 55, "fat": 22}, {"name": "Kale Caesar", "calories": 420, "protein": 28, "carbs": 35, "fat": 18}]},
            {"id": "r2", "name": "CAVA", "cuisine": "mediterranean", "rating": 4.4, "delivery_time_min": 30, "dietary": ["vegetarian", "gluten_free"], "popular_items": [{"name": "Spicy Chicken Grain Bowl", "calories": 620, "protein": 38, "carbs": 52, "fat": 28}, {"name": "Falafel Plate", "calories": 480, "protein": 18, "carbs": 55, "fat": 20}]},
            {"id": "r3", "name": "Chipotle", "cuisine": "mexican", "rating": 4.2, "delivery_time_min": 20, "dietary": ["gluten_free"], "popular_items": [{"name": "Chicken Burrito Bowl", "calories": 580, "protein": 42, "carbs": 48, "fat": 22}, {"name": "Steal Salad", "calories": 380, "protein": 35, "carbs": 18, "fat": 18}]},
            {"id": "r4", "name": "Nekter Juice Bar", "cuisine": "juice_smoothie", "rating": 4.3, "delivery_time_min": 15, "dietary": ["vegan", "raw"], "popular_items": [{"name": "Green Glow Smoothie", "calories": 220, "protein": 6, "carbs": 42, "fat": 3}, {"name": "Acai Bowl", "calories": 340, "protein": 8, "carbs": 58, "fat": 10}]},
            {"id": "r5", "name": "Mendocino Farms", "cuisine": "sandwiches", "rating": 4.4, "delivery_time_min": 25, "dietary": ["vegetarian"], "popular_items": [{"name": "Not So Fried Chicken Sandwich", "calories": 520, "protein": 35, "carbs": 42, "fat": 22}, {"name": "Impossible Burger", "calories": 580, "protein": 28, "carbs": 48, "fat": 26}]},
        ]

    def _init_grocery(self) -> List[Dict]:
        return [
            {"name": "Chicken Breast", "category": "protein", "calories_per_100g": 165, "protein_per_100g": 31, "price": 6.99, "unit": "lb"},
            {"name": "Salmon Fillet", "category": "protein", "calories_per_100g": 208, "protein_per_100g": 20, "price": 12.99, "unit": "lb"},
            {"name": "Brown Rice", "category": "carbs", "calories_per_100g": 112, "protein_per_100g": 2.6, "price": 3.49, "unit": "lb"},
            {"name": "Broccoli", "category": "vegetables", "calories_per_100g": 34, "protein_per_100g": 2.8, "price": 2.99, "unit": "bunch"},
            {"name": "Sweet Potato", "category": "carbs", "calories_per_100g": 86, "protein_per_100g": 1.6, "price": 1.99, "unit": "lb"},
            {"name": "Avocado", "category": "fats", "calories_per_100g": 160, "protein_per_100g": 2, "price": 1.50, "unit": "each"},
        ]

    def search_restaurants(self, dietary: str = "", cuisine: str = "", max_calories: int = 0) -> List[Dict]:
        """Search restaurants by dietary preference."""
        results = self.restaurants
        if dietary:
            results = [r for r in results if dietary in r["dietary"]]
        if cuisine:
            results = [r for r in results if cuisine in r["cuisine"]]
        return results

    def get_menu_items(self, restaurant_id: str, max_calories: int = 0) -> List[Dict]:
        """Get restaurant menu items with nutrition data."""
        for r in self.restaurants:
            if r["id"] == restaurant_id:
                items = r["popular_items"]
                if max_calories > 0:
                    items = [i for i in items if i["calories"] <= max_calories]
                return items
        return []

    def generate_grocery_list(self, meals: List[Dict], days: int = 7) -> Dict[str, Any]:
        """Generate grocery list from meal plan."""
        total_cost = 0
        items_needed = []
        for meal in meals:
            for ingredient in meal.get("ingredients", []):
                items_needed.append(ingredient)
                total_cost += ingredient.get("price", 0)

        return {
            "total_items": len(items_needed),
            "estimated_cost": round(total_cost, 2),
            "items": items_needed,
            "delivery_available": True,
            "partner": "Instacart",
        }

    def filter_by_diet(self, diet_type: str) -> Dict[str, Any]:
        """Get diet-specific recommendations."""
        diets = {
            "keto": {"restrictions": "Very low carb, high fat", "allowed": "Meat, fish, eggs, cheese, nuts, low-carb veggies", "avoid": "Bread, pasta, rice, sugar, most fruits", "calorie_split": "70% fat, 25% protein, 5% carbs"},
            "vegan": {"restrictions": "No animal products", "allowed": "Fruits, vegetables, grains, legumes, nuts, soy", "avoid": "Meat, dairy, eggs, honey", "calorie_split": "Balanced macros"},
            "paleo": {"restrictions": "Whole foods, no processed", "allowed": "Meat, fish, vegetables, fruits, nuts, seeds", "avoid": "Grains, dairy, legumes, processed sugar", "calorie_split": "Higher protein, moderate fat"},
            "mediterranean": {"restrictions": "Heart-healthy fats, lean protein", "allowed": "Fish, olive oil, whole grains, vegetables, legumes", "avoid": "Red meat, processed foods, added sugar", "calorie_split": "Balanced, emphasis on healthy fats"},
        }
        return diets.get(diet_type, {"error": "Diet type not found"})

    def get_meal_prep_suggestions(self, goal: str = "muscle_gain") -> List[Dict]:
        """Get meal prep suggestions based on goal."""
        suggestions = {
            "muscle_gain": [
                {"meal": "Chicken & Rice Bowl", "prep_time": "30 min", "servings": 4, "macros": {"protein": 45, "carbs": 55, "fat": 15}},
                {"meal": "Overnight Oats with Protein", "prep_time": "5 min", "servings": 5, "macros": {"protein": 30, "carbs": 45, "fat": 12}},
            ],
            "weight_loss": [
                {"meal": "Turkey Veggie Stir-Fry", "prep_time": "20 min", "servings": 4, "macros": {"protein": 30, "carbs": 25, "fat": 10}},
                {"meal": "Greek Yogurt Parfait Prep", "prep_time": "10 min", "servings": 5, "macros": {"protein": 20, "carbs": 20, "fat": 8}},
            ],
        }
        return suggestions.get(goal, suggestions["muscle_gain"])


meal_delivery_service = MealDeliveryService()

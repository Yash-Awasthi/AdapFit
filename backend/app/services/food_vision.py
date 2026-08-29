"""Food Vision — AI-powered food recognition and macro estimation from photos.

Uses Gemini Vision API for food detection, portion estimation, and nutrition
calculation. Falls back to database lookup when API is unavailable.

References:
- OpenNutriTracker: food photo recognition flow
- Fud AI: privacy-first calorie tracker pattern
- BiteBuddy: Flutter + Gemini AI for food analysis
"""

from __future__ import annotations
import json
import re
from typing import Optional
from dataclasses import dataclass, field
from app.core.gemini import gemini_endpoint


@dataclass
class FoodItem:
    name: str
    confidence: float
    portion_grams: float
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float = 0
    sodium_mg: float = 0


@dataclass
class MealAnalysis:
    foods: list[FoodItem]
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    total_fiber: float
    meal_quality_score: float  # 0-100
    suggestions: list[str]
    confidence: float


# Common food database for fallback
FOOD_DB = {
    # Proteins
    "chicken breast": {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6, "fiber": 0, "per_100g": True},
    "salmon": {"calories": 208, "protein": 20, "carbs": 0, "fat": 13, "fiber": 0, "per_100g": True},
    "egg": {"calories": 78, "protein": 6, "carbs": 0.6, "fat": 5, "fiber": 0, "per_100g": False, "per_unit": 50},
    "beef steak": {"calories": 271, "protein": 26, "carbs": 0, "fat": 18, "fiber": 0, "per_100g": True},
    "tuna": {"calories": 130, "protein": 29, "carbs": 0, "fat": 1, "fiber": 0, "per_100g": True},
    "greek yogurt": {"calories": 59, "protein": 10, "carbs": 3.6, "fat": 0.7, "fiber": 0, "per_100g": True},
    "tofu": {"calories": 76, "protein": 8, "carbs": 1.9, "fat": 4.8, "fiber": 0.3, "per_100g": True},
    "cottage cheese": {"calories": 98, "protein": 11, "carbs": 3.4, "fat": 4.3, "fiber": 0, "per_100g": True},
    # Carbs
    "rice": {"calories": 130, "protein": 2.7, "carbs": 28, "fat": 0.3, "fiber": 0.4, "per_100g": True},
    "pasta": {"calories": 131, "protein": 5, "carbs": 25, "fat": 1.1, "fiber": 1.8, "per_100g": True},
    "bread": {"calories": 265, "protein": 9, "carbs": 49, "fat": 3.2, "fiber": 2.7, "per_100g": True},
    "oatmeal": {"calories": 68, "protein": 2.4, "carbs": 12, "fat": 1.4, "fiber": 1.7, "per_100g": True},
    "sweet potato": {"calories": 86, "protein": 1.6, "carbs": 20, "fat": 0.1, "fiber": 3, "per_100g": True},
    "banana": {"calories": 89, "protein": 1.1, "carbs": 23, "fat": 0.3, "fiber": 2.6, "per_unit": 120},
    "apple": {"calories": 52, "protein": 0.3, "carbs": 14, "fat": 0.2, "fiber": 2.4, "per_unit": 180},
    # Fats
    "avocado": {"calories": 160, "protein": 2, "carbs": 9, "fat": 15, "fiber": 7, "per_unit": 150},
    "almonds": {"calories": 579, "protein": 21, "carbs": 22, "fat": 50, "fiber": 12, "per_100g": True},
    "peanut butter": {"calories": 588, "protein": 25, "carbs": 20, "fat": 50, "fiber": 6, "per_100g": True},
    "olive oil": {"calories": 884, "protein": 0, "carbs": 0, "fat": 100, "fiber": 0, "per_100g": True},
    # Vegetables
    "broccoli": {"calories": 34, "protein": 2.8, "carbs": 7, "fat": 0.4, "fiber": 2.6, "per_100g": True},
    "spinach": {"calories": 23, "protein": 2.9, "carbs": 3.6, "fat": 0.4, "fiber": 2.2, "per_100g": True},
    "kale": {"calories": 49, "protein": 4.3, "carbs": 9, "fat": 0.9, "fiber": 3.6, "per_100g": True},
    "bell pepper": {"calories": 31, "protein": 1, "carbs": 6, "fat": 0.3, "fiber": 2.1, "per_100g": True},
}


def analyze_food_from_description(description: str) -> MealAnalysis:
    """Analyze food from text description (fallback when no photo)."""
    foods = []
    desc_lower = description.lower()

    # Simple keyword matching
    for food_name, data in FOOD_DB.items():
        if food_name in desc_lower:
            portion = 150  # Default portion
            if "small" in desc_lower:
                portion = 80
            elif "large" in desc_lower:
                portion = 250

            if data.get("per_unit"):
                portion = data["per_unit"]

            scale = portion / 100 if data.get("per_100g") else 1
            foods.append(FoodItem(
                name=food_name.title(),
                confidence=0.8,
                portion_grams=portion,
                calories=round(data["calories"] * scale, 1),
                protein_g=round(data["protein"] * scale, 1),
                carbs_g=round(data["carbs"] * scale, 1),
                fat_g=round(data["fat"] * scale, 1),
                fiber_g=round(data.get("fiber", 0) * scale, 1),
            ))

    if not foods:
        # Generic estimate
        foods.append(FoodItem(
            name="Unknown Food",
            confidence=0.3,
            portion_grams=200,
            calories=300,
            protein_g=15,
            carbs_g=35,
            fat_g=10,
        ))

    return _compute_totals(foods)


def analyze_food_from_gemini_vision(image_base64: str, api_key: str = "") -> MealAnalysis:
    """Analyze food photo using Gemini Vision API.

    When API key is provided, calls Gemini for real analysis.
    Falls back to basic estimation otherwise.
    """
    if not api_key:
        return MealAnalysis(
            foods=[], total_calories=0, total_protein=0,
            total_carbs=0, total_fat=0, total_fiber=0,
            meal_quality_score=0, suggestions=["Set GEMINI_API_KEY for photo analysis"],
            confidence=0,
        )

    try:
        import httpx
        prompt = (
            "Analyze this food photo. For each food item, provide:\n"
            "1. Name\n"
            "2. Estimated portion in grams\n"
            "3. Calories, protein (g), carbs (g), fat (g), fiber (g)\n\n"
            "Return as JSON array: [{\"name\": \"...\", \"portion_grams\": 100, "
            "\"calories\": 200, \"protein_g\": 20, \"carbs_g\": 10, \"fat_g\": 5, \"fiber_g\": 2}]\n"
            "Only return valid JSON, no explanation."
        )

        response = httpx.post(
            gemini_endpoint(api_key)[0],
            json={
                "contents": [{"parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": image_base64}},
                ]}]
            },
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            # Extract JSON
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                items = json.loads(json_match.group())
                foods = [
                    FoodItem(
                        name=item["name"],
                        confidence=0.85,
                        portion_grams=item.get("portion_grams", 100),
                        calories=item.get("calories", 0),
                        protein_g=item.get("protein_g", 0),
                        carbs_g=item.get("carbs_g", 0),
                        fat_g=item.get("fat_g", 0),
                        fiber_g=item.get("fiber_g", 0),
                    )
                    for item in items
                ]
                return _compute_totals(foods)

    except Exception:
        pass

    return MealAnalysis(
        foods=[], total_calories=0, total_protein=0,
        total_carbs=0, total_fat=0, total_fiber=0,
        meal_quality_score=0, suggestions=["Vision analysis unavailable"],
        confidence=0,
    )


def _compute_totals(foods: list[FoodItem]) -> MealAnalysis:
    """Compute totals and quality score from food items."""
    total_cal = sum(f.calories for f in foods)
    total_protein = sum(f.protein_g for f in foods)
    total_carbs = sum(f.carbs_g for f in foods)
    total_fat = sum(f.fat_g for f in foods)
    total_fiber = sum(f.fiber_g for f in foods)

    # Quality score based on macro balance
    suggestions = []
    score = 70  # Base

    if total_protein > 0:
        protein_pct = total_protein * 4 / max(total_cal, 1) * 100
        if protein_pct >= 25:
            score += 10
        elif protein_pct < 15:
            score -= 10
            suggestions.append("Add more protein (target 25%+ of calories)")

    if total_fiber > 0:
        if total_fiber >= 5:
            score += 5
        elif total_fiber < 2:
            score -= 5
            suggestions.append("Add vegetables or whole grains for fiber")

    if total_fat > 0:
        fat_pct = total_fat * 9 / max(total_cal, 1) * 100
        if fat_pct > 40:
            score -= 5
            suggestions.append("Fat is high — consider leaner options")

    if not suggestions:
        suggestions.append("Good balanced meal!")

    avg_confidence = sum(f.confidence for f in foods) / len(foods) if foods else 0

    return MealAnalysis(
        foods=foods,
        total_calories=round(total_cal, 1),
        total_protein=round(total_protein, 1),
        total_carbs=round(total_carbs, 1),
        total_fat=round(total_fat, 1),
        total_fiber=round(total_fiber, 1),
        meal_quality_score=min(100, max(0, round(score))),
        suggestions=suggestions,
        confidence=round(avg_confidence, 2),
    )


def suggest_food_swap(food_name: str) -> list[dict]:
    """Suggest healthier alternatives for a food item."""
    swaps = {
        "white rice": [{"name": "Brown Rice", "reason": "More fiber and nutrients", "calories_saved": 10}],
        "white bread": [{"name": "Whole Wheat Bread", "reason": "Higher fiber, lower glycemic", "calories_saved": 15}],
        "soda": [{"name": "Sparkling Water", "reason": "Zero sugar, zero calories", "calories_saved": 140}],
        "chips": [{"name": "Air-popped Popcorn", "reason": "Whole grain, high volume", "calories_saved": 120}],
        "ice cream": [{"name": "Greek Yogurt", "reason": "High protein, lower sugar", "calories_saved": 100}],
        "pasta": [{"name": "Zucchini Noodles", "reason": "Low carb, high volume", "calories_saved": 200}],
    }

    name_lower = food_name.lower()
    for key, value in swaps.items():
        if key in name_lower:
            return value

    return [{"name": food_name, "reason": "Already a good choice", "calories_saved": 0}]

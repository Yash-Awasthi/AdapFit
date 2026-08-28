"""Diet & Food Logging — comprehensive food tracking with daily charts.

Users log meals throughout the day; the system computes running totals,
shows macro distribution chart, and suggests adjustments.

Supports: quick-add, text description, barcode-style lookup, and photo-based logging.
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()

_meals: dict[str, list[dict]] = {}


class MealLogRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    calories: float = Field(ge=0)
    protein_g: float = Field(ge=0, default=0)
    carbs_g: float = Field(ge=0, default=0)
    fat_g: float = Field(ge=0, default=0)
    fiber_g: float = Field(ge=0, default=0)
    meal_type: str = Field(default="snack", description="breakfast, lunch, dinner, snack, pre_workout, post_workout")
    quantity: float = Field(ge=0, default=1)
    unit: str = Field(default="serving")
    barcode: Optional[str] = None
    photo_url: Optional[str] = None
    notes: str = Field(max_length=200, default="")
    date: Optional[str] = None


class DailyTargetRequest(BaseModel):
    calories_target: float = Field(ge=500, le=10000, default=2500)
    protein_target_g: float = Field(ge=0, default=150)
    carbs_target_g: float = Field(ge=0, default=300)
    fat_target_g: float = Field(ge=0, default=80)


# Common food quick-add database
QUICK_FOODS = [
    {"name": "Chicken Breast (100g)", "calories": 165, "protein": 31, "carbs": 0, "fat": 3.6},
    {"name": "Brown Rice (1 cup)", "calories": 216, "protein": 5, "carbs": 45, "fat": 1.8},
    {"name": "Banana", "calories": 105, "protein": 1.3, "carbs": 27, "fat": 0.4},
    {"name": "Eggs (2 large)", "calories": 156, "protein": 13, "carbs": 1.1, "fat": 11},
    {"name": "Greek Yogurt (200g)", "calories": 118, "protein": 20, "carbs": 7.2, "fat": 1.4},
    {"name": "Oats (100g)", "calories": 389, "protein": 17, "carbs": 66, "fat": 7},
    {"name": "Salmon (100g)", "calories": 208, "protein": 20, "carbs": 0, "fat": 13},
    {"name": "Sweet Potato (1 medium)", "calories": 103, "protein": 2.3, "carbs": 24, "fat": 0.1},
    {"name": "Avocado (1 medium)", "calories": 240, "protein": 3, "carbs": 13, "fat": 22},
    {"name": "Whey Protein Shake", "calories": 120, "protein": 25, "carbs": 3, "fat": 1.5},
    {"name": "Bread (2 slices)", "calories": 132, "protein": 4.4, "carbs": 24, "fat": 1.6},
    {"name": "Apple", "calories": 95, "protein": 0.5, "carbs": 25, "fat": 0.3},
    {"name": "Almonds (30g)", "calories": 173, "protein": 6.3, "carbs": 6.5, "fat": 15},
    {"name": "Pasta (1 cup cooked)", "calories": 220, "protein": 8, "carbs": 43, "fat": 1.3},
    {"name": "Broccoli (1 cup)", "calories": 55, "protein": 3.7, "carbs": 11, "fat": 0.6},
    {"name": "Cottage Cheese (100g)", "calories": 98, "protein": 11, "carbs": 3.4, "fat": 4.3},
    {"name": "Peanut Butter (2 tbsp)", "calories": 188, "protein": 8, "carbs": 6, "fat": 16},
    {"name": "Milk (1 glass 250ml)", "calories": 150, "protein": 8, "carbs": 12, "fat": 8},
    {"name": "Orange", "calories": 62, "protein": 1.2, "carbs": 15, "fat": 0.2},
    {"name": "Steak (150g)", "calories": 390, "protein": 39, "carbs": 0, "fat": 24},
]


@router.post("/log")
async def log_meal(req: MealLogRequest, user_id: str = Query("default")):
    today = req.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    record = {
        **req.model_dump(),
        "id": str(uuid.uuid4())[:10],
        "date": today,
        "logged_at": datetime.now(timezone.utc).isoformat(),
    }
    _meals.setdefault(user_id, []).append(record)
    return {"logged": True, "record": record, "daily_totals": _get_daily_totals(user_id, today)}


@router.get("/daily")
async def get_daily_log(user_id: str = Query("default"), date: Optional[str] = None):
    today = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    meals = [m for m in _meals.get(user_id, []) if m.get("date") == today]
    totals = _get_daily_totals(user_id, today)
    return {"date": today, "meals": meals, "totals": totals, "meal_count": len(meals)}


@router.get("/chart")
async def get_daily_chart(user_id: str = Query("default"), days: int = Query(7, ge=1, le=30)):
    chart_data = []
    for i in range(days):
        d = (datetime.now(timezone.utc) - __import__("datetime").timedelta(days=i)).strftime("%Y-%m-%d")
        totals = _get_daily_totals(user_id, d)
        chart_data.append({"date": d, **totals})
    chart_data.reverse()
    return {"chart": chart_data, "days": days}


@router.get("/quick-add")
async def get_quick_foods():
    return {"foods": QUICK_FOODS, "total": len(QUICK_FOODS)}


@router.post("/quick-add/{food_name}")
async def quick_add_food(food_name: str, user_id: str = Query("default"), quantity: float = 1.0):
    food = next((f for f in QUICK_FOODS if food_name.lower() in f["name"].lower()), None)
    if not food:
        return {"error": f"Food '{food_name}' not found in quick-add list"}

    record = {
        "id": str(uuid.uuid4())[:10],
        "name": food["name"],
        "calories": round(food["calories"] * quantity, 1),
        "protein_g": round(food["protein"] * quantity, 1),
        "carbs_g": round(food["carbs"] * quantity, 1),
        "fat_g": round(food["fat"] * quantity, 1),
        "quantity": quantity,
        "meal_type": "snack",
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "logged_at": datetime.now(timezone.utc).isoformat(),
    }
    _meals.setdefault(user_id, []).append(record)
    today = record["date"]
    return {"logged": True, "record": record, "daily_totals": _get_daily_totals(user_id, today)}


@router.delete("/meal/{meal_id}")
async def delete_meal(meal_id: str, user_id: str = Query("default")):
    meals = _meals.get(user_id, [])
    idx = next((i for i, m in enumerate(meals) if m.get("id") == meal_id), None)
    if idx is None:
        return {"error": "Meal not found"}
    meals.pop(idx)
    return {"deleted": True}


@router.get("/targets")
async def get_default_targets():
    return {
        "calories": 2500, "protein_g": 150, "carbs_g": 300, "fat_g": 80,
        "note": "Defaults for active adult. Adjust based on goals.",
    }


@router.get("/suggestions")
async def get_meal_suggestions(user_id: str = Query("default")):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    totals = _get_daily_totals(user_id, today)
    remaining_cal = max(0, 2500 - totals["calories"])
    remaining_protein = max(0, 150 - totals["protein_g"])

    suggestions = []
    if remaining_cal > 0:
        if remaining_protein > 30:
            suggestions.append({"food": "Chicken Breast (150g + Greek Yogurt)", "calories": 366, "reason": f"Need {remaining_protein:.0f}g more protein"})
        if remaining_cal > 500:
            suggestions.append({"food": "Salmon + Sweet Potato + Broccoli", "calories": 420, "reason": "Balanced meal with protein, carbs, and micronutrients"})
        if remaining_cal < 300:
            suggestions.append({"food": "Greek Yogurt + Almonds", "calories": 291, "reason": "Light snack to hit target"})

    if not suggestions:
        suggestions.append({"food": "You've hit your targets! Great job today.", "calories": 0, "reason": "Target met"})

    return {"remaining_calories": remaining_cal, "remaining_protein_g": remaining_protein, "suggestions": suggestions}


def _get_daily_totals(user_id: str, date: str) -> dict:
    meals = [m for m in _meals.get(user_id, []) if m.get("date") == date]
    return {
        "calories": round(sum(m.get("calories", 0) for m in meals), 1),
        "protein_g": round(sum(m.get("protein_g", 0) for m in meals), 1),
        "carbs_g": round(sum(m.get("carbs_g", 0) for m in meals), 1),
        "fat_g": round(sum(m.get("fat_g", 0) for m in meals), 1),
        "fiber_g": round(sum(m.get("fiber_g", 0) for m in meals), 1),
        "meal_count": len(meals),
    }

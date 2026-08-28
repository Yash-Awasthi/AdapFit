"""Nutrition tracking: calorie and macro logging, daily summaries."""
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter()


class MealLog(BaseModel):
    name: str = Field(min_length=1, max_length=100, examples=["Chicken breast with rice"])
    calories: int = Field(ge=0, examples=[450])
    protein_g: float = Field(ge=0, default=0, examples=[35])
    carbs_g: float = Field(ge=0, default=0, examples=[40])
    fat_g: float = Field(ge=0, default=0, examples=[12])
    meal_type: str = Field(default="snack", examples=["breakfast", "lunch", "dinner", "snack"])
    notes: Optional[str] = Field(None, max_length=200)


class MealResponse(BaseModel):
    id: str
    name: str
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    meal_type: str
    notes: Optional[str] = None
    logged_at: str


class DailySummary(BaseModel):
    date: str
    total_calories: int
    total_protein: float
    total_carbs: float
    total_fat: float
    meal_count: int
    calorie_target: int
    protein_target: float
    remaining_calories: int
    remaining_protein: float


# --- In-memory storage ---
meal_logs: dict = {}  # user_id -> list of meals


@router.get("/daily", response_model=DailySummary)
async def get_daily_summary(
    user_id: str = Query("default"),
    date: Optional[str] = Query(None),
    calorie_target: int = Query(2500, ge=500, le=10000),
    protein_target: float = Query(150, ge=20, le=500),
):
    """Get daily nutrition summary."""
    target_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    user_meals = [
        m for m in meal_logs.get(user_id, [])
        if m["logged_at"].startswith(target_date)
    ]
    total_cal = sum(m["calories"] for m in user_meals)
    total_protein = sum(m["protein_g"] for m in user_meals)
    total_carbs = sum(m["carbs_g"] for m in user_meals)
    total_fat = sum(m["fat_g"] for m in user_meals)

    return DailySummary(
        date=target_date,
        total_calories=total_cal,
        total_protein=total_protein,
        total_carbs=total_carbs,
        total_fat=total_fat,
        meal_count=len(user_meals),
        calorie_target=calorie_target,
        protein_target=protein_target,
        remaining_calories=max(0, calorie_target - total_cal),
        remaining_protein=max(0, protein_target - total_protein),
    )


@router.get("/meals", response_model=List[MealResponse])
async def list_meals(
    user_id: str = Query("default"),
    date: Optional[str] = Query(None),
):
    """List meals for a date (default: today)."""
    target_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    user_meals = [
        m for m in meal_logs.get(user_id, [])
        if m["logged_at"].startswith(target_date)
    ]
    return user_meals


@router.post("/meals", response_model=MealResponse, status_code=201)
async def log_meal(meal: MealLog, user_id: str = Query("default")):
    """Log a meal."""
    mid = str(uuid.uuid4())[:8]
    entry = {
        "id": mid,
        **meal.model_dump(),
        "logged_at": datetime.now(timezone.utc).isoformat(),
    }
    meal_logs.setdefault(user_id, []).append(entry)
    return MealResponse(**entry)


@router.delete("/meals/{meal_id}")
async def delete_meal(meal_id: str, user_id: str = Query("default")):
    """Delete a meal log."""
    user_meals = meal_logs.get(user_id, [])
    for i, m in enumerate(user_meals):
        if m["id"] == meal_id:
            user_meals.pop(i)
            return {"deleted": True}
    raise HTTPException(status_code=404, detail="Meal not found")


@router.get("/targets", response_model=dict)
async def get_targets(user_id: str = Query("default")):
    """Get recommended nutrition targets based on fitness goals."""
    # Simple rule-based targets
    return {
        "calories": 2500,
        "protein_g": 150,
        "carbs_g": 300,
        "fat_g": 70,
        "water_ml": 3500,
        "notes": "Adjust based on your weight and activity level",
    }

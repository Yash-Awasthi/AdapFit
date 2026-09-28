"""Nutrition tracking: calorie and macro logging, daily summaries."""
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from app.core.durable import durable_dict

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
    energy_check: Optional[str] = None


class DailySummary(BaseModel):
    date: str
    total_calories: int
    total_protein: float
    total_carbs: float
    total_fat: float
    meal_count: int
    calorie_target: Optional[int] = None
    protein_target: Optional[float] = None
    remaining_calories: Optional[int] = None
    remaining_protein: Optional[float] = None


# --- In-memory storage ---
meal_logs = durable_dict("app.api.v1.endpoints.nutrition.meal_logs")  # user_id -> list of meals


@router.get("/daily", response_model=DailySummary)
async def get_daily_summary(
    user_id: str = Query("default"),
    date: Optional[str] = Query(None),
    calorie_target: Optional[int] = Query(None, ge=500, le=10000),
    protein_target: Optional[float] = Query(None, ge=20, le=500),
):
    """Daily totals against the user's own targets, or none when the profile cannot produce them."""
    if calorie_target is None or protein_target is None:
        targets = await get_targets(user_id)
        if targets.get("status") == "ok":
            calorie_target = calorie_target or targets["calories"]
            protein_target = protein_target or targets["protein_g"]
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
        remaining_calories=max(0, calorie_target - total_cal) if calorie_target else None,
        remaining_protein=max(0, protein_target - total_protein) if protein_target else None,
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
    from_macros = 4 * meal.protein_g + 4 * meal.carbs_g + 9 * meal.fat_g
    if from_macros > 0 and abs(meal.calories - from_macros) > max(50, 0.2 * from_macros):
        entry = {**entry, "energy_check": (
            f"The macros add up to about {round(from_macros)} kcal, not {meal.calories}. Worth a second look.")}
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


# Goal -> (activity key, goal key) for the protein recommender.
_PROTEIN_PROFILE = {
    "hypertrophy": ("resistance/strength training", "muscle_gain"),
    "strength": ("resistance/strength training", "muscle_gain"),
    "fat_loss": ("resistance/strength training", "fat_loss"),
    "endurance": ("endurance training", "endurance"),
    "general_fitness": ("moderate", "maintenance"),
}
_ENERGY_GOAL = {"fat_loss": 0.85, "hypertrophy": 1.10, "strength": 1.05}


@router.get("/targets", response_model=dict)
async def get_targets(user_id: str = Query("default")):
    """Daily targets from the user's own profile and latest weight (Mifflin-St Jeor)."""
    from app.api.v1.endpoints.body_composition import measurements
    from app.core.storage import storage
    from app.services.protein_recommender import adjust_for_goal, calculate_protein_needs

    profile = await storage.get_user(user_id) or {}
    weights = [m["weight_kg"] for m in measurements.get(user_id, []) if m.get("weight_kg")]
    need = {"weight_kg": weights[-1] if weights else None, "height_cm": profile.get("height_cm"),
            "age": profile.get("age"), "gender": profile.get("gender")}
    missing = [k for k, v in need.items() if v in (None, "")]
    if missing:
        return {"status": "insufficient_data", "missing": missing,
                "message": "Add these to your profile or log your weight to get targets made for you."}
    sex_term = 5 if str(need["gender"]).lower() in ("male", "m", "man") else -161
    bmr = 10 * need["weight_kg"] + 6.25 * need["height_cm"] - 5 * need["age"] + sex_term
    days = profile.get("preferred_days_per_week") or 3
    activity = 1.375 if days <= 2 else 1.55 if days <= 4 else 1.725 if days <= 6 else 1.9
    goal = str(profile.get("primary_goal") or "general_fitness")
    calories = bmr * activity * _ENERGY_GOAL.get(goal, 1.0)
    act_key, goal_key = _PROTEIN_PROFILE.get(goal, _PROTEIN_PROFILE["general_fitness"])
    protein = adjust_for_goal(calculate_protein_needs(need["weight_kg"], act_key), goal_key).daily_grams
    fat = calories * 0.28 / 9
    carbs = max(0.0, (calories - protein * 4 - fat * 9) / 4)
    return {
        "status": "ok",
        "calories": round(calories), "protein_g": round(protein), "carbs_g": round(carbs), "fat_g": round(fat),
        "water_ml": round(need["weight_kg"] * 35),
        "basis": {"bmr": round(bmr), "activity_factor": activity, "goal": goal, "weight_kg": need["weight_kg"]},
        "notes": "Estimates for a healthy adult. Pregnancy, kidney disease or diabetes change these; ask your doctor or a dietitian.",
    }

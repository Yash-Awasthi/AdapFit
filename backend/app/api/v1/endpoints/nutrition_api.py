"""Nutrition Logging API"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from app.services.nutrition_logger import nutrition_logger_service

router = APIRouter()

class ProfileRequest(BaseModel):
    weight_kg: float
    height_cm: float
    age: int
    gender: str = "male"
    activity_level: str = "moderate"
    goal: str = "maintenance"

class MealLogRequest(BaseModel):
    meal_type: str = "lunch"
    foods: list[dict]

class WaterLogRequest(BaseModel):
    amount_ml: float = 250

@router.post("/profile")
async def set_profile(request: ProfileRequest):
    """Set user profile for calorie/macro calculations."""
    nutrition_logger_service.set_user_profile(
        request.weight_kg, request.height_cm, request.age,
        request.gender, request.activity_level, request.goal,
    )
    return {"updated": True}

@router.get("/targets")
async def get_targets():
    """Calculate daily nutrition targets."""
    return nutrition_logger_service.calculate_targets()

@router.post("/meal")
async def log_meal(request: MealLogRequest):
    """Log a meal with food items."""
    return nutrition_logger_service.log_meal(request.meal_type, request.foods)

@router.get("/daily")
async def get_daily_summary():
    """Get today's nutrition summary."""
    return nutrition_logger_service.get_daily_summary()

@router.get("/search")
async def search_food(q: str = Query(..., min_length=1)):
    """Search food database."""
    return {"results": nutrition_logger_service.search_food(q)}

@router.post("/water")
async def log_water(request: WaterLogRequest):
    """Log water intake."""
    return nutrition_logger_service.log_water(request.amount_ml)

@router.get("/weekly")
async def get_weekly_report():
    """Get weekly nutrition report."""
    return nutrition_logger_service.get_weekly_report()

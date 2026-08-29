"""
Precision Nutrition API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/precision-nutrition", tags=["Precision Nutrition"])


class CreateProfileRequest(BaseModel):
    user_id: str
    microbiome_type: str
    metabolic_type: str
    allergies: List[str] = []
    preferences: dict = {}


class LogFoodRequest(BaseModel):
    user_id: str
    meal: str
    items: List[str]
    calories: int
    notes: str = ""


@router.post("/profile/create")
async def create_profile(req: CreateProfileRequest):
    from app.services.precision_nutrition import precision_nutrition
    return precision_nutrition.create_nutrition_profile(req.user_id, req.microbiome_type, req.metabolic_type, req.allergies, req.preferences)


@router.get("/meal-plan/{user_id}")
async def get_meal_plan(user_id: str, days: int = 7):
    from app.services.precision_nutrition import precision_nutrition
    return precision_nutrition.generate_meal_plan(user_id, days)


@router.get("/food-recommendations/{user_id}")
async def get_food_recommendations(user_id: str, category: Optional[str] = None):
    from app.services.precision_nutrition import precision_nutrition
    return precision_nutrition.get_food_recommendations(user_id, category)


@router.get("/supplements/{user_id}/{goal}")
async def get_supplements(user_id: str, goal: str):
    from app.services.precision_nutrition import precision_nutrition
    return precision_nutrition.get_supplement_protocol(user_id, goal)


@router.post("/food/log")
async def log_food(req: LogFoodRequest):
    from app.services.precision_nutrition import precision_nutrition
    return precision_nutrition.log_food(req.user_id, req.meal, req.items, req.calories, req.notes)


@router.get("/daily-summary/{user_id}")
async def get_daily_summary(user_id: str):
    from app.services.precision_nutrition import precision_nutrition
    return precision_nutrition.get_daily_summary(user_id)


@router.get("/microbiome-types")
async def get_microbiome_types():
    from app.services.precision_nutrition import precision_nutrition
    return precision_nutrition.MICROBIOME_PROFILES


@router.get("/metabolic-types")
async def get_metabolic_types():
    from app.services.precision_nutrition import precision_nutrition
    return precision_nutrition.METABOLIC_TYPES


@router.get("/food-database")
async def get_food_database():
    from app.services.precision_nutrition import precision_nutrition
    return precision_nutrition.FOOD_DATABASE

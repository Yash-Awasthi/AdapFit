"""
AI Food Scanner & Photo-Based Nutrition Analysis API Endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/food-scanner", tags=["AI Food Scanner"])


class FoodPhotoRequest(BaseModel):
    photo_description: str
    estimated_portion: str = "standard"


class MealLogRequest(BaseModel):
    foods: List[Dict]


class DailySummaryRequest(BaseModel):
    meals: List[Dict]


class SuggestionsRequest(BaseModel):
    current_intake: Dict
    goal: str = "balanced"


@router.post("/analyze")
async def analyze_food_photo(request: FoodPhotoRequest):
    """Analyze food from photo description"""
    from app.services.ai_food_scanner import ai_food_scanner_service
    result = ai_food_scanner_service.analyze_food_photo(
        photo_description=request.photo_description,
        estimated_portion=request.estimated_portion
    )
    return {"success": True, "data": result}


@router.post("/log-meal")
async def log_meal(request: MealLogRequest):
    """Log a meal with multiple food items"""
    from app.services.ai_food_scanner import ai_food_scanner_service
    result = ai_food_scanner_service.log_meal(request.foods)
    return {"success": True, "data": result}


@router.post("/daily-summary")
async def get_daily_summary(request: DailySummaryRequest):
    """Get daily nutrition summary"""
    from app.services.ai_food_scanner import ai_food_scanner_service
    result = ai_food_scanner_service.get_daily_summary(request.meals)
    return {"success": True, "data": result}


@router.post("/suggestions")
async def get_food_suggestions(request: SuggestionsRequest):
    """Get food suggestions based on current intake"""
    from app.services.ai_food_scanner import ai_food_scanner_service
    result = ai_food_scanner_service.get_suggestions(request.current_intake, request.goal)
    return {"success": True, "data": result, "count": len(result)}


@router.get("/database")
async def get_food_database(category: Optional[str] = None):
    """Get food database"""
    from app.services.ai_food_scanner import ai_food_scanner_service
    foods = ai_food_scanner_service.get_food_database(category)
    return {"success": True, "data": foods, "count": len(foods)}


@router.get("/categories")
async def get_food_categories():
    """Get food categories with daily targets"""
    from app.services.ai_food_scanner import ai_food_scanner_service
    return {"success": True, "data": ai_food_scanner_service.food_categories}

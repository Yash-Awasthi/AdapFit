"""Meal Delivery API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List
from app.services.meal_delivery import meal_delivery_service

router = APIRouter(prefix="/meal-delivery", tags=["Meal Delivery & Grocery"])

class GroceryListRequest(BaseModel):
    meals: List[Dict[str, Any]]
    days: int = 7

@router.get("/restaurants")
async def search_restaurants(dietary: str = "", cuisine: str = "", max_calories: int = 0):
    return {"success": True, "data": meal_delivery_service.search_restaurants(dietary, cuisine, max_calories)}

@router.get("/menu/{restaurant_id}")
async def get_menu(restaurant_id: str, max_calories: int = 0):
    return {"success": True, "data": meal_delivery_service.get_menu_items(restaurant_id, max_calories)}

@router.post("/grocery-list")
async def generate_grocery_list(req: GroceryListRequest):
    return {"success": True, "data": meal_delivery_service.generate_grocery_list(req.meals, req.days)}

@router.get("/diet/{diet_type}")
async def get_diet_info(diet_type: str):
    return {"success": True, "data": meal_delivery_service.filter_by_diet(diet_type)}

@router.get("/meal-prep/{goal}")
async def get_meal_prep(goal: str = "muscle_gain"):
    return {"success": True, "data": meal_delivery_service.get_meal_prep_suggestions(goal)}

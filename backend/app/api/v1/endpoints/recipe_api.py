"""AI Recipe Generator API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.recipe_generator import recipe_generator_service

router = APIRouter()


class MealPlanRequest(BaseModel):
    target_calories: int = 2000
    target_protein: int = 150
    diet: str = ""
    days: int = 7


class PortionRequest(BaseModel):
    recipe_id: str
    target_calories: int = 500


@router.get("/search")
async def search_recipes(query: str = "", diet: str = "", max_calories: int = 0, max_time: int = 0):
    return {"recipes": recipe_generator_service.search_recipes(query, diet, max_calories, max_time)}


@router.get("/all")
async def get_all_recipes():
    return {"recipes": recipe_generator_service.get_all_recipes()}


@router.get("/{recipe_id}")
async def get_recipe(recipe_id: str):
    recipe = recipe_generator_service.get_recipe(recipe_id)
    if not recipe:
        return {"error": "Recipe not found"}
    return {"recipe": recipe}


@router.post("/meal-plan")
async def generate_meal_plan(request: MealPlanRequest):
    return recipe_generator_service.generate_meal_plan(request.target_calories, request.target_protein, request.diet, request.days)


@router.post("/grocery-list")
async def generate_grocery_list(plan: dict | None = None):
    return recipe_generator_service.generate_grocery_list(plan or {})


@router.post("/adjust-portions")
async def adjust_portions(request: PortionRequest):
    return recipe_generator_service.adjust_portions(request.recipe_id, request.target_calories)


@router.get("/diets/options")
async def get_diet_options():
    return {"diets": recipe_generator_service.get_diet_options()}

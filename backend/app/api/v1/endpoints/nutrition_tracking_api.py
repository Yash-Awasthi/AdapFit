"""Nutrition tracking — macro analysis, TDEE, meal quality scoring, dietary restrictions."""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from app.services.nutrition_tracking import (
    MacroNutrients, MicroNutrients, MealEntry, DailyIntake,
    analyze_daily_intake, calculate_tdee, score_meal_quality,
    DIETARY_PROFILES,
)

router = APIRouter()


class MacroInput(BaseModel):
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    fiber_g: float = 0


class MealInput(BaseModel):
    name: str
    calories: float
    macros: MacroInput
    meal_type: str = "snack"


class DailyIntakeInput(BaseModel):
    meals: list[MealInput]
    water_ml: float = 0
    target_calories: float = 2000
    target_protein_g: float = 150
    target_water_ml: float = 3000
    diet: str = "standard"


class TDEEInput(BaseModel):
    weight_kg: float = Field(..., ge=20, le=300)
    height_cm: float = Field(..., ge=100, le=250)
    age: int = Field(..., ge=10, le=120)
    sex: str = Field(..., pattern="^(male|female)$")
    activity_level: str = "moderate"


@router.post("/analyze")
async def analyze_nutrition(req: DailyIntakeInput):
    """Analyze daily nutritional intake against targets."""
    meals = []
    for m in req.meals:
        macros = MacroNutrients(m.macros.protein_g, m.macros.carbs_g, m.macros.fat_g, m.macros.fiber_g)
        meals.append(MealEntry(name=m.name, calories=m.calories, macros=macros, meal_type=m.meal_type))

    intake = DailyIntake(
        meals=meals,
        water_ml=req.water_ml,
        target_calories=req.target_calories,
        target_protein_g=req.target_protein_g,
        target_water_ml=req.target_water_ml,
    )
    return analyze_daily_intake(intake, req.diet)


@router.post("/tdee")
async def get_tdee(req: TDEEInput):
    """Calculate Total Daily Energy Expenditure."""
    return calculate_tdee(req.weight_kg, req.height_cm, req.age, req.sex, req.activity_level)


@router.post("/meal-quality")
async def meal_quality(req: MealInput):
    """Score a meal's nutritional quality."""
    macros = MacroNutrients(req.macros.protein_g, req.macros.carbs_g, req.macros.fat_g, req.macros.fiber_g)
    meal = MealEntry(name=req.name, calories=req.calories, macros=macros, meal_type=req.meal_type)
    return score_meal_quality(meal)


@router.get("/restrictions")
async def list_dietary_restrictions():
    """List available dietary restriction profiles."""
    return {"profiles": {k: {kk: vv for kk, vv in v.items()} for k, v in DIETARY_PROFILES.items()}}

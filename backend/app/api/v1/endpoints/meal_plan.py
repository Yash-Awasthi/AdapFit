"""
AI Meal Planning API endpoints.
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.services.meal_planner import meal_planner
from app.core.storage import storage

router = APIRouter()

_GOAL_ALIASES = {
    "muscle_gain": "hypertrophy",
    "weight_loss": "fat_loss",
    "maintenance": "general_fitness",
}


def _normalize_goal(goal: str) -> str:
    """Map user-facing goal names to planner templates."""
    return _GOAL_ALIASES.get(goal, goal)


class MealPlanRequest(BaseModel):
    weight_kg: float = Field(gt=30, lt=300)
    goal: str = Field(default="general_fitness", pattern="^(hypertrophy|strength|fat_loss|endurance|general_fitness|muscle_gain|weight_loss|maintenance)$")
    body_fat_pct: Optional[float] = Field(default=None, ge=5, lt=50)
    activity_level: str = Field(default="moderate", pattern="^(sedentary|light|moderate|active|very_active)$")
    dietary_restrictions: Optional[List[str]] = None
    training_day: bool = True
    recovery_score: Optional[float] = None


class AnalyzeMealRequest(BaseModel):
    foods: List[Dict[str, Any]]
    weight_kg: float = Field(default=75, gt=30, lt=300)


class PostWorkoutRequest(BaseModel):
    workout_type: str = "general"
    workout_duration_min: int = 45
    weight_kg: float = Field(gt=30, lt=300)
    goal: str = "general_fitness"


class FoodSwapRequest(BaseModel):
    food_id: str
    restrictions: Optional[List[str]] = None


@router.post("/generate")
async def generate_meal_plan(req: MealPlanRequest, user_id: str = Query("default")):
    """Generate a personalized daily meal plan and save it as the user's current plan."""
    goal = _normalize_goal(req.goal)
    plan = meal_planner.generate_day_plan(
        weight_kg=req.weight_kg,
        goal=goal,
        body_fat_pct=req.body_fat_pct,
        activity_level=req.activity_level,
        dietary_restrictions=req.dietary_restrictions,
        training_day=req.training_day,
        recovery_score=req.recovery_score,
    )
    await storage.save_diet_plan(user_id, plan)
    return plan


@router.post("/targets")
async def calculate_targets(req: MealPlanRequest):
    """Calculate daily macro and calorie targets."""
    return meal_planner.calculate_targets(
        req.weight_kg, _normalize_goal(req.goal), req.body_fat_pct, req.activity_level
    )


@router.post("/analyze")
async def analyze_meal(req: AnalyzeMealRequest):
    """Analyze nutritional content of a meal."""
    return meal_planner.analyze_meal(req.foods, req.weight_kg)


@router.post("/post-workout")
async def post_workout_suggestion(req: PostWorkoutRequest):
    """Get post-workout nutrition suggestions."""
    return meal_planner.suggest_post_workout(
        req.workout_type, req.workout_duration_min, req.weight_kg, req.goal
    )


@router.post("/swap")
async def swap_food(req: FoodSwapRequest):
    """Suggest food alternatives."""
    return meal_planner.swap_food(req.food_id, restrictions=req.restrictions)


@router.get("/current")
async def get_current_plan(user_id: str = Query("default")):
    """Get the most recently generated (AI or manual) day plan for a user, if any."""
    plan = await storage.get_diet_plan(user_id)
    return plan or {}


@router.get("/foods")
async def list_foods(category: Optional[str] = None):
    """List available foods in the database."""
    return {"foods": meal_planner.get_food_database(category), "count": len(meal_planner.get_food_database(category))}


@router.get("/status")
async def get_meal_plan_status():
    return meal_planner.get_status()

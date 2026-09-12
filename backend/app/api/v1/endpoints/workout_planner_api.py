"""
AI Workout Planner API — personalized workout and nutrition plan generation.
"""
from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"


class FitnessGoal(str, Enum):
    MAINTENANCE = "maintenance"
    WEIGHT_LOSS = "weight_loss"
    MUSCLE_GAIN = "muscle_gain"
    STRENGTH = "strength"
    ENDURANCE = "endurance"


class ExperienceLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class UserProfileRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    age: int = Field(ge=10, le=120, default=30)
    weight_kg: float = Field(ge=20, le=300, default=70.0)
    height_cm: float = Field(ge=100, le=250, default=170.0)
    sex: str = Field(default="male", pattern=r"^(male|female|other)$")
    activity_level: ActivityLevel = ActivityLevel.MODERATE
    fitness_goal: FitnessGoal = FitnessGoal.MAINTENANCE
    workout_frequency: int = Field(ge=1, le=7, default=3)
    equipment: list[str] = Field(default_factory=lambda: ["barbell", "dumbbells", "pull_up_bar", "bench"], max_length=20)
    injuries: list[str] = Field(default_factory=list, max_length=10)
    experience_level: ExperienceLevel = ExperienceLevel.INTERMEDIATE


@lru_cache(maxsize=1)
def _get_generator():
    from src.planner.fitness_planner import FitnessPlanGenerator
    return FitnessPlanGenerator()


@router.post("/generate-plan", summary="Generate a complete weekly fitness plan")
async def generate_plan(req: UserProfileRequest) -> dict[str, Any]:
    from src.planner.fitness_planner import UserProfile
    generator = _get_generator()
    profile = UserProfile(
        user_id=req.user_id, age=req.age, weight_kg=req.weight_kg,
        height_cm=req.height_cm, sex=req.sex,
        activity_level=req.activity_level, fitness_goal=req.fitness_goal,
        workout_frequency=req.workout_frequency, equipment=req.equipment,
        injuries=req.injuries, experience_level=req.experience_level,
    )
    try:
        plan = generator.generate_weekly_plan(profile)
        nutrition = generator.calculate_macros(profile)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "user_id": plan.user_id,
        "generated_at": plan.generated_at.isoformat(),
        "workouts": [
            {"name": w.name, "focus": w.focus,
             "exercises": [{"name": e.name, "sets": e.sets, "reps": e.reps, "category": e.category} for e in w.exercises]}
            for w in plan.workouts
        ],
        "nutrition": {
            "calories": nutrition.calories, "protein_g": nutrition.protein_g,
            "carbs_g": nutrition.carbs_g, "fat_g": nutrition.fat_g,
            "fiber_g": nutrition.fiber_g, "water_ml": nutrition.water_ml,
        },
        "notes": plan.notes,
    }


@router.post("/calculate-macros", summary="Calculate macro targets from user profile")
async def calculate_macros(req: UserProfileRequest) -> dict[str, Any]:
    from src.planner.fitness_planner import UserProfile
    generator = _get_generator()
    profile = UserProfile(
        user_id=req.user_id, age=req.age, weight_kg=req.weight_kg,
        height_cm=req.height_cm, sex=req.sex,
        activity_level=req.activity_level, fitness_goal=req.fitness_goal,
    )
    try:
        nutrition = generator.calculate_macros(profile)
        tdee = generator.calculate_tdee(profile)
    except (ValueError, ZeroDivisionError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "tdee": round(tdee), "target_calories": nutrition.calories,
        "protein_g": nutrition.protein_g, "carbs_g": nutrition.carbs_g, "fat_g": nutrition.fat_g,
    }

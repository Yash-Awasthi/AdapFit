"""
Workout Plan API — generates personalized training plans.

POST /workout-plans/generate  — generate a plan from user profile
GET  /workout-plans/recovery  — get today's recovery score
POST /workout-plans/nutrition  — analyze a meal
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(
    tags=["Workout Plans & Recovery"],
    responses={
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"},
    },
)


class UserProfileRequest(BaseModel):
    experience_level: int = 5
    age: int = 25
    weight_kg: float = 70.0
    height_cm: float = 175.0
    injuries: List[str] = []
    available_equipment: List[str] = ["barbell", "dumbbells", "pull_up_bar"]
    max_sessions_per_week: int = 4
    max_minutes_per_session: int = 60
    training_goal: str = "hypertrophy"
    duration_weeks: int = 12


class NutritionRequest(BaseModel):
    foods: List[dict]  # [{"name": "chicken_breast", "servings": 2.0}]


@router.post(
    "/generate",
    summary="Generate a personalized workout plan",
    description="Creates a periodized training plan based on user profile, experience, goals, and available equipment. Includes progressive overload, deload weeks, and exercise substitutions.",
    response_model=dict,
    responses={
        200: {
            "description": "Generated workout plan",
            "content": {
                "application/json": {
                    "example": {
                        "name": "Hypertrophy 12-Week Program",
                        "goal": "hypertrophy",
                        "duration_weeks": 12,
                        "sessions_per_week": 4,
                        "periodization": "linear",
                        "weeks_count": 12,
                        "deload_frequency": 4,
                    }
                }
            },
        }
    },
)
async def generate_workout_plan(profile: UserProfileRequest):
    """Generate a personalized workout plan."""
    try:
        from app.services.workout_plan_generator import (
            WorkoutPlanGenerator, UserProfile, TrainingGoal,
            Equipment,
        )

        goal_map = {
            "strength": TrainingGoal.STRENGTH,
            "hypertrophy": TrainingGoal.HYPERTROPHY,
            "endurance": TrainingGoal.ENDURANCE,
            "power": TrainingGoal.POWER,
            "fat_loss": TrainingGoal.FAT_LOSS,
            "maintenance": TrainingGoal.MAINTENANCE,
        }

        equipment_map = {
            "bodyweight": Equipment.BODYWEIGHT,
            "dumbbells": Equipment.DUMBBELLS,
            "barbell": Equipment.BARBELL,
            "cables": Equipment.CABLES,
            "resistance_bands": Equipment.RESISTANCE_BANDS,
            "kettlebell": Equipment.KETTLEBELL,
            "machine": Equipment.MACHINE,
            "pull_up_bar": Equipment.PULL_UP_BAR,
        }

        user = UserProfile(
            experience_level=profile.experience_level,
            age=profile.age,
            weight_kg=profile.weight_kg,
            height_cm=profile.height_cm,
            injuries=profile.injuries,
            available_equipment=[equipment_map.get(e, Equipment.BODYWEIGHT) for e in profile.available_equipment],
            max_sessions_per_week=profile.max_sessions_per_week,
            max_minutes_per_session=profile.max_minutes_per_session,
            training_goal=goal_map.get(profile.training_goal, TrainingGoal.HYPERTROPHY),
            current_1rm={},
        )

        generator = WorkoutPlanGenerator()
        plan = generator.generate_plan(user, weeks=profile.duration_weeks)

        return {
            "name": plan.name,
            "goal": plan.goal.value,
            "duration_weeks": plan.duration_weeks,
            "sessions_per_week": plan.sessions_per_week,
            "periodization": plan.periodization.value,
            "weeks_count": len(plan.weeks),
            "deload_frequency": plan.deload_frequency,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/recovery",
    summary="Get today's recovery score",
    description="Calculates HRV-based recovery score from latest wearable data. Returns readiness level, training recommendations, and trend analysis.",
    responses={
        200: {
            "description": "Recovery score and recommendations",
            "content": {
                "application/json": {
                    "example": {
                        "recovery_score": 78.5,
                        "readiness": "good",
                        "recommendation": "moderate",
                        "trend": "improving",
                        "max_intensity": 0.85,
                        "volume_multiplier": 1.0,
                        "notes": "Good recovery. Resume normal training.",
                        "factors": {"hrv": 85, "sleep": 70, "resting_hr": 75},
                    }
                }
            },
        }
    },
)
async def get_recovery_score():
    """Get today's HRV-based recovery score."""
    try:
        from app.services.hrv_recovery_scorer import HRVRecoveryScorer
        from datetime import datetime

        scorer = HRVRecoveryScorer()
        report = scorer.calculate_recovery(datetime.now().strftime("%Y-%m-%d"))

        return {
            "recovery_score": report.recovery_score,
            "readiness": report.readiness.value,
            "recommendation": report.recommendation.value,
            "trend": report.trend,
            "max_intensity": report.suggested_max_intensity,
            "volume_multiplier": report.suggested_volume_multiplier,
            "notes": report.notes,
            "factors": report.factors,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/nutrition",
    summary="Analyze meal nutritional content",
    description="Analyzes a list of food items and returns detailed macro/micronutrient breakdown with percentage composition.",
    responses={
        200: {
            "description": "Nutritional analysis",
            "content": {
                "application/json": {
                    "example": {
                        "calories": 520.0,
                        "protein_g": 45.0,
                        "carbs_g": 48.0,
                        "fat_g": 15.0,
                        "fiber_g": 6.0,
                        "macro_breakdown": {
                            "protein_pct": 34.6,
                            "carbs_pct": 36.9,
                            "fat_pct": 26.0,
                        },
                    }
                }
            },
        }
    },
)
async def analyze_nutrition(request: NutritionRequest):
    """Analyze a meal's nutritional content."""
    try:
        from app.services.nutrition_analyzer import (
            NutritionAnalyzer, FOOD_DATABASE,
        )

        analyzer = NutritionAnalyzer()
        foods = []

        for item in request.foods:
            food_name = item.get("name", "")
            servings = item.get("servings", 1.0)
            if food_name in FOOD_DATABASE:
                foods.append((FOOD_DATABASE[food_name], servings))

        nutrients = analyzer.analyze_meal(foods)

        return {
            "calories": round(nutrients.calories, 1),
            "protein_g": round(nutrients.protein_g, 1),
            "carbs_g": round(nutrients.carbs_g, 1),
            "fat_g": round(nutrients.fat_g, 1),
            "fiber_g": round(nutrients.fiber_g, 1),
            "macro_breakdown": {
                "protein_pct": round(nutrients.protein_g * 4 / max(nutrients.calories, 1) * 100, 1),
                "carbs_pct": round(nutrients.carbs_g * 4 / max(nutrients.calories, 1) * 100, 1),
                "fat_pct": round(nutrients.fat_g * 9 / max(nutrients.calories, 1) * 100, 1),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

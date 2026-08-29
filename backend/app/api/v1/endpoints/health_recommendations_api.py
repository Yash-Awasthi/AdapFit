"""
Health Recommendations API — Contextual, Explainable Recommendations

Provides personalized health recommendations based on multi-domain data analysis.
Every recommendation includes rationale, data sources, and action links.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
from app.services.health_recommendations import recommendations_engine
from app.core.dependencies import require_user, get_user_id

router = APIRouter()


class RecommendationRequest(BaseModel):
    """Request body for generating personalized recommendations."""
    recovery_score: Optional[float] = Field(None, ge=0, le=100)
    hrv_rmssd: Optional[float] = Field(None, ge=0, le=200)
    resting_hr: Optional[float] = Field(None, ge=30, le=150)
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    sleep_quality: Optional[float] = Field(None, ge=0, le=100)
    steps_today: Optional[int] = Field(None, ge=0)
    active_minutes: Optional[int] = Field(None, ge=0)
    calories_consumed: Optional[float] = Field(None, ge=0)
    water_ml: Optional[int] = Field(None, ge=0)
    water_goal_ml: int = 2000
    stress_score: Optional[float] = Field(None, ge=0, le=100)
    mood_score: Optional[float] = Field(None, ge=1, le=10)
    training_load_today: Optional[float] = Field(None, ge=0)
    acwr: Optional[float] = Field(None, ge=0, le=5)
    sedentary_hours: Optional[float] = Field(None, ge=0)
    screen_time_hours: Optional[float] = Field(None, ge=0)
    medications_taken: Optional[bool] = None
    health_conditions: Optional[list[str]] = None
    fitness_level: str = "intermediate"


class DismissRequest(BaseModel):
    recommendation_id: str


@router.post("/generate")
async def generate_recommendations(request: RecommendationRequest, user: dict = Depends(require_user)):
    """
    Generate personalized health recommendations based on current data.
    
    Provide as much data as you have — the engine will generate
    relevant recommendations for whatever data is available.
    """
    recs = recommendations_engine.generate_recommendations(
        user_id=user["id"],
        recovery_score=request.recovery_score,
        hrv_rmssd=request.hrv_rmssd,
        resting_hr=request.resting_hr,
        sleep_hours=request.sleep_hours,
        sleep_quality=request.sleep_quality,
        steps_today=request.steps_today,
        active_minutes=request.active_minutes,
        calories_consumed=request.calories_consumed,
        water_ml=request.water_ml,
        water_goal_ml=request.water_goal_ml,
        stress_score=request.stress_score,
        mood_score=request.mood_score,
        training_load_today=request.training_load_today,
        acwr=request.acwr,
        sedentary_hours=request.sedentary_hours,
        screen_time_hours=request.screen_time_hours,
        medications_taken=request.medications_taken,
        health_conditions=request.health_conditions,
        fitness_level=request.fitness_level,
    )
    return {
        "user_id": user["id"],
        "recommendations": recs,
        "count": len(recs),
        "high_priority": sum(1 for r in recs if r["priority"] == "high"),
    }


@router.post("/quick")
async def quick_recommendations(user: dict = Depends(require_user)):
    """
    Generate recommendations with just a user ID — uses whatever data is available
    from the storage layer (recovery logs, hydration, sleep, etc.).
    """
    from app.core.storage import storage

    # Pull latest data from storage
    recovery_logs = await storage.get_recovery_logs(user["id"], days=1)
    sleep_logs = await storage.get_sleep_logs(user["id"], days=1)

    kwargs = {"user_id": user["id"]}

    if recovery_logs:
        latest = recovery_logs[-1]
        kwargs["recovery_score"] = latest.get("recovery_score", latest.get("score"))
        wd = latest.get("wearable_data", {})
        if wd.get("hrv_rmssd"):
            kwargs["hrv_rmssd"] = wd["hrv_rmssd"]

    if sleep_logs:
        latest_sleep = sleep_logs[-1]
        kwargs["sleep_hours"] = latest_sleep.get("wearable_data", {}).get("sleep_duration_hours")
        kwargs["sleep_quality"] = latest_sleep.get("sleep_score")

    # Add time-based recommendations
    import time
    kwargs["current_hour"] = time.localtime().tm_hour

    recs = recommendations_engine.generate_recommendations(**kwargs)
    return {
        "user_id": user["id"],
        "recommendations": recs,
        "count": len(recs),
    }


@router.post("/dismiss")
async def dismiss_recommendation(request: DismissRequest, user: dict = Depends(require_user)):
    """Dismiss a recommendation so it won't appear again."""
    return recommendations_engine.dismiss_recommendation(user["id"], request.recommendation_id)


@router.get("/categories")
async def get_recommendation_categories():
    """List all recommendation categories."""
    return {
        "categories": [
            {"id": "recovery", "name": "Recovery", "icon": "meditation", "description": "Rest and recovery recommendations"},
            {"id": "activity", "name": "Activity", "icon": "fitness", "description": "Movement and exercise recommendations"},
            {"id": "nutrition", "name": "Nutrition", "icon": "nutrition", "description": "Meal and calorie recommendations"},
            {"id": "sleep", "name": "Sleep", "icon": "moon", "description": "Sleep quality and schedule recommendations"},
            {"id": "mental", "name": "Mental Health", "icon": "leaf", "description": "Stress and mood recommendations"},
            {"id": "hydration", "name": "Hydration", "icon": "water", "description": "Water intake recommendations"},
            {"id": "education", "name": "Learning", "icon": "bulb", "description": "Health education and tips"},
            {"id": "medication", "name": "Medication", "icon": "medical", "description": "Medication adherence reminders"},
        ]
    }

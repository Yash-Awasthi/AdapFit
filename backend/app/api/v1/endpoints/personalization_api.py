"""
Personalization API — AI-Driven Hyper-Personalization
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.personalization_engine import personalization_engine

router = APIRouter()


class ProfileUpdateRequest(BaseModel):
    fitness_level: Optional[str] = None
    goals: Optional[list[str]] = None
    preferred_workout_time: Optional[str] = None
    preferred_workout_duration: Optional[int] = None
    equipment_available: Optional[list[str]] = None
    health_conditions: Optional[list[str]] = None
    notification_preference: Optional[str] = None


class BehaviorEventRequest(BaseModel):
    event_type: str
    data: dict = {}


@router.post("/profile")
async def update_profile(request: ProfileUpdateRequest):
    """Create or update user profile for personalization."""
    data = {k: v for k, v in request.model_dump().items() if v is not None}
    return personalization_engine.create_or_update_profile("default", data)


@router.post("/behavior")
async def record_behavior(request: BehaviorEventRequest):
    """Record a user behavior event for learning."""
    return personalization_engine.record_behavior("default", request.event_type, request.data)


@router.get("/recommendations")
async def get_recommendations(hour_of_day: Optional[int] = None, stress_level: Optional[float] = None,
                               sleep_quality: Optional[float] = None):
    """Get comprehensive personalized recommendations."""
    context = {}
    if hour_of_day is not None:
        context["hour_of_day"] = hour_of_day
    if stress_level is not None:
        context["stress_level"] = stress_level
    if sleep_quality is not None:
        context["sleep_quality"] = sleep_quality
    
    return personalization_engine.get_personalized_recommendations("default", context)


@router.get("/optimal-workout-time")
async def get_optimal_workout_time():
    """Get the optimal time for user to work out."""
    return personalization_engine.get_optimal_workout_time("default")


@router.get("/notification-optimization")
async def get_notification_optimization():
    """Get optimized notification timing."""
    return personalization_engine.get_notification_optimization("default")


@router.get("/insights")
async def get_insights():
    """Get cross-feature personalized insights."""
    insights = personalization_engine.get_cross_feature_insights("default")
    return {
        "insights": [
            {
                "category": i.category,
                "title": i.title,
                "detail": i.detail,
                "confidence": i.confidence,
                "action": i.action,
                "priority": i.priority,
            }
            for i in insights
        ]
    }


@router.get("/analytics")
async def get_analytics():
    """Get user analytics and behavioral patterns."""
    return personalization_engine.get_user_analytics("default")

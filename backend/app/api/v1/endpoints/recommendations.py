"""Smart workout recommendations based on recovery, history, and goals."""
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from app.services.recommendation_engine_v2 import recommend_workout, UserProfile, WorkoutRecommendation

router = APIRouter()


class RecommendationRequest(BaseModel):
    recovery_score: int = Field(ge=0, le=100, default=50)
    readiness_state: str = Field(default="MODERATE")
    fitness_level: str = Field(default="intermediate")
    primary_goal: str = Field(default="hypertrophy")
    preferred_days_per_week: int = Field(ge=1, le=7, default=4)
    sore_muscles: List[str] = Field(default_factory=list)
    acwr: float = Field(ge=0.1, le=3.0, default=1.0)
    sleep_score: float = Field(ge=0, le=100, default=80)
    days_since_last_workout: int = Field(ge=0, le=30, default=1)
    equipment_access: List[str] = Field(default=["bodyweight", "dumbbells", "barbell"])


@router.post("", response_model=WorkoutRecommendation)
async def get_recommendation(request: RecommendationRequest, user_id: str = Query("default")):
    """Get a smart workout recommendation based on current state."""
    # Try to enrich with real data
    try:
        from app.core.storage import storage
        recovery_logs = await storage.get_recovery_logs(user_id, 7)
        workout_logs = await storage.get_workout_logs(user_id, 14)

        if recovery_logs:
            last = recovery_logs[-1]
            request.recovery_score = last.get("recovery_score", request.recovery_score)
            request.readiness_state = last.get("readiness_state", request.readiness_state)
            mb = last.get("metrics_breakdown", {})
            if mb.get("acwr"):
                request.acwr = mb["acwr"]
    except Exception:
        pass

    # Build training history
    history = {}
    for wl in (workout_logs if 'workout_logs' in dir() else []):
        for ex in wl.get("logged_exercises", []):
            muscle = ex.get("target_muscle", "")
            if muscle:
                history.setdefault(muscle, {"volume_7d": 0, "sessions_14d": 0})
                history[muscle]["volume_7d"] += ex.get("weight_kg", 0) * ex.get("reps_completed", 0)
                history[muscle]["sessions_14d"] += 1

    profile = UserProfile(
        recovery_score=request.recovery_score,
        readiness_state=request.readiness_state,
        fitness_level=request.fitness_level,
        primary_goal=request.primary_goal,
        preferred_days_per_week=request.preferred_days_per_week,
        sore_muscles=request.sore_muscles,
        acwr=request.acwr,
        sleep_score=request.sleep_score,
        days_since_last_workout=request.days_since_last_workout,
        equipment_access=request.equipment_access,
        training_history=history,
    )

    return recommend_workout(profile)


@router.get("/quick")
async def quick_recommendation(user_id: str = Query("default")):
    """Quick recommendation with auto-detected state."""
    profile = UserProfile()
    try:
        from app.core.storage import storage
        recovery_logs = await storage.get_recovery_logs(user_id, 1)
        if recovery_logs:
            last = recovery_logs[-1]
            profile.recovery_score = last.get("recovery_score", 50)
            profile.readiness_state = last.get("readiness_state", "MODERATE")
    except Exception:
        pass

    return recommend_workout(profile)


@router.get("/today")
async def todays_recommendation(user_id: str = Query("default")):
    """Get today's workout recommendation with context."""
    rec = await quick_recommendation(user_id)
    return {
        "recommendation": rec.model_dump(),
        "tips": [
            "Always warm up before training",
            "Stay hydrated during your workout",
            "Focus on form over weight",
        ],
    }

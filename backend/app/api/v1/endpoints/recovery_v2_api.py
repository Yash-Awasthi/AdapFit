"""
Recovery Engine V2 API — Cross-Domain Recovery Intelligence

Combines sleep, HRV, training load, subjective wellness, nutrition,
and heart rate into explainable recovery scores and recommendations.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
from app.services.recovery_engine_v2 import recovery_engine_v2, RecoveryInput
from app.core.dependencies import require_user

router = APIRouter()


class RecoveryCalculationRequest(BaseModel):
    """All recovery inputs — provide whatever data is available."""
    # Sleep
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    sleep_quality: Optional[float] = Field(None, ge=0, le=100)
    deep_sleep_pct: Optional[float] = Field(None, ge=0, le=100)
    sleep_consistency: Optional[float] = Field(None, ge=0, le=100)

    # Heart Rate
    hrv_rmssd: Optional[float] = Field(None, ge=0, le=200)
    resting_hr: Optional[float] = Field(None, ge=30, le=150)
    resting_hr_trend: Optional[str] = Field(None, description="rising, stable, falling")

    # Training
    training_load_today: Optional[float] = Field(None, ge=0)
    acwr: Optional[float] = Field(None, ge=0, le=5)
    session_rpe: Optional[float] = Field(None, ge=1, le=10)
    days_since_rest: Optional[int] = Field(None, ge=0, le=30)

    # Subjective
    fatigue_level: Optional[float] = Field(None, ge=1, le=10)
    mood_score: Optional[float] = Field(None, ge=1, le=10)
    stress_level: Optional[float] = Field(None, ge=0, le=100)

    # Nutrition
    calories_consumed: Optional[float] = Field(None, ge=0)
    water_ml: Optional[int] = Field(None, ge=0)
    protein_g: Optional[float] = Field(None, ge=0)

    # Context
    age: Optional[int] = Field(None, ge=10, le=120)
    fitness_level: str = "intermediate"
    training_goal: str = "general_fitness"


@router.post("/calculate")
async def calculate_recovery(request: RecoveryCalculationRequest, user: dict = Depends(require_user)):
    """
    Calculate comprehensive recovery score with cross-domain insights.

    Provide as much data as you have — the engine generates relevant
    insights from whatever data is available.
    """
    data = RecoveryInput(
        sleep_hours=request.sleep_hours,
        sleep_quality=request.sleep_quality,
        deep_sleep_pct=request.deep_sleep_pct,
        sleep_consistency=request.sleep_consistency,
        hrv_rmssd=request.hrv_rmssd,
        resting_hr=request.resting_hr,
        resting_hr_trend=request.resting_hr_trend,
        training_load_today=request.training_load_today,
        acwr=request.acwr,
        session_rpe=request.session_rpe,
        days_since_rest=request.days_since_rest,
        fatigue_level=request.fatigue_level,
        mood_score=request.mood_score,
        stress_level=request.stress_level,
        calories_consumed=request.calories_consumed,
        water_ml=request.water_ml,
        protein_g=request.protein_g,
        age=request.age,
        fitness_level=request.fitness_level,
        training_goal=request.training_goal,
    )

    result = recovery_engine_v2.calculate_recovery(data)
    result_dict = recovery_engine_v2.result_to_dict(result)
    result_dict["user_id"] = user["id"]
    return result_dict


@router.get("/quick")
async def quick_recovery(user: dict = Depends(require_user)):
    """Quick recovery calculation from stored data."""
    from app.core.storage import storage
    from app.services.recovery_engine_v2 import RecoveryInput

    logs = await storage.get_recovery_logs(user["id"], days=1)
    data = RecoveryInput()

    if logs:
        latest = logs[-1]
        wd = latest.get("wearable_data", {})
        if wd.get("hrv_rmssd"):
            data.hrv_rmssd = wd["hrv_rmssd"]
        if wd.get("resting_hr"):
            data.resting_hr = wd["resting_hr"]
        if wd.get("sleep_duration_hours"):
            data.sleep_hours = wd["sleep_duration_hours"]
        if latest.get("sleep_score"):
            data.sleep_quality = latest["sleep_score"]

    data.fatigue_level = latest.get("fatigue_level") if logs else None
    data.mood_score = latest.get("mood_score") if logs else None

    result = recovery_engine_v2.calculate_recovery(data)
    result_dict = recovery_engine_v2.result_to_dict(result)
    result_dict["user_id"] = user["id"]
    return result_dict


@router.get("/domains")
async def get_domain_info():
    """Get information about recovery domains and their weights."""
    return {
        "domains": [
            {"name": "sleep", "weight": 0.25, "description": "Sleep quality, duration, and consistency"},
            {"name": "hrv", "weight": 0.20, "description": "Heart rate variability (RMSSD)"},
            {"name": "training_load", "weight": 0.20, "description": "Acute:chronic workload ratio and training stress"},
            {"name": "subjective", "weight": 0.15, "description": "Self-reported fatigue, mood, and stress"},
            {"name": "nutrition", "weight": 0.10, "description": "Hydration, calories, and protein intake"},
            {"name": "heart_rate", "weight": 0.10, "description": "Resting heart rate and trends"},
        ]
    }

"""
Stress Management API — Assessment, Breathing, PMR & Interventions
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from app.services.stress_engine import stress_engine

router = APIRouter()


class StressAssessRequest(BaseModel):
    hrv_rmssd: Optional[float] = 45.0
    resting_hr: Optional[float] = 65.0
    sleep_quality: Optional[float] = 70.0
    sleep_hours: Optional[float] = 7.0
    activity_minutes_today: Optional[int] = 30
    mood_score: Optional[float] = 5.0
    energy_level: Optional[float] = 5.0
    self_reported_stress: Optional[float] = None
    screen_time_hours: Optional[float] = None
    meeting_hours: Optional[float] = None
    camera_fatigue_score: Optional[float] = None
    last_break_minutes_ago: Optional[int] = None


class StressLogRequest(BaseModel):
    level: float = Field(ge=0, le=100)
    category: str = "physical"
    notes: str = ""


@router.post("/assess")
async def assess_stress(request: StressAssessRequest):
    """Multi-factor stress assessment using biometric and behavioral data."""
    result = stress_engine.assess_stress(request.model_dump(exclude_none=True))
    return {
        "overall_score": result.overall_score,
        "category_scores": result.category_scores,
        "primary_category": result.primary_category.value,
        "trend": result.trend,
        "recommendations": result.recommendations,
        "intervention_priority": result.intervention_priority.value,
        "cortisol_phase": result.cortisol_phase,
        "recovery_estimate_minutes": result.recovery_estimate_minutes,
        "confidence": result.confidence,
    }


@router.post("/log")
async def log_stress(request: StressLogRequest):
    """Log a manual stress entry."""
    return stress_engine.log_stress_entry(request.level, request.category, request.notes)


@router.get("/breathing-exercises")
async def get_breathing_exercise(stress_level: float = 50, time_of_day: int = 12):
    """Get recommended breathing exercise based on current state."""
    exercise = stress_engine.get_breathing_exercise(stress_level, time_of_day)
    return {
        "name": exercise.name,
        "technique": exercise.technique,
        "inhale_seconds": exercise.inhale_seconds,
        "hold_seconds": exercise.hold_seconds,
        "exhale_seconds": exercise.exhale_seconds,
        "hold_after_exhale": exercise.hold_after_exhale,
        "cycles": exercise.cycles,
        "description": exercise.description,
        "best_for": exercise.best_for,
        "difficulty": exercise.difficulty,
        "total_duration_seconds": (exercise.inhale_seconds + exercise.hold_seconds + exercise.exhale_seconds + exercise.hold_after_exhale) * exercise.cycles,
    }


@router.get("/pmr")
async def get_pmr_script():
    """Get progressive muscle relaxation script."""
    return stress_engine.get_pmr_script()


@router.get("/micro-breaks")
async def get_micro_breaks(screen_time_minutes: int = 60, last_break_minutes: int = 30):
    """Get micro-break recommendations based on usage patterns."""
    breaks = stress_engine.get_micro_break_schedule(screen_time_minutes, last_break_minutes)
    return {
        "breaks": [
            {
                "activity": b.activity,
                "duration_minutes": b.duration_minutes,
                "reason": b.reason,
                "stress_reduction_expected": b.stress_reduction_expected,
            }
            for b in breaks
        ]
    }


@router.get("/trends")
async def get_stress_trends(days: int = 7):
    """Get stress trends over time."""
    return stress_engine.get_stress_trends(days)


@router.get("/interventions")
async def get_intervention_effectiveness():
    """Get effectiveness of different stress interventions."""
    return stress_engine.get_intervention_effectiveness()

"""Recovery and training readiness endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.recovery_detection import (
    DailyRecoveryData, compute_recovery_score, training_readiness,
    compute_acwr, full_recovery_assessment,
)

router = APIRouter()


class RecoveryDataInput(BaseModel):
    date: str
    hrv_rmssd: Optional[float] = None
    resting_hr: Optional[int] = None
    sleep_quality: Optional[float] = None
    sleep_hours: Optional[float] = None
    subjective_readiness: Optional[int] = None
    steps: Optional[int] = None
    active_minutes: Optional[int] = None
    calories_burned: Optional[int] = None
    workout_strain: Optional[float] = None


class StrainEntry(BaseModel):
    date: str
    strain: float


@router.post("/recovery/score")
def recovery_score(body: dict):
    """Compute weighted recovery score."""
    today = DailyRecoveryData(**body["today"])
    history = [DailyRecoveryData(**d) for d in body.get("history", [])]
    window = body.get("window_days", 7)
    return compute_recovery_score(today, history, window)


@router.post("/recovery/readiness")
def readiness(body: dict):
    """Sport-specific training readiness."""
    today = DailyRecoveryData(**body["today"])
    history = [DailyRecoveryData(**d) for d in body.get("history", [])]
    sport = body.get("sport", "general")
    return training_readiness(today, history, sport)


@router.post("/recovery/acwr")
def acwr(body: dict):
    """Acute:Chronic Workload Ratio."""
    strain = body.get("daily_strain", [])
    acute = body.get("acute_window", 7)
    chronic = body.get("chronic_window", 28)
    return compute_acwr(strain, acute, chronic)


@router.post("/recovery/full")
def full_assessment(body: dict):
    """Complete recovery + readiness + ACWR assessment."""
    today = DailyRecoveryData(**body["today"])
    history = [DailyRecoveryData(**d) for d in body.get("history", [])]
    sport = body.get("sport", "general")
    strain = body.get("daily_strain")
    return full_recovery_assessment(today, history, sport, strain)

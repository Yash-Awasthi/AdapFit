"""
Injury Risk Detection API — ACWR-based injury risk assessment.
"""
from __future__ import annotations

from datetime import datetime
from functools import lru_cache

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


# --- Response Models ---

class RiskFactor(BaseModel):
    name: str
    value: float
    explanation: str


class RiskAssessmentResponse(BaseModel):
    overall_risk: float = Field(ge=0, le=1)
    risk_level: str
    acwr: float
    risk_factors: list[RiskFactor]
    recommendations: list[str]
    summary: str


# --- Input Validation ---

VALID_MUSCLES = {
    "quadriceps", "hamstrings", "glutes", "calves", "hip_flexors",
    "adductors", "abductors", "core", "chest", "back",
    "shoulders", "biceps", "triceps", "forearms", "neck",
}

VALID_DOSE_STATUSES = {"taken", "missed", "skipped"}


class TrainingDayModel(BaseModel):
    date: str = Field(description="ISO format date")
    duration_min: float = Field(ge=0, le=600)
    intensity_rpe: float = Field(ge=1, le=10)
    volume_load: float = Field(ge=0)
    muscles_worked: list[str] = Field(default_factory=list, max_length=20)


class RecoveryDayModel(BaseModel):
    date: str
    sleep_hours: float = Field(ge=0, le=24)
    sleep_quality: float = Field(ge=0, le=1, default=0.8)
    hrv_rmssd: float | None = Field(default=None, ge=0)
    soreness_score: float = Field(ge=0, le=10, default=3.0)
    stress_level: float = Field(ge=0, le=10, default=3.0)
    hydration_pct: float = Field(ge=0, le=2, default=1.0)


class RiskAssessmentRequest(BaseModel):
    training_days: list[TrainingDayModel] = Field(min_length=1, max_length=365)
    recovery_days: list[RecoveryDayModel] = Field(default_factory=list, max_length=365)


# --- Cached singleton ---

@lru_cache(maxsize=1)
def _get_detector():
    from src.injury.risk_detector import InjuryRiskDetector
    return InjuryRiskDetector()


# --- Routes ---

@router.post(
    "/assess",
    response_model=RiskAssessmentResponse,
    summary="Assess injury risk from training and recovery data",
)
async def assess_risk(req: RiskAssessmentRequest) -> RiskAssessmentResponse:
    """Compute ACWR, identify risk factors, and generate recommendations."""
    from src.injury.risk_detector import TrainingDay, RecoveryDay, MuscleGroup

    detector = _get_detector()
    try:
        training = []
        for td in req.training_days:
            muscles = []
            for m in td.muscles_worked:
                if m in VALID_MUSCLES:
                    muscles.append(MuscleGroup(m))
            training.append(TrainingDay(
                date=datetime.fromisoformat(td.date),
                duration_min=td.duration_min,
                intensity_rpe=td.intensity_rpe,
                volume_load=td.volume_load,
                muscles_worked=muscles,
            ))

        recovery = []
        for rd in req.recovery_days:
            recovery.append(RecoveryDay(
                date=datetime.fromisoformat(rd.date),
                sleep_hours=rd.sleep_hours,
                sleep_quality=rd.sleep_quality,
                hrv_rmssd=rd.hrv_rmssd,
                soreness_score=rd.soreness_score,
                stress_level=rd.stress_level,
                hydration_pct=rd.hydration_pct,
            ))

        result = detector.assess(training, recovery)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=f"Assessment failed: {exc}") from exc

    return RiskAssessmentResponse(
        overall_risk=result.overall_risk,
        risk_level=result.risk_level.value,
        acwr=result.acwr,
        risk_factors=[
            RiskFactor(name=f.name, value=f.value, explanation=f.explanation)
            for f in result.risk_factors
        ],
        recommendations=result.recommendations,
        summary=result.summary,
    )

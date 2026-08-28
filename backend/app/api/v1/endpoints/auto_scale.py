"""TRACK 3: Auto-scaling endpoints for in-workout dynamic fatigue management."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.auto_scaler import auto_scaler, SetRecord

router = APIRouter()


class SetLogRequest(BaseModel):
    weight: float
    reps: int
    rpe: float
    exercise_id: str = ""


class AutoScaleRequest(BaseModel):
    completed_sets: list[SetLogRequest]
    target_rpe: float = 7.0
    target_reps: int = 8
    rest_seconds: int = 90


class SubstitutionRequest(BaseModel):
    exercise_id: str
    equipment: list[str] = []


@router.post("/auto-scale")
async def evaluate_auto_scale(req: AutoScaleRequest):
    """Evaluate completed sets and return scaling decisions."""
    sets = [
        SetRecord(weight=s.weight, reps=s.reps, rpe=s.rpe, exercise_id=s.exercise_id)
        for s in req.completed_sets
    ]
    result = auto_scaler.evaluate_set(
        completed_sets=sets,
        target_rpe=req.target_rpe,
        target_reps=req.target_reps,
        rest_seconds=req.rest_seconds,
    )
    return {
        "should_scale": result.should_scale,
        "confidence": result.confidence,
        "fatigue_score": result.fatigue_score,
        "summary": result.summary,
        "decisions": [
            {
                "type": d.adjustment_type,
                "description": d.description,
                "magnitude": d.magnitude,
                "original": d.original,
                "reason": d.reason,
            }
            for d in result.decisions
        ],
    }


@router.post("/substitutions")
async def get_substitutions(req: SubstitutionRequest):
    """Get exercise substitution options for a given exercise."""
    options = auto_scaler.get_substitution_options(req.exercise_id, req.equipment)
    return {"exercise_id": req.exercise_id, "substitutions": options}

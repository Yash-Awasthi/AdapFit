"""Periodization planning: multi-week mesocycle generation."""
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional
from app.services.periodization import generate_mesocycle, MesocyclePlan

router = APIRouter()


class PlanGenerateRequest(BaseModel):
    goal: str = Field(default="strength", examples=["strength", "hypertrophy", "endurance"])
    start_date: Optional[str] = Field(None, examples=["2026-09-01"])
    current_acwr: float = Field(default=1.0, ge=0.3, le=2.0)
    current_readiness: str = Field(default="MODERATE", examples=["OPTIMAL", "MODERATE", "REDUCED", "DEPLETED"])


@router.get("", response_model=MesocyclePlan)
async def get_current_plan(user_id: str = Query("default")):
    """Get a default mesocycle plan."""
    return generate_mesocycle()


@router.post("", response_model=MesocyclePlan)
async def generate_plan(request: PlanGenerateRequest, user_id: str = Query("default")):
    """Generate a periodized training plan."""
    return generate_mesocycle(
        goal=request.goal,
        start_date=request.start_date,
        current_acwr=request.current_acwr,
        current_readiness=request.current_readiness,
    )


@router.get("/available", response_model=dict)
async def available_plans():
    """List available mesocycle types."""
    return {
        "plans": [
            {"id": "strength", "name": "Strength Block", "weeks": 5, "focus": "Maximal strength development"},
            {"id": "hypertrophy", "name": "Hypertrophy Block", "weeks": 4, "focus": "Muscle growth"},
            {"id": "endurance", "name": "Endurance Block", "weeks": 5, "focus": "Aerobic capacity"},
        ]
    }

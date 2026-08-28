"""Exercise substitution endpoints — suggests alternatives for exercises."""

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional
from app.services.exercise_substitution import get_substitutions

router = APIRouter()


class SubstitutionRequest(BaseModel):
    exercise_id: str
    equipment: Optional[list[str]] = None
    max_axial_load: Optional[int] = Field(default=None, ge=1, le=5)
    difficulty: Optional[str] = Field(default=None, pattern="^(beginner|intermediate|advanced)$")


@router.post("/suggest")
async def suggest_substitutions(req: SubstitutionRequest):
    """Get exercise substitution suggestions."""
    return {
        "original_exercise": req.exercise_id,
        "substitutions": get_substitutions(
            exercise_id=req.exercise_id,
            equipment=req.equipment,
            max_axial_load=req.max_axial_load,
            difficulty=req.difficulty,
        ),
    }


@router.get("/for/{exercise_id}")
async def get_subs_for_exercise(
    exercise_id: str,
    equipment: Optional[str] = Query(None, description="Comma-separated equipment list"),
    max_axial: Optional[int] = Query(None, ge=1, le=5),
):
    """Get substitution options via GET."""
    equip_list = equipment.split(",") if equipment else None
    return {
        "original_exercise": exercise_id,
        "substitutions": get_substitutions(
            exercise_id=exercise_id,
            equipment=equip_list,
            max_axial_load=max_axial,
        ),
    }

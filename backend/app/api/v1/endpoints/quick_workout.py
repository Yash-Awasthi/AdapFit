"""Quick workout endpoints — one-tap workout generation based on time available."""

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional
from app.services.quick_workout import generate_quick_workout, QUICK_TEMPLATES

router = APIRouter()


class QuickWorkoutRequest(BaseModel):
    duration_minutes: int = Field(default=30, ge=10, le=120)
    equipment: list[str] = Field(default=["bodyweight"])
    target_muscles: Optional[list[str]] = None
    workout_type: str = Field(default="full_body", pattern="^(strength|cardio|full_body)$")


@router.post("/generate")
async def generate(req: QuickWorkoutRequest):
    """Generate a quick workout based on time available and equipment."""
    return generate_quick_workout(
        duration_minutes=req.duration_minutes,
        equipment=req.equipment,
        target_muscles=req.target_muscles,
        workout_type=req.workout_type,
    )


@router.get("/presets")
async def list_presets():
    """List pre-built quick workout templates."""
    presets = []
    for key, gen_fn in QUICK_TEMPLATES.items():
        workout = gen_fn()
        presets.append({
            "id": key,
            "name": key.replace("_", " ").title(),
            "duration_minutes": workout["duration_minutes"],
            "exercise_count": workout["exercise_count"],
            "workout_type": workout["workout_type"],
            "equipment": workout["equipment_used"],
        })
    return {"presets": presets}


@router.get("/preset/{preset_id}")
async def get_preset(preset_id: str):
    """Get a specific pre-built workout template."""
    gen_fn = QUICK_TEMPLATES.get(preset_id)
    if not gen_fn:
        return {"error": "Preset not found", "available": list(QUICK_TEMPLATES.keys())}
    return gen_fn()

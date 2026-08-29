"""
Stroke Recovery & Neurological Rehabilitation API Endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/stroke-rehab", tags=["Stroke Rehabilitation"])


class RehabPlanRequest(BaseModel):
    stroke_date: str
    affected_side: str = "right"
    deficits: List[str] = ["attention", "memory"]


class ProgressRequest(BaseModel):
    sessions: List[Dict]


class DeficitRequest(BaseModel):
    deficit_type: str
    severity: str = "moderate"


@router.post("/plan")
async def get_rehab_plan(request: RehabPlanRequest):
    """Generate personalized stroke rehabilitation plan"""
    from app.services.stroke_rehab import stroke_rehab_service
    plan = stroke_rehab_service.get_rehab_plan(
        stroke_date=request.stroke_date,
        affected_side=request.affected_side,
        deficits=request.deficits
    )
    return {"success": True, "data": plan}


@router.post("/progress")
async def assess_progress(request: ProgressRequest):
    """Analyze rehabilitation progress over time"""
    from app.services.stroke_rehab import stroke_rehab_service
    analysis = stroke_rehab_service.assess_progress(request.sessions)
    return {"success": True, "data": analysis}


@router.post("/exercises")
async def get_exercises_for_deficit(request: DeficitRequest):
    """Get targeted exercises for specific deficit"""
    from app.services.stroke_rehab import stroke_rehab_service
    exercises = stroke_rehab_service.get_exercise_for_deficit(
        deficit_type=request.deficit_type,
        severity=request.severity
    )
    return {"success": True, "data": exercises, "count": len(exercises)}


@router.get("/exercises/motor")
async def get_motor_exercises(category: Optional[str] = None):
    """Get motor rehabilitation exercises"""
    from app.services.stroke_rehab import stroke_rehab_service
    if category and category in stroke_rehab_service.motor_exercises:
        return {"success": True, "data": stroke_rehab_service.motor_exercises[category]}
    return {"success": True, "data": stroke_rehab_service.motor_exercises}


@router.get("/exercises/cognitive")
async def get_cognitive_exercises(domain: Optional[str] = None):
    """Get cognitive rehabilitation exercises"""
    from app.services.stroke_rehab import stroke_rehab_service
    if domain and domain in stroke_rehab_service.cognitive_exercises:
        return {"success": True, "data": stroke_rehab_service.cognitive_exercises[domain]}
    return {"success": True, "data": stroke_rehab_service.cognitive_exercises}


@router.get("/exercises/speech")
async def get_speech_exercises(type: Optional[str] = None):
    """Get speech therapy exercises"""
    from app.services.stroke_rehab import stroke_rehab_service
    if type and type in stroke_rehab_service.speech_exercises:
        return {"success": True, "data": stroke_rehab_service.speech_exercises[type]}
    return {"success": True, "data": stroke_rehab_service.speech_exercises}


@router.get("/fitness")
async def get_fitness_program(phase: Optional[str] = None):
    """Get fitness programs for stroke recovery"""
    from app.services.stroke_rehab import stroke_rehab_service
    return {"success": True, "data": stroke_rehab_service.fitness_programs}


@router.get("/brain-exercises")
async def get_brain_exercises():
    """Get neuroplasticity-based brain exercises"""
    from app.services.stroke_rehab import stroke_rehab_service
    return {"success": True, "data": stroke_rehab_service.brain_exercises}


@router.get("/neuroplasticity-tips")
async def get_neuroplasticity_tips():
    """Get evidence-based neuroplasticity optimization tips"""
    from app.services.stroke_rehab import stroke_rehab_service
    tips = stroke_rehab_service.get_neuroplasticity_tips()
    return {"success": True, "data": tips}


@router.get("/phases")
async def get_rehab_phases():
    """Get information about rehabilitation phases"""
    from app.services.stroke_rehab import stroke_rehab_service
    return {"success": True, "data": stroke_rehab_service.rehab_phases}

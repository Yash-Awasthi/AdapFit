"""Cognitive Training API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.cognitive_training import cognitive_training_service

router = APIRouter(prefix="/cognitive", tags=["Cognitive Training & Brain Health"])


class ProfileRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]


class ExerciseStartRequest(BaseModel):
    user_id: str
    exercise_id: str


class ExerciseCompleteRequest(BaseModel):
    user_id: str
    session_id: str
    results: Dict[str, Any]


@router.post("/profile")
async def create_profile(req: ProfileRequest):
    result = cognitive_training_service.create_profile(req.user_id, req.data)
    return {"success": True, "data": result}


@router.post("/exercise/start")
async def start_exercise(req: ExerciseStartRequest):
    result = cognitive_training_service.start_exercise(req.user_id, req.exercise_id)
    return {"success": True, "data": result}


@router.post("/exercise/complete")
async def complete_exercise(req: ExerciseCompleteRequest):
    result = cognitive_training_service.complete_exercise(req.user_id, req.session_id, req.results)
    return {"success": True, "data": result}


@router.get("/adhd-tools")
async def get_adhd_tools():
    result = cognitive_training_service.get_adhd_tools()
    return {"success": True, "data": result}


@router.get("/brain-health/{user_id}")
async def get_brain_health(user_id: str):
    result = cognitive_training_service.get_brain_health_assessment(user_id)
    return {"success": True, "data": result}


@router.get("/exercises")
async def list_exercises(category: str = ""):
    if category and category in cognitive_training_service.exercises:
        return {"success": True, "data": cognitive_training_service.exercises[category]}
    all_exercises = []
    for cat in cognitive_training_service.exercises.values():
        all_exercises.extend(cat)
    return {"success": True, "data": all_exercises}

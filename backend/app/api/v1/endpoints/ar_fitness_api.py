"""AR Fitness API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.ar_fitness import ar_fitness_service

router = APIRouter(prefix="/ar-fitness", tags=["AR Fitness Guidance"])

class SessionStartRequest(BaseModel):
    user_id: str
    exercise: str

class FrameRequest(BaseModel):
    session_id: str
    pose_data: Dict[str, Any]

@router.post("/start")
async def start_session(req: SessionStartRequest):
    result = ar_fitness_service.start_session(req.user_id, req.exercise)
    return {"success": True, "data": result}

@router.post("/frame")
async def process_frame(req: FrameRequest):
    result = ar_fitness_service.process_frame(req.session_id, req.pose_data)
    return {"success": True, "data": result}

@router.post("/end/{session_id}")
async def end_session(session_id: str):
    result = ar_fitness_service.end_session(session_id)
    return {"success": True, "data": result}

@router.get("/exercises")
async def list_exercises():
    return {"success": True, "data": ar_fitness_service.get_exercise_library()}

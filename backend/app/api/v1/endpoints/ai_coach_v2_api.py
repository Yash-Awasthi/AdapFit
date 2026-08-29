"""AI Workout Coach V2 API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.ai_workout_coach import ai_workout_coach_service

router = APIRouter(prefix="/ai-coach-v2", tags=["AI Workout Coach V2"])

class ProfileRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]

class FormAnalysisRequest(BaseModel):
    user_id: str
    exercise: str
    pose_data: Dict[str, Any]

@router.post("/profile")
async def create_profile(req: ProfileRequest):
    result = ai_workout_coach_service.create_profile(req.user_id, req.data)
    return {"success": True, "data": result}

@router.get("/plan/{user_id}")
async def generate_plan(user_id: str):
    result = ai_workout_coach_service.generate_plan(user_id)
    return {"success": True, "data": result}

@router.post("/form-check")
async def analyze_form(req: FormAnalysisRequest):
    result = ai_workout_coach_service.analyze_form(req.user_id, req.exercise, req.pose_data)
    return {"success": True, "data": result}

@router.get("/demo/{exercise}")
async def get_demo(exercise: str):
    result = ai_workout_coach_service.get_exercise_demo(exercise)
    return {"success": True, "data": result}

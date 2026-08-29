"""Senior Health API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.senior_health import senior_health_service

router = APIRouter(prefix="/senior-health", tags=["Senior Health & Aging"])


class ProfileRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]


class DailyLogRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]


@router.post("/profile")
async def create_profile(req: ProfileRequest):
    result = senior_health_service.create_profile(req.user_id, req.data)
    return {"success": True, "data": result}


@router.get("/fall-risk/{user_id}")
async def assess_fall_risk(user_id: str):
    result = senior_health_service.assess_fall_risk(user_id)
    return {"success": True, "data": result}


@router.post("/log")
async def log_daily(req: DailyLogRequest):
    result = senior_health_service.log_daily(req.user_id, req.data)
    return {"success": True, "data": result}


@router.get("/exercises/{user_id}")
async def get_exercise_program(user_id: str):
    result = senior_health_service.get_exercise_program(user_id)
    return {"success": True, "data": result}


@router.get("/cognitive/{user_id}")
async def get_cognitive_program(user_id: str):
    result = senior_health_service.get_cognitive_program(user_id)
    return {"success": True, "data": result}


@router.get("/home-safety")
async def get_home_safety():
    result = senior_health_service.get_home_safety_checklist()
    return {"success": True, "data": result}


@router.get("/social/{user_id}")
async def get_social_plan(user_id: str):
    result = senior_health_service.get_social_connection_plan(user_id)
    return {"success": True, "data": result}

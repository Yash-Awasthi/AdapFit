"""Workplace Ergonomics API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.workplace_ergonomics import workplace_ergonomics_service

router = APIRouter(prefix="/ergonomics", tags=["Workplace Ergonomics"])


class ProfileRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]


class AssessmentRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]


class BreakRequest(BaseModel):
    user_id: str
    session_id: str
    exercise_done: str = ""


@router.post("/profile")
async def create_profile(req: ProfileRequest):
    result = workplace_ergonomics_service.create_profile(req.user_id, req.data)
    return {"success": True, "data": result}


@router.post("/assess")
async def assess_setup(req: AssessmentRequest):
    result = workplace_ergonomics_service.assess_desk_setup(req.user_id, req.data)
    return {"success": True, "data": result}


@router.post("/start-sitting")
async def start_sitting(req: ProfileRequest):
    result = workplace_ergonomics_service.start_sitting_session(req.user_id)
    return {"success": True, "data": result}


@router.post("/log-break")
async def log_break(req: BreakRequest):
    result = workplace_ergonomics_service.log_break(req.user_id, req.session_id, req.exercise_done)
    return {"success": True, "data": result}


@router.get("/wellness/{user_id}")
async def get_wellness(user_id: str):
    result = workplace_ergonomics_service.get_work_wellness_score(user_id)
    return {"success": True, "data": result}


@router.get("/eye-rule")
async def get_20_20_20():
    result = workplace_ergonomics_service.get_20_20_20_timer()
    return {"success": True, "data": result}


@router.get("/exercises")
async def get_exercises():
    return {"success": True, "data": workplace_ergonomics_service.desk_exercises}


@router.get("/rsi-prevention")
async def get_rsi_prevention():
    return {"success": True, "data": workplace_ergonomics_service.rsi_prevention}

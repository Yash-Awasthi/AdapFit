"""Cardiac Rehabilitation API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.cardiac_rehab import cardiac_rehab_service

router = APIRouter(prefix="/cardiac-rehab", tags=["Cardiac Rehabilitation"])

class ProgramRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]

class DailyLogRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]

@router.post("/setup")
async def setup_program(req: ProgramRequest):
    result = cardiac_rehab_service.setup_program(req.user_id, req.data)
    return {"success": True, "data": result}

@router.post("/log")
async def log_daily(req: DailyLogRequest):
    result = cardiac_rehab_service.log_daily(req.user_id, req.data)
    return {"success": True, "data": result}

@router.get("/exercise/{user_id}")
async def get_exercise(user_id: str):
    result = cardiac_rehab_service.get_exercise_program(user_id)
    return {"success": True, "data": result}

@router.get("/diet")
async def get_diet():
    result = cardiac_rehab_service.get_diet_plan()
    return {"success": True, "data": result}

@router.get("/progress/{user_id}")
async def get_progress(user_id: str):
    result = cardiac_rehab_service.get_progress_summary(user_id)
    return {"success": True, "data": result}

@router.get("/phases")
async def get_phases():
    return {"success": True, "data": cardiac_rehab_service.phases}

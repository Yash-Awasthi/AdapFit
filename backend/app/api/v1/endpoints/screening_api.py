"""Preventive Screening API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List
from app.services.preventive_screening import preventive_screening_service

router = APIRouter(prefix="/screening", tags=["Preventive Screening"])

class ProfileRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]

class ScreeningLogRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]

@router.post("/profile")
async def create_profile(req: ProfileRequest):
    result = preventive_screening_service.create_profile(req.user_id, req.data)
    return {"success": True, "data": result}

@router.get("/schedule/{user_id}")
async def get_schedule(user_id: str):
    result = preventive_screening_service.get_screening_schedule(user_id)
    return {"success": True, "data": result}

@router.get("/cancer-risk/{user_id}")
async def assess_cancer_risk(user_id: str):
    result = preventive_screening_service.assess_cancer_risk(user_id)
    return {"success": True, "data": result}

@router.post("/log")
async def log_screening(req: ScreeningLogRequest):
    result = preventive_screening_service.log_screening(req.user_id, req.data)
    return {"success": True, "data": result}

@router.get("/guidelines")
async def get_guidelines():
    return {"success": True, "data": preventive_screening_service.screenings}

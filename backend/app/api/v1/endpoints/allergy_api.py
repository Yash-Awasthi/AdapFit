"""Allergy Tracker API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List
from app.services.allergy_tracker import allergy_tracker_service

router = APIRouter(prefix="/allergies", tags=["Allergy Tracking"])


class ProfileRequest(BaseModel):
    user_id: str
    profile_data: Dict[str, Any]


class SymptomLogRequest(BaseModel):
    user_id: str
    date: str
    data: Dict[str, Any]


@router.post("/profile")
async def create_profile(req: ProfileRequest):
    result = allergy_tracker_service.create_profile(req.user_id, req.profile_data)
    return {"success": True, "data": result}


@router.post("/symptoms")
async def log_symptoms(req: SymptomLogRequest):
    result = allergy_tracker_service.log_symptoms(req.user_id, req.date, req.data)
    return {"success": True, "data": result}


@router.get("/forecast/{location}")
async def get_pollen_forecast(location: str, days: int = 3):
    result = allergy_tracker_service.get_pollen_forecast(location, days)
    return {"success": True, "data": result}


@router.get("/triggers/{user_id}")
async def analyze_triggers(user_id: str):
    result = allergy_tracker_service.analyze_triggers(user_id)
    return {"success": True, "data": result}


@router.get("/medications/{user_id}")
async def get_reminders(user_id: str):
    result = allergy_tracker_service.get_medication_reminders(user_id)
    return {"success": True, "data": result}


@router.get("/immunotherapy/{user_id}")
async def get_immunotherapy(user_id: str):
    result = allergy_tracker_service.get_immunotherapy_progress(user_id)
    return {"success": True, "data": result}

"""Fertility Tracker API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.fertility_tracker import fertility_tracker_service

router = APIRouter(prefix="/fertility", tags=["Fertility Tracking"])


class ProfileSetupRequest(BaseModel):
    user_id: str
    profile_data: Dict[str, Any]


class DailyLogRequest(BaseModel):
    user_id: str
    date: str
    data: Dict[str, Any]


@router.post("/profile")
async def setup_profile(req: ProfileSetupRequest):
    result = fertility_tracker_service.setup_profile(req.user_id, req.profile_data)
    return {"success": True, "data": result}


@router.post("/log")
async def log_daily(req: DailyLogRequest):
    result = fertility_tracker_service.log_daily(req.user_id, req.date, req.data)
    return {"success": True, "data": result}


@router.get("/predict/{user_id}")
async def predict_cycle(user_id: str):
    result = fertility_tracker_service.predict_next_period(user_id)
    return {"success": True, "data": result}


@router.get("/insights/{user_id}")
async def get_insights(user_id: str):
    result = fertility_tracker_service.get_cycle_insights(user_id)
    return {"success": True, "data": result}

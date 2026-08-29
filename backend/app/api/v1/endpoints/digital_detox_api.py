"""Digital Detox API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.digital_detox import digital_detox_service

router = APIRouter(prefix="/digital-detox", tags=["Digital Wellness & Detox"])


class ProfileRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]


class UsageLogRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]


@router.post("/profile")
async def setup_profile(req: ProfileRequest):
    result = digital_detox_service.setup_profile(req.user_id, req.data)
    return {"success": True, "data": result}


@router.post("/log-usage")
async def log_usage(req: UsageLogRequest):
    result = digital_detox_service.log_usage(req.user_id, req.data)
    return {"success": True, "data": result}


@router.get("/program/{level}")
async def get_detox_program(level: str = "beginner"):
    result = digital_detox_service.get_detox_program(level)
    return {"success": True, "data": result}


@router.get("/dopamine-fasting")
async def get_dopamine_fasting():
    result = digital_detox_service.get_dopamine_fasting_guide()
    return {"success": True, "data": result}


@router.get("/wellness-score/{user_id}")
async def get_wellness_score(user_id: str):
    result = digital_detox_service.get_wellness_score(user_id)
    return {"success": True, "data": result}


@router.get("/focus-presets")
async def get_focus_presets():
    result = digital_detox_service.get_focus_presets()
    return {"success": True, "data": result}

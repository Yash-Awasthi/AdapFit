"""Pregnancy Tracker API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.pregnancy_tracker import pregnancy_tracker_service

router = APIRouter(prefix="/pregnancy", tags=["Pregnancy Tracking"])


class SetupRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]


class DailyLogRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]


class KickCountRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]


class ContractionRequest(BaseModel):
    data: Dict[str, Any]


@router.post("/setup")
async def setup_pregnancy(req: SetupRequest):
    result = pregnancy_tracker_service.setup_pregnancy(req.user_id, req.data)
    return {"success": True, "data": result}


@router.post("/log")
async def log_daily(req: DailyLogRequest):
    result = pregnancy_tracker_service.log_daily(req.user_id, req.data)
    return {"success": True, "data": result}


@router.get("/week-info/{user_id}")
async def get_week_info(user_id: str):
    result = pregnancy_tracker_service.get_week_info(user_id)
    return {"success": True, "data": result}


@router.post("/kick-counter")
async def kick_counter(req: KickCountRequest):
    result = pregnancy_tracker_service.kick_counter(req.user_id, req.data)
    return {"success": True, "data": result}


@router.post("/contractions")
async def contraction_timer(req: ContractionRequest):
    result = pregnancy_tracker_service.contraction_timer(req.data)
    return {"success": True, "data": result}


@router.get("/postpartum")
async def get_postpartum_guide():
    result = pregnancy_tracker_service.get_postpartum_guide()
    return {"success": True, "data": result}

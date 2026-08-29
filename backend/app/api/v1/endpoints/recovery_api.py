"""Recovery Tracker API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.recovery_tracker import recovery_tracker_service

router = APIRouter(prefix="/recovery", tags=["Addiction Recovery"])


class SetupRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]


class DayLogRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]


class CravingLogRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]


@router.post("/setup")
async def setup_recovery(req: SetupRequest):
    result = recovery_tracker_service.setup_recovery(req.user_id, req.data)
    return {"success": True, "data": result}


@router.post("/log-day")
async def log_day(req: DayLogRequest):
    result = recovery_tracker_service.log_day(req.user_id, req.data)
    return {"success": True, "data": result}


@router.post("/log-craving")
async def log_craving(req: CravingLogRequest):
    result = recovery_tracker_service.log_craving(req.user_id, req.data)
    return {"success": True, "data": result}


@router.get("/progress/{user_id}")
async def get_progress(user_id: str):
    result = recovery_tracker_service.get_recovery_progress(user_id)
    return {"success": True, "data": result}


@router.get("/meetings")
async def find_meetings(location: str = "", type: str = "any"):
    result = recovery_tracker_service.get_meeting_finder(location, type)
    return {"success": True, "data": result}

"""Sleep Tracking API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.sleep_tracker import sleep_tracker_service

router = APIRouter()

class SleepLogRequest(BaseModel):
    bedtime: str = "23:00"
    wake_time: str = "07:00"
    quality_rating: int = 5
    heart_rate_avg: Optional[int] = None
    hrv_avg: Optional[float] = None
    notes: str = ""

class ProfileRequest(BaseModel):
    age_group: str = "adult"
    target_bedtime: str = "23:00"
    target_wake: str = "07:00"

@router.post("/log")
async def log_sleep(request: SleepLogRequest):
    """Log a sleep session."""
    return sleep_tracker_service.log_sleep_session(
        request.bedtime, request.wake_time, request.quality_rating,
        request.heart_rate_avg, request.hrv_avg, request.notes,
    )

@router.get("/score")
async def get_sleep_score():
    """Get current sleep score."""
    return sleep_tracker_service.get_sleep_score()

@router.get("/debt")
async def get_sleep_debt():
    """Calculate sleep debt."""
    return sleep_tracker_service.get_sleep_debt()

@router.get("/trend")
async def get_sleep_trend(days: int = 7):
    """Get sleep trends."""
    return sleep_tracker_service.get_sleep_trend(days)

@router.get("/insights")
async def get_sleep_insights():
    """Get personalized sleep insights."""
    return {"insights": sleep_tracker_service.get_sleep_insights()}

@router.get("/smart-alarm")
async def get_smart_alarm():
    """Get smart alarm window suggestion."""
    return sleep_tracker_service.get_smart_alarm_window()

@router.post("/profile")
async def set_profile(request: ProfileRequest):
    """Set sleep profile."""
    sleep_tracker_service.set_profile(request.age_group, request.target_bedtime, request.target_wake)
    return {"updated": True}

"""
Location Tracking API — GPS Walk Tracking & Distance Counter
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from app.services.location_tracker import location_tracker_service

router = APIRouter()


class UserProfileRequest(BaseModel):
    weight_kg: float = 70.0
    height_cm: float = 170.0


class TrackingStartRequest(BaseModel):
    activity_type: str = "auto"


class LocationPointRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    altitude: float = 0.0
    accuracy: float = 10.0
    heart_rate: Optional[int] = None


@router.post("/profile")
async def set_profile(request: UserProfileRequest):
    """Set user physical profile for accurate distance/calorie calculations."""
    location_tracker_service.set_user_profile(request.weight_kg, request.height_cm)
    return {"updated": True, "weight_kg": request.weight_kg, "height_cm": request.height_cm}


@router.post("/start")
async def start_tracking(request: TrackingStartRequest = TrackingStartRequest()):
    """Start GPS tracking session."""
    return location_tracker_service.start_tracking(request.activity_type)


@router.post("/point")
async def add_location_point(point: LocationPointRequest):
    """Add a GPS location point during tracking."""
    return location_tracker_service.add_location_point(
        point.latitude, point.longitude, point.altitude,
        point.accuracy, point.heart_rate,
    )


@router.post("/pause")
async def pause_tracking():
    """Pause current tracking session."""
    return location_tracker_service.pause_tracking()


@router.post("/resume")
async def resume_tracking():
    """Resume paused tracking session."""
    return location_tracker_service.resume_tracking()


@router.post("/stop")
async def stop_tracking():
    """Stop and save current tracking session."""
    return location_tracker_service.stop_tracking()


@router.get("/status")
async def get_tracking_status():
    """Get current tracking status and live stats."""
    return location_tracker_service.get_current_status()


@router.get("/daily-summary")
async def get_daily_summary(date: str = "today"):
    """Get daily walking summary."""
    summary = location_tracker_service.get_daily_summary(date)
    return {
        "date": summary.date,
        "total_steps": summary.total_steps,
        "total_distance_km": summary.total_distance_km,
        "total_active_minutes": summary.total_active_minutes,
        "total_calories": summary.total_calories,
        "floors_climbed": summary.floors_climbed,
        "longest_walk_km": summary.longest_walk_km,
        "avg_pace": summary.avg_pace,
    }


@router.get("/history")
async def get_route_history(limit: int = 10):
    """Get recent tracked routes."""
    return {"routes": location_tracker_service.get_route_history(limit)}

"""Environmental Health API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict, Optional
from app.services.environmental_health import environmental_health_service

router = APIRouter(prefix="/environmental", tags=["Environmental Health"])


class AirQualityReading(BaseModel):
    """A measurement from an air quality provider or a monitor."""
    location: str
    aqi: int
    pollutants: Optional[Dict[str, Any]] = None


class UVReading(BaseModel):
    location: str
    uv_index: float


@router.post("/air-quality")
async def record_air_quality(reading: AirQualityReading):
    """Record an air quality reading so advice for that location has a basis."""
    result = environmental_health_service.record_air_quality(
        reading.location, reading.aqi, reading.pollutants
    )
    return {"success": True, "data": result}


@router.post("/uv-index")
async def record_uv_index(reading: UVReading):
    result = environmental_health_service.record_uv_index(reading.location, reading.uv_index)
    return {"success": True, "data": result}


@router.get("/air-quality/{location}")
async def get_air_quality(location: str, live: bool = True):
    """
    Air quality for a location.

    Fetches from Open-Meteo by default, which needs no API key. Pass
    live=false to read only what has already been recorded.
    """
    if live:
        result = await environmental_health_service.fetch_air_quality(location)
    else:
        result = environmental_health_service.get_air_quality(location)
    return {"success": True, "data": result}


@router.get("/uv-index/{location}")
async def get_uv_index(location: str, live: bool = True):
    if live:
        result = await environmental_health_service.fetch_uv_index(location)
    else:
        result = environmental_health_service.get_uv_index(location)
    return {"success": True, "data": result}


@router.get("/outdoor-safety/{location}")
async def get_outdoor_safety(location: str, activity: str = "running", live: bool = True):
    if live:
        result = await environmental_health_service.fetch_outdoor_exercise_safety(location, activity)
    else:
        result = environmental_health_service.get_outdoor_exercise_safety(location, activity)
    return {"success": True, "data": result}


@router.get("/indoor-air-tips")
async def get_indoor_tips():
    result = environmental_health_service.get_indoor_air_quality_tips()
    return {"success": True, "data": result}

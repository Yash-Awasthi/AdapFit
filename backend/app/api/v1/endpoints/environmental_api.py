"""Environmental Health API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.environmental_health import environmental_health_service

router = APIRouter(prefix="/environmental", tags=["Environmental Health"])


@router.get("/air-quality/{location}")
async def get_air_quality(location: str):
    result = environmental_health_service.get_air_quality(location)
    return {"success": True, "data": result}


@router.get("/uv-index/{location}")
async def get_uv_index(location: str):
    result = environmental_health_service.get_uv_index(location)
    return {"success": True, "data": result}


@router.get("/outdoor-safety/{location}")
async def get_outdoor_safety(location: str, activity: str = "running"):
    result = environmental_health_service.get_outdoor_exercise_safety(location, activity)
    return {"success": True, "data": result}


@router.get("/indoor-air-tips")
async def get_indoor_tips():
    result = environmental_health_service.get_indoor_air_quality_tips()
    return {"success": True, "data": result}

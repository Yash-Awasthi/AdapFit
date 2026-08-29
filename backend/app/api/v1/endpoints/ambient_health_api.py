"""Ambient Health Monitoring API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.services.ambient_health import ambient_health_service

router = APIRouter(prefix="/ambient", tags=["Ambient Health"])


class HomeRequest(BaseModel):
    user_id: str
    home_config: Dict[str, Any]


class DeviceRequest(BaseModel):
    home_id: str
    device_config: Dict[str, Any]


class ReadingRequest(BaseModel):
    device_id: str
    reading: Dict[str, Any]


@router.post("/home")
async def register_home(req: HomeRequest):
    result = ambient_health_service.register_home(req.user_id, req.home_config)
    return {"success": True, "data": result}


@router.post("/device")
async def register_device(req: DeviceRequest):
    result = ambient_health_service.register_device(req.home_id, req.device_config)
    return {"success": True, "data": result}


@router.post("/reading")
async def process_reading(req: ReadingRequest):
    result = ambient_health_service.process_reading(req.device_id, req.reading)
    return {"success": True, "data": result}


@router.get("/health/{home_id}")
async def get_environment_health(home_id: str):
    result = ambient_health_service.get_environment_health(home_id)
    return {"success": True, "data": result}


@router.get("/sleep/{home_id}")
async def get_sleep_environment(home_id: str):
    result = ambient_health_service.get_sleep_environment_score(home_id)
    return {"success": True, "data": result}


@router.get("/activity/{home_id}")
async def get_activity_patterns(home_id: str, days: int = 7):
    result = ambient_health_service.get_activity_patterns(home_id, days)
    return {"success": True, "data": result}


@router.get("/devices")
async def list_supported_devices():
    devices = [
        {"type": k, "name": v["name"], "metrics": v["metrics"]}
        for k, v in ambient_health_service.supported_devices.items()
    ]
    return {"success": True, "data": devices}

"""Wearable Realtime API"""
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.wearable_realtime import wearable_realtime_service

router = APIRouter()

class ConnectRequest(BaseModel):
    device_type: str = "smartwatch"

class HRStreamRequest(BaseModel):
    bpm: int; confidence: float = 0.9

class StepsStreamRequest(BaseModel):
    steps: int; distance_m: float = 0

@router.post("/connect")
async def connect(request: ConnectRequest):
    return wearable_realtime_service.connect(request.device_type)

@router.post("/disconnect")
async def disconnect():
    return wearable_realtime_service.disconnect()

@router.post("/hr")
async def stream_hr(request: HRStreamRequest):
    return wearable_realtime_service.stream_hr(request.bpm, request.confidence)

@router.post("/steps")
async def stream_steps(request: StepsStreamRequest):
    return wearable_realtime_service.stream_steps(request.steps, request.distance_m)

@router.get("/hr/realtime")
async def get_realtime_hr():
    return wearable_realtime_service.get_realtime_hr()

@router.get("/hr/zones")
async def get_hr_zones():
    return wearable_realtime_service.get_hr_zones()

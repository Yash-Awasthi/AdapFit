"""Device & Wearable Sync API"""
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.device_sync import device_sync_service

router = APIRouter()

class ConnectRequest(BaseModel):
    platform: str; display_name: str

@router.post("/connect")
async def connect_device(request: ConnectRequest):
    return device_sync_service.connect_device(request.platform, request.display_name)

@router.delete("/disconnect/{device_id}")
async def disconnect(device_id: str):
    return device_sync_service.disconnect_device(device_id)

@router.get("/devices")
async def get_devices():
    return {"devices": device_sync_service.get_devices()}

@router.post("/sync/{device_id}")
async def trigger_sync(device_id: str):
    return device_sync_service.trigger_sync(device_id)

@router.get("/status")
async def get_sync_status():
    return device_sync_service.get_sync_status()

@router.get("/data/{data_type}")
async def get_synced_data(data_type: str, limit: int = 50):
    return {"data": device_sync_service.get_synced_data(data_type, limit)}

@router.get("/history")
async def get_sync_history(limit: int = 20):
    return {"history": device_sync_service.get_sync_history(limit)}

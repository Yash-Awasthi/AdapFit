"""
Remote Patient Monitoring API Endpoints
"""
from fastapi import APIRouter
from typing import Dict, List
from pydantic import BaseModel

router = APIRouter(prefix="/remote-monitoring", tags=["Remote Patient Monitoring"])


class DeviceRegistrationRequest(BaseModel):
    patient_id: str
    device_type: str
    device_info: Dict = {}


class VitalReadingRequest(BaseModel):
    patient_id: str
    device_type: str
    readings: Dict


@router.post("/register-device")
async def register_device(request: DeviceRegistrationRequest):
    from app.services.remote_monitoring import remote_monitoring_service
    return {"success": True, "data": remote_monitoring_service.register_device(request.patient_id, request.device_type, request.device_info)}


@router.post("/process-reading")
async def process_vital_reading(request: VitalReadingRequest):
    from app.services.remote_monitoring import remote_monitoring_service
    return {"success": True, "data": remote_monitoring_service.process_vital_reading(request.patient_id, request.device_type, request.readings)}


@router.get("/trends/{patient_id}")
async def get_vital_trends(patient_id: str, metric: str = "heart_rate", days: int = 30):
    from app.services.remote_monitoring import remote_monitoring_service
    return {"success": True, "data": remote_monitoring_service.get_vital_trends(patient_id, metric, days)}


@router.get("/dashboard/{patient_id}")
async def get_monitoring_dashboard(patient_id: str):
    from app.services.remote_monitoring import remote_monitoring_service
    return {"success": True, "data": remote_monitoring_service.get_monitoring_dashboard(patient_id)}


@router.get("/devices")
async def get_device_types():
    from app.services.remote_monitoring import remote_monitoring_service
    return {"success": True, "data": list(remote_monitoring_service.device_types.keys())}

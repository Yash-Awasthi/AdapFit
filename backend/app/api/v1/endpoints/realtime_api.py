"""
Real-Time Health Monitoring API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/realtime", tags=["Real-Time Health Monitoring"])


class StartSessionRequest(BaseModel):
    user_id: str
    device_id: str = "phone"


class VitalReadingRequest(BaseModel):
    session_id: str
    vital_type: str
    value: float
    timestamp: Optional[str] = None


class RegisterDeviceRequest(BaseModel):
    user_id: str
    device_type: str
    device_name: str


@router.post("/session/start")
async def start_session(req: StartSessionRequest):
    from app.services.realtime_monitor import realtime_monitor
    return realtime_monitor.start_monitoring_session(req.user_id, req.device_id)


@router.post("/vital")
async def process_vital(req: VitalReadingRequest):
    from app.services.realtime_monitor import realtime_monitor
    return realtime_monitor.process_vital_reading(req.session_id, req.vital_type, req.value, req.timestamp)


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    from app.services.realtime_monitor import realtime_monitor
    return realtime_monitor.get_session_data(session_id)


@router.post("/session/{session_id}/stop")
async def stop_session(session_id: str):
    from app.services.realtime_monitor import realtime_monitor
    return realtime_monitor.stop_monitoring_session(session_id)


@router.get("/history/{user_id}")
async def get_history(user_id: str, limit: int = 10):
    from app.services.realtime_monitor import realtime_monitor
    return realtime_monitor.get_user_monitoring_history(user_id, limit)


@router.get("/alerts/{user_id}")
async def get_alerts(user_id: str, limit: int = 20):
    from app.services.realtime_monitor import realtime_monitor
    return realtime_monitor.get_care_team_notifications(user_id, limit)


@router.post("/device/register")
async def register_device(req: RegisterDeviceRequest):
    from app.services.realtime_monitor import realtime_monitor
    return realtime_monitor.register_device(req.user_id, req.device_type, req.device_name)


@router.get("/thresholds")
async def get_thresholds():
    from app.services.realtime_monitor import realtime_monitor
    return realtime_monitor.VITAL_THRESHOLDS

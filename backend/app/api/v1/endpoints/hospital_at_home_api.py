"""
Hospital at Home API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/hospital-at-home", tags=["Hospital at Home"])


class AdmitRequest(BaseModel):
    user_id: str
    condition: str
    physician: str
    admission_date: Optional[str] = None


class VitalReadingRequest(BaseModel):
    user_id: str
    vital_type: str
    value: float
    timestamp: Optional[str] = None


class DischargeRequest(BaseModel):
    user_id: str
    physician_notes: str = ""
    follow_up_date: str = ""


@router.post("/admit")
async def admit_patient(req: AdmitRequest):
    from app.services.hospital_at_home import hospital_at_home
    return hospital_at_home.admit_patient(req.user_id, req.condition, req.physician, req.admission_date)


@router.post("/vital/log")
async def log_vital(req: VitalReadingRequest):
    from app.services.hospital_at_home import hospital_at_home
    return hospital_at_home.log_vital_reading(req.user_id, req.vital_type, req.value, req.timestamp)


@router.get("/status/{user_id}")
async def get_status(user_id: str):
    from app.services.hospital_at_home import hospital_at_home
    return hospital_at_home.get_patient_status(user_id)


@router.post("/discharge")
async def create_discharge(req: DischargeRequest):
    from app.services.hospital_at_home import hospital_at_home
    return hospital_at_home.create_discharge_plan(req.user_id, req.physician_notes, req.follow_up_date)


@router.get("/escalations/{user_id}")
async def get_escalations(user_id: str, limit: int = 20):
    from app.services.hospital_at_home import hospital_at_home
    return hospital_at_home.get_escalation_history(user_id, limit)


@router.get("/conditions")
async def get_conditions():
    from app.services.hospital_at_home import hospital_at_home
    return hospital_at_home.get_conditions()


@router.get("/escalation-levels")
async def get_escalation_levels():
    from app.services.hospital_at_home import hospital_at_home
    return hospital_at_home.ESCALATION_LEVELS


@router.get("/discharge-criteria")
async def get_discharge_criteria():
    from app.services.hospital_at_home import hospital_at_home
    return hospital_at_home.DISCHARGE_CRITERIA

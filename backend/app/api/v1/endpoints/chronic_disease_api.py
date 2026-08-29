"""
Chronic Disease Management API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/chronic-disease", tags=["Chronic Disease Management"])


class RegisterConditionRequest(BaseModel):
    user_id: str
    condition_key: str
    diagnosed_date: str
    severity: str = "moderate"
    notes: str = ""


class LogSymptomsRequest(BaseModel):
    user_id: str
    condition_key: str
    symptoms: List[str]
    severity: int
    notes: str = ""


class LogVitalsRequest(BaseModel):
    user_id: str
    condition_key: str
    vitals: dict


class LogMedicationRequest(BaseModel):
    user_id: str
    medication: str
    dosage: str
    taken: bool
    side_effects: List[str] = []


@router.post("/register")
async def register_condition(req: RegisterConditionRequest):
    from app.services.chronic_disease_manager import chronic_disease_service
    return chronic_disease_service.register_condition(req.user_id, req.condition_key, req.diagnosed_date, req.severity, req.notes)


@router.post("/symptoms/log")
async def log_symptoms(req: LogSymptomsRequest):
    from app.services.chronic_disease_manager import chronic_disease_service
    return chronic_disease_service.log_symptoms(req.user_id, req.condition_key, req.symptoms, req.severity, req.notes)


@router.post("/vitals/log")
async def log_vitals(req: LogVitalsRequest):
    from app.services.chronic_disease_manager import chronic_disease_service
    return chronic_disease_service.log_vitals(req.user_id, req.condition_key, req.vitals)


@router.post("/medication/log")
async def log_medication(req: LogMedicationRequest):
    from app.services.chronic_disease_manager import chronic_disease_service
    return chronic_disease_service.log_medication(req.user_id, req.medication, req.dosage, req.taken, req.side_effects)


@router.get("/adherence/{user_id}")
async def get_adherence(user_id: str, days: int = 30):
    from app.services.chronic_disease_manager import chronic_disease_service
    return chronic_disease_service.get_adherence_rate(user_id, days)


@router.get("/summary/{user_id}/{condition}")
async def get_condition_summary(user_id: str, condition: str):
    from app.services.chronic_disease_manager import chronic_disease_service
    return chronic_disease_service.get_condition_summary(user_id, condition)


@router.get("/conditions")
async def get_supported_conditions():
    from app.services.chronic_disease_manager import chronic_disease_service
    return chronic_disease_service.SUPPORTED_CONDITIONS

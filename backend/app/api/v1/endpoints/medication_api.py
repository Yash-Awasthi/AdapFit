"""Medication Reminder API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.medication_reminder import medication_reminder_service

router = APIRouter()

class MedAddRequest(BaseModel):
    name: str
    dosage: str
    frequency: str = "once_daily"
    times: list[str] = ["08:00"]
    category: str = "supplement"
    notes: str = ""

class DoseLogRequest(BaseModel):
    medication_id: str
    status: str = "taken"

class MedicalInfoRequest(BaseModel):
    blood_type: str = "unknown"
    allergies: list[str] = []
    conditions: list[str] = []
    medications: list[str] = []
    emergency_note: str = ""

@router.post("/add")
async def add_medication(request: MedAddRequest):
    return medication_reminder_service.add_medication(
        request.name, request.dosage, request.frequency,
        request.times, request.category, request.notes,
    )

@router.post("/dose")
async def log_dose(request: DoseLogRequest):
    return medication_reminder_service.log_dose(request.medication_id, request.status)

@router.get("/today")
async def get_today_schedule():
    return medication_reminder_service.get_today_schedule()

@router.get("/adherence")
async def get_adherence(days: int = 30):
    return medication_reminder_service.get_adherence_score(days)

@router.get("/list")
async def list_medications():
    return {"medications": medication_reminder_service.get_all_medications()}

@router.get("/refills")
async def get_refill_alerts():
    return {"alerts": medication_reminder_service.get_refill_alerts()}

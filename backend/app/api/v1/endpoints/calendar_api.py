"""Health Calendar API — Cycle tracking, appointments, medication schedule"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.health_calendar import health_calendar_service

router = APIRouter()


class LogPeriodRequest(BaseModel):
    start_date: str
    end_date: str
    flow: str = "medium"
    symptoms: list[str] = []
    mood: int = 5
    notes: str = ""


class LogSymptomsRequest(BaseModel):
    date: str
    symptoms: list[str]
    mood: int = 5
    energy: int = 5
    pain_level: int = 0
    notes: str = ""


class AppointmentRequest(BaseModel):
    title: str
    date: str
    time: str
    doctor: str = ""
    location: str = ""
    notes: str = ""


class MedicationRequest(BaseModel):
    name: str
    dosage: str
    times: list[str]
    frequency: str = "daily"


@router.post("/cycle/log")
async def log_period(request: LogPeriodRequest):
    return health_calendar_service.log_period(request.start_date, request.end_date, request.flow, request.symptoms, request.mood, request.notes)


@router.get("/cycle/predictions")
async def get_predictions():
    return health_calendar_service.get_predictions()


@router.get("/cycle/summary")
async def get_cycle_summary():
    return health_calendar_service.get_cycle_summary()


@router.post("/symptoms")
async def log_symptoms(request: LogSymptomsRequest):
    return health_calendar_service.log_symptoms(request.date, request.symptoms, request.mood, request.energy, request.pain_level, request.notes)


@router.get("/symptoms")
async def get_symptoms(days: int = 30):
    return {"symptoms": health_calendar_service.get_symptoms_history(days)}


@router.post("/appointment")
async def add_appointment(request: AppointmentRequest):
    return health_calendar_service.add_appointment(request.title, request.date, request.time, request.doctor, request.location, request.notes)


@router.get("/appointments")
async def get_appointments(month: str = ""):
    return {"appointments": health_calendar_service.get_appointments(month)}


@router.get("/appointments/upcoming")
async def get_upcoming(days: int = 7):
    return {"appointments": health_calendar_service.get_upcoming(days)}


@router.post("/medication")
async def add_medication(request: MedicationRequest):
    return health_calendar_service.add_medication(request.name, request.dosage, request.times, request.frequency)


@router.get("/medications")
async def get_medications():
    return {"medications": health_calendar_service.get_todays_medications()}


@router.get("/medications/adherence")
async def get_adherence(days: int = 30):
    return health_calendar_service.get_medication_adherence(days)

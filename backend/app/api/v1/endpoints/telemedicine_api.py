"""Telemedicine API — Doctor directory, appointments, video consultations"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.telemedicine import telemedicine_service

router = APIRouter()


class BookAppointmentRequest(BaseModel):
    patient_id: str
    doctor_id: str
    date: str
    time_slot: str
    consultation_type: str = "video"


class EndConsultationRequest(BaseModel):
    room_id: str
    notes: str = ""
    prescription: str = ""


class RateDoctorRequest(BaseModel):
    appointment_id: str
    rating: int
    review: str = ""


@router.get("/doctors")
async def list_doctors(specialty: Optional[str] = None, available_today: bool = False, search: str = "", page: int = 1):
    return telemedicine_service.list_doctors(specialty, available_today, search, page)


@router.get("/doctors/{doctor_id}")
async def get_doctor(doctor_id: str):
    doc = telemedicine_service.get_doctor(doctor_id)
    if not doc:
        return {"error": "Doctor not found"}
    return {"doctor": doc}


@router.get("/specialties")
async def get_specialties():
    return {"specialties": telemedicine_service.get_specialties()}


@router.get("/doctors/{doctor_id}/availability")
async def get_availability(doctor_id: str, date: str = ""):
    return telemedicine_service.get_availability(doctor_id, date)


@router.post("/appointments")
async def book_appointment(request: BookAppointmentRequest):
    return telemedicine_service.book_appointment(request.patient_id, request.doctor_id, request.date, request.time_slot, request.consultation_type)


@router.delete("/appointments/{appointment_id}")
async def cancel_appointment(appointment_id: str):
    return telemedicine_service.cancel_appointment(appointment_id)


@router.get("/appointments/{patient_id}")
async def get_appointments(patient_id: str, status: Optional[str] = None):
    return {"appointments": telemedicine_service.get_patient_appointments(patient_id, status)}


@router.post("/consultation/join")
async def join_consultation(appointment_id: str):
    return telemedicine_service.join_consultation(appointment_id)


@router.post("/consultation/end")
async def end_consultation(request: EndConsultationRequest):
    return telemedicine_service.end_consultation(request.room_id, request.notes, request.prescription)


@router.post("/rate")
async def rate_doctor(request: RateDoctorRequest):
    return telemedicine_service.rate_doctor(request.appointment_id, request.rating, request.review)


@router.get("/history/{patient_id}")
async def get_consultation_history(patient_id: str):
    return {"history": telemedicine_service.get_consultation_history(patient_id)}

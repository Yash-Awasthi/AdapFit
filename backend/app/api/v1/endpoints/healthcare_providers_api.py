"""
Healthcare Provider Directory API — Search, Book, Manage Appointments
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional
from app.services.healthcare_providers import healthcare_providers_service
from app.core.dependencies import require_user

router = APIRouter()


class SearchRequest(BaseModel):
    specialty: Optional[str] = None
    provider_type: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: float = 50
    min_rating: float = 0
    online_only: bool = False


class BookAppointmentRequest(BaseModel):
    provider_id: str
    date: str = Field(min_length=8, max_length=20)
    time: str = Field(min_length=4, max_length=20)
    appointment_type: str = Field(default="in_person", description="in_person, video, phone")
    reason: str = Field(default="", max_length=500)


@router.post("/search")
async def search_providers(request: SearchRequest, user: dict = Depends(require_user)):
    """Search healthcare providers by specialty, location, type."""
    return {"providers": healthcare_providers_service.search_providers(
        specialty=request.specialty,
        provider_type=request.provider_type,
        city=request.city,
        latitude=request.latitude,
        longitude=request.longitude,
        radius_km=request.radius_km,
        min_rating=request.min_rating,
        online_only=request.online_only,
    )}


@router.get("/specialties")
async def get_specialties():
    """List available medical specialties."""
    return {"specialties": healthcare_providers_service.get_specialties()}


@router.get("/{provider_id}")
async def get_provider(provider_id: str, user: dict = Depends(require_user)):
    """Get detailed provider information."""
    provider = healthcare_providers_service.get_provider(provider_id)
    if not provider:
        return {"error": "Provider not found"}
    return provider


@router.post("/appointment")
async def book_appointment(request: BookAppointmentRequest, user: dict = Depends(require_user)):
    """Book an appointment with a provider."""
    return healthcare_providers_service.book_appointment(
        user["id"], request.provider_id, request.date, request.time,
        request.appointment_type, request.reason,
    )


@router.get("/appointments/list")
async def get_appointments(user: dict = Depends(require_user), status: Optional[str] = None):
    """Get user's appointments."""
    return {"appointments": healthcare_providers_service.get_appointments(user["id"], status)}


@router.post("/appointment/{appointment_id}/cancel")
async def cancel_appointment(appointment_id: str, user: dict = Depends(require_user)):
    """Cancel an appointment."""
    return healthcare_providers_service.cancel_appointment(appointment_id, user["id"])

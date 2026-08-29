"""Emergency SOS API — Contacts, Medical Info, One-Tap Alert, Safety Check Timer"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.services.emergency_sos import emergency_sos_service
from app.core.dependencies import require_user, get_user_id

router = APIRouter()

class ContactRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=3, max_length=20)
    relationship: str = Field(min_length=1, max_length=50)
    is_primary: bool = False

class MedicalInfoReq(BaseModel):
    blood_type: str = "unknown"
    allergies: list[str] = Field(default_factory=list, max_length=50)
    conditions: list[str] = Field(default_factory=list, max_length=50)
    medications: list[str] = Field(default_factory=list, max_length=50)
    emergency_note: str = Field(default="", max_length=1000)

class SOSActivateRequest(BaseModel):
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)

class SafetyCheckRequest(BaseModel):
    """Safety check timer — user sets a check-in deadline."""
    check_in_minutes: int = Field(ge=5, le=480, default=60,
        description="Minutes until check-in is required (5 min to 8 hours)")
    message: str = Field(default="Are you safe?", max_length=500)
    notify_contacts: bool = True

class SafetyCheckRespondRequest(BaseModel):
    check_id: str
    safe: bool = True
    note: str = Field(default="", max_length=500)


@router.post("/contact")
async def add_contact(request: ContactRequest, user: dict = Depends(require_user)):
    result = emergency_sos_service.add_contact(
        request.name, request.phone, request.relationship, request.is_primary, user["id"]
    )
    return result

@router.delete("/contact/{contact_id}")
async def remove_contact(contact_id: str, user: dict = Depends(require_user)):
    return emergency_sos_service.remove_contact(contact_id, user["id"])

@router.get("/contacts")
async def get_contacts(user: dict = Depends(require_user)):
    return {"contacts": emergency_sos_service.get_contacts(user["id"])}

@router.post("/medical-info")
async def set_medical_info(request: MedicalInfoReq, user: dict = Depends(require_user)):
    return emergency_sos_service.set_medical_info(
        request.blood_type, request.allergies, request.conditions,
        request.medications, request.emergency_note, user["id"],
    )

@router.get("/medical-info")
async def get_medical_info(user: dict = Depends(require_user)):
    return emergency_sos_service.get_medical_info(user["id"])

@router.post("/activate")
async def activate_sos(request: SOSActivateRequest = SOSActivateRequest(), user: dict = Depends(require_user)):
    location = {"latitude": request.latitude, "longitude": request.longitude} if request.latitude else None
    return emergency_sos_service.activate_sos(user["id"], location)

@router.post("/confirm/{alert_id}")
async def confirm_sos(alert_id: str, user: dict = Depends(require_user)):
    return emergency_sos_service.confirm_sos(alert_id, user["id"])

@router.post("/cancel/{alert_id}")
async def cancel_sos(alert_id: str, user: dict = Depends(require_user)):
    return emergency_sos_service.cancel_sos(alert_id, user["id"])

@router.post("/fall-detection")
async def check_fall(data: dict, user: dict = Depends(require_user)):
    return emergency_sos_service.check_fall_detection(data, user["id"])

@router.get("/emergency-card")
async def get_emergency_card(user: dict = Depends(require_user)):
    return emergency_sos_service.get_emergency_card(user["id"])

@router.get("/history")
async def get_alert_history(user: dict = Depends(require_user)):
    return {"history": emergency_sos_service.get_alert_history(user["id"])}


# === Safety Check Timer ===

@router.post("/safety-check/start")
async def start_safety_check(request: SafetyCheckRequest, user: dict = Depends(require_user)):
    """
    Start a safety check timer. If the user doesn't respond within the
    specified time, emergency contacts are notified with location.
    
    Use cases:
    - Going for a solo run/hike
    - Late-night walk home
    - Meeting someone new
    - Any situation where someone should know you're safe
    """
    return emergency_sos_service.start_safety_check(
        user["id"], request.check_in_minutes, request.message, request.notify_contacts
    )


@router.post("/safety-check/respond")
async def respond_safety_check(request: SafetyCheckRespondRequest, user: dict = Depends(require_user)):
    """Respond to a safety check — confirms user is safe."""
    return emergency_sos_service.respond_safety_check(
        request.check_id, user["id"], request.safe, request.note
    )


@router.get("/safety-check/active")
async def get_active_safety_checks(user: dict = Depends(require_user)):
    """Get active safety checks for this user."""
    return {"checks": emergency_sos_service.get_active_safety_checks(user["id"])}


@router.get("/safety-check/history")
async def get_safety_check_history(user: dict = Depends(require_user), limit: int = 20):
    """Get safety check history."""
    return {"history": emergency_sos_service.get_safety_check_history(user["id"], limit)}

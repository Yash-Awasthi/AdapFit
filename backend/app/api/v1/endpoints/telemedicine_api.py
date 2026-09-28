"""Telemedicine: real consultation services and NMC registration checks."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.telemedicine import telemedicine_service

router = APIRouter()


class VerifyRequest(BaseModel):
    registration_no: str = Field(min_length=1, max_length=30)
    council_code: str = Field("", max_length=5)
    name: str = Field("", max_length=100)


class SaveDoctorRequest(VerifyRequest):
    name: str = Field(min_length=2, max_length=100)
    specialty: str = Field("", max_length=60)
    notes: str = Field("", max_length=500)


@router.get("/overview")
async def overview():
    return telemedicine_service.overview()


@router.post("/verify")
async def verify(request: VerifyRequest):
    return await telemedicine_service.verify_registration(request.registration_no, request.council_code, request.name)


@router.post("/doctors")
async def save_doctor(request: SaveDoctorRequest):
    """Saved with whatever the register says now, so 'verified' is never the client's claim."""
    check = await telemedicine_service.verify_registration(request.registration_no, request.council_code, request.name)
    found = check.get("status") == "found" and not any(m["removed"] for m in check.get("matches", []))
    council = check["matches"][0]["council"] if found else request.council_code
    doctor = telemedicine_service.save_doctor(request.name, request.registration_no, council or "",
                                              request.specialty, found, request.notes)
    return {"doctor": doctor, "check": check}


@router.delete("/doctors/{registration_no:path}")
async def remove_doctor(registration_no: str):
    if not telemedicine_service.remove_doctor(registration_no):
        raise HTTPException(404, "Not in your list")
    return {"removed": True}

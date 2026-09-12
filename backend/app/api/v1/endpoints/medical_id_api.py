"""Medical ID API endpoints.

Every route here reads or writes one person's medical record, so each one
resolves the caller and checks they are that person (or an admin). The
emergency view carries blood type, allergies, current medications and
emergency contacts.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any
from app.core.dependencies import ensure_owner, require_user
from app.services.medical_id import medical_id_service

router = APIRouter(prefix="/medical-id", tags=["Medical ID & Emergency"])


class MedicalIDRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]


class ContactRequest(BaseModel):
    user_id: str
    contact: Dict[str, Any]


class UpdateRequest(BaseModel):
    user_id: str
    updates: Dict[str, Any]


@router.post("/create")
async def create_medical_id(req: MedicalIDRequest, caller: dict = Depends(require_user)):
    ensure_owner(caller, req.user_id)
    result = medical_id_service.create_medical_id(req.user_id, req.data)
    return {"success": True, "data": result}


@router.get("/emergency/{user_id}")
async def get_emergency_view(user_id: str, caller: dict = Depends(require_user)):
    ensure_owner(caller, user_id)
    result = medical_id_service.get_emergency_view(user_id)
    return {"success": True, "data": result}


@router.get("/wallet/{user_id}")
async def get_wallet_card(user_id: str, caller: dict = Depends(require_user)):
    ensure_owner(caller, user_id)
    result = medical_id_service.get_wallet_card(user_id)
    return {"success": True, "data": result}


@router.post("/contact")
async def add_contact(req: ContactRequest, caller: dict = Depends(require_user)):
    ensure_owner(caller, req.user_id)
    result = medical_id_service.add_emergency_contact(req.user_id, req.contact)
    return {"success": True, "data": result}


@router.get("/provider-summary/{user_id}")
async def get_provider_summary(user_id: str, caller: dict = Depends(require_user)):
    ensure_owner(caller, user_id)
    result = medical_id_service.get_health_summary_for_provider(user_id)
    return {"success": True, "data": result}


@router.put("/update")
async def update_medical_id(req: UpdateRequest, caller: dict = Depends(require_user)):
    ensure_owner(caller, req.user_id)
    result = medical_id_service.update_medical_id(req.user_id, req.updates)
    return {"success": True, "data": result}

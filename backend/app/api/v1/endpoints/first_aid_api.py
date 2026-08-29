"""
Emergency First Aid Guide & Disaster Health Preparedness API Endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/first-aid", tags=["First Aid & Emergency"])


class EmergencyTriageRequest(BaseModel):
    symptoms: List[str]


@router.post("/assess")
async def assess_emergency(request: EmergencyTriageRequest):
    """Triage symptoms and provide emergency guidance"""
    from app.services.first_aid import first_aid_service
    assessment = first_aid_service.assess_emergency(request.symptoms)
    return {"success": True, "data": assessment}


@router.get("/protocols")
async def get_all_protocols():
    """Get all emergency protocols"""
    from app.services.first_aid import first_aid_service
    return {"success": True, "data": first_aid_service.emergency_protocols}


@router.get("/protocols/{emergency_type}")
async def get_protocol(emergency_type: str):
    """Get specific emergency protocol"""
    from app.services.first_aid import first_aid_service
    protocol = first_aid_service.get_emergency_protocol(emergency_type)
    return {"success": True, "data": protocol}


@router.get("/cpr")
async def get_cpr_training(age_group: str = "adult"):
    """Get CPR training module"""
    from app.services.first_aid import first_aid_service
    training = first_aid_service.get_cpr_training(age_group)
    return {"success": True, "data": training}


@router.get("/cpr/all")
async def get_all_cpr_training():
    """Get all CPR training modules"""
    from app.services.first_aid import first_aid_service
    return {"success": True, "data": first_aid_service.cpr_training}


@router.get("/preparedness")
async def get_disaster_preparedness():
    """Get disaster preparedness guide"""
    from app.services.first_aid import first_aid_service
    guide = first_aid_service.get_disaster_preparedness()
    return {"success": True, "data": guide}


@router.get("/first-aid-kit")
async def get_first_aid_kit_guide():
    """Get first aid kit guide"""
    from app.services.first_aid import first_aid_service
    kit = first_aid_service.get_first_aid_kit()
    return {"success": True, "data": kit}

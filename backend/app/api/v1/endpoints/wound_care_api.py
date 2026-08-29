"""Wound Care Assessment API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.wound_care import wound_care_service

router = APIRouter(prefix="/wound-care", tags=["AI Wound Care"])


class WoundRegistrationRequest(BaseModel):
    user_id: str
    wound_data: Dict[str, Any]


class WoundAssessmentRequest(BaseModel):
    wound_id: str
    assessment_data: Dict[str, Any]


@router.post("/register")
async def register_wound(req: WoundRegistrationRequest):
    result = wound_care_service.register_wound(req.user_id, req.wound_data)
    return {"success": True, "data": result}


@router.post("/assess")
async def assess_wound(req: WoundAssessmentRequest):
    result = wound_care_service.assess_wound(req.wound_id, req.assessment_data)
    return {"success": True, "data": result}


@router.get("/progress/{wound_id}")
async def get_progress(wound_id: str):
    result = wound_care_service.get_healing_progress(wound_id)
    return {"success": True, "data": result}


@router.get("/protocols/{wound_type}")
async def get_protocols(wound_type: str):
    result = wound_care_service.get_care_protocols(wound_type)
    return {"success": True, "data": result}


@router.get("/types")
async def list_wound_types():
    types = [
        {"id": k, "name": v["name"], "stages": list(v["stages"].keys())}
        for k, v in wound_care_service.wound_types.items()
    ]
    return {"success": True, "data": types}

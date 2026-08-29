"""
Social Determinants of Health API Endpoints
"""
from fastapi import APIRouter
from typing import Dict, List
from pydantic import BaseModel

router = APIRouter(prefix="/sdoh", tags=["Social Determinants of Health"])


class SDOHScreeningRequest(BaseModel):
    patient_id: str
    responses: Dict


@router.post("/screen")
async def screen_sdoh(request: SDOHScreeningRequest):
    from app.services.social_determinants import social_determinants_service
    return {"success": True, "data": social_determinants_service.screen_sdoh(request.patient_id, request.responses)}


@router.get("/screening-questions")
async def get_screening_questions():
    from app.services.social_determinants import social_determinants_service
    return {"success": True, "data": social_determinants_service.screening_categories}


@router.get("/resources")
async def find_resources(resource_type: str = "food"):
    from app.services.social_determinants import social_determinants_service
    return {"success": True, "data": social_determinants_service.find_resources(resource_type)}

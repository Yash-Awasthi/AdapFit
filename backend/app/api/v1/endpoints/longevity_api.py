"""Longevity Tracker API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.services.longevity_tracker import longevity_tracker_service

router = APIRouter(prefix="/longevity", tags=["Longevity"])


class LongevityAssessmentRequest(BaseModel):
    user_id: str
    lifestyle_data: Dict[str, Any]


class InterventionRequest(BaseModel):
    user_id: str
    intervention: Dict[str, Any]


@router.post("/assess")
async def assess_longevity(req: LongevityAssessmentRequest):
    result = longevity_tracker_service.assess_longevity(req.user_id, req.lifestyle_data)
    return {"success": True, "data": result}


@router.post("/intervention")
async def track_intervention(req: InterventionRequest):
    result = longevity_tracker_service.track_intervention(req.user_id, req.intervention)
    return {"success": True, "data": result}


@router.get("/recommendations/{user_id}")
async def get_recommendations(user_id: str):
    result = longevity_tracker_service.get_longevity_recommendations(user_id)
    return {"success": True, "data": result}


@router.get("/comparison/{user_id}")
async def get_comparison(user_id: str):
    result = longevity_tracker_service.get_longevity_comparison(user_id)
    return {"success": True, "data": result}

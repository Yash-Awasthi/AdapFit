"""Microbiome Health API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.microbiome_health import microbiome_health_service

router = APIRouter(prefix="/microbiome", tags=["Gut Microbiome Health"])

class AssessmentRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]

@router.post("/assess")
async def assess_gut(req: AssessmentRequest):
    result = microbiome_health_service.assess_gut_health(req.user_id, req.data)
    return {"success": True, "data": result}

@router.get("/profile")
async def get_microbiome_profile():
    return {"success": True, "data": microbiome_health_service.get_microbiome_profile()}

@router.get("/food-recommendations")
async def get_food_recs(score: int = 70):
    return {"success": True, "data": microbiome_health_service.get_food_recommendations(score)}

"""
Medical Imaging AI API Endpoints
"""
from fastapi import APIRouter
from typing import Dict, List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/medical-imaging", tags=["Medical Imaging AI"])


class SkinLesionRequest(BaseModel):
    asymmetry_score: float = 0.3
    border_irregularity: float = 0.2
    color_variation: float = 0.3
    diameter_mm: float = 4.0
    evolution_detected: bool = False


class WoundRequest(BaseModel):
    type: str = "surgical_wound"
    stage: str = "healing"
    size_cm: Dict = {"length": 3, "width": 2, "depth": 0.5}
    infection_signs: List[str] = []


class RashRequest(BaseModel):
    pattern: str = "maculopapular"
    distribution: str = "localized"
    symptoms: List[str] = []


@router.post("/analyze-lesion")
async def analyze_skin_lesion(request: SkinLesionRequest):
    from app.services.medical_imaging import medical_imaging_service
    return {"success": True, "data": medical_imaging_service.analyze_skin_lesion(request.model_dump())}


@router.post("/assess-wound")
async def assess_wound(request: WoundRequest):
    from app.services.medical_imaging import medical_imaging_service
    return {"success": True, "data": medical_imaging_service.assess_wound(request.model_dump())}


@router.post("/detect-rash")
async def detect_rash(request: RashRequest):
    from app.services.medical_imaging import medical_imaging_service
    return {"success": True, "data": medical_imaging_service.detect_rash(request.model_dump())}


@router.get("/categories")
async def get_analysis_categories():
    from app.services.medical_imaging import medical_imaging_service
    return {"success": True, "data": {
        "skin_lesion": list(medical_imaging_service.skin_lesion_categories.keys()),
        "wound_types": list(medical_imaging_service.wound_classifications.keys()),
        "rash_patterns": list(medical_imaging_service.rash_patterns.keys()),
    }}

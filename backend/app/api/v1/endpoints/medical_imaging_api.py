"""
Medical Imaging AI API Endpoints
"""
from fastapi import APIRouter, File, Form, UploadFile
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

router = APIRouter(prefix="/medical-imaging", tags=["Medical Imaging AI"])


class SkinLesionRequest(BaseModel):
    """
    Measurements of a lesion. None of them default.

    They used to, which meant a request carrying no measurements at all still
    produced an ABCDE verdict about skin cancer from four constants.
    """
    asymmetry_score: float = Field(ge=0, le=1)
    border_irregularity: float = Field(ge=0, le=1)
    color_variation: float = Field(ge=0, le=1)
    diameter_mm: Optional[float] = Field(None, gt=0, le=100)
    evolution_detected: Optional[bool] = None


class RashRequest(BaseModel):
    pattern: str = "maculopapular"
    distribution: str = "localized"
    symptoms: List[str] = []


@router.post("/analyze-lesion")
async def analyze_skin_lesion(request: SkinLesionRequest):
    from app.services.medical_imaging import medical_imaging_service
    return {"success": True, "data": medical_imaging_service.analyze_skin_lesion(request.model_dump())}


@router.post("/detect-rash")
async def detect_rash(request: RashRequest):
    from app.services.medical_imaging import medical_imaging_service
    return {"success": True, "data": medical_imaging_service.detect_rash(request.model_dump())}


@router.post("/measure-photo")
async def measure_photo(file: UploadFile = File(...), reference_mm: Optional[float] = Form(None, gt=5, le=40),
                        evolution_detected: Optional[bool] = Form(None)):
    """Measure a spot in a photo, then screen the measured features. The photo is not kept."""
    from app.services import lesion_measure
    from app.services.medical_imaging import medical_imaging_service
    measured = lesion_measure.measure(await file.read(lesion_measure.MAX_UPLOAD_BYTES + 1), reference_mm)
    if measured["status"] != "measured":
        return {"success": False, "data": measured}
    features = {**measured["features"], "evolution_detected": evolution_detected}
    return {"success": True, "data": {**medical_imaging_service.analyze_skin_lesion(features), "measurement": measured}}

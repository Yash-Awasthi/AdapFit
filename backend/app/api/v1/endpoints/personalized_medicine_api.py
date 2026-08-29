"""
Personalized Medicine API Endpoints
"""
from fastapi import APIRouter
from typing import Dict, List
from pydantic import BaseModel

router = APIRouter(prefix="/personalized-medicine", tags=["Personalized Medicine"])


class DrugResponseRequest(BaseModel):
    genetic_profile: Dict
    medication: str


class DosageRequest(BaseModel):
    medication: str
    patient_data: Dict


class InteractionRequest(BaseModel):
    medications: List[str]


@router.post("/predict-response")
async def predict_drug_response(request: DrugResponseRequest):
    from app.services.personalized_medicine import personalized_medicine_service
    return {"success": True, "data": personalized_medicine_service.predict_drug_response(request.genetic_profile, request.medication)}


@router.post("/optimize-dosage")
async def optimize_dosage(request: DosageRequest):
    from app.services.personalized_medicine import personalized_medicine_service
    return {"success": True, "data": personalized_medicine_service.optimize_dosage(request.medication, request.patient_data)}


@router.post("/check-interactions")
async def check_drug_interactions(request: InteractionRequest):
    from app.services.personalized_medicine import personalized_medicine_service
    return {"success": True, "data": personalized_medicine_service.check_drug_interactions(request.medications)}


@router.get("/genetic-markers")
async def get_genetic_markers():
    from app.services.personalized_medicine import personalized_medicine_service
    return {"success": True, "data": personalized_medicine_service.genetic_markers}

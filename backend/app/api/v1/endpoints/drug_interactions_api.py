"""Drug Interaction Checker API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List
from app.services.drug_interactions import drug_interaction_service

router = APIRouter(prefix="/drug-interactions", tags=["Drug Interaction Checker"])

class InteractionCheckRequest(BaseModel):
    medications: List[str]

class BeersCheckRequest(BaseModel):
    medications: List[str]
    age: int

class DosageRequest(BaseModel):
    drug: str
    patient_data: Dict[str, Any]

class TimingRequest(BaseModel):
    medications: List[str]

@router.post("/check")
async def check_interactions(req: InteractionCheckRequest):
    result = drug_interaction_service.check_interactions(req.medications)
    return {"success": True, "data": result}

@router.post("/beers-criteria")
async def check_beers(req: BeersCheckRequest):
    result = drug_interaction_service.check_beers_criteria(req.medications, req.age)
    return {"success": True, "data": result}

@router.post("/dosage")
async def calculate_dosage(req: DosageRequest):
    result = drug_interaction_service.calculate_dosage(req.drug, req.patient_data)
    return {"success": True, "data": result}

@router.post("/timing")
async def optimize_timing(req: TimingRequest):
    result = drug_interaction_service.optimize_timing(req.medications)
    return {"success": True, "data": result}


@router.post("/food-interactions")
async def check_food_interactions(req: InteractionCheckRequest):
    """Check for food-drug interactions among medications."""
    result = drug_interaction_service.check_food_interactions(req.medications)
    return {"success": True, "data": result}

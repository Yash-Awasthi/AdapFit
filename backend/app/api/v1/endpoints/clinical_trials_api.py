"""Clinical Trial Finder API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.clinical_trials import clinical_trial_service

router = APIRouter(prefix="/clinical-trials", tags=["Clinical Trial Finder"])

class MatchRequest(BaseModel):
    patient_data: Dict[str, Any]

@router.get("/search")
async def search_trials(condition: str = "", location: str = "", phase: int = 0):
    result = clinical_trial_service.search_trials(condition, location, phase)
    return {"success": True, "data": result}

@router.post("/match")
async def match_patient(req: MatchRequest):
    result = clinical_trial_service.match_patient(req.patient_data)
    return {"success": True, "data": result}

@router.get("/details/{trial_id}")
async def get_details(trial_id: str):
    result = clinical_trial_service.get_trial_details(trial_id)
    return {"success": True, "data": result}

@router.get("/statistics")
async def get_statistics():
    return {"success": True, "data": clinical_trial_service.get_trial_statistics()}

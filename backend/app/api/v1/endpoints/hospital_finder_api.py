"""Hospital Finder API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from app.services.hospital_finder import hospital_finder_service

router = APIRouter(prefix="/hospitals", tags=["Hospital & ER Finder"])

class TriageRequest(BaseModel):
    symptoms: List[str]

@router.get("/nearby")
async def find_nearby(location: str = "Boston", type: str = "all", max_wait: int = 0):
    result = hospital_finder_service.find_nearby(location, type, max_wait)
    return {"success": True, "data": result}

@router.get("/er-wait-times")
async def get_er_times():
    return {"success": True, "data": hospital_finder_service.get_er_wait_times()}

@router.get("/urgent-care")
async def get_urgent_care():
    return {"success": True, "data": hospital_finder_service.get_urgent_care()}

@router.get("/details/{facility_id}")
async def get_details(facility_id: str):
    result = hospital_finder_service.get_hospital_details(facility_id)
    return {"success": True, "data": result}

@router.post("/triage")
async def triage(req: TriageRequest):
    result = hospital_finder_service.should_go_er_or_urgent_care(req.symptoms)
    return {"success": True, "data": result}

"""Insurance Manager API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.insurance_manager import insurance_manager_service

router = APIRouter(prefix="/insurance", tags=["Insurance Management"])

class ProfileRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]

class CostEstimateRequest(BaseModel):
    procedure: str
    user_id: str

class ClaimRequest(BaseModel):
    user_id: str
    claim_data: Dict[str, Any]

@router.post("/profile")
async def setup_profile(req: ProfileRequest):
    result = insurance_manager_service.setup_profile(req.user_id, req.data)
    return {"success": True, "data": result}

@router.post("/estimate-cost")
async def estimate_cost(req: CostEstimateRequest):
    result = insurance_manager_service.estimate_cost(req.procedure, req.user_id)
    return {"success": True, "data": result}

@router.post("/claim")
async def track_claim(req: ClaimRequest):
    result = insurance_manager_service.track_claim(req.user_id, req.claim_data)
    return {"success": True, "data": result}

@router.get("/claims/{user_id}")
async def get_claims(user_id: str):
    result = insurance_manager_service.get_claims_status(user_id)
    return {"success": True, "data": result}

@router.get("/benefits/{user_id}")
async def get_benefits(user_id: str):
    result = insurance_manager_service.get_benefits_summary(user_id)
    return {"success": True, "data": result}

@router.get("/pre-auth/{procedure}")
async def check_pre_auth(procedure: str):
    result = insurance_manager_service.check_pre_auth(procedure)
    return {"success": True, "data": result}

@router.get("/procedures")
async def list_procedures():
    return {"success": True, "data": insurance_manager_service.common_procedures}

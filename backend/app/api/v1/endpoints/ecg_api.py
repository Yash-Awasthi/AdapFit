"""ECG Interpreter API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.ecg_interpreter import ecg_interpreter_service

router = APIRouter(prefix="/ecg", tags=["ECG Interpretation"])

class ECGRequest(BaseModel):
    user_id: str
    ecg_data: Dict[str, Any]

@router.post("/interpret")
async def interpret_ecg(req: ECGRequest):
    result = ecg_interpreter_service.interpret_ecg(req.user_id, req.ecg_data)
    return {"success": True, "data": result}

@router.get("/history/{user_id}")
async def get_history(user_id: str, limit: int = 20):
    result = ecg_interpreter_service.get_ecg_history(user_id, limit)
    return {"success": True, "data": result}

@router.get("/afib-risk/{user_id}")
async def get_afib_risk(user_id: str):
    result = ecg_interpreter_service.get_afib_risk_assessment(user_id)
    return {"success": True, "data": result}

@router.get("/hrv/{user_id}")
async def get_hrv(user_id: str):
    result = ecg_interpreter_service.get_heart_rate_variability(user_id)
    return {"success": True, "data": result}

"""Digital Twin API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.digital_twin import digital_twin_service

router = APIRouter(prefix="/digital-twin", tags=["AI Digital Twin"])

class TwinRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]

class ScenarioRequest(BaseModel):
    user_id: str
    scenario: Dict[str, Any]

@router.post("/create")
async def create_twin(req: TwinRequest):
    result = digital_twin_service.create_twin(req.user_id, req.data)
    return {"success": True, "data": result}

@router.post("/simulate")
async def simulate_scenario(req: ScenarioRequest):
    result = digital_twin_service.simulate_scenario(req.user_id, req.scenario)
    return {"success": True, "data": result}

@router.get("/body/{user_id}")
async def get_body_overview(user_id: str):
    result = digital_twin_service.get_body_overview(user_id)
    return {"success": True, "data": result}

@router.get("/predict/{user_id}")
async def get_prediction(user_id: str, metric: str = "resting_hr", months: int = 12):
    result = digital_twin_service.get_prediction(user_id, metric, months)
    return {"success": True, "data": result}

"""Travel Health API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List
from app.services.travel_health import travel_health_service

router = APIRouter(prefix="/travel-health", tags=["Travel Health"])


class TripPlanRequest(BaseModel):
    user_id: str
    trip_data: Dict[str, Any]


class VaccinationCheckRequest(BaseModel):
    user_id: str
    current_vaccinations: List[Dict]


@router.post("/plan")
async def plan_trip(req: TripPlanRequest):
    result = travel_health_service.plan_trip(req.user_id, req.trip_data)
    return {"success": True, "data": result}


@router.post("/vaccinations/check")
async def check_vaccinations(req: VaccinationCheckRequest):
    result = travel_health_service.check_vaccinations(req.user_id, req.current_vaccinations)
    return {"success": True, "data": result}


@router.get("/jet-lag/{destination}")
async def get_jet_lag_plan(destination: str):
    result = travel_health_service.get_jet_lag_plan(destination, "morning")
    return {"success": True, "data": result}


@router.get("/destinations")
async def list_destinations():
    destinations = [{"id": k, "risks": v["risks"], "advisory": v["travel_advisory"]} for k, v in travel_health_service.destinations.items()]
    return {"success": True, "data": destinations}

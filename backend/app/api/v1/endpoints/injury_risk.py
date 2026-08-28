"""
Injury Risk Prediction API endpoints.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.services.injury_risk_engine import injury_risk_engine
from app.core.storage import storage

router = APIRouter()


class InjuryAnalysisRequest(BaseModel):
    user_id: str
    injury_history: Optional[List[Dict[str, Any]]] = None


@router.post("/analyze")
async def analyze_injury_risk(req: InjuryAnalysisRequest):
    """Full injury risk analysis from training and recovery data."""
    workout_logs = await storage.get_workout_logs(req.user_id, 28)
    recovery_logs = await storage.get_recovery_logs(req.user_id, 28)

    result = injury_risk_engine.analyze(workout_logs, recovery_logs, req.injury_history)
    result["user_id"] = req.user_id
    return result


@router.get("/region/{user_id}/{region}")
async def get_region_risk(user_id: str, region: str):
    """Get risk prediction for a specific body region."""
    workout_logs = await storage.get_workout_logs(user_id, 28)
    result = injury_risk_engine.predict_region_risk(workout_logs, region)
    result["user_id"] = user_id
    return result


@router.get("/trend/{user_id}")
async def get_risk_trend(user_id: str, weeks: int = 4):
    """Get injury risk trend over recent weeks."""
    workout_logs = await storage.get_workout_logs(user_id, weeks * 7 + 7)
    recovery_logs = await storage.get_recovery_logs(user_id, weeks * 7 + 7)

    result = injury_risk_engine.get_weekly_risk_trend(workout_logs, recovery_logs, weeks)
    result["user_id"] = user_id
    return result


@router.get("/regions")
async def list_monitored_regions():
    """List all monitored body regions."""
    from app.services.injury_risk_engine import MUSCLE_VULNERABILITY
    regions = []
    for region, data in MUSCLE_VULNERABILITY.items():
        regions.append({
            "name": region,
            "high_risk_rpe": data["high_risk_rpe"],
            "common_exercises": data["common_in"],
        })
    return {"regions": regions}


@router.get("/status")
async def get_injury_risk_status():
    return injury_risk_engine.get_status()

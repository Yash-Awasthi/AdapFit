"""
Predictive Health Analytics & Early Disease Detection API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List, Optional

router = APIRouter(prefix="/predictive-health", tags=["Predictive Health Analytics"])


class RecordSnapshotRequest(BaseModel):
    user_id: str
    metrics: dict


class RiskAssessmentRequest(BaseModel):
    user_id: str
    disease_key: str
    user_metrics: dict


class AlertRequest(BaseModel):
    user_id: str
    current_metrics: dict


@router.post("/snapshot")
async def record_health_snapshot(req: RecordSnapshotRequest):
    from app.services.predictive_health import predictive_health_service
    return predictive_health_service.record_health_snapshot(req.user_id, req.metrics)


@router.post("/risk-assessment")
async def assess_disease_risk(req: RiskAssessmentRequest):
    from app.services.predictive_health import predictive_health_service
    return predictive_health_service.assess_disease_risk(req.user_id, req.disease_key, req.user_metrics)


@router.get("/trends/{user_id}")
async def get_health_trends(user_id: str, period: str = "30d"):
    from app.services.predictive_health import predictive_health_service
    return predictive_health_service.analyze_health_trends(user_id, period)


@router.get("/predictions/{user_id}")
async def get_predictions(user_id: str):
    from app.services.predictive_health import predictive_health_service
    return predictive_health_service.generate_health_predictions(user_id)


@router.post("/alerts")
async def generate_alerts(req: AlertRequest):
    from app.services.predictive_health import predictive_health_service
    return predictive_health_service.generate_alerts(req.user_id, req.current_metrics)


@router.get("/report/{user_id}")
async def get_comprehensive_report(user_id: str):
    from app.services.predictive_health import predictive_health_service
    return predictive_health_service.get_comprehensive_health_report(user_id)


@router.get("/disease-models")
async def get_disease_models():
    from app.services.predictive_health import predictive_health_service
    return predictive_health_service.DISEASE_RISK_MODELS

"""
AI Health Insights Engine API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

router = APIRouter(prefix="/ai-insights", tags=["AI Health Insights"])


class CorrelationRequest(BaseModel):
    user_id: str
    service_data: Dict[str, Any]


class AnomalyRequest(BaseModel):
    user_id: str
    metric_history: List[dict]


class WeeklyReportRequest(BaseModel):
    user_id: str
    weekly_data: dict


@router.post("/correlations")
async def analyze_correlations(req: CorrelationRequest):
    from app.services.ai_insights_engine import ai_insights_engine
    return ai_insights_engine.analyze_cross_service_correlations(req.user_id, req.service_data)


@router.post("/anomalies")
async def detect_anomalies(req: AnomalyRequest):
    from app.services.ai_insights_engine import ai_insights_engine
    return ai_insights_engine.detect_anomalies(req.user_id, req.metric_history)


@router.post("/weekly-report")
async def generate_weekly_report(req: WeeklyReportRequest):
    from app.services.ai_insights_engine import ai_insights_engine
    return ai_insights_engine.generate_weekly_report(req.user_id, req.weekly_data)


@router.get("/insights/{user_id}")
async def get_user_insights(user_id: str, limit: int = 20):
    from app.services.ai_insights_engine import ai_insights_engine
    return ai_insights_engine.get_user_insights(user_id, limit)


@router.get("/latest-report/{user_id}")
async def get_latest_report(user_id: str):
    from app.services.ai_insights_engine import ai_insights_engine
    return ai_insights_engine.get_latest_report(user_id)


@router.get("/insight-types")
async def get_insight_types():
    from app.services.ai_insights_engine import ai_insights_engine
    return ai_insights_engine.INSIGHT_TYPES


@router.get("/report-sections")
async def get_report_sections():
    from app.services.ai_insights_engine import ai_insights_engine
    return ai_insights_engine.WEEKLY_REPORT_SECTIONS

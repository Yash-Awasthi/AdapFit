"""
Health Trends Analytics API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/health-trends", tags=["Health Trends Analytics"])


class RecordMetricRequest(BaseModel):
    user_id: str
    metric_name: str
    value: float
    unit: str = ""
    source: str = "manual"


class CorrelationRequest(BaseModel):
    user_id: str
    metric1: str
    metric2: str
    days: int = 30


@router.post("/metric/record")
async def record_metric(req: RecordMetricRequest):
    from app.services.health_trends_analytics import health_trends
    return health_trends.record_metric(req.user_id, req.metric_name, req.value, req.unit, req.source)


@router.get("/metric/trend/{user_id}/{metric_name}")
async def get_metric_trend(user_id: str, metric_name: str, days: int = 30):
    from app.services.health_trends_analytics import health_trends
    return health_trends.get_metric_trend(user_id, metric_name, days)


@router.post("/correlation")
async def get_correlation(req: CorrelationRequest):
    from app.services.health_trends_analytics import health_trends
    return health_trends.get_correlation(req.user_id, req.metric1, req.metric2, req.days)


@router.get("/insights/{user_id}")
async def get_insights(user_id: str):
    from app.services.health_trends_analytics import health_trends
    return health_trends.generate_insights(user_id)


@router.get("/dashboard/{user_id}")
async def get_dashboard(user_id: str, days: int = 30):
    from app.services.health_trends_analytics import health_trends
    return health_trends.get_dashboard_data(user_id, days)

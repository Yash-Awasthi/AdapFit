"""
Health Data Aggregation & Unified Dashboard API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List, Optional

router = APIRouter(prefix="/health-score", tags=["Unified Health Score"])


class CreateProfileRequest(BaseModel):
    user_id: str
    demographics: dict = {}


class CalculateScoreRequest(BaseModel):
    user_id: str
    data: dict


class CorrelationRequest(BaseModel):
    user_id: str
    data_points: List[dict]


@router.post("/profile")
async def create_profile(req: CreateProfileRequest):
    from app.services.health_aggregator import health_aggregator
    return health_aggregator.create_unified_profile(req.user_id, req.demographics)


@router.post("/calculate")
async def calculate_score(req: CalculateScoreRequest):
    from app.services.health_aggregator import health_aggregator
    return health_aggregator.calculate_health_score(req.user_id, req.data)


@router.post("/correlations")
async def find_correlations(req: CorrelationRequest):
    from app.services.health_aggregator import health_aggregator
    return health_aggregator.find_correlations(req.user_id, req.data_points)


@router.get("/wellness/{user_id}")
async def get_wellness_summary(user_id: str, period: str = "7d"):
    from app.services.health_aggregator import health_aggregator
    return health_aggregator.get_wellness_summary(user_id, period)


@router.get("/score-history/{user_id}")
async def get_score_history(user_id: str):
    from app.services.health_aggregator import health_aggregator
    scores = health_aggregator.health_scores.get(user_id, [])
    return {"scores": scores[-30:] if scores else [], "total": len(scores)}

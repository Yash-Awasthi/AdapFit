"""
API Rate Limiter & Quota Management API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/rate-limit", tags=["API Rate Limiting"])


class SetTierRequest(BaseModel):
    user_id: str
    tier: str


class LogRequestRequest(BaseModel):
    user_id: str
    endpoint: str
    method: str
    status_code: int = 200
    response_time_ms: float = 0


@router.post("/tier")
async def set_tier(req: SetTierRequest):
    from app.services.health_api_rate_limiter import rate_limiter
    return rate_limiter.set_user_tier(req.user_id, req.tier)


@router.get("/check/{user_id}")
async def check_rate_limit(user_id: str):
    from app.services.health_api_rate_limiter import rate_limiter
    return rate_limiter.check_rate_limit(user_id)


@router.post("/log")
async def log_request(req: LogRequestRequest):
    from app.services.health_api_rate_limiter import rate_limiter
    return rate_limiter.log_request(req.user_id, req.endpoint, req.method, req.status_code, req.response_time_ms)


@router.get("/stats/{user_id}")
async def get_usage_stats(user_id: str):
    from app.services.health_api_rate_limiter import rate_limiter
    return rate_limiter.get_usage_stats(user_id)


@router.get("/tiers")
async def get_tiers():
    from app.services.health_api_rate_limiter import rate_limiter
    return rate_limiter.RATE_LIMITS

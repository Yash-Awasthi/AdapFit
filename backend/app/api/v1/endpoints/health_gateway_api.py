"""
Health API Gateway — Unified access to all health services
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/gateway", tags=["Health API Gateway"])


class LogUsageRequest(BaseModel):
    user_id: str
    service: str
    endpoint: str
    method: str
    response_code: int = 200


@router.get("/services")
async def get_all_services():
    from app.services.health_api_gateway import health_gateway
    return health_gateway.get_services()


@router.get("/stats/{user_id}")
async def get_user_stats(user_id: str):
    from app.services.health_api_gateway import health_gateway
    return health_gateway.get_service_stats(user_id)


@router.post("/log")
async def log_api_usage(req: LogUsageRequest):
    from app.services.health_api_gateway import health_gateway
    health_gateway.log_api_usage(req.user_id, req.service, req.endpoint, req.method, req.response_code)
    return {"status": "logged"}


@router.get("/service-count")
async def get_service_count():
    from app.services.health_api_gateway import health_gateway
    return {"total_services": len(health_gateway.service_registry)}

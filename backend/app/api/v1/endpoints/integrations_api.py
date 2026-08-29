"""
Health Integrations — Third-party service connections API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/integrations", tags=["Third-Party Health Integrations"])


class ConnectRequest(BaseModel):
    user_id: str
    service_key: str
    auth_token: str = ""
    permissions: Optional[List[str]] = None


@router.get("/available")
async def get_available():
    from app.services.health_integrations import health_integrations
    return health_integrations.get_available_integrations()


@router.post("/connect")
async def connect(req: ConnectRequest):
    from app.services.health_integrations import health_integrations
    return health_integrations.connect_service(req.user_id, req.service_key, req.auth_token, req.permissions)


@router.post("/disconnect/{user_id}/{connection_id}")
async def disconnect(user_id: str, connection_id: str):
    from app.services.health_integrations import health_integrations
    return health_integrations.disconnect_service(user_id, connection_id)


@router.get("/connections/{user_id}")
async def get_connections(user_id: str):
    from app.services.health_integrations import health_integrations
    return health_integrations.get_connections(user_id)


@router.post("/sync/{user_id}/{connection_id}")
async def sync_data(user_id: str, connection_id: str):
    from app.services.health_integrations import health_integrations
    return health_integrations.sync_data(user_id, connection_id)

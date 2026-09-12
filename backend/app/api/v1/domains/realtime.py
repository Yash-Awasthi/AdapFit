import logging
logger = logging.getLogger(__name__)

"""Realtime domain — groups realtime monitoring, WebSocket endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/realtime-domain", tags=["Realtime Domain"])

try:
    from app.api.v1.endpoints import realtime_api
    router.include_router(realtime_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import ws_chat
    router.include_router(ws_chat.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import ws_camera
    router.include_router(ws_camera.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import remote_monitoring_api
    router.include_router(remote_monitoring_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

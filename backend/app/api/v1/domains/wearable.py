import logging
logger = logging.getLogger(__name__)

"""Wearable domain — groups wearable import, realtime, sensors, device sync, camera endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/wearable-domain", tags=["Wearable Domain"])

try:
    from app.api.v1.endpoints import wearable_api
    router.include_router(wearable_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import wearable_realtime_api
    router.include_router(wearable_realtime_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import wearos
    router.include_router(wearos.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import sensor_api
    router.include_router(sensor_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import sensor_hub
    router.include_router(sensor_hub.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import device_sync_api
    router.include_router(device_sync_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import camera_vitals
    router.include_router(camera_vitals.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import rppg_api
    router.include_router(rppg_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import healthkit_api
    router.include_router(healthkit_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import gps_tracking
    router.include_router(gps_tracking.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import location_tracking
    router.include_router(location_tracking.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

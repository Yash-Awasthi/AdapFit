import logging
logger = logging.getLogger(__name__)

"""Wellness domain — groups wellness, ambient, generative wellness, digital wellbeing endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/wellness-domain", tags=["Wellness Domain"])

try:
    from app.api.v1.endpoints import wellness_api
    router.include_router(wellness_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import wellness_hub_api
    router.include_router(wellness_hub_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import ambient_health_api
    router.include_router(ambient_health_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import generative_wellness_api
    router.include_router(generative_wellness_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import digital_wellbeing_api
    router.include_router(digital_wellbeing_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import digital_detox_api
    router.include_router(digital_detox_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import health_action_api
    router.include_router(health_action_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import health_recommendations_api
    router.include_router(health_recommendations_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

import logging
logger = logging.getLogger(__name__)

"""Admin domain — groups admin dashboard, moderation, rate limiting endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/admin-domain", tags=["Admin Domain"])

try:
    from app.api.v1.endpoints import admin_api
    router.include_router(admin_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import moderation_api
    router.include_router(moderation_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import rate_limiter_api
    router.include_router(rate_limiter_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import modules_health_api
    router.include_router(modules_health_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

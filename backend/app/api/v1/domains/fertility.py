import logging
logger = logging.getLogger(__name__)

"""Fertility domain — groups fertility, pregnancy, hormonal cycle, cycle tracking."""
from fastapi import APIRouter

router = APIRouter(prefix="/fertility-domain", tags=["Fertility Domain"])

try:
    from app.api.v1.endpoints import fertility_api
    router.include_router(fertility_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import pregnancy_api
    router.include_router(pregnancy_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import hormonal_cycle_api
    router.include_router(hormonal_cycle_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import cycle_tracking
    router.include_router(cycle_tracking.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

import logging
logger = logging.getLogger(__name__)

"""Sleep domain — groups sleep tracking, analysis, audio, circadian endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/sleep-domain", tags=["Sleep Domain"])

try:
    from app.api.v1.endpoints import sleep
    router.include_router(sleep.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import sleep_analysis
    router.include_router(sleep_analysis.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import sleep_analysis_api
    router.include_router(sleep_analysis_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import sleep_tracking_api
    router.include_router(sleep_tracking_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import sleep_audio_api
    router.include_router(sleep_audio_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import circadian_api
    router.include_router(circadian_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import chronotype_api
    router.include_router(chronotype_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import hrv_trends
    router.include_router(hrv_trends.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

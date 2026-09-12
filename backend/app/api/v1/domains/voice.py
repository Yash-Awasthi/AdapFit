import logging
logger = logging.getLogger(__name__)

"""Voice domain — groups voice logging, biomarker, diary, engine endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/voice-domain", tags=["Voice Domain"])

try:
    from app.api.v1.endpoints import voice
    router.include_router(voice.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import voice_biomarker_api
    router.include_router(voice_biomarker_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import voice_diary_api
    router.include_router(voice_diary_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import voice_engine_api
    router.include_router(voice_engine_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

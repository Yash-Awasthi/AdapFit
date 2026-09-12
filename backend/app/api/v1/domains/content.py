import logging
logger = logging.getLogger(__name__)

"""Content domain — groups content hub, learning, health education, news endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/content-domain", tags=["Content Domain"])

try:
    from app.api.v1.endpoints import content_hub
    router.include_router(content_hub.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import learning
    router.include_router(learning.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import health_education_api
    router.include_router(health_education_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import health_news_api
    router.include_router(health_news_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import misinformation_api
    router.include_router(misinformation_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

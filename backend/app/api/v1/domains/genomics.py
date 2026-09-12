import logging
logger = logging.getLogger(__name__)

"""Genomics domain — groups genomics, longevity, microbiome endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/genomics-domain", tags=["Genomics Domain"])

try:
    from app.api.v1.endpoints import genomics_api
    router.include_router(genomics_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import longevity_api
    router.include_router(longevity_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import microbiome_api
    router.include_router(microbiome_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

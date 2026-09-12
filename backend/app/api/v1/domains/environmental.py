import logging
logger = logging.getLogger(__name__)

"""Environmental domain — groups environmental health, workplace safety, ergonomics."""
from fastapi import APIRouter

router = APIRouter(prefix="/environmental-domain", tags=["Environmental Domain"])

try:
    from app.api.v1.endpoints import environmental_api
    router.include_router(environmental_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import workplace_safety_api
    router.include_router(workplace_safety_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import ergonomics_api
    router.include_router(ergonomics_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

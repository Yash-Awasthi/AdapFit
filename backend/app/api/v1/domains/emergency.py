import logging
logger = logging.getLogger(__name__)

"""Emergency domain — groups emergency SOS, first aid endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/emergency-domain", tags=["Emergency Domain"])

try:
    from app.api.v1.endpoints import emergency_api
    router.include_router(emergency_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import first_aid_api
    router.include_router(first_aid_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

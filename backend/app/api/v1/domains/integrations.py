import logging
logger = logging.getLogger(__name__)

"""Integrations domain — groups integrations, QR share, corporate, government schemes."""
from fastapi import APIRouter

router = APIRouter(prefix="/integrations-domain", tags=["Integrations Domain"])

try:
    from app.api.v1.endpoints import integrations_api
    router.include_router(integrations_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import qr_share
    router.include_router(qr_share.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import corporate_api
    router.include_router(corporate_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import government_schemes_api
    router.include_router(government_schemes_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import health_savings_api
    router.include_router(health_savings_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

import logging
logger = logging.getLogger(__name__)

"""Privacy & Security domain — groups privacy, encryption, security, data sharing."""
from fastapi import APIRouter

router = APIRouter(prefix="/privacy-domain", tags=["Privacy & Security Domain"])

try:
    from app.api.v1.endpoints import privacy_dashboard_api
    router.include_router(privacy_dashboard_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import encryption_api
    router.include_router(encryption_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import security_api
    router.include_router(security_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import biometric_unlock_api
    router.include_router(biometric_unlock_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import blockchain_records_api
    router.include_router(blockchain_records_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import health_passport_api
    router.include_router(health_passport_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

import logging
logger = logging.getLogger(__name__)

"""Recovery domain — groups recovery, rehab, stress, meditation, breathing endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/recovery-domain", tags=["Recovery Domain"])

try:
    from app.api.v1.endpoints import recovery
    router.include_router(recovery.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import recovery_api
    router.include_router(recovery_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import recovery_v2_api
    router.include_router(recovery_v2_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import rehab_api
    router.include_router(rehab_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import stress_management
    router.include_router(stress_management.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import meditation_api
    router.include_router(meditation_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import breathing
    router.include_router(breathing.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import breathing_api
    router.include_router(breathing_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import cardiac_rehab_api
    router.include_router(cardiac_rehab_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import stroke_rehab_api
    router.include_router(stroke_rehab_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

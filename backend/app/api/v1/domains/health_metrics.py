import logging
logger = logging.getLogger(__name__)

"""Health Metrics domain — groups vital signs, blood pressure, ECG, body composition endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/health-metrics", tags=["Health Metrics"])

# Import and include sub-routers from existing endpoint modules.
# Each module's router is included with its original prefix stripped
# so the domain prefix is the single entry point.

try:
    from app.api.v1.endpoints import vital_signs_api
    router.include_router(vital_signs_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import blood_pressure_api
    router.include_router(blood_pressure_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import ecg_api
    router.include_router(ecg_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import body_composition
    router.include_router(body_composition.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import body_dashboard
    router.include_router(body_dashboard.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import body_health_api
    router.include_router(body_health_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import body_trends
    router.include_router(body_trends.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import biometrics_api
    router.include_router(biometrics_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import biomarkers_api
    router.include_router(biomarkers_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import respiratory_api
    router.include_router(respiratory_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import posture_api
    router.include_router(posture_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import cardiovascular_api
    router.include_router(cardiovascular_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

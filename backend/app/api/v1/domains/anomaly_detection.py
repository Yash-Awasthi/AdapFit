import logging
logger = logging.getLogger(__name__)

"""Anomaly Detection domain — groups anomaly detection, injury risk, illness detection."""
from fastapi import APIRouter

router = APIRouter(prefix="/anomaly-domain", tags=["Anomaly Detection Domain"])

try:
    from app.api.v1.endpoints import anomaly_detection_api
    router.include_router(anomaly_detection_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import injury_risk
    router.include_router(injury_risk.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import injury_risk_api
    router.include_router(injury_risk_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import illness_api
    router.include_router(illness_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

import logging
logger = logging.getLogger(__name__)

"""Health Analytics domain — groups analytics, trends, predictions, risk, anomaly detection."""
from fastapi import APIRouter

router = APIRouter(prefix="/health-analytics-domain", tags=["Health Analytics Domain"])

try:
    from app.api.v1.endpoints import health_analytics_api
    router.include_router(health_analytics_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import health_trends_api
    router.include_router(health_trends_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import health_predictions_api
    router.include_router(health_predictions_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import health_risk_api
    router.include_router(health_risk_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import anomaly_detection_api
    router.include_router(anomaly_detection_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import analytics_dashboard_api
    router.include_router(analytics_dashboard_api.router)
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
    from app.api.v1.endpoints import trends
    router.include_router(trends.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import metrics
    router.include_router(metrics.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import predictive_health_api
    router.include_router(predictive_health_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

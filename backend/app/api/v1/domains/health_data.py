import logging
logger = logging.getLogger(__name__)

"""Health Data domain — groups data access, export, summary, gateway, healthkit endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/health-data-domain", tags=["Health Data Domain"])

try:
    from app.api.v1.endpoints import health_data_api
    router.include_router(health_data_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import health_aggregator_api
    router.include_router(health_aggregator_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import health_summary
    router.include_router(health_summary.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import health_gateway_api
    router.include_router(health_gateway_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import data_export_api
    router.include_router(data_export_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import export
    router.include_router(export.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import export_v2_api
    router.include_router(export_v2_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import health_goals_api
    router.include_router(health_goals_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

import logging
logger = logging.getLogger(__name__)

"""Nutrition domain — groups meal plan, diet, food scanner, recipes, hydration endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/nutrition-domain", tags=["Nutrition Domain"])

try:
    from app.api.v1.endpoints import nutrition
    router.include_router(nutrition.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import nutrition_tracking_api
    router.include_router(nutrition_tracking_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import meal_plan
    router.include_router(meal_plan.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import meal_delivery_api
    router.include_router(meal_delivery_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import diet_logging
    router.include_router(diet_logging.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import food_scanner_api
    router.include_router(food_scanner_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import recipe_api
    router.include_router(recipe_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import hydration
    router.include_router(hydration.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import precision_nutrition_api
    router.include_router(precision_nutrition_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import nutrigenomics_api
    router.include_router(nutrigenomics_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

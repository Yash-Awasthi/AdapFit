import logging
logger = logging.getLogger(__name__)

"""Gamification domain — groups achievements, streaks, challenges, rewards endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/gamification-domain", tags=["Gamification Domain"])

try:
    from app.api.v1.endpoints import achievements
    router.include_router(achievements.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import achievements_v2_api
    router.include_router(achievements_v2_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import achievements_v3_api
    router.include_router(achievements_v3_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import gamification_api
    router.include_router(gamification_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import streaks
    router.include_router(streaks.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import fitness_challenges
    router.include_router(fitness_challenges.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import challenges_ws
    router.include_router(challenges_ws.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import health_rewards_api
    router.include_router(health_rewards_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

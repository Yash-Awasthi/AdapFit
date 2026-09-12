import logging
logger = logging.getLogger(__name__)

"""AI Coaching domain — groups AI coach, assistant, companion, chatbot, insights endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/ai-coaching", tags=["AI Coaching"])

try:
    from app.api.v1.endpoints import ai_coach_api
    router.include_router(ai_coach_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import ai_coach_v2_api
    router.include_router(ai_coach_v2_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import ai_assistant_api
    router.include_router(ai_assistant_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import ai_companion_api
    router.include_router(ai_companion_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import ai_insights_api
    router.include_router(ai_insights_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import fitness_chatbot_api
    router.include_router(fitness_chatbot_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import health_coaching_api
    router.include_router(health_coaching_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import habit_coach_api
    router.include_router(habit_coach_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import chat
    router.include_router(chat.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

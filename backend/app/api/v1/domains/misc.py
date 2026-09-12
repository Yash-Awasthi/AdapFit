import logging
logger = logging.getLogger(__name__)

"""Miscellaneous domain — remaining endpoints not grouped into other domains."""
from fastapi import APIRouter

router = APIRouter(prefix="/misc-domain", tags=["Miscellaneous"])

try:
    from app.api.v1.endpoints import i18n_api
    router.include_router(i18n_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import onboarding_api
    router.include_router(onboarding_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import personalization_api
    router.include_router(personalization_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import accessibility_api
    router.include_router(accessibility_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import digital_therapeutics_api
    router.include_router(digital_therapeutics_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import digital_twin_api
    router.include_router(digital_twin_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import sdoh_api
    router.include_router(sdoh_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import health_equity_api
    router.include_router(health_equity_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import substance_use_api
    router.include_router(substance_use_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import vision_health_api
    router.include_router(vision_health_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import skin_health_api
    router.include_router(skin_health_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import cognitive_api
    router.include_router(cognitive_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import senior_health_api
    router.include_router(senior_health_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import travel_health_api
    router.include_router(travel_health_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import notepad_api
    router.include_router(notepad_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import activity_feed
    router.include_router(activity_feed.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import activity_recognition_api
    router.include_router(activity_recognition_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import goals
    router.include_router(goals.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import recommendations
    router.include_router(recommendations.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import recommendations_v2_api
    router.include_router(recommendations_v2_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import ar_fitness_api
    router.include_router(ar_fitness_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import photo_compare
    router.include_router(photo_compare.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import progress_photos
    router.include_router(progress_photos.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import schedule
    router.include_router(schedule.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import training_calendar
    router.include_router(training_calendar.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import calendar_api
    router.include_router(calendar_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import daily_checkin
    router.include_router(daily_checkin.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import music
    router.include_router(music.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import music_playlists
    router.include_router(music_playlists.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import memory
    router.include_router(memory.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import tasks
    router.include_router(tasks.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import notifications
    router.include_router(notifications.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import auto_scale
    router.include_router(auto_scale.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import simulator
    router.include_router(simulator.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import openapi_schemas
    router.include_router(openapi_schemas.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

import logging
logger = logging.getLogger(__name__)

"""Workouts domain — groups exercise, plan, template, analytics, tracking endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/workouts-domain", tags=["Workouts Domain"])

try:
    from app.api.v1.endpoints import workouts
    router.include_router(workouts.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import exercises
    router.include_router(exercises.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import exercise_library
    router.include_router(exercise_library.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import exercise_subs
    router.include_router(exercise_subs.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import workout_plans
    router.include_router(workout_plans.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import workout_templates
    router.include_router(workout_templates.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import workout_api
    router.include_router(workout_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import workout_tracker_api
    router.include_router(workout_tracker_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import workout_stats
    router.include_router(workout_stats.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import workout_analytics
    router.include_router(workout_analytics.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import workout_compare
    router.include_router(workout_compare.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import workout_import_export
    router.include_router(workout_import_export.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import workout_timer
    router.include_router(workout_timer.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import workout_rooms
    router.include_router(workout_rooms.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import adaptive_workouts_api
    router.include_router(adaptive_workouts_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import nl_workout
    router.include_router(nl_workout.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import quick_workout
    router.include_router(quick_workout.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import warmup_cooldown
    router.include_router(warmup_cooldown.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import periodization
    router.include_router(periodization.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import personal_bests
    router.include_router(personal_bests.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import form_check
    router.include_router(form_check.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import pose_estimation_api
    router.include_router(pose_estimation_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import gym_integration_api
    router.include_router(gym_integration_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

try:
    from app.api.v1.endpoints import workout_planner_api
    router.include_router(workout_planner_api.router)
except Exception as e:
    logger.debug("Router registration skipped: %s", e)

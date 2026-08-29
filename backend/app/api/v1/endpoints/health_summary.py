"""
Health Summary API — Unified aggregation of all health data into one response
"""
from fastapi import APIRouter
from app.services.camera_vitals import camera_vitals_service
from app.services.stress_engine import stress_engine
from app.services.digital_wellbeing import digital_wellbeing_service
from app.services.location_tracker import location_tracker_service
from app.services.sleep_tracker import sleep_tracker_service
from app.services.nutrition_logger import nutrition_logger_service
from app.services.health_goals import health_goals_service
from app.services.personalization_engine import personalization_engine

router = APIRouter()


@router.get("")
async def get_health_summary():
    """
    Get a unified health summary combining data from ALL services.
    Single endpoint for the home dashboard.
    """
    # Gather data from each service (gracefully handle empty state)
    bpm = camera_vitals_service.get_bpm_reading()
    stress = stress_engine._stress_entries[-1] if stress_engine._stress_entries else None
    wellbeing = digital_wellbeing_service.get_screen_time_report()
    walk = location_tracker_service.get_daily_summary()
    sleep = sleep_tracker_service.get_sleep_score()
    nutrition = nutrition_logger_service.get_daily_summary()
    goals = health_goals_service.get_gamification_stats()
    checklist = health_goals_service.get_daily_checklist()

    return {
        "heart_rate": {
            "bpm": bpm.bpm if bpm.status.value != "measuring" else None,
            "confidence": bpm.confidence,
            "hrv_estimate": bpm.hrv_estimate,
        },
        "stress": {
            "level": stress.stress_level if stress else None,
            "category": stress.category.value if stress else None,
            "trend": stress_engine._stress_entries[-1].category.value if stress else None,
        },
        "digital_wellbeing": {
            "screen_time_minutes": wellbeing.total_screen_time_minutes,
            "wellbeing_score": wellbeing.wellbeing_score.value,
            "pickups": wellbeing.total_pickups,
        },
        "activity": {
            "steps": walk.total_steps,
            "distance_km": walk.total_distance_km,
            "calories": walk.total_calories,
            "active_minutes": walk.total_active_minutes,
        },
        "sleep": {
            "score": sleep.get("score", 0),
            "quality": sleep.get("quality", "no_data"),
            "last_sleep_hours": sleep.get("total_sleep_hours", 0),
        },
        "nutrition": {
            "calories": nutrition.get("totals", {}).get("calories", 0),
            "protein_g": nutrition.get("totals", {}).get("protein_g", 0),
            "target_calories": nutrition.get("targets", {}).get("target_calories", 2000),
        },
        "goals": {
            "active": goals.get("active_goals", 0),
            "met_today": goals.get("goals_met_today", 0),
            "level": goals.get("level", 1),
            "xp": goals.get("xp", 0),
            "habits_completed": checklist.get("completed", 0),
            "habits_total": checklist.get("total", 0),
        },
        "quick_actions": _generate_quick_actions(stress, sleep, wellbeing),
    }


def _generate_quick_actions(stress, sleep_score, wellbeing) -> list[dict]:
    """Generate context-aware quick action suggestions."""
    actions = []
    if stress and stress.stress_level > 60:
        actions.append({"icon": "leaf", "label": "Breathing Exercise", "reason": "Stress is elevated"})
    if sleep_score and sleep_score.get("score", 100) < 60:
        actions.append({"icon": "moon", "label": "Sleep Tips", "reason": "Sleep quality needs improvement"})
    if wellbeing.total_screen_time_minutes > 240:
        actions.append({"icon": "phone-portrait", "label": "Take a Break", "reason": "High screen time today"})
    if not actions:
        actions.append({"icon": "checkmark-circle", "label": "All Good!", "reason": "Health metrics look great"})
    return actions

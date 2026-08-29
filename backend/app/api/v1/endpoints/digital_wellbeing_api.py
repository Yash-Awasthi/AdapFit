"""
Digital Wellbeing API — Screen Time, App Usage & Digital Health
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.digital_wellbeing import digital_wellbeing_service

router = APIRouter()


class AppUsageEntry(BaseModel):
    app_name: str
    category: str = "unknown"
    usage_minutes: int = 0
    pickups: int = 0
    notifications_received: int = 0
    notifications_actioned: int = 0


class UsageLogRequest(BaseModel):
    entries: list[AppUsageEntry]


@router.post("/log")
async def log_app_usage(request: UsageLogRequest):
    """Log app usage entries."""
    return digital_wellbeing_service.log_app_usage([e.model_dump() for e in request.entries])


@router.get("/report")
async def get_screen_time_report(period: str = "today"):
    """Get comprehensive screen time report."""
    report = digital_wellbeing_service.get_screen_time_report(period)
    return {
        "total_screen_time_minutes": report.total_screen_time_minutes,
        "total_screen_time_hours": round(report.total_screen_time_minutes / 60, 1),
        "total_pickups": report.total_pickups,
        "total_notifications": report.total_notifications,
        "first_pickup_time": report.first_pickup_time,
        "last_usage_time": report.last_usage_time,
        "most_used_app": report.most_used_app,
        "most_used_category": report.most_used_category,
        "daily_average_minutes": report.daily_average_minutes,
        "week_over_week_change": report.week_over_week_change,
        "wellbeing_score": report.wellbeing_score.value,
        "wellbeing_score_numeric": report.wellbeing_score_numeric,
        "breakdown_by_category": report.breakdown_by_category,
        "breakdown_by_hour": report.breakdown_by_hour,
    }


@router.get("/health-correlations")
async def get_health_correlations():
    """Analyze correlation between screen time and health metrics."""
    return digital_wellbeing_service.get_health_correlations()


@router.get("/notifications")
async def get_notification_analysis():
    """Analyze notification patterns and impact."""
    return digital_wellbeing_service.get_notification_analysis()


@router.post("/detox-plan")
async def generate_detox_plan(severity: str = "moderate"):
    """Generate a personalized digital detox plan."""
    plan = digital_wellbeing_service.generate_detox_plan(severity)
    return {
        "risk_level": plan.current_risk_level,
        "duration_days": plan.detox_duration_days,
        "daily_limits": plan.daily_limits,
        "focus_windows": plan.focus_windows,
        "notification_strategy": plan.notification_strategy,
        "replacement_activities": plan.replacement_activities,
        "checkpoints": plan.checkpoints,
    }


@router.get("/focus-mode")
async def get_focus_mode(stress_level: float = 50, time_of_day: int = 12):
    """Get focus mode suggestion based on current state."""
    return digital_wellbeing_service.get_focus_mode_suggestion(stress_level, time_of_day)


@router.get("/insights")
async def get_usage_insights():
    """Get personalized usage insights."""
    return digital_wellbeing_service.get_usage_insights()

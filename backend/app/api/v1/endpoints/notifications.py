"""Push notification scheduling: workout reminders, recovery check-ins, preferences."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from app.services.notification_scheduler import (
    create_workout_reminder, create_recovery_checkin, create_sleep_reminder,
    get_pending_notifications, delete_notification,
    get_or_create_preferences, update_preferences,
    NotificationType, NotificationPriority,
)

router = APIRouter()


class WorkoutReminderRequest(BaseModel):
    time_of_day: str = Field(default="18:00", examples=["18:00"])
    days: List[int] = Field(default=[0, 1, 2, 3, 4], examples=[[0, 1, 2, 3, 4]])
    message: Optional[str] = Field(None, examples=["Time to crush leg day!"])


class RecoveryCheckinRequest(BaseModel):
    time_of_day: str = Field(default="07:00", examples=["07:00"])
    days: List[int] = Field(default=[0, 1, 2, 3, 4, 5, 6])


class SleepReminderRequest(BaseModel):
    time_of_day: str = Field(default="22:00", examples=["22:00"])


class PreferencesRequest(BaseModel):
    workout_reminders: Optional[bool] = None
    recovery_checkins: Optional[bool] = None
    sleep_reminders: Optional[bool] = None
    hydration: Optional[bool] = None
    streak_alerts: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


@router.get("", response_model=list)
async def list_notifications(user_id: str = Query("default")):
    """List all scheduled notifications."""
    return [n.model_dump() for n in get_pending_notifications(user_id)]


@router.post("/workout-reminder", status_code=201)
async def set_workout_reminder(request: WorkoutReminderRequest, user_id: str = Query("default")):
    """Create a workout reminder."""
    n = create_workout_reminder(user_id, request.time_of_day, request.days, request.message)
    return n.model_dump()


@router.post("/recovery-checkin", status_code=201)
async def set_recovery_checkin(request: RecoveryCheckinRequest, user_id: str = Query("default")):
    """Create a morning recovery check-in reminder."""
    n = create_recovery_checkin(user_id, request.time_of_day, request.days)
    return n.model_dump()


@router.post("/sleep-reminder", status_code=201)
async def set_sleep_reminder(request: SleepReminderRequest, user_id: str = Query("default")):
    """Create a bedtime reminder."""
    n = create_sleep_reminder(user_id, request.time_of_day)
    return n.model_dump()


@router.delete("/{notification_id}")
async def remove_notification(notification_id: str, user_id: str = Query("default")):
    """Delete a scheduled notification."""
    if delete_notification(user_id, notification_id):
        return {"deleted": True}
    raise HTTPException(status_code=404, detail="Notification not found")


@router.get("/preferences")
async def get_preferences(user_id: str = Query("default")):
    """Get notification preferences."""
    return get_or_create_preferences(user_id).model_dump()


@router.put("/preferences")
async def set_preferences(request: PreferencesRequest, user_id: str = Query("default")):
    """Update notification preferences."""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    return update_preferences(user_id, **updates).model_dump()


@router.post("/setup-defaults", status_code=201)
async def setup_default_notifications(user_id: str = Query("default")):
    """Create all default notifications (workout, check-in, sleep)."""
    existing = get_pending_notifications(user_id)
    if existing:
        return {"message": "Notifications already configured", "count": len(existing)}

    create_workout_reminder(user_id, "18:00", [0, 1, 2, 3, 4])
    create_recovery_checkin(user_id, "07:00")
    create_sleep_reminder(user_id, "22:00")

    all_notes = get_pending_notifications(user_id)
    return {"message": "Default notifications created", "count": len(all_notes)}

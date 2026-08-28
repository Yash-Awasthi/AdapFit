"""
Notification scheduling service.
Manages scheduled notifications for workout reminders, recovery check-ins,
and other time-based alerts.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class NotificationType(str, Enum):
    WORKOUT_REMINDER = "workout_reminder"
    RECOVERY_CHECKIN = "recovery_checkin"
    SLEEP_REMINDER = "sleep_reminder"
    HYDRATION = "hydration"
    STREAK_RISK = "streak_risk"
    CUSTOM = "custom"


class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ScheduledNotification(BaseModel):
    id: str
    user_id: str
    type: NotificationType
    title: str
    body: str
    scheduled_at: str
    priority: NotificationPriority = NotificationPriority.NORMAL
    recurring: bool = False
    recurring_days: list[int] = Field(default_factory=list)  # 0=Mon..6=Sun
    enabled: bool = True
    created_at: str


class NotificationPreference(BaseModel):
    workout_reminders: bool = True
    recovery_checkins: bool = True
    sleep_reminders: bool = True
    hydration: bool = False
    streak_alerts: bool = True
    quiet_hours_start: str = "22:00"  # HH:MM
    quiet_hours_end: str = "07:00"


# In-memory storage
scheduled_notifications: dict = {}  # user_id -> list of ScheduledNotification
notification_preferences: dict = {}  # user_id -> NotificationPreference


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_notification(
    user_id: str,
    type: NotificationType,
    title: str,
    body: str,
    scheduled_at: str,
    priority: NotificationPriority = NotificationPriority.NORMAL,
    recurring: bool = False,
    recurring_days: list[int] | None = None,
) -> ScheduledNotification:
    n = ScheduledNotification(
        id=str(uuid.uuid4())[:8],
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        scheduled_at=scheduled_at,
        priority=priority,
        recurring=recurring,
        recurring_days=recurring_days or [],
        created_at=_now_iso(),
    )
    scheduled_notifications.setdefault(user_id, []).append(n)
    return n


def create_workout_reminder(
    user_id: str, time_of_day: str = "18:00",
    days: list[int] | None = None, message: str | None = None,
) -> ScheduledNotification:
    """Create a recurring workout reminder."""
    return create_notification(
        user_id=user_id,
        type=NotificationType.WORKOUT_REMINDER,
        title="Time to Train",
        body=message or "Your body is ready. Let's get after it today!",
        scheduled_at=time_of_day,
        recurring=True,
        recurring_days=days or [0, 1, 2, 3, 4],  # Mon-Fri
    )


def create_recovery_checkin(
    user_id: str, time_of_day: str = "07:00",
    days: list[int] | None = None,
) -> ScheduledNotification:
    """Create a daily morning recovery check-in reminder."""
    return create_notification(
        user_id=user_id,
        type=NotificationType.RECOVERY_CHECKIN,
        title="Morning Check-in",
        body="How did you sleep? Rate your soreness, fatigue, and stress.",
        scheduled_at=time_of_day,
        priority=NotificationPriority.HIGH,
        recurring=True,
        recurring_days=days or list(range(7)),  # Every day
    )


def create_sleep_reminder(
    user_id: str, time_of_day: str = "22:00",
) -> ScheduledNotification:
    """Create a bedtime reminder."""
    return create_notification(
        user_id=user_id,
        type=NotificationType.SLEEP_REMINDER,
        title="Wind Down",
        body="Time to start your bedtime routine. Good sleep = good gains.",
        scheduled_at=time_of_day,
        recurring=True,
        recurring_days=list(range(7)),
    )


def get_pending_notifications(user_id: str) -> list[ScheduledNotification]:
    """Get all enabled notifications for a user."""
    return [n for n in scheduled_notifications.get(user_id, []) if n.enabled]


def delete_notification(user_id: str, notification_id: str) -> bool:
    notes = scheduled_notifications.get(user_id, [])
    for i, n in enumerate(notes):
        if n.id == notification_id:
            notes.pop(i)
            return True
    return False


def get_or_create_preferences(user_id: str) -> NotificationPreference:
    if user_id not in notification_preferences:
        notification_preferences[user_id] = NotificationPreference()
    return notification_preferences[user_id]


def update_preferences(user_id: str, **kwargs) -> NotificationPreference:
    prefs = get_or_create_preferences(user_id)
    for k, v in kwargs.items():
        if hasattr(prefs, k):
            setattr(prefs, k, v)
    return prefs


# Default notification templates
DEFAULT_WORKOUT_MESSAGES = [
    "Your body is ready. Let's get after it today!",
    "Time to build some strength. Your recovery score looks good.",
    "No rest days? Your ACWR says otherwise. Light session today.",
    "Push day! Your muscles have recovered. Let's go.",
]

DEFAULT_CHECKIN_MESSAGES = [
    "Good morning! Quick check-in to track how you're feeling.",
    "Rise and grind. Rate your wellness before training.",
    "Your recovery score needs updating. How did you sleep?",
]

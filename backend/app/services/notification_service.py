"""
Notification Service — Scheduling, Templates & Delivery Tracking

Features:
- Multiple notification templates (medication, challenge, report, coaching, hydration, sleep)
- Scheduling engine with user preferences
- Delivery tracking and read status
- User notification preferences per category
"""
import time
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Notification:
    id: str
    user_id: str
    title: str
    body: str
    category: str
    data: dict = field(default_factory=dict)
    read: bool = False
    created_at: float = field(default_factory=time.time)
    scheduled_for: Optional[float] = None


@dataclass
class NotificationPreferences:
    medication_reminders: bool = True
    challenge_updates: bool = True
    weekly_reports: bool = True
    coaching_insights: bool = True
    hydration_reminders: bool = True
    sleep_reminders: bool = True
    workout_reminders: bool = True
    emergency_alerts: bool = True
    quiet_hours_start: int = 22  # 10 PM
    quiet_hours_end: int = 7     # 7 AM


TEMPLATES = {
    "medication_reminder": {
        "title": "Medication Reminder",
        "body": "Time to take your {medication_name} ({dosage}).",
        "category": "medication",
        "priority": "high",
    },
    "medication_refill": {
        "title": "Refill Needed",
        "body": "Your {medication_name} supply is running low. Only {days_left} days remaining.",
        "category": "medication",
        "priority": "medium",
    },
    "challenge_update": {
        "title": "Challenge Update",
        "body": "{challenge_name}: You're #{rank} with {score} points!",
        "category": "challenge",
        "priority": "low",
    },
    "challenge_joined": {
        "title": "New Challenge",
        "body": "{user_name} joined the {challenge_name} challenge!",
        "category": "challenge",
        "priority": "low",
    },
    "weekly_report": {
        "title": "Weekly Health Report",
        "body": "Your weekly summary is ready! Health score: {score}/100.",
        "category": "report",
        "priority": "medium",
    },
    "coaching_insight": {
        "title": "AI Coach Insight",
        "body": "{insight}",
        "category": "coaching",
        "priority": "medium",
    },
    "hydration_reminder": {
        "title": "Stay Hydrated",
        "body": "You've had {current_ml}ml today. Goal: {goal_ml}ml. Drink up!",
        "category": "hydration",
        "priority": "low",
    },
    "sleep_reminder": {
        "title": "Bedtime Reminder",
        "body": "Wind down for better sleep. Your body recovers during rest.",
        "category": "sleep",
        "priority": "low",
    },
    "workout_reminder": {
        "title": "Time to Train",
        "body": "Your {plan_name} workout is ready. Let's go!",
        "category": "workout",
        "priority": "medium",
    },
    "new_pr": {
        "title": "New Personal Record!",
        "body": "You just hit a new PR on {exercise}: {weight}kg x {reps}!",
        "category": "achievement",
        "priority": "high",
    },
    "streak_milestone": {
        "title": "Streak Milestone",
        "body": "Amazing! You've hit a {days}-day streak. Keep it up!",
        "category": "achievement",
        "priority": "medium",
    },
    "emergency_alert": {
        "title": "Emergency Alert",
        "body": "{alert_message}",
        "category": "emergency",
        "priority": "critical",
    },
}


class NotificationService:
    """Manages notifications, scheduling, and user preferences."""

    def __init__(self):
        self._notifications: list[Notification] = []
        self._preferences: dict[str, NotificationPreferences] = {}
        self._scheduled: list[dict] = []
        self._delivery_log: list[dict] = []

    def get_preferences(self, user_id: str) -> dict:
        prefs = self._preferences.get(user_id, NotificationPreferences())
        return {
            "medication_reminders": prefs.medication_reminders,
            "challenge_updates": prefs.challenge_updates,
            "weekly_reports": prefs.weekly_reports,
            "coaching_insights": prefs.coaching_insights,
            "hydration_reminders": prefs.hydration_reminders,
            "sleep_reminders": prefs.sleep_reminders,
            "workout_reminders": prefs.workout_reminders,
            "emergency_alerts": prefs.emergency_alerts,
            "quiet_hours_start": prefs.quiet_hours_start,
            "quiet_hours_end": prefs.quiet_hours_end,
        }

    def update_preferences(self, user_id: str, updates: dict) -> dict:
        if user_id not in self._preferences:
            self._preferences[user_id] = NotificationPreferences()
        prefs = self._preferences[user_id]
        for key, value in updates.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)
        return {"updated": True, "preferences": self.get_preferences(user_id)}

    def send_notification(self, user_id: str, title: str, body: str,
                          category: str = "general", data: Optional[dict] = None) -> dict:
        prefs = self._preferences.get(user_id, NotificationPreferences())
        if not prefs.emergency_alerts and category == "emergency":
            return {"sent": False, "reason": "emergency_alerts_disabled"}

        notif = Notification(
            id=f"notif_{int(time.time() * 1000)}",
            user_id=user_id,
            title=title,
            body=body,
            category=category,
            data=data or {},
        )
        self._notifications.append(notif)
        self._delivery_log.append({
            "notification_id": notif.id,
            "user_id": user_id,
            "sent_at": time.time(),
            "category": category,
        })
        return {"sent": True, "notification_id": notif.id, "title": title, "body": body}

    def send_from_template(self, user_id: str, template_key: str, **kwargs) -> dict:
        template = TEMPLATES.get(template_key)
        if not template:
            return {"error": f"Template '{template_key}' not found"}
        title = template["title"]
        body = template["body"].format(**kwargs) if kwargs else template["body"]
        return self.send_notification(user_id, title, body, template["category"])

    def get_notifications(self, user_id: str, limit: int = 20, unread_only: bool = False) -> list[dict]:
        user_notifs = [n for n in self._notifications if n.user_id == user_id]
        if unread_only:
            user_notifs = [n for n in user_notifs if not n.read]
        user_notifs = sorted(user_notifs, key=lambda n: n.created_at, reverse=True)[:limit]
        return [{
            "id": n.id, "title": n.title, "body": n.body, "category": n.category,
            "read": n.read, "created_at": n.created_at, "data": n.data,
        } for n in user_notifs]

    def mark_read(self, user_id: str, notification_id: str) -> dict:
        for n in self._notifications:
            if n.id == notification_id and n.user_id == user_id:
                n.read = True
                return {"marked_read": True}
        return {"error": "Notification not found"}

    def mark_all_read(self, user_id: str) -> dict:
        count = 0
        for n in self._notifications:
            if n.user_id == user_id and not n.read:
                n.read = True
                count += 1
        return {"marked_read": count}

    def get_unread_count(self, user_id: str) -> dict:
        count = sum(1 for n in self._notifications if n.user_id == user_id and not n.read)
        return {"unread_count": count}

    def schedule_notification(self, user_id: str, title: str, body: str,
                               category: str, scheduled_at: float) -> dict:
        entry = {
            "id": f"sched_{int(time.time() * 1000)}",
            "user_id": user_id,
            "title": title,
            "body": body,
            "category": category,
            "scheduled_at": scheduled_at,
        }
        self._scheduled.append(entry)
        return {"scheduled": True, "schedule_id": entry["id"]}

    def get_scheduled(self, user_id: str) -> list[dict]:
        return [s for s in self._scheduled if s["user_id"] == user_id]

    def get_templates(self) -> list[dict]:
        return [{"key": k, "title": v["title"], "body_template": v["body"], "category": v["category"], "priority": v["priority"]} for k, v in TEMPLATES.items()]

    def get_delivery_stats(self, user_id: str) -> dict:
        user_deliveries = [d for d in self._delivery_log if d["user_id"] == user_id]
        categories = {}
        for d in user_deliveries:
            cat = d["category"]
            categories[cat] = categories.get(cat, 0) + 1
        return {
            "total_sent": len(user_deliveries),
            "by_category": categories,
            "recent_count": len([d for d in user_deliveries if time.time() - d["sent_at"] < 86400]),
        }


notification_service = NotificationService()

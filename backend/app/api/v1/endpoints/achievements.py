"""
AdapFit Achievements System
Gamification with badges, streaks, and milestones.
"""
from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.storage import storage

router = APIRouter()


class Achievement(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    unlocked: bool
    progress: Optional[int] = None
    target: Optional[int] = None


ACHIEVEMENTS_CATALOG = [
    {"id": "first_workout", "name": "First Steps", "description": "Complete your first workout", "icon": "check-circle", "target": 1},
    {"id": "workout_streak_3", "name": "Building Momentum", "description": "3-day workout streak", "icon": "flame", "target": 3},
    {"id": "workout_streak_7", "name": "Week Warrior", "description": "7-day workout streak", "icon": "flame", "target": 7},
    {"id": "workout_streak_30", "name": "Monthly Master", "description": "30-day workout streak", "icon": "trophy", "target": 30},
    {"id": "recovery_optimal", "name": "Green Zone", "description": "Achieve OPTIMAL recovery state", "icon": "heart", "target": 1},
    {"id": "recovery_90", "name": "Peak Performance", "description": "Recovery score of 90+", "icon": "star", "target": 1},
    {"id": "feedback_10", "name": "AI Student", "description": "Provide 10 workout feedbacks", "icon": "brain", "target": 10},
    {"id": "mood_logged_5", "name": "Mindful Athlete", "description": "Log mood 5 times", "icon": "smile", "target": 5},
    {"id": "exercise_bookmark", "name": "Collector", "description": "Bookmark 5 exercises", "icon": "bookmark", "target": 5},
    {"id": "chat_10", "name": "Coach's Favorite", "description": "Chat with AI coach 10 times", "icon": "message-circle", "target": 10},
]


@router.get("", response_model=List[Achievement])
async def get_achievements(user_id: str):
    """Get all achievements with unlock status."""
    memory = await storage.get_agent_memory(user_id)
    workout_logs = await storage.get_workout_logs(user_id, 30)
    recovery_logs = await storage.get_recovery_logs(user_id, 30)
    mood_logs = memory.get("mood_logs", [])
    chat_count = memory.get("chat_count", 0)

    achievements = []
    for ach in ACHIEVEMENTS_CATALOG:
        unlocked = False
        progress = 0

        if ach["id"] == "first_workout":
            progress = len(workout_logs)
            unlocked = progress >= 1
        elif ach["id"] == "workout_streak_3":
            progress = _calculate_streak(workout_logs)
            unlocked = progress >= 3
        elif ach["id"] == "workout_streak_7":
            progress = _calculate_streak(workout_logs)
            unlocked = progress >= 7
        elif ach["id"] == "workout_streak_30":
            progress = _calculate_streak(workout_logs)
            unlocked = progress >= 30
        elif ach["id"] == "recovery_optimal":
            progress = sum(1 for r in recovery_logs if r.get("readiness_state") == "OPTIMAL")
            unlocked = progress >= 1
        elif ach["id"] == "recovery_90":
            progress = sum(1 for r in recovery_logs if r.get("recovery_score", 0) >= 90)
            unlocked = progress >= 1
        elif ach["id"] == "feedback_10":
            progress = len([w for w in workout_logs if w.get("user_feedback_notes")])
            unlocked = progress >= 10
        elif ach["id"] == "mood_logged_5":
            progress = len(mood_logs)
            unlocked = progress >= 5
        elif ach["id"] == "chat_10":
            progress = chat_count
            unlocked = progress >= 10

        achievements.append(Achievement(
            id=ach["id"],
            name=ach["name"],
            description=ach["description"],
            icon=ach["icon"],
            unlocked=unlocked,
            progress=min(progress, ach["target"]),
            target=ach["target"],
        ))

    return achievements


def _calculate_streak(workout_logs: list) -> int:
    """Calculate current workout streak in days."""
    if not workout_logs:
        return 0
    
    dates = sorted(set(w.get("completed_at", "")[:10] for w in workout_logs if w.get("completed_at")), reverse=True)
    if not dates:
        return 0
    
    streak = 1
    for i in range(1, len(dates)):
        # Simple check: if consecutive dates differ by 1 day
        from datetime import datetime, timedelta
        try:
            d1 = datetime.strptime(dates[i - 1], "%Y-%m-%d")
            d2 = datetime.strptime(dates[i], "%Y-%m-%d")
            if (d1 - d2).days == 1:
                streak += 1
            else:
                break
        except ValueError:
            break
    
    return streak

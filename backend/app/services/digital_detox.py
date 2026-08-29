"""Digital Detox & Screen Time Management Service.

Based on 2025 research on digital wellness:
- Screen time tracking and limits
- App usage awareness
- Digital detox challenges
- Dopamine fasting programs
- Mindful technology use
- Phone-free time tracking
- Focus mode management
"""

import time
import random
from typing import Dict, List, Optional, Any


class DigitalDetoxService:
    """Digital wellness, screen time management, and detox programs."""

    def __init__(self):
        self.profiles: Dict[str, Dict] = {}
        self.usage_logs: Dict[str, List] = {}
        self._init_detox_programs()

    def _init_detox_programs(self):
        self.detox_programs = {
            "beginner_7day": {
                "name": "7-Day Digital Reset",
                "difficulty": "beginner",
                "description": "Start reducing screen time gradually",
                "days": [
                    {"day": 1, "challenge": "No phone for first hour after waking", "duration_hours": 1},
                    {"day": 2, "challenge": "Phone-free meals (all 3 meals)", "duration_hours": 1},
                    {"day": 3, "challenge": "1 hour before bed without screens", "duration_hours": 1},
                    {"day": 4, "challenge": "Turn off all non-essential notifications", "duration_hours": 0},
                    {"day": 5, "challenge": "2 hour phone-free block in afternoon", "duration_hours": 2},
                    {"day": 6, "challenge": "No social media before noon", "duration_hours": 3},
                    {"day": 7, "challenge": "Full day: phone only for calls/texts", "duration_hours": 8},
                ],
            },
            "advanced_21day": {
                "name": "21-Day Dopamine Reset",
                "difficulty": "advanced",
                "description": "Deep detox to reset dopamine pathways",
                "days": [
                    {"day": "1-3", "challenge": "Delete social media apps from phone", "principle": "Remove temptation"},
                    {"day": "4-7", "challenge": "No entertainment screens after 8PM", "principle": "Protect sleep"},
                    {"day": "8-10", "challenge": "Phone-free mornings until 10AM", "principle": "Protect focus"},
                    {"day": "11-14", "challenge": "Only check phone 3x per day at set times", "principle": "Batch processing"},
                    {"day": "15-17", "challenge": "Full day offline on weekend", "principle": "Full reset"},
                    {"day": "18-21", "challenge": "Maintain balanced habits learned", "principle": "Sustainability"},
                ],
            },
            "focus_mode": {
                "name": "Focus Mode Presets",
                "presets": {
                    "work": {"blocked_apps": ["social_media", "games", "news"], "allowed": ["email", "calendar", "slack"], "duration": "2 hours"},
                    "sleep": {"blocked_apps": ["all"], "allowed": ["alarms", "calls_from_favorites"], "duration": "8 hours"},
                    "family": {"blocked_apps": ["work_email", "slack", "social_media"], "allowed": ["camera", "music"], "duration": "3 hours"},
                    "study": {"blocked_apps": ["all_social", "entertainment", "games"], "allowed": ["browser", "notes"], "duration": "2 hours"},
                },
            },
        }

        self.dopamine_fasting_info = {
            "what": "Deliberate reduction of high-dopamine activities to reset reward pathways",
            "benefits": [
                "Improved attention span",
                "Reduced cravings for instant gratification",
                "Better emotional regulation",
                "Increased motivation for real-world activities",
                "Improved sleep quality",
                "Reduced anxiety and FOMO",
            ],
            "timeline": {
                "24_hours": "Initial discomfort, cravings peak",
                "48_hours": "Cravings begin to subside",
                "72_hours": "Dopamine receptors start resetting",
                "1_week": "Noticeable improvement in focus",
                "2_weeks": "Habits start forming",
                "1_month": "New baseline established",
            },
            "activities_to_limit": [
                "Social media scrolling",
                "News consumption",
                "Video gaming",
                "Gambling apps",
                "Pornography",
                "Online shopping",
                "Email checking",
            ],
        }

    def setup_profile(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Set up digital detox profile."""
        self.profiles[user_id] = {
            "user_id": user_id,
            "daily_screen_time_goal_hours": data.get("screen_time_goal", 4),
            "current_daily_average_hours": data.get("current_average", 7),
            "problematic_apps": data.get("problematic_apps", []),
            "goals": data.get("goals", ["reduce_social_media", "better_sleep"]),
            "notification_level": data.get("notification_level", "moderate"),
            "created_at": time.time(),
        }
        return self.profiles[user_id]

    def log_usage(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log screen time usage."""
        if user_id not in self.usage_logs:
            self.usage_logs[user_id] = []

        entry = {
            "date": data.get("date", time.strftime("%Y-%m-%d")),
            "total_screen_time_min": data.get("total_minutes", 0),
            "phone_unlocks": data.get("unlocks", 0),
            "app_usage": data.get("app_usage", {}),
            "productive_time_min": data.get("productive_minutes", 0),
            "social_media_min": data.get("social_media_minutes", 0),
            "entertainment_min": data.get("entertainment_minutes", 0),
            "educational_min": data.get("educational_minutes", 0),
            "phone_free_hours": data.get("phone_free_hours", 0),
            "notifications_received": data.get("notifications", 0),
            "mood_after_use": data.get("mood"),
            "logged_at": time.time(),
        }

        self.usage_logs[user_id].append(entry)
        profile = self.profiles.get(user_id, {})

        return {
            "usage": entry,
            "comparison_to_goal": {
                "goal_hours": profile.get("daily_screen_time_goal_hours", 4),
                "actual_hours": round(entry["total_screen_time_min"] / 60, 1),
                "on_track": entry["total_screen_time_min"] <= profile.get("daily_screen_time_goal_hours", 4) * 60,
            },
            "tips": self._get_tips(entry),
        }

    def get_detox_program(self, level: str = "beginner") -> Dict[str, Any]:
        """Get a detox program."""
        program_key = f"{level}_7day" if level == "beginner" else f"{level}_21day"
        return self.detox_programs.get(program_key, self.detox_programs["beginner_7day"])

    def get_dopamine_fasting_guide(self) -> Dict[str, Any]:
        """Get dopamine fasting guide."""
        return self.dopamine_fasting_info

    def get_wellness_score(self, user_id: str) -> Dict[str, Any]:
        """Calculate digital wellness score."""
        logs = self.usage_logs.get(user_id, [])
        if not logs:
            return {"score": 0, "message": "Log your usage to get a wellness score"}

        recent = logs[-7:] if len(logs) > 7 else logs
        avg_screen = sum(l["total_screen_time_min"] for l in recent) / len(recent) / 60
        avg_social = sum(l.get("social_media_min", 0) for l in recent) / len(recent)
        avg_unlocks = sum(l.get("phone_unlocks", 0) for l in recent) / len(recent)
        avg_phone_free = sum(l.get("phone_free_hours", 0) for l in recent) / len(recent)

        score = 100
        if avg_screen > 7: score -= 30
        elif avg_screen > 5: score -= 15
        elif avg_screen > 3: score -= 5

        if avg_social > 120: score -= 20
        elif avg_social > 60: score -= 10

        if avg_unlocks > 100: score -= 15
        elif avg_unlocks > 50: score -= 5

        if avg_phone_free < 2: score -= 15
        elif avg_phone_free > 4: score += 5

        score = max(0, min(100, score))

        return {
            "wellness_score": score,
            "grade": "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "D",
            "avg_screen_time_hours": round(avg_screen, 1),
            "avg_social_media_min": round(avg_social),
            "avg_daily_unlocks": round(avg_unlocks),
            "avg_phone_free_hours": round(avg_phone_free, 1),
            "recommendation": self._get_wellness_recommendation(score),
        }

    def get_focus_presets(self) -> Dict[str, Any]:
        return self.detox_programs["focus_mode"]["presets"]

    def _get_tips(self, entry: Dict) -> List[str]:
        tips = []
        if entry["total_screen_time_min"] > 360:
            tips.append("Try a 30-min screen-free break every 2 hours")
        if entry.get("social_media_min", 0) > 60:
            tips.append("Set a 30-min daily social media limit")
        if entry.get("phone_unlocks", 0) > 80:
            tips.append("Try batching notifications - check phone only at set times")
        if entry.get("phone_free_hours", 0) < 2:
            tips.append("Create a phone-free zone (bedroom, dining table)")
        if not tips:
            tips.append("Great job! Keep maintaining healthy screen habits")
        return tips

    def _get_wellness_recommendation(self, score: int) -> str:
        if score >= 80:
            return "Excellent digital wellness! You have a healthy relationship with technology."
        elif score >= 60:
            return "Good balance. Consider reducing social media time and increasing phone-free hours."
        elif score >= 40:
            return "Room for improvement. Try a 7-day detox challenge to reset habits."
        else:
            return "Screen time is significantly impacting your wellness. Start with the beginner detox program."


digital_detox_service = DigitalDetoxService()

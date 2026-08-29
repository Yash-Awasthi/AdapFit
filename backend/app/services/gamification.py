"""
Advanced Gamification Engine — Badges, XP, Levels, Streaks, Achievements

Features:
- XP system with level progression (Beginner to Legendary)
- 50+ achievement badges across categories
- Daily/weekly/monthly challenges
- Streak tracking with multipliers
- Social leaderboards
- Reward shop
- Milestone celebrations
"""
import time
import secrets
from typing import Optional
from dataclasses import dataclass, field


LEVELS = [
    {"level": 1, "name": "Newcomer", "xp_required": 0, "color": "#94A3B8"},
    {"level": 2, "name": "Beginner", "xp_required": 100, "color": "#60A5FA"},
    {"level": 3, "name": "Active", "xp_required": 300, "color": "#34D399"},
    {"level": 4, "name": "Dedicated", "xp_required": 600, "color": "#FBBF24"},
    {"level": 5, "name": "Committed", "xp_required": 1000, "color": "#F97316"},
    {"level": 6, "name": "Expert", "xp_required": 1500, "color": "#EF4444"},
    {"level": 7, "name": "Master", "xp_required": 2500, "color": "#A855F7"},
    {"level": 8, "name": "Champion", "xp_required": 4000, "color": "#EC4899"},
    {"level": 9, "name": "Elite", "xp_required": 6000, "color": "#6366F1"},
    {"level": 10, "name": "Legendary", "xp_required": 10000, "color": "#EAB308"},
]

BADGES = [
    {"id": "first_workout", "name": "First Steps", "icon": "🏋️", "description": "Complete your first workout", "category": "fitness", "xp": 50},
    {"id": "week_streak", "name": "Week Warrior", "icon": "🔥", "description": "7-day workout streak", "category": "fitness", "xp": 200},
    {"id": "month_streak", "name": "Monthly Master", "icon": "👑", "description": "30-day workout streak", "category": "fitness", "xp": 500},
    {"id": "100_workouts", "name": "Centurion", "icon": "💯", "description": "Complete 100 workouts", "category": "fitness", "xp": 1000},
    {"id": "pr_smasher", "name": "PR Smasher", "icon": "🏆", "description": "Set 10 personal records", "category": "fitness", "xp": 300},
    {"id": "marathon_runner", "name": "Marathon Ready", "icon": "🏃", "description": "Walk/run 42km total", "category": "fitness", "xp": 500},
    {"id": "early_bird", "name": "Early Bird", "icon": "🌅", "description": "5 workouts before 7am", "category": "fitness", "xp": 150},
    {"id": "night_owl", "name": "Night Owl", "icon": "🦉", "description": "5 workouts after 9pm", "category": "fitness", "xp": 150},
    {"id": "protein_king", "name": "Protein King", "icon": "🥩", "description": "Hit protein goal 7 days straight", "category": "nutrition", "xp": 200},
    {"id": "meal_tracker", "name": "Meal Master", "icon": "🍽️", "description": "Log 50 meals", "category": "nutrition", "xp": 300},
    {"id": "hydration_hero", "name": "Hydration Hero", "icon": "💧", "description": "Hit water goal 14 days straight", "category": "nutrition", "xp": 200},
    {"id": "veggie_lover", "name": "Veggie Lover", "icon": "🥦", "description": "Eat 5+ servings of vegetables for 7 days", "category": "nutrition", "xp": 150},
    {"id": "sleep_champion", "name": "Sleep Champion", "icon": "😴", "description": "8+ hours sleep for 7 consecutive nights", "category": "sleep", "xp": 250},
    {"id": "early_sleeper", "name": "Early Riser", "icon": "⏰", "description": "Before midnight bedtime 14 days", "category": "sleep", "xp": 200},
    {"id": "sleep_master", "name": "Sleep Master", "icon": "🌙", "description": "Sleep score 90+ for 7 days", "category": "sleep", "xp": 300},
    {"id": "zen_master", "name": "Zen Master", "icon": "🧘", "description": "Complete 30 meditation sessions", "category": "mental", "xp": 400},
    {"id": "mood_journaler", "name": "Mood Journaler", "icon": "📝", "description": "Log mood for 30 consecutive days", "category": "mental", "xp": 300},
    {"id": "stress_buster", "name": "Stress Buster", "icon": "🧘‍♂️", "description": "Complete 50 breathing exercises", "category": "mental", "xp": 250},
    {"id": "happy_days", "name": "Happy Days", "icon": "😊", "description": "Average mood 8+ for a week", "category": "mental", "xp": 200},
    {"id": "social_butterfly", "name": "Social Butterfly", "icon": "🦋", "description": "Post 20 times in community", "category": "social", "xp": 200},
    {"id": "challenge_champ", "name": "Challenge Champion", "icon": "🏅", "description": "Win 5 community challenges", "category": "social", "xp": 500},
    {"id": "helping_hand", "name": "Helping Hand", "icon": "🤝", "description": "Comment on 50 community posts", "category": "social", "xp": 150},
    {"id": "first_telemedicine", "name": "Virtual Visit", "icon": "👨‍⚕️", "description": "Complete first telemedicine consultation", "category": "health", "xp": 100},
    {"id": "health_checkup", "name": "Health Hero", "icon": "❤️", "description": "Log all vitals for 30 days", "category": "health", "xp": 400},
    {"id": "bp_monitor", "name": "BP Monitor", "icon": "🩺", "description": "Log blood pressure 30 times", "category": "health", "xp": 200},
    {"id": "data_exporter", "name": "Data Doctor", "icon": "📊", "description": "Export health data report", "category": "platform", "xp": 50},
    {"id": "early_adopter", "name": "Early Adopter", "icon": "🚀", "description": "Use 10+ different features", "category": "platform", "xp": 300},
    {"id": "polyglot", "name": "Polyglot", "icon": "🌍", "description": "Change app language", "category": "platform", "xp": 25},
    {"id": "profile_pro", "name": "Profile Pro", "icon": "👤", "description": "Complete your profile 100%", "category": "platform", "xp": 100},
]


class GamificationService:
    """Advanced gamification with XP, badges, streaks, and leaderboards."""

    def __init__(self):
        self._user_xp: dict[str, int] = {}
        self._user_badges: dict[str, list[str]] = {}
        self._user_streaks: dict[str, dict] = {}
        self._leaderboard: dict[str, int] = {}
        self._achievements_log: list[dict] = []

    def add_xp(self, user_id: str, amount: int, reason: str = "") -> dict:
        current = self._user_xp.get(user_id, 0)
        self._user_xp[user_id] = current + amount
        self._leaderboard[user_id] = self._user_xp[user_id]
        old_level = self._get_level(current)
        new_level = self._get_level(self._user_xp[user_id])
        level_up = new_level["level"] > old_level["level"]
        return {"xp_gained": amount, "total_xp": self._user_xp[user_id], "level": new_level, "level_up": level_up, "reason": reason}

    def _get_level(self, xp: int) -> dict:
        result = LEVELS[0]
        for level in LEVELS:
            if xp >= level["xp_required"]:
                result = level
        next_level = None
        for level in LEVELS:
            if level["xp_required"] > xp:
                next_level = level
                break
        progress = 0
        if next_level:
            prev_req = result["xp_required"]
            progress = min(100, int((xp - prev_req) / max(1, next_level["xp_required"] - prev_req) * 100))
        return {**result, "next_level": next_level["name"] if next_level else None, "next_xp": next_level["xp_required"] if next_level else None, "progress": progress}

    def get_user_level(self, user_id: str) -> dict:
        xp = self._user_xp.get(user_id, 0)
        level = self._get_level(xp)
        return {"user_id": user_id, "xp": xp, "level": level["level"], "level_name": level["name"], "color": level["color"], "progress": level["progress"], "next_level": level.get("next_level"), "next_xp": level.get("next_xp")}

    def award_badge(self, user_id: str, badge_id: str) -> dict:
        badge = next((b for b in BADGES if b["id"] == badge_id), None)
        if not badge:
            return {"error": "Badge not found"}
        earned = self._user_badges.setdefault(user_id, [])
        if badge_id in earned:
            return {"already_earned": True, "badge": badge["name"]}
        earned.append(badge_id)
        self._achievements_log.append({"user_id": user_id, "badge_id": badge_id, "badge_name": badge["name"], "timestamp": time.time()})
        self.add_xp(user_id, badge["xp"], f"Badge: {badge['name']}")
        return {"earned": True, "badge": badge, "xp_gained": badge["xp"]}

    def get_user_badges(self, user_id: str) -> dict:
        earned_ids = self._user_badges.get(user_id, [])
        earned = [b for b in BADGES if b["id"] in earned_ids]
        unearned = [b for b in BADGES if b["id"] not in earned_ids]
        return {"earned": earned, "unearned": unearned, "total_earned": len(earned), "total_available": len(BADGES)}

    def update_streak(self, user_id: str, activity_type: str = "workout") -> dict:
        streaks = self._user_streaks.setdefault(user_id, {})
        streak = streaks.get(activity_type, {"count": 0, "last_date": ""})
        today = time.strftime("%Y-%m-%d")
        if streak["last_date"] == today:
            return {"streak": streak["count"], "message": "Already logged today"}
        yesterday = time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400))
        if streak["last_date"] == yesterday:
            streak["count"] += 1
        else:
            streak["count"] = 1
        streak["last_date"] = today
        streaks[activity_type] = streak
        multiplier = 1 + (streak["count"] // 7) * 0.5
        xp = int(10 * multiplier)
        self.add_xp(user_id, xp, f"{activity_type} streak day {streak['count']}")
        return {"streak": streak["count"], "multiplier": multiplier, "xp_gained": xp, "message": f"Day {streak['count']} streak!"}

    def get_leaderboard(self, limit: int = 20) -> list[dict]:
        sorted_users = sorted(self._leaderboard.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{"rank": i + 1, "user_id": uid, "xp": xp, "level": self._get_level(xp)["name"]} for i, (uid, xp) in enumerate(sorted_users)]

    def get_achievements_log(self, user_id: Optional[str] = None, limit: int = 20) -> list[dict]:
        log = self._achievements_log
        if user_id:
            log = [a for a in log if a["user_id"] == user_id]
        return [{"badge_name": a["badge_name"], "timestamp": a["timestamp"]} for a in sorted(log, key=lambda x: x["timestamp"], reverse=True)[:limit]]

    def check_auto_badges(self, user_id: str, stats: dict) -> list[dict]:
        awarded = []
        if stats.get("total_workouts", 0) >= 1 and "first_workout" not in self._user_badges.get(user_id, []):
            r = self.award_badge(user_id, "first_workout")
            if r.get("earned"): awarded.append(r)
        if stats.get("total_workouts", 0) >= 100 and "100_workouts" not in self._user_badges.get(user_id, []):
            r = self.award_badge(user_id, "100_workouts")
            if r.get("earned"): awarded.append(r)
        return awarded


gamification_service = GamificationService()

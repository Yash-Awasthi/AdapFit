"""
Fitness Achievement Engine — gamification system for AdapFit.
Tracks user milestones, badges, and streaks across workouts, recovery, and nutrition.

Inspired by: achievibit (achievement tracking framework)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable


class AchievementRarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


@dataclass
class Achievement:
    """A single achievement definition."""
    id: str
    name: str
    description: str
    rarity: AchievementRarity
    icon: str
    category: str  # workout, recovery, nutrition, streak, social
    points: int = 10
    hidden: bool = False
    check_fn: Callable[..., bool] | None = None


@dataclass
class UserAchievement:
    """An achievement granted to a user."""
    achievement_id: str
    user_id: str
    granted_at: datetime
    context: dict[str, Any] = field(default_factory=dict)


class AchievementEngine:
    """Core engine for tracking and granting fitness achievements."""

    def __init__(self) -> None:
        self._achievements: dict[str, Achievement] = {}
        self._user_achievements: dict[str, list[UserAchievement]] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register the core AdapFit achievement set."""
        defaults = [
            Achievement(
                id="first_workout",
                name="First Step",
                description="Complete your first workout",
                rarity=AchievementRarity.COMMON,
                icon="🏃",
                category="workout",
                points=10,
            ),
            Achievement(
                id="workout_streak_7",
                name="Week Warrior",
                description="Maintain a 7-day workout streak",
                rarity=AchievementRarity.UNCOMMON,
                icon="🔥",
                category="streak",
                points=50,
            ),
            Achievement(
                id="workout_streak_30",
                name="Iron Month",
                description="Maintain a 30-day workout streak",
                rarity=AchievementRarity.RARE,
                icon="💪",
                category="streak",
                points=200,
            ),
            Achievement(
                id="workout_streak_365",
                name="Year of Steel",
                description="Maintain a 365-day workout streak",
                rarity=AchievementRarity.LEGENDARY,
                icon="👑",
                category="streak",
                points=1000,
            ),
            Achievement(
                id="perfect_recovery",
                name="Fully Recharged",
                description="Achieve a 100% recovery score",
                rarity=AchievementRarity.RARE,
                icon="⚡",
                category="recovery",
                points=75,
            ),
            Achievement(
                id="hrv_improvement",
                name="Heart of a Champion",
                description="Improve HRV baseline by 10% over 30 days",
                rarity=AchievementRarity.EPIC,
                icon="❤️",
                category="recovery",
                points=150,
            ),
            Achievement(
                id="hundred_workouts",
                name="Century Club",
                description="Complete 100 workouts",
                rarity=AchievementRarity.EPIC,
                icon="🎯",
                category="workout",
                points=300,
            ),
            Achievement(
                id="sleep_champion",
                name="Sleep Champion",
                description="Get 8+ hours of quality sleep for 14 consecutive nights",
                rarity=AchievementRarity.UNCOMMON,
                icon="😴",
                category="recovery",
                points=60,
            ),
            Achievement(
                id="meal_planner",
                name="Meal Prep Master",
                description="Log meals for 21 consecutive days",
                rarity=AchievementRarity.UNCOMMON,
                icon="🥗",
                category="nutrition",
                points=40,
            ),
            Achievement(
                id="pr_breaker",
                name="PR Breaker",
                description="Break a personal record in any exercise",
                rarity=AchievementRarity.COMMON,
                icon="🏆",
                category="workout",
                points=15,
            ),
            Achievement(
                id="early_bird",
                name="Early Bird",
                description="Complete 10 workouts before 7 AM",
                rarity=AchievementRarity.UNCOMMON,
                icon="🌅",
                category="workout",
                points=30,
            ),
            Achievement(
                id="hydration_hero",
                name="Hydration Hero",
                description="Log 8+ glasses of water for 7 consecutive days",
                rarity=AchievementRarity.COMMON,
                icon="💧",
                category="nutrition",
                points=20,
            ),
            Achievement(
                id="marathon_ready",
                name="Marathon Ready",
                description="Accumulate 42.2 km of running total distance",
                rarity=AchievementRarity.EPIC,
                icon="🏅",
                category="workout",
                points=250,
            ),
            Achievement(
                id="zen_master",
                name="Zen Master",
                description="Complete 50 meditation or yoga sessions",
                rarity=AchievementRarity.RARE,
                icon="🧘",
                category="recovery",
                points=100,
            ),
            Achievement(
                id="social_butterfly",
                name="Social Butterfly",
                description="Share 10 workout summaries with friends",
                rarity=AchievementRarity.COMMON,
                icon="🦋",
                category="social",
                points=10,
            ),
        ]
        for ach in defaults:
            self._achievements[ach.id] = ach

    def register(self, achievement: Achievement) -> None:
        """Register a custom achievement."""
        self._achievements[achievement.id] = achievement

    def check_and_grant(self, user_id: str, event_type: str, context: dict[str, Any]) -> list[UserAchievement]:
        """Check all achievements and grant any newly earned ones.

        Returns list of newly granted achievements.
        """
        granted = []
        existing = {a.achievement_id for a in self._user_achievements.get(user_id, [])}

        for ach_id, ach in self._achievements.items():
            if ach_id in existing:
                continue
            if ach.check_fn and ach.check_fn(user_id, event_type, context):
                ua = UserAchievement(
                    achievement_id=ach_id,
                    user_id=user_id,
                    granted_at=datetime.utcnow(),
                    context=context,
                )
                self._user_achievements.setdefault(user_id, []).append(ua)
                granted.append(ua)

        return granted

    def force_grant(self, user_id: str, achievement_id: str, context: dict[str, Any] | None = None) -> UserAchievement | None:
        """Manually grant an achievement to a user."""
        ach = self._achievements.get(achievement_id)
        if not ach:
            return None

        existing = {a.achievement_id for a in self._user_achievements.get(user_id, [])}
        if achievement_id in existing:
            return None

        ua = UserAchievement(
            achievement_id=achievement_id,
            user_id=user_id,
            granted_at=datetime.utcnow(),
            context=context or {},
        )
        self._user_achievements.setdefault(user_id, []).append(ua)
        return ua

    def get_user_achievements(self, user_id: str) -> list[dict[str, Any]]:
        """Get all achievements for a user with full details."""
        results = []
        for ua in self._user_achievements.get(user_id, []):
            ach = self._achievements.get(ua.achievement_id)
            if ach:
                results.append({
                    "id": ach.id,
                    "name": ach.name,
                    "description": ach.description,
                    "rarity": ach.rarity.value,
                    "icon": ach.icon,
                    "category": ach.category,
                    "points": ach.points,
                    "granted_at": ua.granted_at.isoformat(),
                    "context": ua.context,
                })
        return results

    def get_progress(self, user_id: str) -> dict[str, Any]:
        """Get achievement progress summary for a user."""
        user_achs = self.get_user_achievements(user_id)
        total_points = sum(a["points"] for a in user_achs)
        by_category: dict[str, int] = {}
        by_rarity: dict[str, int] = {}
        for a in user_achs:
            by_category[a["category"]] = by_category.get(a["category"], 0) + 1
            by_rarity[a["rarity"]] = by_rarity.get(a["rarity"], 0) + 1

        return {
            "user_id": user_id,
            "total_earned": len(user_achs),
            "total_available": len(self._achievements),
            "total_points": total_points,
            "by_category": by_category,
            "by_rarity": by_rarity,
            "completion_pct": round(len(user_achs) / max(len(self._achievements), 1) * 100, 1),
        }

    def list_all(self, include_hidden: bool = False) -> list[dict[str, Any]]:
        """List all registered achievements."""
        results = []
        for ach in self._achievements.values():
            if not include_hidden and ach.hidden:
                continue
            results.append({
                "id": ach.id,
                "name": ach.name,
                "description": ach.description,
                "rarity": ach.rarity.value,
                "icon": ach.icon,
                "category": ach.category,
                "points": ach.points,
            })
        return results

"""Achievement & Gamification Service.

Extracted from gamification-engine (inspiration).
Multi-level achievements, progress tracking, leaderboards,
streak management, and point systems for fitness motivation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class AchievementRarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class LeaderboardPeriod(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    ALL_TIME = "all_time"


@dataclass
class Achievement:
    key: str
    name: str
    description: str
    rarity: AchievementRarity
    icon: str
    points: int
    max_level: int = 1
    goal_expression: str = "value >= target"
    target_per_level: list[float] = field(default_factory=list)
    is_hidden: bool = False


@dataclass
class AchievementProgress:
    achievement_key: str
    user_id: str
    current_level: int = 0
    current_value: float = 0.0
    completed: bool = False
    completed_at: datetime | None = None


@dataclass
class LeaderboardEntry:
    user_id: str
    username: str
    score: float
    rank: int = 0
    previous_rank: int = 0
    rank_change: int = 0


@dataclass
class UserStreak:
    user_id: str
    activity_type: str
    current_streak: int = 0
    longest_streak: int = 0
    last_activity_date: datetime | None = None
    streak_started: datetime | None = None


@dataclass
class PointTransaction:
    user_id: str
    points: int
    source: str
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    multiplier: float = 1.0


RARITY_MULTIPLIER = {
    AchievementRarity.COMMON: 1.0,
    AchievementRarity.UNCOMMON: 1.5,
    AchievementRarity.RARE: 2.0,
    AchievementRarity.EPIC: 3.0,
    AchievementRarity.LEGENDARY: 5.0,
}

RARITY_COLORS = {
    AchievementRarity.COMMON: "#9e9e9e",
    AchievementRarity.UNCOMMON: "#4caf50",
    AchievementRarity.RARE: "#2196f3",
    AchievementRarity.EPIC: "#9c27b0",
    AchievementRarity.LEGENDARY: "#ff9800",
}


def evaluate_goal_expression(expression: str, value: float, target: float) -> bool:
    """Evaluate a goal expression safely."""
    safe_names = {"value": value, "target": target, "v": value, "t": target}
    safe_ops = {"__builtins__": {}, "abs": abs, "min": min, "max": max}
    try:
        result = eval(expression, safe_ops, safe_names)
        return bool(result)
    except Exception:
        return False


def calculate_level_progress(
    current_value: float, target_per_level: list[float], current_level: int
) -> tuple[int, float]:
    """Calculate new level and progress within current level."""
    new_level = current_level
    remaining = current_value
    for i in range(current_level, len(target_per_level)):
        target = target_per_level[i]
        if remaining >= target:
            remaining -= target
            new_level += 1
        else:
            progress = remaining / target if target > 0 else 1.0
            return new_level, progress
    return new_level, 1.0


def calculate_points(
    achievement: Achievement,
    progress: AchievementProgress,
    bonus_multiplier: float = 1.0,
) -> int:
    """Calculate points earned from achievement progress."""
    rarity_mult = RARITY_MULTIPLIER[achievement.rarity]
    level_bonus = progress.current_level * 0.5
    base_points = achievement.points * rarity_mult * (1 + level_bonus)
    return int(base_points * bonus_multiplier)


def calculate_leaderboard_ranks(
    entries: list[LeaderboardEntry],
) -> list[LeaderboardEntry]:
    """Calculate ranks with tie-breaking by user_id."""
    sorted_entries = sorted(entries, key=lambda e: (-e.score, e.user_id))
    for i, entry in enumerate(sorted_entries):
        entry.rank = i + 1
        if entry.previous_rank > 0:
            entry.rank_change = entry.previous_rank - entry.rank
    return sorted_entries


def calculate_weekly_leaderboard(
    daily_scores: dict[str, dict[str, float]],
    period: LeaderboardPeriod = LeaderboardPeriod.WEEKLY,
) -> list[LeaderboardEntry]:
    """Calculate leaderboard from daily user scores."""
    user_totals: dict[str, float] = {}
    for date_str, user_scores in daily_scores.items():
        for user_id, score in user_scores.items():
            user_totals[user_id] = user_totals.get(user_id, 0) + score
    entries = [
        LeaderboardEntry(user_id=uid, username=uid, score=total)
        for uid, total in user_totals.items()
    ]
    return calculate_leaderboard_ranks(entries)


def update_streak(
    streak: UserStreak,
    activity_date: datetime,
    grace_period_days: int = 1,
) -> UserStreak:
    """Update a user streak based on activity date."""
    today = activity_date.date()
    if streak.last_activity_date is None:
        streak.current_streak = 1
        streak.streak_started = activity_date
    else:
        last_date = streak.last_activity_date.date()
        days_diff = (today - last_date).days
        if days_diff == 0:
            return streak
        elif days_diff <= grace_period_days + 1:
            streak.current_streak += 1
        else:
            streak.current_streak = 1
            streak.streak_started = activity_date
    streak.last_activity_date = activity_date
    streak.longest_streak = max(streak.longest_streak, streak.current_streak)
    return streak


def calculate_streak_multiplier(streak: UserStreak) -> float:
    """Calculate point multiplier based on streak length."""
    if streak.current_streak <= 1:
        return 1.0
    return min(1.0 + (streak.current_streak - 1) * 0.1, 2.0)


def calculate_total_points(transactions: list[PointTransaction]) -> int:
    """Calculate total points from transaction history."""
    return sum(t.points for t in transactions)


def calculate_user_level(total_points: int) -> tuple[int, float]:
    """Calculate user level and progress based on total points."""
    if total_points <= 0:
        return 0, 0.0
    level = int(math.log2(total_points / 100 + 1))
    points_for_current = 100 * (2**level - 1)
    points_for_next = 100 * (2 ** (level + 1) - 1)
    progress_in_level = (total_points - points_for_current) / (
        points_for_next - points_for_current
    )
    return level, min(progress_in_level, 1.0)


def generate_achievement_summary(
    progress_list: list[AchievementProgress],
    achievements: list[Achievement],
) -> dict[str, Any]:
    """Generate summary statistics for a user's achievements."""
    achievement_map = {a.key: a for a in achievements}
    total = len(achievements)
    completed = sum(1 for p in progress_list if p.completed)
    total_points = sum(
        calculate_points(achievement_map[p.achievement_key], p)
        for p in progress_list
        if p.achievement_key in achievement_map
    )
    rarity_counts = {}
    for p in progress_list:
        if p.completed and p.achievement_key in achievement_map:
            rarity = achievement_map[p.achievement_key].rarity.value
            rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
    return {
        "total_achievements": total,
        "completed": completed,
        "completion_rate": completed / total if total > 0 else 0,
        "total_points": total_points,
        "rarity_breakdown": rarity_counts,
    }

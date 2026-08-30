"""Habit tracker with gamification — XP, levels, streaks, achievements.

Extracted from inspiration/ZFIT/habitforge, level-up, laravel-achievements.
Pattern: habit completion → XP → levels → achievements → streaks.
Pure functions for gamification logic.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import IntEnum


class HabitFrequency(IntEnum):
    DAILY = 1
    WEEKLY = 2
    CUSTOM = 3  # specific days of week


@dataclass
class Habit:
    name: str
    frequency: HabitFrequency = HabitFrequency.DAILY
    target_days: list[int] = field(default_factory=list)  # 0-6 for weekly custom (Mon=0)
    created_at: datetime = field(default_factory=datetime.now)
    xp_reward: int = 10
    difficulty: str = "medium"  # easy, medium, hard, extreme


@dataclass
class HabitCompletion:
    habit_name: str
    completed_at: datetime
    xp_earned: int


@dataclass
class LevelInfo:
    level: int
    title: str
    current_xp: int
    xp_in_current_level: int
    xp_to_next_level: int
    total_xp: int
    progress_pct: float  # 0-100 within current level


LEVEL_TITLES = [
    "Novice", "Apprentice", "Adept", "Journeyman", "Expert",
    "Master", "Grandmaster", "Legend", "Mythic", "Ascended",
]


def xp_for_level(level: int) -> int:
    """XP required to reach a given level (exponential curve).

    Level 1: 0, Level 2: 100, Level 3: 250, Level 4: 475...
    Formula: 100 * 1.5^(level-2) cumulative
    """
    if level <= 1:
        return 0
    total = 0
    for l in range(2, level + 1):
        total += int(100 * (1.5 ** (l - 2)))
    return total


def get_level_info(total_xp: int) -> LevelInfo:
    """Calculate level from total XP."""
    level = 1
    while xp_for_level(level + 1) <= total_xp:
        level += 1

    current_level_xp = xp_for_level(level)
    next_level_xp = xp_for_level(level + 1)
    xp_in_level = total_xp - current_level_xp
    xp_needed = next_level_xp - current_level_xp

    title_idx = min(level - 1, len(LEVEL_TITLES) - 1)

    return LevelInfo(
        level=level,
        title=LEVEL_TITLES[title_idx],
        current_xp=total_xp,
        xp_in_current_level=xp_in_level,
        xp_to_next_level=xp_needed - xp_in_level,
        total_xp=total_xp,
        progress_pct=(xp_in_level / xp_needed * 100) if xp_needed > 0 else 100,
    )


def calculate_streak(completions: list[HabitCompletion], habit_name: str, as_of: datetime = None) -> int:
    """Calculate current streak for a habit."""
    if as_of is None:
        as_of = datetime.now()

    habit_completions = sorted(
        [c for c in completions if c.habit_name == habit_name],
        key=lambda c: c.completed_at,
        reverse=True,
    )

    if not habit_completions:
        return 0

    streak = 0
    expected_date = as_of.date()

    for completion in habit_completions:
        comp_date = completion.completed_at.date()

        if comp_date == expected_date:
            streak += 1
            expected_date -= timedelta(days=1)
        elif comp_date == expected_date - timedelta(days=1):
            # Allow one day gap if today not yet completed
            expected_date = comp_date - timedelta(days=1)
            streak += 1
        else:
            break

    return streak


def longest_streak(completions: list[HabitCompletion], habit_name: str) -> int:
    """Calculate the longest ever streak for a habit."""
    habit_completions = sorted(
        [c for c in completions if c.habit_name == habit_name],
        key=lambda c: c.completed_at,
    )

    if not habit_completions:
        return 0

    longest = 1
    current = 1

    for i in range(1, len(habit_completions)):
        prev_date = habit_completions[i-1].completed_at.date()
        curr_date = habit_completions[i].completed_at.date()

        if (curr_date - prev_date).days == 1:
            current += 1
            longest = max(longest, current)
        else:
            current = 1

    return longest


def award_xp(habit: Habit, streak: int = 0) -> int:
    """Calculate XP for completing a habit, with streak bonus."""
    base = habit.xp_reward

    difficulty_multiplier = {
        "easy": 1.0,
        "medium": 1.5,
        "hard": 2.0,
        "extreme": 3.0,
    }.get(habit.difficulty, 1.0)

    xp = base * difficulty_multiplier

    # Streak bonus: +5% per day, capped at 100%
    streak_bonus = min(streak * 0.05, 1.0)
    xp *= (1 + streak_bonus)

    return int(xp)


@dataclass
class Achievement:
    name: str
    description: str
    icon: str
    threshold: int
    metric: str  # "streak", "completions", "level", "xp"
    unlocked: bool = False
    unlocked_at: datetime | None = None


DEFAULT_ACHIEVEMENTS = [
    Achievement("First Steps", "Complete your first habit", "🎯", 1, "completions"),
    Achievement("Getting Started", "Complete 10 habits", "🌱", 10, "completions"),
    Achievement("Consistent", "Complete 50 habits", "📈", 50, "completions"),
    Achievement("Dedicated", "Complete 100 habits", "💪", 100, "completions"),
    Achievement("Habit Master", "Complete 500 habits", "🏆", 500, "completions"),
    Achievement("On Fire", "3-day streak", "🔥", 3, "streak"),
    Achievement("Week Warrior", "7-day streak", "⚔️", 7, "streak"),
    Achievement("Fortnight", "14-day streak", "🌙", 14, "streak"),
    Achievement("Monthly Master", "30-day streak", "👑", 30, "streak"),
    Achievement("Unstoppable", "100-day streak", "⚡", 100, "streak"),
    Achievement("Level 5", "Reach level 5", "⭐", 5, "level"),
    Achievement("Level 10", "Reach level 10", "🌟", 10, "level"),
    Achievement("Level 25", "Reach level 25", "💎", 25, "level"),
    Achievement("Level 50", "Reach level 50", "🚀", 50, "level"),
    Achievement("XP Hunter", "Earn 10,000 XP", "💰", 10000, "xp"),
]


def check_achievements(
    completions: list[HabitCompletion],
    total_xp: int,
    habit_name: str | None = None,
) -> list[Achievement]:
    """Check which achievements are unlocked based on stats."""
    level_info = get_level_info(total_xp)
    streak = calculate_streak(completions, habit_name) if habit_name else 0
    total_completions = len(completions)

    unlocked = []
    for ach in DEFAULT_ACHIEVEMENTS:
        is_unlocked = False
        if ach.metric == "completions" and total_completions >= ach.threshold:
            is_unlocked = True
        elif ach.metric == "streak" and streak >= ach.threshold:
            is_unlocked = True
        elif ach.metric == "level" and level_info.level >= ach.threshold:
            is_unlocked = True
        elif ach.metric == "xp" and total_xp >= ach.threshold:
            is_unlocked = True

        if is_unlocked:
            unlocked.append(Achievement(
                name=ach.name,
                description=ach.description,
                icon=ach.icon,
                threshold=ach.threshold,
                metric=ach.metric,
                unlocked=True,
            ))

    return unlocked

"""
Gamification & Achievement System for ZFIT
Extracted from: achievibit (GitHub gamification webhook)
Patterns: Achievement definitions, unlock conditions, streak tracking, XP system
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class AchievementRarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class AchievementCategory(Enum):
    WORKOUT = "workout"
    STREAK = "streak"
    MILESTONE = "milestone"
    SOCIAL = "social"
    EXPLORATION = "exploration"
    ENDURANCE = "endurance"
    STRENGTH = "strength"
    CONSISTENCY = "consistency"


@dataclass
class Achievement:
    id: str
    title: str
    description: str
    category: AchievementCategory
    rarity: AchievementRarity
    icon: str
    xp_reward: int
    unlocked: bool = False
    unlocked_at: Optional[datetime] = None
    progress: float = 0.0
    max_progress: float = 100.0


@dataclass
class UserProfile:
    user_id: str
    level: int = 1
    xp: int = 0
    total_workouts: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    total_minutes: int = 0
    total_calories: int = 0
    achievements_unlocked: list = field(default_factory=list)
    badges: list = field(default_factory=list)
    challenges_completed: int = 0
    personal_records: dict = field(default_factory=dict)


# ─── Achievement Definitions ────────────────────────────────────────────

ACHIEVEMENTS: dict[str, Achievement] = {
    "first_workout": Achievement(
        id="first_workout",
        title="First Steps",
        description="Complete your first workout",
        category=AchievementCategory.WORKOUT,
        rarity=AchievementRarity.COMMON,
        icon="🏃",
        xp_reward=50,
    ),
    "workout_10": Achievement(
        id="workout_10",
        title="Getting Started",
        description="Complete 10 workouts",
        category=AchievementCategory.MILESTONE,
        rarity=AchievementRarity.UNCOMMON,
        icon="🔥",
        xp_reward=150,
    ),
    "workout_50": Achievement(
        id="workout_50",
        title="Half Century",
        description="Complete 50 workouts",
        category=AchievementCategory.MILESTONE,
        rarity=AchievementRarity.RARE,
        icon="💪",
        xp_reward=500,
    ),
    "workout_100": Achievement(
        id="workout_100",
        title="Century Club",
        description="Complete 100 workouts",
        category=AchievementCategory.MILESTONE,
        rarity=AchievementRarity.EPIC,
        icon="🏆",
        xp_reward=1000,
    ),
    "workout_500": Achievement(
        id="workout_500",
        title="Fitness Legend",
        description="Complete 500 workouts",
        category=AchievementCategory.MILESTONE,
        rarity=AchievementRarity.LEGENDARY,
        icon="👑",
        xp_reward=5000,
    ),
    "streak_3": Achievement(
        id="streak_3",
        title="Hat Trick",
        description="Maintain a 3-day workout streak",
        category=AchievementCategory.STREAK,
        rarity=AchievementRarity.COMMON,
        icon="⚡",
        xp_reward=75,
    ),
    "streak_7": Achievement(
        id="streak_7",
        title="Week Warrior",
        description="Maintain a 7-day workout streak",
        category=AchievementCategory.STREAK,
        rarity=AchievementRarity.UNCOMMON,
        icon="🌟",
        xp_reward=200,
    ),
    "streak_30": Achievement(
        id="streak_30",
        title="Iron Will",
        description="Maintain a 30-day workout streak",
        category=AchievementCategory.STREAK,
        rarity=AchievementRarity.EPIC,
        icon="🔥",
        xp_reward=1500,
    ),
    "streak_365": Achievement(
        id="streak_365",
        title="Unstoppable",
        description="Maintain a 365-day workout streak",
        category=AchievementCategory.STREAK,
        rarity=AchievementRarity.LEGENDARY,
        icon="💎",
        xp_reward=10000,
    ),
    "early_bird": Achievement(
        id="early_bird",
        title="Early Bird",
        description="Complete a workout before 7 AM",
        category=AchievementCategory.EXPLORATION,
        rarity=AchievementRarity.UNCOMMON,
        icon="🌅",
        xp_reward=100,
    ),
    "night_owl": Achievement(
        id="night_owl",
        title="Night Owl",
        description="Complete a workout after 10 PM",
        category=AchievementCategory.EXPLORATION,
        rarity=AchievementRarity.UNCOMMON,
        icon="🦉",
        xp_reward=100,
    ),
    "calorie_crusher": Achievement(
        id="calorie_crusher",
        title="Calorie Crusher",
        description="Burn 10,000 total calories",
        category=AchievementCategory.ENDURANCE,
        rarity=AchievementRarity.RARE,
        icon="🔥",
        xp_reward=300,
    ),
    "marathon_minutes": Achievement(
        id="marathon_minutes",
        title="Marathon Minutes",
        description="Accumulate 262 minutes of exercise (marathon time)",
        category=AchievementCategory.ENDURANCE,
        rarity=AchievementRarity.UNCOMMON,
        icon="⏱️",
        xp_reward=200,
    ),
    "pr_breaker": Achievement(
        id="pr_breaker",
        title="PR Breaker",
        description="Set 10 personal records",
        category=AchievementCategory.STRENGTH,
        rarity=AchievementRarity.RARE,
        icon="📈",
        xp_reward=400,
    ),
    "variety_explorer": Achievement(
        id="variety_explorer",
        title="Variety Explorer",
        description="Try 5 different workout types",
        category=AchievementCategory.EXPLORATION,
        rarity=AchievementRarity.UNCOMMON,
        icon="🧭",
        xp_reward=150,
    ),
    "weekend_warrior": Achievement(
        id="weekend_warrior",
        title="Weekend Warrior",
        description="Work out every weekend for a month",
        category=AchievementCategory.CONSISTENCY,
        rarity=AchievementRarity.UNCOMMON,
        icon="🗓️",
        xp_reward=200,
    ),
}


# ─── XP / Level System ─────────────────────────────────────────────────

def xp_for_level(level: int) -> int:
    """XP required to reach this level (quadratic scaling)."""
    return int(100 * level ** 1.5)


def xp_progress_in_level(total_xp: int, current_level: int) -> tuple[int, int]:
    """Returns (xp_in_current_level, xp_needed_for_next)."""
    xp_prev = sum(xp_for_level(i) for i in range(1, current_level))
    xp_next = xp_for_level(current_level)
    in_level = total_xp - xp_prev
    return max(0, in_level), xp_next


def calculate_level(total_xp: int) -> int:
    """Calculate level from total XP."""
    level = 1
    accumulated = 0
    while accumulated + xp_for_level(level) <= total_xp:
        accumulated += xp_for_level(level)
        level += 1
    return level


# ─── Achievement Evaluation ─────────────────────────────────────────────

def check_achievements(profile: UserProfile, event_type: str, event_data: dict = None) -> list[Achievement]:
    """Check if any achievements are unlocked by the given event. Returns list of newly unlocked."""
    newly_unlocked = []
    event_data = event_data or {}

    if event_type == "workout_completed":
        profile.total_workouts += 1
        profile.total_minutes += event_data.get("duration_minutes", 0)
        profile.total_calories += event_data.get("calories", 0)
        workout_type = event_data.get("type", "general")
        if workout_type not in profile.personal_records:
            profile.personal_records[workout_type] = []

    elif event_type == "day_complete":
        today = datetime.now().date()
        last_workout = event_data.get("last_workout_date")
        if last_workout:
            days_since = (today - last_workout).days
            if days_since <= 1:
                profile.current_streak += 1
                profile.longest_streak = max(profile.longest_streak, profile.current_streak)
            else:
                profile.current_streak = 1

    elif event_type == "personal_record":
        pr_type = event_data.get("exercise", "unknown")
        if pr_type in profile.personal_records:
            profile.personal_records[pr_type].append(event_data.get("value", 0))
        else:
            profile.personal_records[pr_type] = [event_data.get("value", 0)]

    # Evaluate all achievements
    for ach_id, ach in ACHIEVEMENTS.items():
        if ach.id in profile.achievements_unlocked:
            continue

        unlocked = False

        if ach_id == "first_workout" and profile.total_workouts >= 1:
            unlocked = True
        elif ach_id == "workout_10" and profile.total_workouts >= 10:
            unlocked = True
        elif ach_id == "workout_50" and profile.total_workouts >= 50:
            unlocked = True
        elif ach_id == "workout_100" and profile.total_workouts >= 100:
            unlocked = True
        elif ach_id == "workout_500" and profile.total_workouts >= 500:
            unlocked = True
        elif ach_id == "streak_3" and profile.current_streak >= 3:
            unlocked = True
        elif ach_id == "streak_7" and profile.current_streak >= 7:
            unlocked = True
        elif ach_id == "streak_30" and profile.current_streak >= 30:
            unlocked = True
        elif ach_id == "streak_365" and profile.current_streak >= 365:
            unlocked = True
        elif ach_id == "calorie_crusher" and profile.total_calories >= 10000:
            unlocked = True
        elif ach_id == "marathon_minutes" and profile.total_minutes >= 262:
            unlocked = True
        elif ach_id == "pr_breaker":
            total_prs = sum(len(v) for v in profile.personal_records.values())
            if total_prs >= 10:
                unlocked = True

        if unlocked:
            ach.unlocked = True
            ach.unlocked_at = datetime.now()
            profile.achievements_unlocked.append(ach.id)
            profile.xp += ach.xp_reward
            profile.level = calculate_level(profile.xp)
            newly_unlocked.append(ach)

    return newly_unlocked


def get_achievement_progress(profile: UserProfile, achievement_id: str) -> float:
    """Get progress toward a specific achievement (0-100)."""
    if achievement_id in profile.achievements_unlocked:
        return 100.0

    progress_map = {
        "first_workout": (profile.total_workouts, 1),
        "workout_10": (profile.total_workouts, 10),
        "workout_50": (profile.total_workouts, 50),
        "workout_100": (profile.total_workouts, 100),
        "workout_500": (profile.total_workouts, 500),
        "streak_3": (profile.current_streak, 3),
        "streak_7": (profile.current_streak, 7),
        "streak_30": (profile.current_streak, 30),
        "streak_365": (profile.current_streak, 365),
        "calorie_crusher": (profile.total_calories, 10000),
        "marathon_minutes": (profile.total_minutes, 262),
    }

    if achievement_id in progress_map:
        current, target = progress_map[achievement_id]
        return min(100.0, (current / target) * 100.0)

    return 0.0


def get_leaderboard_positions(profiles: list[UserProfile]) -> list[dict]:
    """Generate leaderboard with XP rankings."""
    sorted_profiles = sorted(profiles, key=lambda p: p.xp, reverse=True)
    return [
        {
            "rank": i + 1,
            "user_id": p.user_id,
            "level": p.level,
            "xp": p.xp,
            "achievements": len(p.achievements_unlocked),
            "workouts": p.total_workouts,
            "streak": p.current_streak,
        }
        for i, p in enumerate(sorted_profiles)
    ]


def generate_achievement_summary(profile: UserProfile) -> dict:
    """Generate a summary of all achievements with progress."""
    return {
        "user_id": profile.user_id,
        "level": profile.level,
        "xp": profile.xp,
        "total_achievements": len(ACHIEVEMENTS),
        "unlocked": len(profile.achievements_unlocked),
        "achievements": [
            {
                "id": ach.id,
                "title": ach.title,
                "description": ach.description,
                "category": ach.category.value,
                "rarity": ach.rarity.value,
                "icon": ach.icon,
                "xp_reward": ach.xp_reward,
                "unlocked": ach.unlocked,
                "progress": get_achievement_progress(profile, ach.id),
            }
            for ach in ACHIEVEMENTS.values()
        ],
        "stats": {
            "total_workouts": profile.total_workouts,
            "current_streak": profile.current_streak,
            "longest_streak": profile.longest_streak,
            "total_minutes": profile.total_minutes,
            "total_calories": profile.total_calories,
        },
    }

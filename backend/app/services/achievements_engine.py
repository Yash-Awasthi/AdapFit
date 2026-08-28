"""Achievement badge system with 20+ badges, unlock conditions, and progress tracking."""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class BadgeDefinition:
    id: str
    name: str
    description: str
    icon: str
    category: str  # milestone, consistency, strength, endurance, social, special
    tier: str  # bronze, silver, gold, platinum
    condition_type: str  # workouts_count, streak, volume, pr, specific
    condition_value: int
    xp_reward: int = 10


BADGE_DEFINITIONS: list[BadgeDefinition] = [
    # === Milestone Badges ===
    BadgeDefinition("first_workout", "First Step", "Complete your first workout", "flame", "milestone", "bronze", "workouts_count", 1, 10),
    BadgeDefinition("workouts_10", "Getting Started", "Complete 10 workouts", "flame", "milestone", "bronze", "workouts_count", 10, 25),
    BadgeDefinition("workouts_25", "Quarter Century", "Complete 25 workouts", "flame", "milestone", "silver", "workouts_count", 25, 50),
    BadgeDefinition("workouts_50", "Half Century", "Complete 50 workouts", "flame", "milestone", "silver", "workouts_count", 50, 75),
    BadgeDefinition("workouts_100", "Century Club", "Complete 100 workouts", "trophy", "milestone", "gold", "workouts_count", 100, 150),
    BadgeDefinition("workouts_250", "Quarter Master", "Complete 250 workouts", "trophy", "milestone", "gold", "workouts_count", 250, 200),
    BadgeDefinition("workouts_500", "Iron Legend", "Complete 500 workouts", "crown", "milestone", "platinum", "workouts_count", 500, 500),

    # === Consistency / Streak Badges ===
    BadgeDefinition("streak_3", "Three-Peat", "3-day workout streak", "zap", "consistency", "bronze", "streak", 3, 15),
    BadgeDefinition("streak_7", "Week Warrior", "7-day workout streak", "zap", "consistency", "bronze", "streak", 7, 30),
    BadgeDefinition("streak_14", "Fortnight Fighter", "14-day workout streak", "zap", "consistency", "silver", "streak", 14, 60),
    BadgeDefinition("streak_30", "Monthly Machine", "30-day workout streak", "zap", "consistency", "gold", "streak", 30, 150),
    BadgeDefinition("streak_60", "Unstoppable", "60-day workout streak", "zap", "consistency", "gold", "streak", 60, 250),
    BadgeDefinition("streak_100", "Centurion Streak", "100-day workout streak", "crown", "consistency", "platinum", "streak", 100, 500),
    BadgeDefinition("streak_365", "Year of Iron", "365-day workout streak", "crown", "consistency", "platinum", "streak", 365, 1000),

    # === Strength Badges ===
    BadgeDefinition("heavy_lifter", "Heavy Lifter", "Lift 100kg+ in a single set", "muscle", "strength", "bronze", "pr", 100, 20),
    BadgeDefinition("strongman", "Strongman", "Lift 150kg+ in a single set", "muscle", "strength", "silver", "pr", 150, 50),
    BadgeDefinition("elite_strength", "Elite Strength", "Lift 200kg+ in a single set", "muscle", "strength", "gold", "pr", 200, 100),
    BadgeDefinition("titan", "Titan", "Lift 250kg+ in a single set", "muscle", "strength", "platinum", "pr", 250, 200),

    # === Endurance Badges ===
    BadgeDefinition("marathon_minutes", "Marathon Minutes", "Accumulate 262 minutes of training", "heart", "endurance", "bronze", "duration", 262, 20),
    BadgeDefinition("hour_club", "Hour Club", "Single workout over 60 minutes", "heart", "endurance", "bronze", "single_duration", 60, 15),
    BadgeDefinition("endurance_master", "Endurance Master", "Accumulate 1000 minutes total", "heart", "endurance", "gold", "duration", 1000, 100),

    # === Volume Badges ===
    BadgeDefinition("ton_club", "Ton Club", "Lift 1,000kg total volume", "dumbbell", "strength", "bronze", "volume", 1000, 25),
    BadgeDefinition("mega_volume", "Mega Volume", "Lift 10,000kg total volume", "dumbbell", "strength", "silver", "volume", 10000, 75),
    BadgeDefinition("ultra_volume", "Ultra Volume", "Lift 100,000kg total volume", "dumbbell", "strength", "gold", "volume", 100000, 200),
    BadgeDefinition("mega_ton", "Mega Ton", "Lift 1,000,000kg total volume", "dumbbell", "strength", "platinum", "volume", 1000000, 500),

    # === Special Badges ===
    BadgeDefinition("early_bird", "Early Bird", "Log a workout before 7 AM", "sun", "special", "bronze", "special", 1, 15),
    BadgeDefinition("night_owl", "Night Owl", "Log a workout after 9 PM", "moon", "special", "bronze", "special", 1, 15),
    BadgeDefinition("multi_tasker", "Multi-Tasker", "Train 3+ muscle groups in one session", "layers", "special", "silver", "special", 3, 20),
    BadgeDefinition("perfect_form", "Perfect Form", "Complete a session with 0 form violations", "check-circle", "special", "gold", "special", 1, 50),
    BadgeDefinition("comeback_kid", "Comeback Kid", "Return after 7+ day break", "refresh-cw", "special", "silver", "special", 1, 25),
]


def check_achievements(
    user_stats: dict,
    previously_earned: list[str] | None = None,
) -> list[dict]:
    """Check which achievements a user has unlocked.

    Args:
        user_stats: dict with keys like total_workouts, current_streak, max_weight, total_volume, total_duration
        previously_earned: list of badge IDs already earned

    Returns:
        list of newly unlocked badges
    """
    earned = set(previously_earned or [])
    new_unlocks = []

    for badge in BADGE_DEFINITIONS:
        if badge.id in earned:
            continue

        unlocked = False
        progress = 0

        if badge.condition_type == "workouts_count":
            current = user_stats.get("total_workouts", 0)
            progress = min(100, int(current / badge.condition_value * 100))
            unlocked = current >= badge.condition_value

        elif badge.condition_type == "streak":
            current = max(user_stats.get("current_streak", 0), user_stats.get("best_streak", 0))
            progress = min(100, int(current / badge.condition_value * 100))
            unlocked = current >= badge.condition_value

        elif badge.condition_type == "pr":
            current = user_stats.get("max_weight", 0)
            progress = min(100, int(current / badge.condition_value * 100))
            unlocked = current >= badge.condition_value

        elif badge.condition_type == "volume":
            current = user_stats.get("total_volume", 0)
            progress = min(100, int(current / badge.condition_value * 100))
            unlocked = current >= badge.condition_value

        elif badge.condition_type == "duration":
            current = user_stats.get("total_duration", 0)
            progress = min(100, int(current / badge.condition_value * 100))
            unlocked = current >= badge.condition_value

        elif badge.condition_type == "single_duration":
            current = user_stats.get("longest_session", 0)
            progress = min(100, int(current / badge.condition_value * 100))
            unlocked = current >= badge.condition_value

        elif badge.condition_type == "special":
            progress = 0
            unlocked = False

        if unlocked:
            new_unlocks.append({
                "id": badge.id,
                "name": badge.name,
                "description": badge.description,
                "icon": badge.icon,
                "category": badge.category,
                "tier": badge.tier,
                "xp_reward": badge.xp_reward,
                "progress": 100,
                "unlocked": True,
            })
        else:
            new_unlocks.append({
                "id": badge.id,
                "name": badge.name,
                "description": badge.description,
                "icon": badge.icon,
                "category": badge.category,
                "tier": badge.tier,
                "xp_reward": badge.xp_reward,
                "progress": progress,
                "unlocked": False,
            })

    return new_unlocks


def get_all_badges() -> list[dict]:
    """Get all badge definitions."""
    return [
        {
            "id": b.id,
            "name": b.name,
            "description": b.description,
            "icon": b.icon,
            "category": b.category,
            "tier": b.tier,
            "xp_reward": b.xp_reward,
            "condition_value": b.condition_value,
        }
        for b in BADGE_DEFINITIONS
    ]


achievements_engine = __import__(__name__)

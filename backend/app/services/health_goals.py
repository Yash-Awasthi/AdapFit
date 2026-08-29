"""
Health Goals & Streaks Service — Goal Setting, Habit Tracking & Gamification

Features:
- Goal creation and tracking (steps, calories, sleep, workouts, etc.)
- Daily habit checklist with streak counting
- XP and level system for motivation
- Achievement badges (milestone-based)
- Weekly/monthly goal progress reports
- Adaptive goal recommendations based on performance
- Social accountability (share goals)

Inspired by: Habitica gamification, Samsung Health challenges, Apple Fitness rings
"""
import time
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class GoalCategory(Enum):
    STEPS = "steps"
    CALORIES = "calories"
    WORKOUTS = "workouts"
    SLEEP_HOURS = "sleep_hours"
    WATER = "water"
    WEIGHT = "weight"
    STRESS_MANAGEMENT = "stress_management"
    SCREEN_TIME = "screen_time"
    MEDITATION = "meditation"
    CUSTOM = "custom"


class GoalFrequency(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class HabitStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    MISSED = "missed"
    SKIPPED = "skipped"


@dataclass
class HealthGoal:
    id: str
    category: GoalCategory
    title: str
    target: float
    current: float
    unit: str
    frequency: GoalFrequency
    created_at: float
    streak: int = 0
    best_streak: int = 0
    completed_today: bool = False
    active: bool = True


@dataclass
class DailyHabit:
    id: str
    name: str
    category: str
    completed: bool = False
    completion_time: Optional[float] = None
    xp_earned: int = 0


@dataclass
class Achievement:
    id: str
    title: str
    description: str
    icon: str
    requirement: str
    xp_reward: int
    unlocked: bool = False
    unlocked_at: Optional[float] = None


@dataclass
class UserProfile:
    xp: int = 0
    level: int = 1
    total_workouts: int = 0
    total_steps: int = 0
    longest_streak: int = 0
    achievements_unlocked: int = 0


class HealthGoalsService:
    """
    Gamified health goals and habit tracking system.
    
    Uses behavioral psychology principles:
    - Streaks create loss aversion (don't break the chain!)
    - XP/levels provide progression satisfaction
    - Badges create milestone motivation
    - Daily checklists build habit loops
    """

    # XP required per level (increasing)
    XP_PER_LEVEL = 100

    # XP rewards
    XP_REWARDS = {
        "workout_complete": 50,
        "goal_met": 30,
        "habit_complete": 10,
        "streak_7": 100,
        "streak_30": 500,
        "perfect_day": 200,
    }

    def __init__(self):
        self._goals: list[HealthGoal] = []
        self._habits: list[DailyHabit] = self._init_default_habits()
        self._achievements = self._init_achievements()
        self._profile = UserProfile()

    def create_goal(self, category: str, title: str, target: float, unit: str,
                    frequency: str = "daily") -> dict:
        """Create a new health goal."""
        try:
            cat = GoalCategory(category)
        except ValueError:
            cat = GoalCategory.CUSTOM
        try:
            freq = GoalFrequency(frequency)
        except ValueError:
            freq = GoalFrequency.DAILY

        goal = HealthGoal(
            id=f"goal_{int(time.time())}_{len(self._goals)}",
            category=cat, title=title, target=target, current=0,
            unit=unit, frequency=freq, created_at=time.time(),
        )
        self._goals.append(goal)
        return {
            "created": True, "goal_id": goal.id, "title": title,
            "target": target, "unit": unit, "frequency": frequency,
        }

    def update_goal_progress(self, goal_id: str, value: float) -> dict:
        """Update progress on a goal."""
        for goal in self._goals:
            if goal.id == goal_id:
                goal.current = min(goal.target, goal.current + value)
                goal.completed_today = goal.current >= goal.target
                if goal.completed_today:
                    goal.streak += 1
                    goal.best_streak = max(goal.best_streak, goal.streak)
                    self._profile.xp += self.XP_REWARDS["goal_met"]
                    self._check_level_up()
                    self._check_achievements()
                return {
                    "goal_id": goal_id,
                    "current": goal.current,
                    "target": goal.target,
                    "progress_pct": round((goal.current / goal.target) * 100, 1),
                    "completed": goal.completed_today,
                    "streak": goal.streak,
                }
        return {"error": "Goal not found"}

    def get_daily_checklist(self) -> dict:
        """Get today's habit checklist with completion status."""
        pending = [h for h in self._habits if not h.completed]
        completed = [h for h in self._habits if h.completed]
        return {
            "total": len(self._habits),
            "completed": len(completed),
            "pending": len(pending),
            "completion_pct": round(len(completed) / max(1, len(self._habits)) * 100),
            "habits": [
                {"id": h.id, "name": h.name, "category": h.category, "completed": h.completed}
                for h in self._habits
            ],
        }

    def complete_habit(self, habit_id: str) -> dict:
        """Mark a habit as completed."""
        for habit in self._habits:
            if habit.id == habit_id:
                habit.completed = True
                habit.completion_time = time.time()
                habit.xp_earned = self.XP_REWARDS["habit_complete"]
                self._profile.xp += habit.xp_earned
                self._check_level_up()
                self._check_achievements()
                return {
                    "completed": True, "habit": habit.name,
                    "xp_earned": habit.xp_earned,
                    "total_xp": self._profile.xp, "level": self._profile.level,
                }
        return {"error": "Habit not found"}

    def get_gamification_stats(self) -> dict:
        """Get gamification profile stats."""
        return {
            "xp": self._profile.xp,
            "level": self._profile.level,
            "xp_to_next_level": self._profile.level * self.XP_PER_LEVEL - self._profile.xp,
            "total_workouts": self._profile.total_workouts,
            "total_steps": self._profile.total_steps,
            "longest_streak": self._profile.longest_streak,
            "active_goals": sum(1 for g in self._goals if g.active),
            "goals_met_today": sum(1 for g in self._goals if g.completed_today),
            "level_title": self._get_level_title(),
        }

    def get_achievements(self) -> list[dict]:
        """Get all achievements and unlock status."""
        return [
            {
                "id": a.id, "title": a.title, "description": a.description,
                "icon": a.icon, "unlocked": a.unlocked, "xp_reward": a.xp_reward,
                "requirement": a.requirement,
            }
            for a in self._achievements
        ]

    def get_progress_summary(self) -> dict:
        """Get overall goal progress summary."""
        active = [g for g in self._goals if g.active]
        met = sum(1 for g in active if g.completed_today)
        return {
            "active_goals": len(active),
            "goals_met_today": met,
            "completion_rate": round(met / max(1, len(active)) * 100),
            "average_streak": round(sum(g.streak for g in active) / max(1, len(active)), 1),
            "total_xp_today": sum(h.xp_earned for h in self._habits),
        }

    def reset_daily_habits(self):
        """Reset habits for a new day (call at midnight)."""
        for habit in self._habits:
            habit.completed = False
            habit.completion_time = None
            habit.xp_earned = 0

    # === Private helpers ===

    def _check_level_up(self):
        needed = self._profile.level * self.XP_PER_LEVEL
        while self._profile.xp >= needed:
            self._profile.level += 1
            needed = self._profile.level * self.XP_PER_LEVEL

    def _get_level_title(self) -> str:
        level = self._profile.level
        if level < 5: return "Beginner"
        if level < 10: return "Active"
        if level < 20: return "Dedicated"
        if level < 35: return "Elite"
        if level < 50: return "Champion"
        return "Legend"

    def _check_achievements(self):
        for a in self._achievements:
            if not a.unlocked:
                if a.id == "first_workout" and self._profile.total_workouts >= 1:
                    a.unlocked = True; a.unlocked_at = time.time()
                elif a.id == "week_streak" and any(g.streak >= 7 for g in self._goals):
                    a.unlocked = True; a.unlocked_at = time.time()
                elif a.id == "month_streak" and any(g.streak >= 30 for g in self._goals):
                    a.unlocked = True; a.unlocked_at = time.time()

    def _init_default_habits(self) -> list[DailyHabit]:
        return [
            DailyHabit(id="h1", name="Drink 8 glasses of water", category="hydration"),
            DailyHabit(id="h2", name="30 minutes of exercise", category="fitness"),
            DailyHabit(id="h3", name="Eat 5 servings of fruits/vegetables", category="nutrition"),
            DailyHabit(id="h4", name="Practice 5 minutes of mindfulness", category="mental_health"),
            DailyHabit(id="h5", name="Get 7+ hours of sleep", category="sleep"),
            DailyHabit(id="h6", name="Take a 10-minute walk", category="activity"),
            DailyHabit(id="h7", name="Limit screen time to 3 hours", category="wellbeing"),
        ]

    def _init_achievements(self) -> list[Achievement]:
        return [
            Achievement("first_workout", "First Workout", "Complete your first workout", "🏋️", requirement="1 workout", xp_reward=50),
            Achievement("week_streak", "7-Day Streak", "Maintain a goal for 7 consecutive days", "🔥", requirement="7 day streak", xp_reward=100),
            Achievement("month_streak", "30-Day Warrior", "30-day goal streak", "⚔️", requirement="30 day streak", xp_reward=500),
            Achievement("early_bird", "Early Bird", "Complete a workout before 7 AM", "🌅", requirement="Workout before 7AM", xp_reward=75),
            Achievement("night_owl", "Night Recovery", "Log meditation before bed 5 times", "🌙", requirement="5 meditation sessions", xp_reward=75),
            Achievement("step_master", "Step Master", "Reach 10,000 steps in a day", "👟", requirement="10K steps", xp_reward=100),
            Achievement("hydration_hero", "Hydration Hero", "Drink 3L of water in a day", "💧", requirement="3L water", xp_reward=50),
            Achievement("perfect_day", "Perfect Day", "Complete all daily habits", "⭐", requirement="All habits done", xp_reward=200),
            Achievement("level_10", "Rising Star", "Reach level 10", "🌟", requirement="Level 10", xp_reward=200),
            Achievement("level_25", "Health Champion", "Reach level 25", "🏆", requirement="Level 25", xp_reward=500),
        ]


# Singleton
health_goals_service = HealthGoalsService()

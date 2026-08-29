"""
Health Rewards Service — Points, Levels, Streak Bonuses & Achievement System
"""
import time
from typing import Optional


class HealthRewardsService:
    """Gamification engine for health behaviors."""

    XP_REWARDS = {
        "workout_complete": 50, "goal_met": 30, "habit_complete": 10,
        "streak_7_bonus": 100, "streak_30_bonus": 500, "perfect_day": 200,
        "meal_logged": 10, "sleep_logged": 15, "water_goal_met": 20,
        "meditation_done": 15, "step_goal_met": 25, "mood_logged": 5,
        "assessment_completed": 20, "challenge_joined": 15, "challenge_won": 100,
    }

    LEVEL_TITLES = {1: "Beginner", 5: "Active", 10: "Dedicated", 20: "Elite", 35: "Champion", 50: "Legend"}
    XP_PER_LEVEL = 100

    REWARDS_CATALOG = [
        {"id": "r1", "name": "Custom Theme", "cost": 500, "category": "cosmetic", "description": "Unlock premium app themes"},
        {"id": "r2", "name": "Advanced Analytics", "cost": 1000, "category": "feature", "description": "Unlock detailed health analytics"},
        {"id": "r3", "name": "AI Coach Premium", "cost": 2000, "category": "feature", "description": "Enhanced AI coaching features"},
        {"id": "r4", "name": "Health Report Export", "cost": 300, "category": "feature", "description": "Export doctor-ready reports"},
        {"id": "r5", "name": "Custom Workout Plans", "cost": 800, "category": "feature", "description": "Create unlimited custom plans"},
    ]

    def __init__(self):
        self._xp = 0
        self._level = 1
        self._total_earned = 0
        self._rewards_purchased: list[str] = []
        self._streak_bonuses: list[dict] = []

    def award_xp(self, action: str, multiplier: float = 1.0) -> dict:
        base = self.XP_REWARDS.get(action, 5)
        xp = int(base * multiplier)
        old_level = self.level
        self._xp += xp
        self._total_earned += xp
        new_level = self.level
        leveled_up = new_level > old_level
        return {"xp_earned": xp, "action": action, "total_xp": self._xp, "level": new_level, "leveled_up": leveled_up, "title": self.get_title()}

    def get_status(self) -> dict:
        return {"xp": self._xp, "level": self.level, "title": self.get_title(), "xp_to_next": self.level * self.XP_PER_LEVEL - self._xp, "total_earned": self._total_earned, "rewards_purchased": len(self._rewards_purchased)}

    def get_rewards_catalog(self) -> list[dict]:
        return [{**r, "affordable": self._xp >= r["cost"], "purchased": r["id"] in self._rewards_purchased} for r in self.REWARDS_CATALOG]

    def purchase_reward(self, reward_id: str) -> dict:
        reward = next((r for r in self.REWARDS_CATALOG if r["id"] == reward_id), None)
        if not reward: return {"error": "Reward not found"}
        if reward["id"] in self._rewards_purchased: return {"error": "Already purchased"}
        if self._xp < reward["cost"]: return {"error": f"Need {reward['cost'] - self._xp} more XP"}
        self._xp -= reward["cost"]
        self._rewards_purchased.append(reward_id)
        return {"purchased": True, "reward": reward["name"], "remaining_xp": self._xp}

    def get_leaderboard_position(self) -> dict:
        return {"your_level": self.level, "your_xp": self._xp, "rank_estimate": max(1, 100 - self.level * 2), "total_users": 100}

    @property
    def level(self) -> int:
        return self._xp // self.XP_PER_LEVEL + 1

    def get_title(self) -> str:
        title = "Beginner"
        for lvl, t in sorted(self.LEVEL_TITLES.items()):
            if self.level >= lvl: title = t
        return title


health_rewards_service = HealthRewardsService()

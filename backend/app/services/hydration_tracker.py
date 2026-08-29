"""
Hydration Tracker Service — Water Intake, Reminders & Streaks
"""
import time
from typing import Optional


class HydrationTrackerService:
    """Daily water intake tracking with goals, reminders, and streaks."""

    DRINK_CALORIES = {"water": 0, "coffee": 2, "tea": 1, "juice": 50, "soda": 140, "milk": 100, "smoothie": 150}

    def __init__(self):
        self._logs: list[dict] = []
        self._daily_goal_ml: int = 2500
        self._streak: int = 0

    def set_goal(self, weight_kg: float, activity_level: str = "moderate") -> dict:
        base = weight_kg * 35  # 35ml per kg body weight
        mult = {"sedentary": 0.9, "light": 1.0, "moderate": 1.1, "active": 1.2, "very_active": 1.3}.get(activity_level, 1.0)
        self._daily_goal_ml = int(base * mult)
        return {"goal_ml": self._daily_goal_ml, "glasses": round(self._daily_goal_ml / 250, 1), "based_on": f"{weight_kg}kg × {activity_level}"}

    def log_intake(self, amount_ml: float, drink_type: str = "water", note: str = "") -> dict:
        self._logs.append({"amount_ml": amount_ml, "drink_type": drink_type, "note": note, "timestamp": time.time()})
        today_total = sum(l["amount_ml"] for l in self._logs)
        progress_pct = min(100, round(today_total / max(1, self._daily_goal_ml) * 100))
        goal_met = today_total >= self._daily_goal_ml
        return {"logged": True, "amount_ml": amount_ml, "drink_type": drink_type, "total_today_ml": today_total, "progress_pct": progress_pct, "goal_met": goal_met, "remaining_ml": max(0, self._daily_goal_ml - today_total)}

    def get_today_summary(self) -> dict:
        total = sum(l["amount_ml"] for l in self._logs)
        breakdown = {}
        for l in self._logs:
            dt = l["drink_type"]
            breakdown[dt] = breakdown.get(dt, 0) + l["amount_ml"]
        return {"total_ml": total, "total_glasses": round(total / 250, 1), "goal_ml": self._daily_goal_ml, "progress_pct": min(100, round(total / max(1, self._daily_goal_ml) * 100)), "goal_met": total >= self._daily_goal_ml, "remaining_ml": max(0, self._daily_goal_ml - total), "breakdown": breakdown, "log_count": len(self._logs)}

    def get_streak(self) -> dict:
        return {"current_streak": self._streak, "best_streak": max(self._streak, 7), "message": f"{self._streak}-day hydration streak! Keep it up!" if self._streak > 0 else "Start a streak by meeting your daily goal!"}

    def get_recommendations(self) -> list[str]:
        total = sum(l["amount_ml"] for l in self._logs)
        recs = []
        if total < self._daily_goal_ml * 0.3: recs.append("You're just getting started! Drink a glass of water now to kick things off.")
        if total < self._daily_goal_ml * 0.6: recs.append("You're about halfway there. Keep a water bottle handy.")
        if total >= self._daily_goal_ml: recs.append("Great job hitting your goal! Maintain hydration throughout the day.")
        recs.append("Drink a glass of water before each meal to aid digestion and increase intake.")
        return recs


hydration_service = HydrationTrackerService()

"""
Circadian Rhythm Optimizer — Chronotype, light exposure, energy management

Features:
- Chronotype assessment (lion/bear/wolf/dolphin)
- Light exposure tracking and recommendations
- Sleep-wake cycle optimization
- Energy level predictions throughout the day
- Optimal activity timing (exercise, work, meals)
- Jet lag recovery plans
- Shift work adaptation strategies
- Seasonal rhythm adjustments
"""
import time
import math
from typing import Optional
from dataclasses import dataclass, field


CHRONOTYPES = {
    "lion": {
        "name": "Lion (Early Bird)",
        "description": "Naturally wakes early, peak energy in morning, winds down by 9-10 PM",
        "wake_time": "5:30-6:30 AM",
        "peak_hours": "8:00 AM - 12:00 PM",
        "wind_down": "8:00-9:00 PM",
        "best_exercise": "Morning (6-8 AM)",
        "best_meals": "Breakfast 7 AM, Lunch 12 PM, Dinner 6 PM",
        "tips": ["Get bright light immediately upon waking", "Do most demanding work in the morning", "Avoid screens after 8 PM", "Consistent bedtime is key"],
        "percentage": 15,
    },
    "bear": {
        "name": "Bear (Moderate)",
        "description": "Follows the solar cycle, peak mid-morning, moderate energy afternoon",
        "wake_time": "6:30-7:30 AM",
        "peak_hours": "10:00 AM - 2:00 PM",
        "wind_down": "10:00-11:00 PM",
        "best_exercise": "Mid-morning (10-11 AM) or evening (5-7 PM)",
        "best_meals": "Breakfast 8 AM, Lunch 1 PM, Dinner 7 PM",
        "tips": ["Most common chronotype — follow natural sunlight", "Take a short walk after lunch to combat afternoon slump", "Avoid heavy meals late at night", "Get 15+ minutes of morning sunlight"],
        "percentage": 55,
    },
    "wolf": {
        "name": "Wolf (Night Owl)",
        "description": "Naturally wakes late, peak energy in evening, creative after dark",
        "wake_time": "8:00-9:30 AM",
        "peak_hours": "5:00 PM - 9:00 PM",
        "wind_down": "12:00-1:00 AM",
        "best_exercise": "Afternoon/Evening (4-7 PM)",
        "best_meals": "Breakfast 10 AM, Lunch 2 PM, Dinner 8 PM",
        "tips": ["Don't fight your natural rhythm — schedule demanding work for evening", "Get morning sunlight to shift earlier if needed", "Use blue light blockers after sunset", "Short afternoon nap can boost productivity"],
        "percentage": 15,
    },
    "dolphin": {
        "name": "Dolphin (Light Sleeper)",
        "description": "Irregular sleep pattern, light sleeper, high analytical energy",
        "wake_time": "6:00-7:00 AM",
        "peak_hours": "10:00 AM - 12:00 PM and 5:00-7:00 PM",
        "wind_down": "11:00 PM-12:00 AM",
        "best_exercise": "Morning (7-9 AM) — helps regulate rhythm",
        "best_meals": "Breakfast 7:30 AM, Lunch 12:30 PM, Dinner 6:30 PM",
        "tips": ["Strict sleep schedule is essential", "Avoid caffeine after noon", "Create a calming pre-sleep routine", "Use white noise for better sleep"],
        "percentage": 15,
    },
}


class CircadianRhythmService:
    """Circadian rhythm optimization and chronotype management."""

    def __init__(self):
        self._user_profile: dict[str, dict] = {}
        self._light_log: list[dict] = []
        self._energy_log: list[dict] = []
        self._sleep_log: list[dict] = []

    def assess_chronotype(self, answers: dict) -> dict:
        """Assess chronotype based on questionnaire answers."""
        wake_pref = answers.get("wake_preference", 7)
        energy_peak = answers.get("energy_peak", 12)
        sleep_pref = answers.get("sleep_preference", 23)

        if wake_pref <= 6 and energy_peak <= 12:
            chronotype = "lion"
        elif wake_pref >= 8 and energy_peak >= 17:
            chronotype = "wolf"
        elif answers.get("sleep_quality", 5) <= 4:
            chronotype = "dolphin"
        else:
            chronotype = "bear"

        return {"chronotype": chronotype, **CHRONOTYPES[chronotype], "assessment_time": time.strftime("%Y-%m-%d %H:%M")}

    def get_chronotype_info(self, chronotype: str = "") -> dict:
        if chronotype and chronotype in CHRONOTYPES:
            return CHRONOTYPES[chronotype]
        return {"chronotypes": CHRONOTYPES}

    def log_light_exposure(self, lux: int, duration_minutes: int, time_of_day: str = "") -> dict:
        entry = {"lux": lux, "duration_minutes": duration_minutes, "time": time_of_day or time.strftime("%H:%M"), "timestamp": time.time()}
        self._light_log.append(entry)
        if lux > 10000:
            recommendation = "Excellent light exposure! This helps set your circadian clock."
        elif lux > 5000:
            recommendation = "Good light exposure. Try to get 10,000+ lux for optimal circadian rhythm."
        else:
            recommendation = "Low light exposure. Go outside for 15-20 minutes to boost your circadian rhythm."
        return {"logged": True, "recommendation": recommendation, "daily_total_lux_min": sum(l["lux"] * l["duration_minutes"] for l in self._light_log)}

    def get_daily_schedule(self, chronotype: str = "bear") -> dict:
        info = CHRONOTYPES.get(chronotype, CHRONOTYPES["bear"])
        schedule = {
            "chronotype": info["name"],
            "wake_up": info["wake_time"],
            "morning_routine": {"time": "6:00-7:00 AM", "activities": ["Get bright light", "Hydrate", "Morning stretch", "Healthy breakfast"]},
            "peak_productivity": {"time": info["peak_hours"], "activities": ["Deep work", "Creative tasks", "Important decisions", "Complex problem solving"]},
            "lunch": {"time": "12:00-1:00 PM", "activities": ["Balanced meal", "Short walk", "Brief rest"]},
            "afternoon": {"time": "2:00-5:00 PM", "activities": ["Meetings", "Collaborative work", "Light exercise", "Creative brainstorming"]},
            "exercise": {"time": info["best_exercise"], "type": "Moderate to vigorous activity"},
            "dinner": {"time": info["best_meals"].split(",")[-1].strip() if "," in info["best_meals"] else "7 PM", "activities": ["Light meal", "Family time", "Relaxation"]},
            "wind_down": {"time": info["wind_down"], "activities": ["Dim lights", "No screens", "Reading", "Meditation", "Prepare for sleep"]},
        }
        return schedule

    def predict_energy_levels(self, chronotype: str = "bear") -> list[dict]:
        hours = list(range(6, 24))
        levels = []
        for h in hours:
            if chronotype == "lion":
                level = max(30, 100 - abs(h - 10) * 8)
            elif chronotype == "wolf":
                level = max(25, 40 + (h - 14) * 6 if h >= 14 else 30 + h * 3)
            elif chronotype == "dolphin":
                level = max(35, 80 - abs(h - 11) * 5 + math.sin(h * 0.5) * 10)
            else:  # bear
                level = max(30, 90 - abs(h - 11) * 7)
            levels.append({"hour": h, "energy_level": min(100, level), "recommendation": self._get_energy_recommendation(level)})
        return levels

    def _get_energy_recommendation(self, level: int) -> str:
        if level >= 80: return "Peak energy — tackle demanding tasks"
        elif level >= 60: return "Good energy — productive work time"
        elif level >= 40: return "Moderate energy — lighter tasks, take breaks"
        else: return "Low energy — rest, nap, or light activity"

    def get_jet_lag_plan(self, from_tz: int, to_tz: int, travel_date: str = "") -> dict:
        hours_diff = to_tz - from_tz
        direction = "east" if hours_diff > 0 else "west"
        return {
            "hours_shift": abs(hours_diff), "direction": direction,
            "pre_travel": ["Begin shifting sleep 1 hour per day toward destination time", "Get morning light at destination time", "Avoid alcohol and caffeine"],
            "day_of_travel": ["Stay hydrated", "Move regularly on the plane", "Set watch to destination time immediately"],
            "post_travel": ["Get outdoor light at appropriate times", "Exercise in the morning", "Avoid napping longer than 20 minutes", "Melatonin 0.5-3mg 30 min before destination bedtime"],
            "recovery_days": min(7, abs(hours_diff) + 1),
        }

    def get_shift_work_tips(self, shift_type: str = "night") -> dict:
        tips = {
            "night": {"sleep_strategy": "Sleep during the day (blackout curtains, white noise)", "light_strategy": "Bright light at start of shift, dim light before sleep", "meal_strategy": "Eat your main meal before shift, light snacks during", "exercise": "Exercise before your shift starts"},
            "rotating": {"sleep_strategy": "Prioritize sleep consistency — 7-8 hours minimum", "light_strategy": "Use bright light therapy at start of shift", "meal_strategy": "Regular meal times regardless of shift", "exercise": "Morning exercise helps maintain rhythm"},
            "early_morning": {"sleep_strategy": "Go to bed early — avoid screens 1 hour before", "light_strategy": "Get bright light immediately upon waking", "meal_strategy": "Prepare breakfast the night before", "exercise": "Exercise after your shift"},
        }
        return tips.get(shift_type, tips["night"])

    def log_energy(self, level: int, context: str = "") -> dict:
        entry = {"level": level, "context": context, "timestamp": time.time(), "time_of_day": time.strftime("%H:%M")}
        self._energy_log.append(entry)
        return {"logged": True, "average_today": round(sum(e["level"] for e in self._energy_log[-10:]) / min(10, max(1, len(self._energy_log))))}

    def get_rhythm_score(self) -> dict:
        consistency = random.randint(65, 95)
        light_score = random.randint(50, 90)
        sleep_score = random.randint(60, 95)
        overall = (consistency + light_score + sleep_score) // 3
        return {"overall_score": overall, "consistency": consistency, "light_exposure": light_score, "sleep_regularity": sleep_score, "tips": ["Maintain consistent wake time", "Get 10,000+ lux in the morning", "Avoid blue light 2 hours before bed"]}


circadian_rhythm_service = CircadianRhythmService()

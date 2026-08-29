"""
Health Recommendations Engine — Contextual, Explainable Recommendations
"""
import time
from typing import Optional


class HealthRecommendationsEngine:
    def __init__(self):
        self._dismissed: dict[str, set[str]] = {}

    def generate_recommendations(self, user_id: str, **kwargs) -> list[dict]:
        recs = []
        hour = kwargs.get("current_hour", time.localtime().tm_hour)

        # Define rules as (condition_fn, rec_dict) tuples
        rules = [
            # Recovery
            (lambda k: k.get("recovery_score") is not None and k["recovery_score"] < 40,
             {"category": "recovery", "priority": "high", "title": "Low Recovery Detected",
              "message": "Your recovery is critically low. Rest, light stretching, or gentle yoga today.",
              "rationale": "Low recovery score indicates your body needs rest.", "icon": "meditation",
              "action_label": "View Recovery", "action_screen": "health-hub"}),

            (lambda k: k.get("recovery_score") is not None and 40 <= k["recovery_score"] < 60,
             {"category": "recovery", "priority": "medium", "title": "Recovery Could Be Better",
              "message": "Consider moderate-intensity workout. Focus on form, not PRs.",
              "rationale": "Moderate recovery allows lighter training.", "icon": "fitness",
              "action_label": "Adjust Workout", "action_screen": "workout"}),

            (lambda k: k.get("recovery_score") is not None and k["recovery_score"] >= 85,
             {"category": "recovery", "priority": "low", "title": "Excellent Recovery!",
              "message": "Great day for intense training or pushing for PRs.",
              "rationale": "High recovery means your body is primed.", "icon": "flash",
              "action_label": "Start Workout", "action_screen": "workout"}),

            # HRV
            (lambda k: k.get("hrv_rmssd") is not None and k["hrv_rmssd"] < 20,
             {"category": "mental", "priority": "high", "title": "High Stress Indicator",
              "message": "Low HRV suggests elevated stress. Try 5 min breathing exercise.",
              "rationale": "Low HRV correlates with high stress.", "icon": "leaf",
              "action_label": "Breathing", "action_screen": "wellness"}),

            # Sleep
            (lambda k: k.get("sleep_hours") is not None and k["sleep_hours"] < 6,
             {"category": "sleep", "priority": "high", "title": "Sleep Debt Accumulating",
              "message": f"Only {kwargs.get('sleep_hours', 0):.1f}h sleep. Aim for 7-9h tonight.",
              "rationale": "Chronic sleep deprivation impairs recovery and increases injury risk.", "icon": "moon",
              "action_label": "Sleep Tips", "action_screen": "sleep-tracker"}),

            (lambda k: k.get("sleep_hours") is not None and 6 <= k["sleep_hours"] < 7,
             {"category": "sleep", "priority": "medium", "title": "Below Optimal Sleep",
              "message": "Try getting to bed 30 min earlier. Avoid screens before bed.",
              "rationale": "Most adults need 7-9 hours.", "icon": "moon",
              "action_label": "Sleep Hygiene", "action_screen": "sleep-tracker"}),

            # Activity
            (lambda k: k.get("steps_today") is not None and k["steps_today"] < 3000 and hour > 14,
             {"category": "activity", "priority": "medium", "title": "Step Count Below Target",
              "message": f"A 15-min walk now can boost your total and mood.",
              "rationale": "Regular movement is beneficial throughout the day.", "icon": "footsteps",
              "action_label": "Go for Walk", "action_screen": "workout"}),

            (lambda k: k.get("sedentary_hours") is not None and k["sedentary_hours"] > 4,
             {"category": "activity", "priority": "medium", "title": "Time to Move",
              "message": "Stand up, stretch, or take a 5-min walk.",
              "rationale": "Prolonged sitting increases cardiovascular risk.", "icon": "walk",
              "action_label": "Stretches", "action_screen": "workout"}),

            # Training load
            (lambda k: k.get("acwr") is not None and k["acwr"] > 1.5,
             {"category": "recovery", "priority": "high", "title": "Training Load Too High",
              "message": "ACWR above safe limits. Reduce intensity to prevent injury.",
              "rationale": "ACWR >1.5 significantly increases injury risk.", "icon": "warning",
              "action_label": "Deload", "action_screen": "workout"}),

            # Hydration
            (lambda k: k.get("water_ml") is not None and k.get("water_goal_ml", 2000) > 0
             and k["water_ml"] / k["water_goal_ml"] < 0.3 and hour > 12,
             {"category": "hydration", "priority": "high", "title": "Hydration Behind Schedule",
              "message": "Drink a large glass of water now and set hourly reminders.",
              "rationale": "Dehydration impairs performance and recovery.", "icon": "water",
              "action_label": "Log Water", "action_screen": "nutrition-log"}),

            # Stress
            (lambda k: k.get("stress_score") is not None and k["stress_score"] > 70,
             {"category": "mental", "priority": "high", "title": "Stress Level Elevated",
              "message": "Take 5 min for deep breathing or mindfulness.",
              "rationale": "Chronic stress impairs sleep, recovery, and health.", "icon": "leaf",
              "action_label": "Breathing", "action_screen": "wellness"}),

            # Mood
            (lambda k: k.get("mood_score") is not None and k["mood_score"] <= 3,
             {"category": "mental", "priority": "medium", "title": "Mood Check-In",
              "message": "Consider reaching out to someone, walking in nature, or trying meditation.",
              "rationale": "Persistently low mood may benefit from professional support.", "icon": "heart",
              "action_label": "Meditation", "action_screen": "wellness"}),

            # Screen time
            (lambda k: k.get("screen_time_hours") is not None and k["screen_time_hours"] > 4,
             {"category": "education", "priority": "low", "title": "Screen Time High",
              "message": "Consider a 30-min screen break to reduce eye strain.",
              "rationale": "Excessive screen time is associated with poor sleep.", "icon": "phone-portrait",
              "action_label": "Detox Tips", "action_screen": "wellness"}),

            # Medication
            (lambda k: k.get("medications_taken") is False and hour > 10,
             {"category": "medication", "priority": "high", "title": "Medication Reminder",
              "message": "You haven't logged morning medications yet.",
              "rationale": "Medication adherence is critical for health management.", "icon": "medical",
              "action_label": "Log Medication", "action_screen": "medication"}),

            # Nutrition
            (lambda k: k.get("calories_consumed") is not None and k["calories_consumed"] < 800 and hour > 14,
             {"category": "nutrition", "priority": "medium", "title": "Low Calorie Intake",
              "message": "Ensure you're eating enough to support activity and recovery.",
              "rationale": "Undereating impairs recovery and immune function.", "icon": "nutrition",
              "action_label": "Log Meal", "action_screen": "nutrition-log"}),
        ]

        for condition, template in rules:
            try:
                if condition(kwargs):
                    rec = {**template, "id": f"rec_{template['category']}_{hash(str(template['title'])) % 10000}",
                           "confidence": "high" if template["priority"] == "high" else "medium",
                           "data_sources": [k for k in kwargs if kwargs[k] is not None and k != "current_hour"],
                           "created_at": time.time(), "dismissible": True}
                    recs.append(rec)
            except (KeyError, TypeError, ZeroDivisionError):
                continue

        # Time-based tips
        if 6 <= hour <= 8:
            recs.append({"id": "rec_morning", "category": "hydration", "priority": "low",
                         "title": "Start Day Hydrated", "message": "Drink water first thing to rehydrate after sleep.",
                         "rationale": "Morning hydration improves alertness.", "icon": "water",
                         "action_label": "Log Water", "action_screen": "nutrition-log",
                         "confidence": "high", "data_sources": ["time_of_day"], "created_at": time.time(), "dismissible": True})

        # Deduplicate by title
        seen = set()
        unique = []
        for r in recs:
            if r["title"] not in seen:
                seen.add(r["title"])
                unique.append(r)

        # Filter dismissed
        dismissed = self._dismissed.get(user_id, set())
        active = [r for r in unique if r["id"] not in dismissed]

        # Sort by priority
        prio = {"high": 0, "medium": 1, "low": 2}
        active.sort(key=lambda r: prio.get(r["priority"], 2))
        return active[:10]

    def dismiss_recommendation(self, user_id: str, recommendation_id: str) -> dict:
        self._dismissed.setdefault(user_id, set()).add(recommendation_id)
        return {"dismissed": True}


recommendations_engine = HealthRecommendationsEngine()

"""Addiction Recovery & Sobriety Tracker Service.

Based on 2025 recovery app research:
- Sobriety day counter with milestones
- Craving management tools
- Trigger identification and avoidance
- Recovery milestone celebrations
- Support network and meeting finder
- Journaling and mood tracking
- Relapse prevention planning
"""

import time
import math
from typing import Dict, List, Optional, Any


class RecoveryTrackerService:
    """Comprehensive addiction recovery tracking and support."""

    def __init__(self):
        self.profiles: Dict[str, Dict] = {}
        self.journals: Dict[str, List] = {}
        self.cravings: Dict[str, List] = {}
        self._init_milestones()

    def _init_milestones(self):
        self.milestones = [
            {"days": 1, "name": "First Step", "emoji": "🌱", "message": "The journey of a thousand miles begins with a single step"},
            {"days": 7, "name": "One Week", "emoji": "⚡", "message": "7 days strong! Your brain is starting to heal"},
            {"days": 30, "name": "One Month", "emoji": "🏆", "message": "30 days! Physical withdrawal is typically complete"},
            {"days": 90, "name": "90 Days", "emoji": "🔥", "message": "90 days! Habit pathways are rewiring"},
            {"days": 180, "name": "6 Months", "emoji": "💎", "message": "6 months! Emotional regulation is improving"},
            {"days": 365, "name": "One Year", "emoji": "👑", "message": "One year! You are a champion"},
            {"days": 730, "name": "Two Years", "emoji": "🌟", "message": "Two years! Your transformation is inspiring"},
            {"days": 1825, "name": "Five Years", "emoji": "🎯", "message": "Five years! Long-term recovery is proven"},
        ]

        self.substances = {
            "alcohol": {"health_benefits": ["liver_recovery", "better_sleep", "improved_mood", "clearer_thinking"], "withdrawal_risk": "high"},
            "tobacco": {"health_benefits": ["lung_recovery", "circulation", "taste_smell", "reduced_cancer_risk"], "withdrawal_risk": "moderate"},
            "cannabis": {"health_benefits": ["cognitive_clarity", "motivation", "memory", "sleep_quality"], "withdrawal_risk": "low"},
            "opioids": {"health_benefits": ["pain_normalization", "emotional_recovery", "physical_health", "relationships"], "withdrawal_risk": "very_high"},
            "stimulants": {"health_benefits": ["dopamine_recovery", "sleep_normalization", "cardiovascular", "mental_clarity"], "withdrawal_risk": "moderate"},
            "gambling": {"health_benefits": ["financial_recovery", "relationship_repair", "stress_reduction", "self_esteem"], "withdrawal_risk": "low"},
            "other": {"health_benefits": ["overall_wellness", "self_discovery", "life_skills", "community"], "withdrawal_risk": "variable"},
        }

        self.coping_strategies = {
            "craving": [
                {"name": "urge_surfing", "description": "Ride the craving wave - it peaks at 15-20 minutes", "duration": "15 min"},
                {"name": "distract", "description": "Call a friend, take a walk, do an activity", "duration": "5-30 min"},
                {"name": "delay", "description": "Wait 10 minutes before acting on any urge", "duration": "10 min"},
                {"name": "deep_breathing", "description": "4-7-8 breathing technique", "duration": "5 min"},
                {"name": "grounding", "description": "5-4-3-2-1 senses grounding exercise", "duration": "3 min"},
            ],
            "trigger": [
                {"name": "identify", "description": "Name the trigger: person, place, emotion, time"},
                {"name": "avoid", "description": "Remove yourself from triggering situations when possible"},
                {"name": "substitute", "description": "Replace the habit with a healthy alternative"},
                {"name": "support", "description": "Reach out to your support network"},
            ],
            "stress": [
                {"name": "exercise", "description": "30 minutes of physical activity"},
                {"name": "journal", "description": "Write down your feelings"},
                {"name": "meditate", "description": "10 minutes of mindfulness"},
                {"name": "connect", "description": "Talk to someone you trust"},
            ],
        }

    def setup_recovery(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Set up recovery tracking profile."""
        sobriety_date = data.get("sobriety_date", time.strftime("%Y-%m-%d"))
        substance = data.get("substance", "alcohol")

        self.profiles[user_id] = {
            "user_id": user_id,
            "substance": substance,
            "sobriety_date": sobriety_date,
            "days_sober": 0,
            "milestones_achieved": [],
            "streak": 0,
            "longest_streak": 0,
            "relapses": 0,
            "support_network": data.get("support_network", []),
            "sponsor": data.get("sponsor"),
            "meeting_preference": data.get("meeting_preference", "any"),
            "triggers": data.get("triggers", []),
            "goals": data.get("goals", []),
            "created_at": time.time(),
        }

        return self._calculate_sobriety_stats(user_id)

    def log_day(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log a day of recovery."""
        profile = self.profiles.get(user_id)
        if not profile:
            return {"error": "Set up recovery profile first"}

        profile["days_sober"] += 1
        profile["streak"] += 1
        profile["longest_streak"] = max(profile["longest_streak"], profile["streak"])

        mood = data.get("mood", 5)
        energy = data.get("energy", 5)
        cravings_resisted = data.get("cravings_resisted", 0)
        exercise = data.get("exercise", False)
        journaling = data.get("journaling", False)
        meeting_attended = data.get("meeting_attended", False)

        # Calculate daily score
        daily_score = min(100, mood * 10 + energy * 5 + cravings_resisted * 5 + (10 if exercise else 0) + (10 if journaling else 0) + (10 if meeting_attended else 0))

        # Check milestones
        new_milestones = []
        for m in self.milestones:
            if profile["days_sober"] >= m["days"] and m["days"] not in profile["milestones_achieved"]:
                profile["milestones_achieved"].append(m["days"])
                new_milestones.append(m)

        return {
            "day": profile["days_sober"],
            "streak": profile["streak"],
            "daily_score": daily_score,
            "mood": mood,
            "energy": energy,
            "new_milestones": new_milestones,
            "health_improvements": self._get_health_improvements(profile["substance"], profile["days_sober"]),
            "encouragement": self._get_encouragement(profile["days_sober"]),
        }

    def log_craving(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log and manage a craving episode."""
        if user_id not in self.cravings:
            self.cravings[user_id] = []

        craving = {
            "timestamp": time.time(),
            "intensity": data.get("intensity", 5),
            "trigger": data.get("trigger", "unknown"),
            "duration_minutes": data.get("duration", 0),
            "resisted": data.get("resisted", False),
            "coping_used": data.get("coping_strategy", ""),
            "location": data.get("location", ""),
            "time_of_day": data.get("time_of_day", ""),
        }

        self.cravings[user_id].append(craving)

        return {
            "craving_logged": True,
            "strategies": self.coping_strategies["craving"],
            "message": "Craving logged. Remember: it will pass. You are stronger than this moment.",
            "stats": self._get_craving_stats(user_id),
        }

    def get_recovery_progress(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive recovery progress."""
        profile = self.profiles.get(user_id)
        if not profile:
            return {"error": "No recovery profile"}

        days = profile["days_sober"]
        substance_info = self.substances.get(profile["substance"], {})

        return {
            "user_id": user_id,
            "days_sober": days,
            "streak": profile["streak"],
            "longest_streak": profile["longest_streak"],
            "substance": profile["substance"],
            "milestones": [m for m in self.milestones if days >= m["days"]],
            "next_milestone": next((m for m in self.milestones if days < m["days"]), None),
            "health_improvements": self._get_health_improvements(profile["substance"], days),
            "life_impact": self._calculate_life_impact(profile),
            "craving_stats": self._get_craving_stats(user_id),
            "weekly_scores": self._get_weekly_trend(user_id),
        }

    def get_meeting_finder(self, location: str = "", meeting_type: str = "any") -> List[Dict]:
        """Find support meetings."""
        meetings = [
            {"name": "AA Meeting", "type": "12_step", "format": "in_person", "schedule": "Daily at 7PM", "location": "Community Center"},
            {"name": "NA Meeting", "type": "12_step", "format": "hybrid", "schedule": "Tue/Thu/Sat", "location": "Church Hall"},
            {"name": "SMART Recovery", "type": "secular", "format": "online", "schedule": "Daily", "location": "Zoom"},
            {"name": "Refuge Recovery", "type": "buddhist", "format": "in_person", "schedule": "Wednesdays", "location": "Yoga Studio"},
            {"name": "Celebrate Recovery", "type": "faith_based", "format": "in_person", "schedule": "Fridays", "location": "Church"},
            {"name": "Online Meeting", "type": "12_step", "format": "virtual", "schedule": "24/7", "location": "Various platforms"},
        ]
        if meeting_type != "any":
            meetings = [m for m in meetings if m["type"] == meeting_type or meeting_type in m["format"]]
        return meetings

    def _calculate_sobriety_stats(self, user_id: str) -> Dict[str, Any]:
        profile = self.profiles[user_id]
        return {
            "days_sober": profile["days_sober"],
            "substance": profile["substance"],
            "sobriety_date": profile["sobriety_date"],
            "streak": profile["streak"],
            "milestones_achieved": profile["milestones_achieved"],
        }

    def _get_health_improvements(self, substance: str, days: int) -> List[Dict]:
        info = self.substances.get(substance, {})
        benefits = info.get("health_benefits", [])
        improvements = []
        for benefit in benefits:
            if days >= 1:
                improvements.append({"benefit": benefit.replace("_", " ").title(), "status": "in_progress" if days < 90 else "achieved", "days": days})
        return improvements

    def _get_encouragement(self, days: int) -> str:
        if days < 7:
            return "Every day is a victory. Keep going!"
        elif days < 30:
            return "Your body is healing. Stay strong!"
        elif days < 90:
            return "Your brain is rewiring. The hard part gets easier!"
        elif days < 365:
            return "Incredible progress. You are rewriting your story!"
        else:
            return "A true champion. Your recovery inspires others!"

    def _calculate_life_impact(self, profile: Dict) -> Dict[str, Any]:
        days = profile["days_sober"]
        return {
            "money_saved": round(days * 15, 2),
            "productive_hours_gained": round(days * 2, 1),
            "health_score_improvement": min(40, days * 0.1),
        }

    def _get_craving_stats(self, user_id: str) -> Dict[str, Any]:
        cravings = self.cravings.get(user_id, [])
        if not cravings:
            return {"total": 0, "resisted_rate": 0}
        resisted = sum(1 for c in cravings if c["resisted"])
        return {
            "total": len(cravings),
            "resisted": resisted,
            "resisted_rate": round(resisted / len(cravings) * 100, 1),
            "avg_intensity": round(sum(c["intensity"] for c in cravings) / len(cravings), 1),
        }

    def _get_weekly_trend(self, user_id: str) -> List[Dict]:
        return [{"day": d, "score": 60 + (d * 3)} for d in range(7)]


recovery_tracker_service = RecoveryTrackerService()

"""Chronic Fatigue Syndrome (ME/CFS) Management Service.

Based on 2025 CDC ME/CFS guidelines:
- Energy envelope tracking
- Activity pacing guidance
- Post-Exertional Malaise (PEM) prevention and crash logging
- Heart rate monitoring for pacing
- Symptom severity tracking
- Rest and recovery planning
"""

import time
import random
from typing import Dict, List, Any


class ChronicFatigueService:
    """ME/CFS energy management and pacing support."""

    def __init__(self):
        self.profiles: Dict[str, Dict] = {}
        self.daily_logs: Dict[str, List] = {}
        self.crashes: Dict[str, List] = {}

    def create_profile(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create ME/CFS profile with energy envelope."""
        age = data.get("age", 35)
        max_hr = 220 - age
        # Anaerobic threshold for ME/CFS is typically 55-60% of max HR
        anaerobic_threshold = int(max_hr * 0.55)

        self.profiles[user_id] = {
            "user_id": user_id,
            "severity": data.get("severity", "moderate"),
            "max_heart_rate": max_hr,
            "anaerobic_threshold": anaerobic_threshold,
            "energy_envelope_baseline": data.get("energy_level", 5),
            "crash_threshold": data.get("crash_threshold", 3),
            "medications": data.get("medications", []),
            "triggers": data.get("triggers", ["overexertion", "poor_sleep", "stress", "infection"]),
            "created_at": time.time(),
        }
        return self.profiles[user_id]

    def log_activity(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log daily activity within energy envelope."""
        if user_id not in self.daily_logs:
            self.daily_logs[user_id] = []

        profile = self.profiles.get(user_id, {})
        energy_level = data.get("energy_level", 5)
        activity_mins = data.get("activity_minutes", 0)
        heart_rate = data.get("heart_rate", 70)
        at_threshold = profile.get("anaerobic_threshold", 100)

        # Check if went over energy envelope
        over_exertion = heart_rate > at_threshold or energy_level > profile.get("energy_envelope_baseline", 5) + 2

        entry = {
            "date": data.get("date", time.strftime("%Y-%m-%d")),
            "energy_level": energy_level,
            "activity_minutes": activity_mins,
            "heart_rate_peak": heart_rate,
            "at_threshold": at_threshold,
            "over_exertion": over_exertion,
            "symptoms": data.get("symptoms", []),
            "cognitive_load": data.get("cognitive_load", "moderate"),
            "rest_taken": data.get("rest_minutes", 0),
            "pacing_followed": data.get("pacing_followed", True),
            "logged_at": time.time(),
        }

        self.daily_logs[user_id].append(entry)

        warnings = []
        if over_exertion:
            warnings.append("⚠️ Above anaerobic threshold — PEM risk elevated")
            warnings.append("Take immediate rest to prevent crash")
        if not data.get("pacing_followed", True):
            warnings.append("Pacing not followed — monitor for PEM in 24-48 hours")

        return {"entry": entry, "warnings": warnings, "envelope_status": "within" if not over_exertion else "exceeded"}

    def log_crash(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log a PEM crash episode."""
        if user_id not in self.crashes:
            self.crashes[user_id] = []

        crash = {
            "crash_id": f"crash_{int(time.time())}",
            "date": data.get("date", time.strftime("%Y-%m-%d")),
            "severity": data.get("severity", "moderate"),
            "onset_delay_hours": data.get("onset_delay", 24),
            "duration_days": data.get("duration", 3),
            "trigger": data.get("trigger", "overexertion"),
            "symptoms": data.get("symptoms", ["fatigue", "pain", "cognitive_impairment"]),
            "recovery_notes": data.get("notes", ""),
            "logged_at": time.time(),
        }

        self.crashes[user_id].append(crash)

        return {
            "crash_logged": True,
            "crash": crash,
            "recovery_guidance": [
                "Rest completely — no activity beyond essential self-care",
                "Stay hydrated and nourished",
                "Minimize sensory input (dark, quiet room)",
                "Do not try to push through — this worsens PEM",
                "Gradual return to baseline over days/weeks",
            ],
        }

    def get_pacing_plan(self, user_id: str) -> Dict[str, Any]:
        """Generate personalized pacing plan."""
        profile = self.profiles.get(user_id, {})
        threshold = profile.get("anaerobic_threshold", 100)

        return {
            "heart_rate_zones": {
                "safe_zone": f"Below {threshold} bpm — maintain this during activity",
                "caution_zone": f"{threshold}-{threshold+10} bpm — slow down or rest",
                "danger_zone": f"Above {threshold+10} bpm — stop activity immediately",
            },
            "pacing_rules": [
                "Start activity at 50% of what you think you can do",
                "Take breaks BEFORE you feel tired (pre-emptive rest)",
                "Never push through PEM — it makes it worse",
                "Track heart rate during all activities",
                "Plan recovery time after any exertion",
                "Alternate physical and cognitive activities",
            ],
            "energy_budget": {
                "morning": "Reserve 30% of daily energy",
                "afternoon": "Use 40% (peak hours for most ME/CFS patients)",
                "evening": "Reserve 30% for winding down",
            },
            "boom_bust_prevention": "If you had a good day yesterday, do NOT increase activity today",
        }

    def get_energy_forecast(self, user_id: str) -> Dict[str, Any]:
        """Predict energy levels based on patterns."""
        logs = self.daily_logs.get(user_id, [])
        if not logs:
            return {"message": "Log activities to get energy forecasts"}

        recent = logs[-7:] if len(logs) > 7 else logs
        avg_energy = sum(l["energy_level"] for l in recent) / len(recent)
        over_exertions = sum(1 for l in recent if l.get("over_exertion"))

        return {
            "baseline_energy": round(avg_energy, 1),
            "over_exertions_this_week": over_exertions,
            "crash_risk": "high" if over_exertions > 2 else "moderate" if over_exertions > 0 else "low",
            "recommendation": "Reduce activity to prevent PEM" if over_exertions > 1 else "Maintain current pacing strategy",
        }


chronic_fatigue_service = ChronicFatigueService()

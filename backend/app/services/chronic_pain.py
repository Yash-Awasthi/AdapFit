"""Chronic Pain Management Service - Pain journal, triggers, treatment tracking.

Based on 2025 chronic pain app research:
- Pain diary with body map
- Trigger identification and correlation analysis
- Treatment effectiveness tracking
- Flare detection and management
- Functional ability tracking
- Medication log and side effects
- Pain education and CBT techniques
"""

import time
import random
from typing import Dict, List, Optional, Any


class ChronicPainService:
    """Comprehensive chronic pain management and tracking."""

    def __init__(self):
        self.profiles: Dict[str, Dict] = {}
        self.pain_logs: Dict[str, List] = {}
        self._init_pain_resources()

    def _init_pain_resources(self):
        self.pain_conditions = {
            "fibromyalgia": {
                "name": "Fibromyalgia",
                "common_symptoms": ["widespread_pain", "fatigue", "brain_fog", "sleep_disturbance", "headaches"],
                "triggers": ["stress", "weather_changes", "poor_sleep", "overexertion", "infection"],
                "treatments": ["medication", "exercise", "CBT", "sleep_hygiene", "stress_management"],
            },
            "migraine": {
                "name": "Migraine",
                "common_symptoms": ["throbbing_headache", "nausea", "light_sensitivity", "sound_sensitivity", "aura"],
                "triggers": ["stress", "certain_foods", "hormones", "sleep_changes", "weather"],
                "treatments": ["acute_medication", "preventive_medication", "biofeedback", "lifestyle_modification"],
            },
            "back_pain": {
                "name": "Chronic Back Pain",
                "common_symptoms": ["local_pain", "stiffness", "radiating_pain", "muscle_spasm", "limited_mobility"],
                "triggers": ["prolonged_sitting", "heavy_lifting", "poor_posture", "stress", "cold_weather"],
                "treatments": ["physical_therapy", "exercise", "ergonomics", "meditation", "medication"],
            },
            "arthritis": {
                "name": "Arthritis",
                "common_symptoms": ["joint_pain", "swelling", "stiffness", "reduced_range_of_motion", "warmth"],
                "triggers": ["cold_weather", "overuse", "stress", "infection", "diet"],
                "treatments": ["anti_inflammatories", "physical_therapy", "joint_protection", "exercise", "diet_modification"],
            },
            "neuropathy": {
                "name": "Neuropathic Pain",
                "common_symptoms": ["burning", "tingling", "numbness", "shooting_pain", "allodynia"],
                "triggers": ["stress", "temperature_extremes", "tight_clothing", "fatigue"],
                "treatments": ["neuropathic_medication", "TENS", "acupuncture", "physical_therapy"],
            },
        }

        self.cbt_techniques = [
            {"name": "Thought Challenging", "description": "Identify and challenge catastrophizing thoughts about pain", "duration": "10 min", "evidence": "strong"},
            {"name": "Pacing", "description": "Break activities into manageable chunks with rest periods", "duration": "ongoing", "evidence": "strong"},
            {"name": "Acceptance", "description": "Practice accepting pain without fighting it", "duration": "ongoing", "evidence": "moderate"},
            {"name": "Graded Exposure", "description": "Gradually increase activity despite pain", "duration": "weeks", "evidence": "strong"},
            {"name": "Mindful Breathing", "description": "Focus on breath to reduce pain perception", "duration": "5 min", "evidence": "moderate"},
            {"name": "Body Scan", "description": "Progressive relaxation to reduce muscle tension", "duration": "15 min", "evidence": "moderate"},
        ]

        self.pain_scale = {
            0: {"label": "No pain", "color": "#10B981", "function": "Normal activities"},
            1: {"label": "Mild", "color": "#34D399", "function": "Barely noticeable"},
            2: {"label": "Uncomfortable", "color": "#FBBF24", "function": "Can ignore with effort"},
            3: {"label": "Distracting", "color": "#F59E0B", "function": "Hard to ignore sometimes"},
            4: {"label": "Moderate", "color": "#F97316", "function": "Interferes with some activities"},
            5: {"label": "Strong", "color": "#EF4444", "function": "Hard to concentrate"},
            6: {"label": "Severe", "color": "#DC2626", "function": "Interferes with most activities"},
            7: {"label": "Very Severe", "color": "#B91C1C", "function": "Difficult to do anything"},
            8: {"label": "Intense", "color": "#991B1B", "function": "Unable to function"},
            9: {"label": "Excruciating", "color": "#7F1D1D", "function": "Bedridden"},
            10: {"label": "Unbearable", "color": "#450A0A", "function": "Emergency care needed"},
        }

    def create_profile(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create chronic pain profile."""
        conditions = data.get("conditions", ["back_pain"])

        self.profiles[user_id] = {
            "user_id": user_id,
            "conditions": conditions,
            "baseline_pain": data.get("baseline_pain", 4),
            "current_treatments": data.get("treatments", []),
            "medications": data.get("medications", []),
            "allergies": data.get("allergies", []),
            "care_team": data.get("care_team", []),
            "goals": data.get("goals", ["reduce_pain", "improve_function"]),
            "created_at": time.time(),
        }

        return self.profiles[user_id]

    def log_pain(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log pain entry."""
        if user_id not in self.pain_logs:
            self.pain_logs[user_id] = []

        pain_level = data.get("pain_level", 5)
        entry = {
            "date": data.get("date", time.strftime("%Y-%m-%d")),
            "time": data.get("time", time.strftime("%H:%M")),
            "pain_level": pain_level,
            "pain_type": data.get("pain_type", "aching"),
            "location": data.get("location", "general"),
            "duration": data.get("duration_minutes", 0),
            "triggers": data.get("triggers", []),
            "associated_symptoms": data.get("symptoms", []),
            "functional_impact": data.get("functional_impact", 5),
            "mood": data.get("mood", 5),
            "sleep_quality": data.get("sleep_quality", 5),
            "medications_taken": data.get("medications_taken", []),
            "treatments_used": data.get("treatments_used", []),
            "relief_obtained": data.get("relief_percent", 0),
            "notes": data.get("notes", ""),
            "logged_at": time.time(),
        }

        self.pain_logs[user_id].append(entry)
        return entry

    def analyze_triggers(self, user_id: str) -> Dict[str, Any]:
        """Analyze pain triggers and correlations."""
        logs = self.pain_logs.get(user_id, [])
        if len(logs) < 5:
            return {"message": "Log at least 5 entries for trigger analysis", "days_logged": len(logs)}

        trigger_correlations = {}
        for log in logs:
            for trigger in log.get("triggers", []):
                if trigger not in trigger_correlations:
                    trigger_correlations[trigger] = {"total": 0, "high_pain_days": 0, "avg_pain": []}
                trigger_correlations[trigger]["total"] += 1
                trigger_correlations[trigger]["avg_pain"].append(log["pain_level"])
                if log["pain_level"] >= 6:
                    trigger_correlations[trigger]["high_pain_days"] += 1

        triggers = []
        for trigger, data in trigger_correlations.items():
            avg = sum(data["avg_pain"]) / max(1, len(data["avg_pain"]))
            triggers.append({
                "trigger": trigger,
                "occurrences": data["total"],
                "avg_pain_when_present": round(avg, 1),
                "high_pain_rate": round(data["high_pain_days"] / max(1, data["total"]) * 100),
            })

        triggers.sort(key=lambda x: x["high_pain_rate"], reverse=True)

        # Time patterns
        pain_by_hour = {}
        for log in logs:
            hour = log.get("time", "12:00").split(":")[0]
            pain_by_hour[hour] = pain_by_hour.get(hour, []) + [log["pain_level"]]

        return {
            "top_triggers": triggers[:5],
            "pain_by_time": {h: round(sum(v)/len(v), 1) for h, v in pain_by_hour.items()},
            "most_painful_trigger": triggers[0]["trigger"] if triggers else "unknown",
            "recommendation": f"Focus on managing {triggers[0]['trigger']}" if triggers else "Keep logging to identify patterns",
        }

    def get_treatment_effectiveness(self, user_id: str) -> Dict[str, Any]:
        """Analyze treatment effectiveness."""
        logs = self.pain_logs.get(user_id, [])
        if not logs:
            return {"message": "No pain data yet"}

        treatment_data = {}
        for log in logs:
            for treatment in log.get("treatments_used", []):
                if treatment not in treatment_data:
                    treatment_data[treatment] = {"relief_scores": [], "pain_levels": []}
                treatment_data[treatment]["relief_scores"].append(log.get("relief_obtained", 0))
                treatment_data[treatment]["pain_levels"].append(log["pain_level"])

        treatments = []
        for treatment, data in treatment_data.items():
            treatments.append({
                "treatment": treatment,
                "times_used": len(data["relief_scores"]),
                "avg_relief_percent": round(sum(data["relief_scores"]) / max(1, len(data["relief_scores"])), 1),
                "avg_pain_during": round(sum(data["pain_levels"]) / max(1, len(data["pain_levels"])), 1),
                "effectiveness": "high" if sum(data["relief_scores"]) / max(1, len(data["relief_scores"])) > 50 else "moderate" if sum(data["relief_scores"]) / max(1, len(data["relief_scores"])) > 25 else "low",
            })

        treatments.sort(key=lambda x: x["avg_relief_percent"], reverse=True)
        return {"treatments": treatments, "best_treatment": treatments[0] if treatments else None}

    def get_flare_management(self) -> Dict[str, Any]:
        """Get flare management plan."""
        return {
            "flare_recognition": [
                "Sudden increase in pain level (3+ points above baseline)",
                "New symptoms appearing",
                "Significant functional decline",
                "Duration longer than usual",
            ],
            "immediate_actions": [
                "Cancel non-essential activities",
                "Apply heat or cold to affected area",
                "Take prescribed rescue medication",
                "Practice gentle breathing exercises",
                "Hydrate well",
            ],
            "days_1_3": [
                "Rest but avoid complete bed rest",
                "Gentle movement every 2 hours",
                "Use pacing strategies",
                "Continue core treatments",
            ],
            "recovery": [
                "Gradually return to normal activities",
                "Identify what triggered the flare",
                "Adjust prevention strategies",
                "Log the flare for pattern recognition",
            ],
        }

    def get_cbt_techniques(self) -> List[Dict]:
        return self.cbt_techniques


chronic_pain_service = ChronicPainService()

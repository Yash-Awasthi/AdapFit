"""Allergy Tracker Service - Pollen forecast, allergy management, immunotherapy tracking.

Based on 2025 research on allergy apps:
- Personalized allergy profile and trigger identification
- Pollen and environmental allergen tracking
- Symptom diary with correlation analysis
- Medication management and reminders
- Immunotherapy progress tracking
- Food allergy management
"""

import time
import random
from typing import Dict, List, Optional, Any


class AllergyTrackerService:
    """Comprehensive allergy tracking and management."""

    def __init__(self):
        self.profiles: Dict[str, Dict] = {}
        self.symptom_logs: Dict[str, List] = {}
        self._init_allergen_data()

    def _init_allergen_data(self):
        self.pollen_types = {
            "tree": {"seasons": ["spring"], "months": [2, 3, 4, 5], "types": ["oak", "birch", "cedar", "pine", "maple"]},
            "grass": {"seasons": ["spring", "summer"], "months": [4, 5, 6, 7], "types": ["rye", "timothy", "bermuda", "bluegrass"]},
            "weed": {"seasons": ["summer", "fall"], "months": [7, 8, 9, 10], "types": ["ragweed", "plantain", "sagebrush"]},
            "mold": {"seasons": ["all"], "months": list(range(1, 13)), "types": ["alternaria", "cladosporium", "aspergillus"]},
        }

        self.severity_scale = {
            1: {"label": "Mild", "symptoms": ["sneezing", "itchy eyes"], "impact": "Minimal impact on daily activities"},
            2: {"label": "Moderate", "symptoms": ["sneezing", "congestion", "runny nose"], "impact": "Some impact on sleep and concentration"},
            3: {"label": "Severe", "symptoms": ["all_above", "wheezing", "skin_rash"], "impact": "Significant impact on quality of life"},
            4: {"label": "Very Severe", "symptoms": ["all_above", "breathing_difficulty", "anaphylaxis_risk"], "impact": "Immediate medical attention may be needed"},
        }

    def create_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create allergy profile."""
        self.profiles[user_id] = {
            "user_id": user_id,
            "known_allergies": profile_data.get("known_allergies", []),
            "allergy_types": profile_data.get("types", []),  # environmental, food, drug, contact
            "severity_baseline": profile_data.get("severity", "moderate"),
            "medications": profile_data.get("current_medications", []),
            "immunotherapy": profile_data.get("immunotherapy", None),
            "created_at": time.time(),
        }
        return self.profiles[user_id]

    def log_symptoms(self, user_id: str, date: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log daily allergy symptoms."""
        if user_id not in self.symptom_logs:
            self.symptom_logs[user_id] = []

        severity = data.get("severity", 3)
        entry = {
            "date": date,
            "symptoms": data.get("symptoms", []),
            "severity": severity,
            "nose": data.get("nose", {"sneezing": False, "congestion": 0, "runny": False}),
            "eyes": data.get("eyes", {"itchy": False, "watery": False, "red": False}),
            "throat": data.get("throat", {"itchy": False, "scratchy": False}),
            "skin": data.get("skin", {"rash": False, "hives": False, "itchy": False}),
            "respiratory": data.get("respiratory", {"wheezing": False, "cough": False, "breathlessness": False}),
            "medication_taken": data.get("medication_taken", []),
            "possible_triggers": data.get("triggers", []),
            "location": data.get("location", "home"),
            "weather": data.get("weather", {}),
            "mood": data.get("mood"),
            "sleep_quality": data.get("sleep_quality"),
            "activity_level": data.get("activity_level"),
            "logged_at": time.time(),
        }

        self.symptom_logs[user_id].append(entry)
        return entry

    def get_pollen_forecast(self, location: str, days: int = 3) -> List[Dict[str, Any]]:
        """Get pollen forecast for a location."""
        forecast = []
        month = 7  # simulated

        for day in range(days):
            day_forecast = {"day": day + 1, "pollen_levels": {}}
            for pollen_type, info in self.pollen_types.items():
                if month in info["months"]:
                    level = random.choice(["low", "moderate", "high", "very_high"])
                    day_forecast["pollen_levels"][pollen_type] = {
                        "level": level,
                        "count": random.randint(1, 12) if level == "low" else random.randint(12, 30) if level == "moderate" else random.randint(30, 80),
                        "dominant_species": random.choice(info["types"]),
                    }
                else:
                    day_forecast["pollen_levels"][pollen_type] = {"level": "none", "count": 0}
            forecast.append(day_forecast)
        return forecast

    def analyze_triggers(self, user_id: str) -> Dict[str, Any]:
        """Analyze symptom patterns to identify triggers."""
        logs = self.symptom_logs.get(user_id, [])
        if len(logs) < 3:
            return {"message": "Log more symptoms for trigger analysis", "days_logged": len(logs)}

        trigger_frequency = {}
        for log in logs:
            for trigger in log.get("possible_triggers", []):
                if trigger not in trigger_frequency:
                    trigger_frequency[trigger] = {"total": 0, "severe_days": 0}
                trigger_frequency[trigger]["total"] += 1
                if log["severity"] >= 3:
                    trigger_frequency[trigger]["severe_days"] += 1

        for trigger in trigger_frequency:
            freq = trigger_frequency[trigger]
            freq["correlation_score"] = round(freq["severe_days"] / max(1, freq["total"]) * 100)

        sorted_triggers = sorted(trigger_frequency.items(), key=lambda x: x[1]["correlation_score"], reverse=True)

        avg_severity = sum(l["severity"] for l in logs) / len(logs)
        worst_symptoms = self._get_worst_symptoms(logs)

        return {
            "user_id": user_id,
            "days_analyzed": len(logs),
            "average_severity": round(avg_severity, 1),
            "top_triggers": [{"trigger": t, **d} for t, d in sorted_triggers[:5]],
            "worst_symptoms": worst_symptoms,
            "seasonal_pattern": self._detect_seasonal_pattern(logs),
            "medication_effectiveness": self._analyze_medication_effectiveness(logs),
        }

    def get_medication_reminders(self, user_id: str) -> List[Dict[str, Any]]:
        """Get medication reminders based on profile and symptoms."""
        profile = self.profiles.get(user_id, {})
        meds = profile.get("medications", [])

        reminders = []
        for med in meds:
            reminders.append({
                "medication": med.get("name", "Unknown"),
                "dosage": med.get("dosage", ""),
                "frequency": med.get("frequency", "daily"),
                "next_dose": "Morning",
                "with_food": med.get("with_food", False),
            })

        if not reminders:
            reminders.append({
                "medication": "Antihistamine (if needed)",
                "dosage": "As directed",
                "frequency": "as needed",
                "note": "Add your medications to your profile for personalized reminders",
            })

        return reminders

    def get_immunotherapy_progress(self, user_id: str) -> Dict[str, Any]:
        """Track immunotherapy progress."""
        profile = self.profiles.get(user_id, {})
        immunotherapy = profile.get("immunotherapy")
        if not immunotherapy:
            return {"status": "not_started", "message": "No immunotherapy program active"}

        return {
            "type": immunotherapy.get("type", "SCIT"),
            "allergen": immunotherapy.get("allergen", "multiple"),
            "start_date": immunotherapy.get("start_date"),
            "current_phase": "build_up",
            "doses_completed": immunotherapy.get("doses_completed", 0),
            "total_doses_planned": immunotherapy.get("total_doses", 52),
            "progress_percent": round(immunotherapy.get("doses_completed", 0) / max(1, immunotherapy.get("total_doses", 52)) * 100, 1),
            "effectiveness": "Monitor symptom changes over 6-12 months",
            "next_appointment": "Schedule with allergist",
        }

    def _get_worst_symptoms(self, logs: List[Dict]) -> List[str]:
        symptom_counts = {}
        for log in logs:
            for symptom in log.get("symptoms", []):
                symptom_counts[symptom] = symptom_counts.get(symptom, 0) + 1
        return sorted(symptom_counts.keys(), key=lambda x: symptom_counts[x], reverse=True)[:5]

    def _detect_seasonal_pattern(self, logs: List[Dict]) -> Dict[str, Any]:
        return {"pattern": "spring_fall", "peak_months": ["March", "September"], "confidence": 0.8}

    def _analyze_medication_effectiveness(self, logs: List[Dict]) -> Dict[str, Any]:
        med_days = [l for l in logs if l.get("medication_taken")]
        no_med_days = [l for l in logs if not l.get("medication_taken")]
        avg_med = sum(l["severity"] for l in med_days) / max(1, len(med_days))
        avg_no_med = sum(l["severity"] for l in no_med_days) / max(1, len(no_med_days))
        return {
            "medication_days_avg_severity": round(avg_med, 1),
            "no_medication_days_avg_severity": round(avg_no_med, 1),
            "effectiveness": "effective" if avg_med < avg_no_med else "needs_adjustment",
        }


allergy_tracker_service = AllergyTrackerService()

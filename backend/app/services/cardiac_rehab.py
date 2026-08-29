"""Cardiac Rehabilitation Service.

Based on 2025 AHA/ACC cardiac rehab guidelines:
- Post-surgery exercise program (phased recovery)
- Heart rate zone training
- Daily vital monitoring (BP, HR, weight, SpO2)
- Medication tracking
- Dietary recommendations (DASH, heart-healthy)
- Fluid balance monitoring
- Risk factor management
- Progress milestones
"""

import time
import random
from typing import Dict, List, Any


class CardiacRehabService:
    """Cardiac rehabilitation and heart failure management."""

    def __init__(self):
        self.profiles: Dict[str, Dict] = {}
        self.daily_logs: Dict[str, List] = {}
        self._init_rehab_phases()

    def _init_rehab_phases(self):
        self.phases = {
            1: {
                "name": "Inpatient/Immediate Post-Op",
                "duration_weeks": "0-2",
                "exercises": ["Deep breathing exercises", "Gentle walking (hallway)", "Bed exercises", "Arm raises"],
                "heart_rate_zone": "50-60% max HR",
                "precautions": ["Monitor vitals every 4 hours", "Report chest pain immediately", "No lifting >2kg"],
            },
            2: {
                "name": "Early Outpatient",
                "duration_weeks": "2-6",
                "exercises": ["Walking 10-20 min", "Light stationary cycling", "Gentle stretching", "Light resistance bands"],
                "heart_rate_zone": "60-70% max HR",
                "precautions": ["Warm up 5-10 min", "Cool down 5-10 min", "Stop if dizzy or short of breath"],
            },
            3: {
                "name": "Progressive Training",
                "duration_weeks": "6-12",
                "exercises": ["Walking 30 min", "Swimming", "Moderate cycling", "Light weight training"],
                "heart_rate_zone": "70-80% max HR",
                "precautions": ["Gradual progression", "Self-monitor RPE (Rate of Perceived Exertion)"],
            },
            4: {
                "name": "Maintenance",
                "duration_weeks": "12+",
                "exercises": ["Regular aerobic exercise 150 min/week", "Resistance training 2x/week", "Flexibility work", "Recreational activities"],
                "heart_rate_zone": "70-85% max HR",
                "precautions": ["Lifelong heart-healthy habits", "Annual cardiac checkup"],
            },
        }

        self.heart_healthy_diet = {
            "recommended": [
                {"food": "Fatty fish (salmon, mackerel)", "benefit": "Omega-3 reduces inflammation", "frequency": "2-3x/week"},
                {"food": "Leafy greens (spinach, kale)", "benefit": "Nitrates lower blood pressure", "frequency": "Daily"},
                {"food": "Berries", "benefit": "Antioxidants protect blood vessels", "frequency": "Daily"},
                {"food": "Oats and whole grains", "benefit": "Fiber lowers cholesterol", "frequency": "Daily"},
                {"food": "Nuts (almonds, walnuts)", "benefit": "Healthy fats for heart", "frequency": "Handful daily"},
                {"food": "Olive oil", "benefit": "Monounsaturated fats", "frequency": "Daily"},
            ],
            "avoid": [
                "Processed meats (bacon, sausage)",
                "Excessive salt (>2300mg/day)",
                "Trans fats and fried foods",
                "Sugary beverages",
                "Refined carbohydrates",
                "Excessive alcohol",
            ],
        }

    def setup_program(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Set up cardiac rehabilitation program."""
        age = data.get("age", 65)
        max_hr = 220 - age

        self.profiles[user_id] = {
            "user_id": user_id,
            "condition": data.get("condition", "post_mi"),
            "surgery_date": data.get("surgery_date"),
            "current_phase": data.get("current_phase", 1),
            "age": age,
            "max_heart_rate": max_hr,
            "target_hr_min": int(max_hr * 0.6),
            "target_hr_max": int(max_hr * 0.8),
            "resting_hr": data.get("resting_hr", 72),
            "medications": data.get("medications", []),
            "weight_kg": data.get("weight", 80),
            "fluid_limit_ml": data.get("fluid_limit_ml", 2000),
            "created_at": time.time(),
        }

        return {
            "program": self.profiles[user_id],
            "current_phase": self.phases[1],
            "heart_rate_zones": {
                "resting": self.profiles[user_id]["resting_hr"],
                "target_min": self.profiles[user_id]["target_hr_min"],
                "target_max": self.profiles[user_id]["target_hr_max"],
                "maximum": max_hr,
            },
        }

    def log_daily(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log daily cardiac rehab data."""
        if user_id not in self.daily_logs:
            self.daily_logs[user_id] = []

        entry = {
            "date": data.get("date", time.strftime("%Y-%m-%d")),
            "weight_kg": data.get("weight"),
            "blood_pressure": data.get("bp", "120/80"),
            "resting_hr": data.get("resting_hr"),
            "spo2": data.get("spo2", 97),
            "fluid_intake_ml": data.get("fluid_ml", 0),
            "exercise_min": data.get("exercise_min", 0),
            "exercise_type": data.get("exercise_type", "walking"),
            "avg_hr_during_exercise": data.get("avg_hr"),
            "max_hr_during_exercise": data.get("max_hr"),
            "medications_taken": data.get("medications_taken", True),
            "symptoms": data.get("symptoms", []),
            "rpe": data.get("rpe", 5),
            "mood": data.get("mood", 5),
            "logged_at": time.time(),
        }

        self.daily_logs[user_id].append(entry)

        # Alerts
        alerts = []
        bp = entry["blood_pressure"]
        if "/" in bp:
            systolic = int(bp.split("/")[0])
            if systolic > 140: alerts.append("Blood pressure elevated")
            if systolic < 90: alerts.append("Blood pressure low")
        if entry.get("spo2", 100) < 94: alerts.append("Oxygen saturation low")
        if entry.get("fluid_intake_ml", 0) > self.profiles.get(user_id, {}).get("fluid_limit_ml", 2000):
            alerts.append("Fluid intake over daily limit")
        if entry.get("weight_kg") and self.daily_logs[user_id]:
            prev = self.daily_logs[user_id][-2] if len(self.daily_logs[user_id]) > 1 else None
            if prev and prev.get("weight_kg"):
                gain = entry["weight_kg"] - prev["weight_kg"]
                if gain > 1: alerts.append(f"Weight gain of {gain}kg in one day — possible fluid retention")

        return {"entry": entry, "alerts": alerts}

    def get_exercise_program(self, user_id: str) -> Dict[str, Any]:
        """Get current phase exercise program."""
        profile = self.profiles.get(user_id, {})
        phase = profile.get("current_phase", 1)
        program = self.phases.get(phase, self.phases[1])

        return {
            "phase": phase,
            "phase_name": program["name"],
            "duration": program["duration_weeks"],
            "exercises": program["exercises"],
            "target_heart_rate": f"{profile.get('target_hr_min', 90)}-{profile.get('target_hr_max', 120)} bpm",
            "precautions": program["precautions"],
        }

    def get_diet_plan(self) -> Dict[str, Any]:
        """Get heart-healthy diet recommendations."""
        return self.heart_healthy_diet

    def get_progress_summary(self, user_id: str) -> Dict[str, Any]:
        """Get rehab progress summary."""
        logs = self.daily_logs.get(user_id, [])
        if not logs:
            return {"message": "Start logging to see your progress"}

        recent = logs[-7:] if len(logs) > 7 else logs
        total_exercise = sum(l.get("exercise_min", 0) for l in recent)
        avg_rpe = sum(l.get("rpe", 5) for l in recent) / len(recent)

        return {
            "total_exercise_minutes": total_exercise,
            "avg_exercise_per_day": round(total_exercise / max(1, len(recent)), 1),
            "average_rpe": round(avg_rpe, 1),
            "days_logged": len(recent),
            "medication_adherence": round(sum(1 for l in recent if l.get("medications_taken")) / max(1, len(recent)) * 100),
            "encouragement": "Great progress! Keep up the exercise routine." if total_exercise > 150 else "Try to increase your daily exercise gradually.",
        }


cardiac_rehab_service = CardiacRehabService()

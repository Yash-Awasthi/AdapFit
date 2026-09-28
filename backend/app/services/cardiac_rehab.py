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
from typing import Dict, List, Any


EFFORT_GUIDE = ("Aim for RPE 11-14 on the 6-20 scale: you can talk but not sing. Stop and rest for chest pain, "
                "dizziness or unusual breathlessness; call 108 if chest pain lasts more than a few minutes of rest.")


def _zone_text(profile: dict) -> str:
    lo, hi = profile.get("target_hr_min"), profile.get("target_hr_max")
    if lo and hi:
        return f"{lo}-{hi} bpm (from your rehab team)"
    if hi:
        return f"Stay under {hi} bpm (resting + 20) unless your rehab team gave you a zone"
    return "Go by effort; ask your rehab team for a heart-rate zone from your exercise test"


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
                "heart_rate_zone": "RPE 11-12 (fairly light)",
                "precautions": ["Monitor vitals every 4 hours", "Report chest pain immediately", "No lifting >2kg"],
            },
            2: {
                "name": "Early Outpatient",
                "duration_weeks": "2-6",
                "exercises": ["Walking 10-20 min", "Light stationary cycling", "Gentle stretching", "Light resistance bands"],
                "heart_rate_zone": "RPE 11-13",
                "precautions": ["Warm up 5-10 min", "Cool down 5-10 min", "Stop if dizzy or short of breath"],
            },
            3: {
                "name": "Progressive Training",
                "duration_weeks": "6-12",
                "exercises": ["Walking 30 min", "Swimming", "Moderate cycling", "Light weight training"],
                "heart_rate_zone": "RPE 12-14 (somewhat hard)",
                "precautions": ["Gradual progression", "Self-monitor RPE (Rate of Perceived Exertion)"],
            },
            4: {
                "name": "Maintenance",
                "duration_weeks": "12+",
                "exercises": ["Regular aerobic exercise 150 min/week", "Resistance training 2x/week", "Flexibility work", "Recreational activities"],
                "heart_rate_zone": "RPE 12-14, or the zone from your exercise test",
                "precautions": ["Lifelong heart-healthy habits", "Annual cardiac checkup"],
            },
        }

        self.heart_healthy_diet = {
            "recommended": [
                {"food": "Fish such as mackerel (bangda), sardines or rohu", "benefit": "Omega-3 fats", "frequency": "2-3x/week"},
                {"food": "Dal, chana, rajma and other pulses", "benefit": "Fibre and protein without saturated fat", "frequency": "Daily"},
                {"food": "Leafy greens (palak, methi, amaranth)", "benefit": "Potassium and fibre", "frequency": "Daily"},
                {"food": "Whole grains (atta, millets like ragi and jowar, oats)", "benefit": "Fibre lowers cholesterol", "frequency": "Daily"},
                {"food": "Fruit such as guava, amla, oranges", "benefit": "Fibre and potassium", "frequency": "Daily"},
                {"food": "A handful of nuts (almonds, walnuts, groundnuts)", "benefit": "Unsaturated fats", "frequency": "Daily"},
            ],
            "avoid": [
                "Salt above 5 g a day (about one teaspoon), including pickles, papad and namkeen",
                "Vanaspati and reused frying oil (trans fats)",
                "Deep-fried snacks and sweets",
                "Sugary drinks",
                "Processed meats",
                "Alcohol and all tobacco, including chewed",
            ],
        }

    def setup_program(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set up a cardiac rehabilitation program.

        Age-predicted zones (220 minus age) do not hold for heart patients,
        especially on beta blockers, so the zone is the one the rehab team
        prescribed, else a cap of resting heart rate plus 20 bpm, and always
        an effort of RPE 11-14 on the 6-20 Borg scale.
        """
        def bpm(key):
            v = data.get(key)
            return int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and 30 <= v <= 220 else None

        rx_min, rx_max, resting = bpm("prescribed_hr_min"), bpm("prescribed_hr_max"), bpm("resting_hr")
        if rx_min and rx_max and rx_min < rx_max:
            zone = {"target_min": rx_min, "target_max": rx_max, "source": "prescribed"}
        elif resting:
            zone = {"target_min": None, "target_max": resting + 20, "source": "resting_plus_20"}
        else:
            zone = {"target_min": None, "target_max": None, "source": "effort_only"}

        self.profiles[user_id] = {
            "user_id": user_id,
            "condition": data.get("condition"),
            "surgery_date": data.get("surgery_date"),
            "current_phase": data.get("current_phase") if data.get("current_phase") in self.phases else 2,
            "resting_hr": resting,
            "target_hr_min": zone["target_min"],
            "target_hr_max": zone["target_max"],
            "zone_source": zone["source"],
            "medications": data.get("medications", []),
            "weight_kg": data.get("weight"),
            "fluid_limit_ml": data.get("fluid_limit_ml"),
            "created_at": time.time(),
        }

        return {
            "status": "ok",
            "program": self.profiles[user_id],
            "current_phase": self.phases[1],
            "heart_rate_zones": {
                "resting": self.profiles[user_id]["resting_hr"],
                "target_min": self.profiles[user_id]["target_hr_min"],
                "target_max": self.profiles[user_id]["target_hr_max"],
                "effort": EFFORT_GUIDE,
                "source": self.profiles[user_id]["zone_source"],
            },
        }

    def log_daily(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log daily cardiac rehab data."""
        if user_id not in self.daily_logs:
            self.daily_logs[user_id] = []

        entry = {
            "date": data.get("date", time.strftime("%Y-%m-%d")),
            "weight_kg": data.get("weight"),
            # Not defaulted: "120/80" and a saturation of 97 are reassuring
            # values, and defaulting to them silenced the alerts below for
            # exactly the patient who did not record a reading.
            "blood_pressure": data.get("bp"),
            "resting_hr": data.get("resting_hr"),
            "spo2": data.get("spo2"),
            "fluid_intake_ml": data.get("fluid_ml", 0),
            "exercise_min": data.get("exercise_min", 0),
            "exercise_type": data.get("exercise_type", "walking"),
            "avg_hr_during_exercise": data.get("avg_hr"),
            "max_hr_during_exercise": data.get("max_hr"),
            "medications_taken": data.get("medications_taken", True),
            "symptoms": data.get("symptoms", []),
            "rpe": data.get("rpe"),
            "mood": data.get("mood"),
            "logged_at": time.time(),
        }

        self.daily_logs[user_id].append(entry)

        # Alerts
        alerts = []
        bp = entry["blood_pressure"]
        if isinstance(bp, str) and "/" in bp:
            try:
                systolic = int(bp.split("/")[0])
            except ValueError:
                systolic = None
            if systolic is not None:
                if systolic > 140: alerts.append("Blood pressure elevated")
                if systolic < 90: alerts.append("Blood pressure low")
        spo2 = entry.get("spo2")
        if isinstance(spo2, (int, float)) and spo2 < 94:
            alerts.append("Oxygen saturation low")
        limit = self.profiles.get(user_id, {}).get("fluid_limit_ml")
        if limit and entry.get("fluid_intake_ml", 0) > limit:
            alerts.append("Fluid intake over daily limit")
        if entry.get("weight_kg") and self.daily_logs[user_id]:
            prev = self.daily_logs[user_id][-2] if len(self.daily_logs[user_id]) > 1 else None
            if prev and prev.get("weight_kg"):
                gain = entry["weight_kg"] - prev["weight_kg"]
                if gain > 1: alerts.append(f"Weight gain of {gain}kg in one day — possible fluid retention")

        return {"entry": entry, "alerts": alerts}

    def get_program(self, user_id: str) -> Dict[str, Any]:
        """
        This user's program, in the same shape setup_program returns.

        Nothing is invented for a user who has not set one up.
        """
        profile = self.profiles.get(user_id)
        if not profile:
            return {"status": "insufficient_data", "message": "Set up your rehab program first."}
        phase = self.phases.get(profile["current_phase"], self.phases[1])
        return {
            "status": "ok",
            "program": profile,
            "current_phase": phase,
            "heart_rate_zones": {
                "resting": profile.get("resting_hr"),
                "target_min": profile["target_hr_min"],
                "target_max": profile["target_hr_max"],
                "effort": EFFORT_GUIDE,
                "source": profile.get("zone_source"),
            },
        }

    def get_exercise_program(self, user_id: str) -> Dict[str, Any]:
        """Current phase exercises, with the target zone only if one exists."""
        profile = self.profiles.get(user_id)
        if not profile:
            return {
                "status": "insufficient_data",
                "message": "Set up a program to see the exercises and target zone for your phase.",
            }
        program = self.phases.get(profile["current_phase"], self.phases[1])
        return {
            "status": "ok",
            "phase": profile["current_phase"],
            "phase_name": program["name"],
            "duration": program["duration_weeks"],
            "exercises": program["exercises"],
            "target_heart_rate": _zone_text(profile),
            "effort": EFFORT_GUIDE,
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
        total_exercise = sum(l.get("exercise_min") or 0 for l in recent)
        # Averaged over the days that recorded one, rather than treating a
        # blank as a middling 5.
        rpes = [l["rpe"] for l in recent if isinstance(l.get("rpe"), (int, float))]
        avg_rpe = sum(rpes) / len(rpes) if rpes else None

        return {
            "total_exercise_minutes": total_exercise,
            "avg_exercise_per_day": round(total_exercise / max(1, len(recent)), 1),
            "average_rpe": round(avg_rpe, 1) if avg_rpe is not None else None,
            "days_logged": len(recent),
            "medication_adherence": round(sum(1 for l in recent if l.get("medications_taken")) / max(1, len(recent)) * 100),
            "encouragement": "Great progress! Keep up the exercise routine." if total_exercise > 150 else "Try to increase your daily exercise gradually.",
        }


from app.core.durable import shared  # noqa: E402

cardiac_rehab_service = shared("app.services.cardiac_rehab.cardiac_rehab_service", CardiacRehabService())
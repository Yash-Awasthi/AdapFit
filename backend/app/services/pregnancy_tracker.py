"""Pregnancy Tracker Service - Comprehensive prenatal and postpartum tracking.

Based on 2025 pregnancy app research:
- Week-by-week fetal development tracking
- Prenatal appointment scheduling
- Weight and nutrition tracking
- Contraction timer
- Kick counter
- Postpartum recovery tracking
- Breastfeeding tracker
- Baby milestone tracking
"""

import time
from typing import Dict, List, Optional, Any


class PregnancyTrackerService:
    """Complete pregnancy and postpartum tracking."""

    def __init__(self):
        self.profiles: Dict[str, Dict] = {}
        self.daily_logs: Dict[str, List] = {}
        self._init_fetal_development()

    def _init_fetal_development(self):
        self.weekly_development = {
            4: {"size": "poppy seed", "size_mm": 2, "weight_g": 0, "milestones": ["Implantation complete", "Amniotic sac forming"], "tip": "Start prenatal vitamins with folic acid"},
            8: {"size": "raspberry", "size_mm": 16, "weight_g": 1, "milestones": ["Heartbeat detectable", "Arms and legs forming", "Facial features developing"], "tip": "Schedule first prenatal visit"},
            12: {"size": "lime", "size_mm": 54, "weight_g": 14, "milestones": ["Organs formed", "Fingerprints forming", "Can suck thumb"], "tip": "NT scan and blood tests this week"},
            16: {"size": "avocado", "size_mm": 116, "weight_g": 100, "milestones": ["Can hear sounds", "Facial expressions", "Movement felt"], "tip": "Consider announcing pregnancy"},
            20: {"size": "banana", "size_mm": 164, "weight_g": 300, "milestones": ["Halfway point!", "Anatomy scan", "Gender may be visible"], "tip": "20-week anatomy scan — important milestone"},
            24: {"size": "corn", "size_mm": 300, "weight_g": 600, "milestones": ["Viability milestone", "Lungs developing", "Regular sleep/wake cycle"], "tip": "Glucose tolerance test usually scheduled now"},
            28: {"size": "eggplant", "size_mm": 370, "weight_g": 1000, "milestones": ["Eyes can open/close", "Dreams may begin", "Kicking regularly"], "tip": "Third trimester begins — start birth plan"},
            32: {"size": "jicama", "size_mm": 420, "weight_g": 1800, "milestones": ["Toenails growing", "Practice breathing", "Head down position"], "tip": "Childbirth classes recommended"},
            36: {"size": "lettuce", "size_mm": 470, "weight_g": 2600, "milestones": ["Lungs nearly mature", "Ready for birth", "Less room to move"], "tip": "Pack hospital bag"},
            40: {"size": "watermelon", "size_mm": 510, "weight_g": 3400, "milestones": ["Full term", "Ready to be born!", "Bones hardening"], "tip": "Monitor for signs of labor"},
        }

        self.prenatal_appointments = [
            {"week": 8, "name": "First Prenatal Visit", "tests": ["Blood work", "Urine test", "Medical history", "Ultrasound"]},
            {"week": 12, "name": "NT Scan", "tests": ["Nuchal translucency scan", "Blood screening"]},
            {"week": 16, "name": "Quad Screen", "tests": ["Blood test for genetic conditions"]},
            {"week": 20, "name": "Anatomy Scan", "tests": ["Detailed ultrasound", "Organ check", "Gender reveal"]},
            {"week": 24, "name": "Glucose Test", "tests": ["Glucose tolerance test", "Anemia screening"]},
            {"week": 28, "name": "Third Trimester Start", "tests": ["Blood type", "Antibodies", "Rh factor"]},
            {"week": 32, "name": "Growth Scan", "tests": ["Ultrasound", "Position check"]},
            {"week": 36, "name": "Group B Strep", "tests": ["GBS swab", "Cervical check"]},
            {"week": 38, "name": "Pre-Labor Check", "tests": ["Cervical dilation", "Baby position"]},
        ]

    def setup_pregnancy(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Set up pregnancy tracking."""
        last_period = data.get("last_period")
        due_date = data.get("due_date")

        profile = {
            "user_id": user_id,
            "last_period": last_period,
            "due_date": due_date,
            "current_week": self._calculate_week(last_period),
            "trimester": None,
            "weight_before_pregnancy": data.get("pre_pregnancy_weight"),
            "height": data.get("height"),
            "blood_type": data.get("blood_type"),
            "conditions": data.get("conditions", []),
            "medications": data.get("medications", []),
            "created_at": time.time(),
        }

        week = profile["current_week"]
        profile["trimester"] = 1 if week <= 12 else 2 if week <= 26 else 3
        profile["baby_size"] = self.weekly_development.get(week, {}).get("size", "developing")
        profile["upcoming_appointments"] = [a for a in self.prenatal_appointments if a["week"] >= week][:3]

        self.profiles[user_id] = profile
        return profile

    def log_daily(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log daily pregnancy data."""
        if user_id not in self.daily_logs:
            self.daily_logs[user_id] = []

        entry = {
            "date": data.get("date", time.strftime("%Y-%m-%d")),
            "weight_kg": data.get("weight_kg"),
            "blood_pressure": data.get("blood_pressure"),
            "mood": data.get("mood"),
            "energy": data.get("energy"),
            "sleep_quality": data.get("sleep_quality"),
            "nausea_level": data.get("nausea", 0),
            "food_cravings": data.get("cravings", []),
            "exercise": data.get("exercise", False),
            "water_intake_ml": data.get("water_ml", 0),
            "prenatal_vitamin": data.get("prenatal_vitamin", True),
            "kick_count": data.get("kick_count", 0),
            "contractions": data.get("contractions", []),
            "symptoms": data.get("symptoms", []),
            "notes": data.get("notes", ""),
            "logged_at": time.time(),
        }

        self.daily_logs[user_id].append(entry)
        return entry

    def get_week_info(self, user_id: str) -> Dict[str, Any]:
        """Get week-by-week development info."""
        profile = self.profiles.get(user_id)
        if not profile:
            return {"error": "Set up pregnancy profile first"}

        week = profile["current_week"]
        dev = self.weekly_development.get(week, self.weekly_development.get(40))
        next_week_dev = self.weekly_development.get(week + 1, dev)

        return {
            "current_week": week,
            "trimester": profile["trimester"],
            "days_until_due": self._days_until_due(profile.get("due_date")),
            "baby_development": dev,
            "next_week_preview": next_week_dev,
            "appointment_checklist": [a for a in self.prenatal_appointments if a["week"] == week],
            "health_tips": self._get_weekly_tips(week),
            "warning_signs": self._get_warning_signs(week),
        }

    def kick_counter(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Track baby kicks."""
        kicks = data.get("kicks", 10)
        duration_min = data.get("duration_minutes", 10)

        return {
            "kicks_counted": kicks,
            "duration_minutes": duration_min,
            "rate": round(kicks / max(1, duration_min), 1),
            "normal_range": "6-10 kicks in 2 hours",
            "status": "normal" if kicks >= 6 else "low — try again after a snack",
            "tip": "Best time to count: baby is usually most active after meals",
        }

    def contraction_timer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Time contractions and assess labor progress."""
        contractions = data.get("contractions", [])

        if len(contractions) < 2:
            return {"message": "Log at least 2 contractions to assess pattern"}

        intervals = []
        for i in range(1, len(contractions)):
            diff = contractions[i] - contractions[i-1]
            intervals.append(diff)

        avg_interval = sum(intervals) / len(intervals)
        avg_duration = data.get("avg_duration_seconds", 45)

        if avg_interval <= 5 * 60:
            phase = "active_labor"
            advice = "Time to go to the hospital!"
        elif avg_interval <= 10 * 60:
            phase = "early_labor"
            advice = "Start timing and prepare to go"
        else:
            phase = "prodromal"
            advice = "False alarms or early labor. Rest and hydrate."

        return {
            "contractions_counted": len(contractions),
            "average_interval_minutes": round(avg_interval / 60, 1),
            "average_duration_seconds": avg_duration,
            "phase": phase,
            "advice": advice,
            "go_to_hospital": avg_interval <= 5 * 60,
        }

    def get_postpartum_guide(self) -> Dict[str, Any]:
        """Postpartum recovery guide."""
        return {
            "recovery_timeline": {
                "immediate": ["Skin-to-skin contact", "First breastfeeding", "Rest"],
                "first_week": ["Perineal care", "Incision care (C-section)", "Sleep when baby sleeps"],
                "first_month": ["Healing", "Feeding routine", "Mental health check"],
                "6_weeks": ["Postpartum checkup", "Exercise clearance", "Birth control discussion"],
            },
            "warning_signs_seek_help": [
                "Heavy bleeding (soaking pad in <1 hour)",
                "Fever above 38°C",
                "Severe headache with vision changes",
                "Chest pain or difficulty breathing",
                "Thoughts of harming self or baby",
            ],
            "mental_health": {
                "baby_blues": "Common in first 2 weeks, resolves on its own",
                "postpartum_depression": "If symptoms persist beyond 2 weeks, seek help",
                "screening": "PHQ-9 screening recommended at 2-week and 6-week visits",
            },
        }

    def _calculate_week(self, last_period: str) -> int:
        if not last_period:
            return 20
        try:
            from datetime import datetime
            lmp = datetime.strptime(last_period, "%Y-%m-%d")
            days = (datetime.now() - lmp).days
            return max(1, min(42, days // 7))
        except (ValueError, TypeError):
            return 20

    def _days_until_due(self, due_date: Optional[str]) -> int:
        if not due_date:
            return 140
        try:
            from datetime import datetime
            due = datetime.strptime(due_date, "%Y-%m-%d")
            return max(0, (due - datetime.now()).days)
        except (ValueError, TypeError):
            return 140

    def _get_weekly_tips(self, week: int) -> List[str]:
        if week <= 12:
            return ["Continue prenatal vitamins", "Stay hydrated", "Get plenty of rest", "Avoid raw fish and deli meats"]
        elif week <= 26:
            return ["Stay active with gentle exercise", "Monitor weight gain", "Attend all prenatal appointments", "Practice sleeping on your side"]
        else:
            return ["Practice breathing exercises", "Pack your hospital bag", "Finalize birth plan", "Install car seat"]

    def _get_warning_signs(self, week: int) -> List[str]:
        signs = ["Severe abdominal pain", "Heavy vaginal bleeding", "Fluid leaking from vagina", "Sudden severe swelling"]
        if week >= 20:
            signs.append("Decreased fetal movement")
        if week >= 28:
            signs.extend(["Severe headache", "Vision changes", "Upper abdominal pain"])
        return signs


pregnancy_tracker_service = PregnancyTrackerService()

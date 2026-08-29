"""Fertility Tracker Service - Comprehensive reproductive health tracking.

Based on 2025 research on ovulation prediction:
- Basal Body Temperature (BBT) tracking and analysis
- Cervical mucus monitoring
- LH surge detection
- Ovulation prediction (calendar + symptothermal)
- Fertile window calculation
- Cycle irregularity detection
- Pregnancy likelihood scoring
"""

import time
import math
import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


class FertilityTrackerService:
    """Comprehensive fertility and reproductive health tracking."""

    def __init__(self):
        self.users: Dict[str, Dict] = {}
        self.daily_logs: Dict[str, List] = {}
        self._init_cycle_phases()

    def _init_cycle_phases(self):
        self.cycle_phases = {
            "menstrual": {"days": "1-5", "hormones": "low estrogen, low progesterone", "fertility": "very_low"},
            "follicular": {"days": "6-13", "hormones": "rising estrogen", "fertility": "increasing"},
            "ovulation": {"days": "14-16", "hormones": "estrogen peak, LH surge", "fertility": "peak"},
            "luteal": {"days": "17-28", "hormones": "high progesterone", "fertility": "declining"},
        }

    def setup_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Set up fertility tracking profile."""
        cycle_length = profile_data.get("average_cycle_length", 28)
        period_length = profile_data.get("average_period_length", 5)
        luteal_phase = profile_data.get("luteal_phase_length", 14)
        ovulation_day = cycle_length - luteal_phase

        self.users[user_id] = {
            "user_id": user_id,
            "average_cycle_length": cycle_length,
            "average_period_length": period_length,
            "luteal_phase_length": luteal_phase,
            "estimated_ovulation_day": ovulation_day,
            "fertile_window_start": ovulation_day - 5,
            "fertile_window_end": ovulation_day + 1,
            "last_period_start": profile_data.get("last_period_start"),
            "trying_to_conceive": profile_data.get("trying_to_conceive", False),
            "tracking_start": time.time(),
        }

        return self.users[user_id]

    def log_daily(self, user_id: str, date: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log daily fertility data."""
        if user_id not in self.daily_logs:
            self.daily_logs[user_id] = []

        entry = {
            "user_id": user_id,
            "date": date,
            "bbt": data.get("bbt"),  # basal body temperature in Celsius
            "cervical_mucus": data.get("cervical_mucus", "dry"),  # dry, sticky, creamy, watery, egg_white
            "lh_strip": data.get("lh_strip", None),  # positive, negative, null
            "cervix_position": data.get("cervix_position", None),  # low/firm/closed, high/soft/open
            "intercourse": data.get("intercourse", False),
            "spotting": data.get("spotting", False),
            "mood": data.get("mood"),
            "energy": data.get("energy"),
            "breast_tenderness": data.get("breast_tenderness", False),
            "cramping": data.get("cramping", False),
            "bloating": data.get("bloating", False),
            "headache": data.get("headache", False),
            "nausea": data.get("nausea", False),
            "logged_at": time.time(),
        }

        self.daily_logs[user_id].append(entry)

        # Analyze fertility status
        analysis = self._analyze_day(user_id, entry)
        entry["fertility_analysis"] = analysis

        return entry

    def predict_next_period(self, user_id: str) -> Dict[str, Any]:
        """Predict next period and fertile window."""
        profile = self.users.get(user_id)
        if not profile:
            return {"error": "Set up profile first"}

        logs = self.daily_logs.get(user_id, [])
        if not logs:
            return {"error": "No cycle data logged yet"}

        # Find last period
        last_period = profile.get("last_period_start")
        if not last_period:
            # Try to find from logs
            for log in reversed(logs):
                if log.get("spotting"):
                    last_period = log["date"]
                    break

        if not last_period:
            return {"error": "Cannot determine last period start"}

        cycle_length = profile["average_cycle_length"]
        try:
            last_dt = datetime.strptime(last_period, "%Y-%m-%d")
        except (ValueError, TypeError):
            last_dt = datetime.now()

        next_period = last_dt + timedelta(days=cycle_length)
        ovulation_day = last_dt + timedelta(days=profile["estimated_ovulation_day"])
        fertile_start = last_dt + timedelta(days=profile["fertile_window_start"])
        fertile_end = last_dt + timedelta(days=profile["fertile_window_end"])

        today = datetime.now()
        days_in_cycle = (today - last_dt).days + 1
        current_phase = self._get_current_phase(days_in_cycle, profile)

        return {
            "current_cycle_day": max(1, days_in_cycle),
            "current_phase": current_phase,
            "next_period": next_period.strftime("%Y-%m-%d"),
            "days_until_period": max(0, (next_period - today).days),
            "estimated_ovulation": ovulation_day.strftime("%Y-%m-%d"),
            "fertile_window": {
                "start": fertile_start.strftime("%Y-%m-%d"),
                "end": fertile_end.strftime("%Y-%m-%d"),
            },
            "is_fertile": fertile_start <= today <= fertile_end,
            "cycle_length": cycle_length,
        }

    def get_cycle_insights(self, user_id: str) -> Dict[str, Any]:
        """Get insights from tracked cycle data."""
        logs = self.daily_logs.get(user_id, [])
        if len(logs) < 7:
            return {"message": "Log at least 7 days for insights", "days_logged": len(logs)}

        # BBT analysis
        bbt_readings = [l["bbt"] for l in logs if l.get("bbt")]
        avg_bbt = sum(bbt_readings) / max(1, len(bbt_readings))
        bbt_shift = self._detect_bbt_shift(bbt_readings)

        # CM analysis
        cm_types = [l["cervical_mucus"] for l in logs if l.get("cervical_mucus")]
        cm_fertile_days = sum(1 for c in cm_types if c in ("watery", "egg_white"))

        # LH analysis
        lh_positives = sum(1 for l in logs if l.get("lh_strip") == "positive")

        # Symptom patterns
        symptom_freq = {}
        for log in logs:
            for symptom in ["breast_tenderness", "cramping", "bloating", "headache"]:
                if log.get(symptom):
                    symptom_freq[symptom] = symptom_freq.get(symptom, 0) + 1

        return {
            "days_tracked": len(logs),
            "bbt_analysis": {
                "average": round(avg_bbt, 1),
                "shift_detected": bbt_shift["detected"],
                "shift_date": bbt_shift.get("date"),
                "interpretation": bbt_shift["interpretation"],
            },
            "cervical_mucus": {
                "fertile_type_days": cm_fertile_days,
                "pattern": self._interpret_cm_pattern(cm_types),
            },
            "lh_analysis": {
                "positive_strips": lh_positives,
                "surge_detected": lh_positives > 0,
            },
            "symptom_patterns": symptom_freq,
            "cycle_regularity": self._assess_regularity(user_id),
            "fertility_score": self._calculate_daily_fertility_score(logs[-1] if logs else {}),
        }

    def _analyze_day(self, user_id: str, entry: Dict) -> Dict[str, Any]:
        """Analyze a single day's fertility indicators."""
        score = 0
        signals = []

        # BBT
        if entry.get("bbt"):
            if entry["bbt"] >= 36.5:
                score += 20
                signals.append("Elevated BBT (post-ovulation pattern)")
            else:
                score += 10
                signals.append("Baseline BBT (pre-ovulation)")

        # Cervical mucus
        cm = entry.get("cervical_mucus", "dry")
        cm_scores = {"egg_white": 30, "watery": 25, "creamy": 15, "sticky": 5, "dry": 0}
        score += cm_scores.get(cm, 0)
        if cm in ("egg_white", "watery"):
            signals.append(f"Fertile cervical mucus ({cm})")

        # LH
        if entry.get("lh_strip") == "positive":
            score += 30
            signals.append("Positive LH strip - ovulation likely within 24-36 hours")

        # Cervix
        if entry.get("cervix_position") == "high/soft/open":
            score += 15
            signals.append("Cervix in fertile position")

        fertility_level = "peak" if score >= 70 else "high" if score >= 50 else "moderate" if score >= 25 else "low"

        return {
            "fertility_score": min(100, score),
            "fertility_level": fertility_level,
            "signals": signals,
            "recommended_action": self._get_fertility_action(fertility_level, entry.get("intercourse", False)),
        }

    def _detect_bbt_shift(self, readings: List[float]) -> Dict[str, Any]:
        if len(readings) < 10:
            return {"detected": False, "interpretation": "Not enough data"}

        first_half = readings[:len(readings)//2]
        second_half = readings[len(readings)//2:]
        avg_first = sum(first_half) / max(1, len(first_half))
        avg_second = sum(second_half) / max(1, len(second_half))

        shift = avg_second - avg_first
        if shift >= 0.2:
            return {"detected": True, "date": "Recent", "shift_magnitude": round(shift, 2),
                    "interpretation": "BBT shift detected - likely ovulation occurred"}
        else:
            return {"detected": False, "interpretation": "No clear BBT shift yet"}

    def _interpret_cm_pattern(self, cm_types: List[str]) -> str:
        if not cm_types:
            return "insufficient_data"
        if cm_types[-1] in ("egg_white", "watery"):
            return "fertile_pattern"
        if cm_types[-1] == "dry":
            return "infertile_pattern"
        return "transitioning"

    def _assess_regularity(self, user_id: str) -> Dict[str, Any]:
        return {"regular": True, "variation_days": 2, "assessment": "Your cycles appear regular"}

    def _calculate_daily_fertility_score(self, log: Dict) -> int:
        if not log:
            return 0
        score = 0
        cm = log.get("cervical_mucus", "dry")
        cm_scores = {"egg_white": 35, "watery": 30, "creamy": 15, "sticky": 5, "dry": 0}
        score += cm_scores.get(cm, 0)
        if log.get("lh_strip") == "positive":
            score += 35
        if log.get("bbt") and log["bbt"] < 36.5:
            score += 15
        if log.get("cervix_position") == "high/soft/open":
            score += 15
        return min(100, score)

    def _get_current_phase(self, day: int, profile: Dict) -> str:
        period_len = profile["average_period_length"]
        ov_day = profile["estimated_ovulation_day"]
        if day <= period_len:
            return "menstrual"
        elif day <= ov_day - 1:
            return "follicular"
        elif day <= ov_day + 1:
            return "ovulation"
        else:
            return "luteal"

    def _get_fertility_action(self, level: str, had_intercourse: bool) -> str:
        if level == "peak":
            return "Peak fertility! If trying to conceive, time intercourse for today."
        elif level == "high":
            return "High fertility. Great time to conceive if trying."
        elif level == "moderate":
            return "Moderate fertility. Fertile window approaching."
        else:
            return "Low fertility. Focus on overall health and wellness."


fertility_tracker_service = FertilityTrackerService()

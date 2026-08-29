"""
Medication Reminder Service — Schedule, Track & Adhere

Features:
- Medication schedule management (name, dosage, frequency, times)
- Smart reminders based on medication timing
- Adherence tracking and scoring
- Missed dose alerts
- Medication interaction warnings (basic)
- Refill reminders
- Historical adherence reports
"""
import time
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class MedicationFrequency(Enum):
    ONCE_DAILY = "once_daily"
    TWICE_DAILY = "twice_daily"
    THREE_TIMES = "three_times_daily"
    FOUR_TIMES = "four_times_daily"
    AS_NEEDED = "as_needed"
    WEEKLY = "weekly"


class DoseStatus(Enum):
    TAKEN = "taken"
    MISSED = "missed"
    SKIPPED = "skipped"
    PENDING = "pending"


@dataclass
class Medication:
    id: str
    name: str
    dosage: str
    frequency: MedicationFrequency
    times: list[str]  # ["08:00", "20:00"]
    category: str  # "supplement", "prescription", "otc"
    notes: str = ""
    refill_date: Optional[str] = None
    refill_quantity: int = 0
    active: bool = True


@dataclass
class DoseLog:
    medication_id: str
    scheduled_time: str
    actual_time: Optional[str]
    status: DoseStatus
    date: str
    notes: str = ""


class MedicationReminderService:
    """Medication management and adherence tracking system."""

    # Common supplement interactions (simplified)
    INTERACTIONS = {
        ("iron", "calcium"): "Take iron and calcium 2 hours apart for better absorption",
        ("iron", "coffee"): "Avoid coffee within 1 hour of iron supplements",
        ("zinc", "copper"): "Take zinc and copper at different times",
        ("vitamin_d", "vitamin_k"): "These work well together — can take simultaneously",
        ("omega3", "blood_thinner"): "Consult doctor — omega-3 may increase bleeding risk",
    }

    def __init__(self):
        self._medications: list[Medication] = []
        self._dose_logs: list[DoseLog] = []

    def add_medication(self, name: str, dosage: str, frequency: str, times: list[str],
                       category: str = "supplement", notes: str = "") -> dict:
        """Add a new medication to track."""
        try:
            freq = MedicationFrequency(frequency)
        except ValueError:
            freq = MedicationFrequency.ONCE_DAILY

        med = Medication(
            id=f"med_{int(time.time())}_{len(self._medications)}",
            name=name, dosage=dosage, frequency=freq,
            times=times, category=category, notes=notes,
        )
        self._medications.append(med)

        # Check for interactions
        warnings = self._check_interactions(name.lower())

        return {
            "added": True, "medication_id": med.id, "name": name,
            "schedule": times, "frequency": frequency,
            "interactions": warnings,
        }

    def log_dose(self, medication_id: str, status: str = "taken") -> dict:
        """Log a dose as taken, missed, or skipped."""
        try:
            dose_status = DoseStatus(status)
        except ValueError:
            dose_status = DoseStatus.TAKEN

        now = time.localtime()
        log = DoseLog(
            medication_id=medication_id,
            scheduled_time=f"{now.tm_hour:02d}:{now.tm_min:02d}",
            actual_time=f"{now.tm_hour:02d}:{now.tm_min:02d}" if dose_status == DoseStatus.TAKEN else None,
            status=dose_status,
            date=time.strftime("%Y-%m-%d"),
        )
        self._dose_logs.append(log)
        return {"logged": True, "status": status, "medication_id": medication_id}

    def get_today_schedule(self) -> dict:
        """Get today's medication schedule with adherence status."""
        schedule = []
        for med in self._medications:
            if not med.active:
                continue
            for t in med.times:
                today_logs = [l for l in self._dose_logs if l.medication_id == med.id and l.date == time.strftime("%Y-%m-%d") and l.scheduled_time == t]
                status = today_logs[-1].status.value if today_logs else "pending"
                schedule.append({
                    "medication": med.name, "dosage": med.dosage,
                    "time": t, "status": status, "category": med.category,
                    "med_id": med.id,
                })
        schedule.sort(key=lambda x: x["time"])
        taken = sum(1 for s in schedule if s["status"] == "taken")
        return {
            "date": time.strftime("%Y-%m-%d"),
            "total_doses": len(schedule),
            "taken": taken,
            "pending": sum(1 for s in schedule if s["status"] == "pending"),
            "missed": sum(1 for s in schedule if s["status"] == "missed"),
            "adherence_pct": round(taken / max(1, len(schedule)) * 100),
            "schedule": schedule,
        }

    def get_adherence_score(self, days: int = 30) -> dict:
        """Calculate adherence score over a period."""
        recent_logs = self._dose_logs[-100:]  # placeholder window
        if not recent_logs:
            return {"score": 0, "message": "No dose data yet. Start logging!"}
        taken = sum(1 for l in recent_logs if l.status == DoseStatus.TAKEN)
        total = len(recent_logs)
        score = round(taken / max(1, total) * 100)
        return {
            "score": score,
            "total_scheduled": total,
            "total_taken": taken,
            "total_missed": sum(1 for l in recent_logs if l.status == DoseStatus.MISSED),
            "streak": self._calculate_streak(),
            "rating": "excellent" if score >= 90 else "good" if score >= 75 else "fair" if score >= 50 else "poor",
        }

    def get_refill_alerts(self) -> list[dict]:
        """Check for medications needing refill."""
        alerts = []
        for med in self._medications:
            if med.refill_date:
                refill_ts = time.mktime(time.strptime(med.refill_date, "%Y-%m-%d"))
                days_until = (refill_ts - time.time()) / 86400
                if days_until <= 7:
                    alerts.append({
                        "medication": med.name,
                        "refill_date": med.refill_date,
                        "days_until": max(0, round(days_until)),
                        "urgency": "critical" if days_until <= 2 else "warning",
                    })
        return alerts

    def get_all_medications(self) -> list[dict]:
        """List all tracked medications."""
        return [
            {"id": m.id, "name": m.name, "dosage": m.dosage, "frequency": m.frequency.value,
             "times": m.times, "category": m.category, "active": m.active}
            for m in self._medications
        ]

    # === Private ===
    def _check_interactions(self, new_med: str) -> list[str]:
        warnings = []
        existing = [m.name.lower() for m in self._medications]
        for (a, b), msg in self.INTERACTIONS.items():
            if (new_med in a and any(b in e for e in existing)) or (new_med in b and any(a in e for e in existing)):
                warnings.append(msg)
        return warnings

    def _calculate_streak(self) -> int:
        streak = 0
        for log in reversed(self._dose_logs):
            if log.status == DoseStatus.TAKEN:
                streak += 1
            else:
                break
        return streak


medication_reminder_service = MedicationReminderService()

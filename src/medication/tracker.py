"""
Medication Tracker — tracks medication schedules, doses, and interactions.
Provides reminders, adherence tracking, and safety checks.

Inspired by: dosezy (medicine tracking app)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class MedicationFrequency(Enum):
    ONCE_DAILY = "once_daily"
    TWICE_DAILY = "twice_daily"
    THREE_TIMES = "three_times_daily"
    FOUR_TIMES = "four_times_daily"
    WEEKLY = "weekly"
    AS_NEEDED = "as_needed"
    CUSTOM = "custom"


class DoseStatus(Enum):
    TAKEN = "taken"
    MISSED = "missed"
    SKIPPED = "skipped"
    PENDING = "pending"
    SNOOZED = "snoozed"


@dataclass
class Medication:
    """A medication definition."""
    id: str
    name: str
    dosage: str  # e.g., "500mg"
    frequency: MedicationFrequency
    times_of_day: list[str] = field(default_factory=lambda: ["08:00"])  # HH:MM
    start_date: datetime | None = None
    end_date: datetime | None = None
    instructions: str = ""  # "Take with food"
    side_effects: list[str] = field(default_factory=list)
    contraindications: list[str] = field(default_factory=list)
    category: str = ""  # supplement, prescription, otc
    notes: str = ""


@dataclass
class DoseRecord:
    """A record of a medication dose."""
    medication_id: str
    scheduled_time: datetime
    actual_time: datetime | None = None
    status: DoseStatus = DoseStatus.PENDING
    notes: str = ""


@dataclass
class MedicationAdherence:
    """Adherence statistics for a medication."""
    medication_id: str
    medication_name: str
    total_scheduled: int
    total_taken: int
    total_missed: int
    total_skipped: int
    adherence_pct: float
    streak_days: int
    last_taken: datetime | None


class MedicationTracker:
    """Tracks medication schedules, doses, and adherence."""

    def __init__(self) -> None:
        self._medications: dict[str, Medication] = {}
        self._records: dict[str, list[DoseRecord]] = {}  # med_id -> records

    def add_medication(self, med: Medication) -> None:
        """Register a medication."""
        self._medications[med.id] = med
        self._records.setdefault(med.id, [])

    def remove_medication(self, med_id: str) -> None:
        """Remove a medication."""
        self._medications.pop(med_id, None)
        self._records.pop(med_id, None)

    def get_todays_schedule(self, date: datetime | None = None) -> list[dict[str, Any]]:
        """Get today's medication schedule with status."""
        target_date = date or datetime.utcnow()
        schedule: list[dict[str, Any]] = []

        for med_id, med in self._medications.items():
            if med.end_date and target_date > med.end_date:
                continue

            for time_str in med.times_of_day:
                hour, minute = map(int, time_str.split(":"))
                scheduled = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

                # Check if already recorded
                status = DoseStatus.PENDING
                actual_time = None
                for record in self._records.get(med_id, []):
                    if record.scheduled_time.date() == target_date.date():
                        if abs((record.scheduled_time - scheduled).total_seconds()) < 3600:
                            status = record.status
                            actual_time = record.actual_time
                            break

                schedule.append({
                    "medication_id": med_id,
                    "medication_name": med.name,
                    "dosage": med.dosage,
                    "scheduled_time": scheduled.isoformat(),
                    "time_display": time_str,
                    "status": status.value,
                    "actual_time": actual_time.isoformat() if actual_time else None,
                    "instructions": med.instructions,
                })

        schedule.sort(key=lambda x: x["scheduled_time"])
        return schedule

    def log_dose(
        self,
        med_id: str,
        scheduled_time: datetime,
        status: DoseStatus,
        actual_time: datetime | None = None,
        notes: str = "",
    ) -> DoseRecord | None:
        """Log a medication dose."""
        if med_id not in self._medications:
            return None

        record = DoseRecord(
            medication_id=med_id,
            scheduled_time=scheduled_time,
            actual_time=actual_time or datetime.utcnow(),
            status=status,
            notes=notes,
        )
        self._records.setdefault(med_id, []).append(record)
        return record

    def get_adherence(self, med_id: str, days: int = 30) -> MedicationAdherence | None:
        """Calculate adherence for a medication over the past N days."""
        med = self._medications.get(med_id)
        if not med:
            return None

        cutoff = datetime.utcnow() - timedelta(days=days)
        records = [r for r in self._records.get(med_id, []) if r.scheduled_time >= cutoff]

        total_scheduled = len(records)
        total_taken = sum(1 for r in records if r.status == DoseStatus.TAKEN)
        total_missed = sum(1 for r in records if r.status == DoseStatus.MISSED)
        total_skipped = sum(1 for r in records if r.status == DoseStatus.SKIPPED)

        adherence_pct = (total_taken / max(total_scheduled, 1)) * 100

        # Calculate streak
        streak = 0
        taken_dates = sorted(set(
            r.scheduled_time.date()
            for r in records
            if r.status == DoseStatus.TAKEN
        ), reverse=True)

        if taken_dates:
            today = datetime.utcnow().date()
            for i, d in enumerate(taken_dates):
                expected = today - timedelta(days=i)
                if d == expected:
                    streak += 1
                else:
                    break

        last_taken = max(
            (r.actual_time for r in records if r.status == DoseStatus.TAKEN and r.actual_time),
            default=None,
        )

        return MedicationAdherence(
            medication_id=med_id,
            medication_name=med.name,
            total_scheduled=total_scheduled,
            total_taken=total_taken,
            total_missed=total_missed,
            total_skipped=total_skipped,
            adherence_pct=round(adherence_pct, 1),
            streak_days=streak,
            last_taken=last_taken,
        )

    def get_overall_adherence(self, days: int = 30) -> dict[str, Any]:
        """Get overall adherence across all medications."""
        total_scheduled = 0
        total_taken = 0
        med_count = 0

        for med_id in self._medications:
            adherence = self.get_adherence(med_id, days)
            if adherence:
                total_scheduled += adherence.total_scheduled
                total_taken += adherence.total_taken
                med_count += 1

        overall_pct = (total_taken / max(total_scheduled, 1)) * 100

        return {
            "medications_tracked": med_count,
            "total_scheduled": total_scheduled,
            "total_taken": total_taken,
            "overall_adherence_pct": round(overall_pct, 1),
            "period_days": days,
        }

    def get_upcoming_reminders(self, hours_ahead: int = 2) -> list[dict[str, Any]]:
        """Get upcoming medication reminders within the next N hours."""
        now = datetime.utcnow()
        cutoff = now + timedelta(hours=hours_ahead)
        schedule = self.get_todays_schedule(now)

        return [
            s for s in schedule
            if s["status"] == DoseStatus.PENDING.value
            and now.isoformat() <= s["scheduled_time"] <= cutoff.isoformat()
        ]

    def check_interactions(self, med_ids: list[str]) -> list[dict[str, str]]:
        """Check for known interactions between medications."""
        # Simplified interaction check based on contraindications
        interactions: list[dict[str, str]] = []
        meds = [self._medications.get(mid) for mid in med_ids if mid in self._medications]

        for i, med_a in enumerate(meds):
            for med_b in meds[i+1:]:
                if med_b.name.lower() in [c.lower() for c in med_a.contraindications]:
                    interactions.append({
                        "drug_a": med_a.name,
                        "drug_b": med_b.name,
                        "severity": "moderate",
                        "description": f"{med_a.name} may interact with {med_b.name}",
                    })
                if med_a.name.lower() in [c.lower() for c in med_b.contraindications]:
                    interactions.append({
                        "drug_a": med_b.name,
                        "drug_b": med_a.name,
                        "severity": "moderate",
                        "description": f"{med_b.name} may interact with {med_a.name}",
                    })

        return interactions

"""
Health Calendar — Menstrual Cycle, Medication Schedule, Appointments

Features:
- Menstrual cycle tracking with predictions
- Ovulation window estimation
- PMS symptom logging
- Medication schedule management
- Appointment calendar
- Period predictions (next 6 cycles)
- Fertility window indicators
"""
import time
import math
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class CycleEntry:
    start_date: str
    end_date: str
    length: int
    flow_intensity: str  # light, medium, heavy
    symptoms: list[str]
    mood: int
    notes: str = ""


class HealthCalendarService:
    """Comprehensive health calendar with cycle tracking and scheduling."""

    def __init__(self):
        self._cycle_entries: list[CycleEntry] = []
        self._medication_schedule: list[dict] = []
        self._appointments: list[dict] = []
        self._symptoms_log: list[dict] = []
        self._cycle_length: int = 28
        self._period_length: int = 5

    # === Menstrual Cycle ===

    def log_period(self, start_date: str, end_date: str, flow: str = "medium", symptoms: list[str] = None, mood: int = 5, notes: str = "") -> dict:
        start = time.mktime(time.strptime(start_date, "%Y-%m-%d"))
        end = time.mktime(time.strptime(end_date, "%Y-%m-%d"))
        length = int((end - start) / 86400) + 1
        entry = CycleEntry(start_date=start_date, end_date=end_date, length=length, flow_intensity=flow, symptoms=symptoms or [], mood=mood, notes=notes)
        self._cycle_entries.append(entry)
        if len(self._cycle_entries) >= 2:
            self._update_cycle_length()
        return {"logged": True, "cycle_length": length, "period_length": len(self._get_period_days(start_date, end_date))}

    def _update_cycle_length(self):
        if len(self._cycle_entries) < 2:
            return
        dates = sorted([time.mktime(time.strptime(e.start_date, "%Y-%m-%d")) for e in self._cycle_entries])
        diffs = [(dates[i+1] - dates[i]) / 86400 for i in range(len(dates)-1)]
        self._cycle_length = int(sum(diffs) / len(diffs)) if diffs else 28

    def _get_period_days(self, start: str, end: str) -> list[str]:
        s = time.mktime(time.strptime(start, "%Y-%m-%d"))
        e = time.mktime(time.strptime(end, "%Y-%m-%d"))
        days = []
        while s <= e:
            days.append(time.strftime("%Y-%m-%d", time.localtime(s)))
            s += 86400
        return days

    def get_predictions(self) -> dict:
        if not self._cycle_entries:
            return {"message": "No cycle data yet. Start logging to see predictions."}
        last = max(self._cycle_entries, key=lambda e: e.start_date)
        last_start = time.mktime(time.strptime(last.start_date, "%Y-%m-%d"))
        predictions = []
        for i in range(1, 7):
            next_start = last_start + self._cycle_length * i * 86400
            next_end = next_start + self._period_length * 86400
            ovulation = next_start - 14 * 86400
            fertile_start = ovulation - 5 * 86400
            fertile_end = ovulation + 1 * 86400
            predictions.append({
                "cycle": i,
                "predicted_start": time.strftime("%Y-%m-%d", time.localtime(next_start)),
                "predicted_end": time.strftime("%Y-%m-%d", time.localtime(next_end)),
                "ovulation_date": time.strftime("%Y-%m-%d", time.localtime(ovulation)),
                "fertile_window": {"start": time.strftime("%Y-%m-%d", time.localtime(fertile_start)), "end": time.strftime("%Y-%m-%d", time.localtime(fertile_end))},
                "confidence": "high" if i <= 2 else "medium" if i <= 4 else "low",
            })
        return {"average_cycle_length": self._cycle_length, "average_period_length": self._period_length, "predictions": predictions, "total_cycles_logged": len(self._cycle_entries)}

    def get_cycle_summary(self) -> dict:
        if not self._cycle_entries:
            return {"status": "no_data"}
        lengths = [e.length for e in self._cycle_entries]
        symptoms_all = []
        for e in self._cycle_entries:
            symptoms_all.extend(e.symptoms)
        from collections import Counter
        common_symptoms = Counter(symptoms_all).most_common(5)
        return {
            "total_cycles": len(self._cycle_entries),
            "average_cycle_length": round(sum(lengths) / len(lengths), 1),
            "shortest_cycle": min(lengths),
            "longest_cycle": max(lengths),
            "regularity": "regular" if max(lengths) - min(lengths) <= 7 else "irregular",
            "common_symptoms": [{"symptom": s, "count": c} for s, c in common_symptoms],
        }

    def log_symptoms(self, date: str, symptoms: list[str], mood: int = 5, energy: int = 5, pain_level: int = 0, notes: str = "") -> dict:
        entry = {"date": date, "symptoms": symptoms, "mood": mood, "energy": energy, "pain_level": pain_level, "notes": notes, "timestamp": time.time()}
        self._symptoms_log.append(entry)
        return {"logged": True, "symptoms": symptoms}

    def get_symptoms_history(self, days: int = 30) -> list[dict]:
        cutoff = time.time() - days * 86400
        return [s for s in self._symptoms_log if s["timestamp"] > cutoff]

    # === Appointments ===

    def add_appointment(self, title: str, date: str, time_str: str, doctor: str = "", location: str = "", notes: str = "") -> dict:
        appt = {"id": f"appt_{int(time.time())}", "title": title, "date": date, "time": time_str, "doctor": doctor, "location": location, "notes": notes, "created_at": time.time()}
        self._appointments.append(appt)
        return {"added": True, "appointment": appt}

    def get_appointments(self, month: str = "") -> list[dict]:
        appts = self._appointments
        if month:
            appts = [a for a in appts if a["date"].startswith(month)]
        return sorted(appts, key=lambda a: a["date"])

    def get_upcoming(self, days: int = 7) -> list[dict]:
        cutoff = time.time() + days * 86400
        return [a for a in self._appointments if time.mktime(time.strptime(a["date"], "%Y-%m-%d")) <= cutoff]

    # === Medication Schedule ===

    def add_medication(self, name: str, dosage: str, times: list[str], frequency: str = "daily") -> dict:
        med = {"id": f"med_{int(time.time())}", "name": name, "dosage": dosage, "times": times, "frequency": frequency, "active": True}
        self._medication_schedule.append(med)
        return {"added": True, "medication": med}

    def get_todays_medications(self) -> list[dict]:
        return [m for m in self._medication_schedule if m["active"]]

    def get_medication_adherence(self, days: int = 30) -> dict:
        total = len(self._medication_schedule) * days
        taken = int(total * 0.85)  # simulated
        return {"adherence_rate": round(taken / max(1, total) * 100), "total_doses": total, "taken": taken, "missed": total - taken}


health_calendar_service = HealthCalendarService()

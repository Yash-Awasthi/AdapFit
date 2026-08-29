"""
Blood Pressure Service — BP Logging, Classification & Trend Analysis

Based on AHA (American Heart Association) guidelines:
- Normal: <120/<80
- Elevated: 120-129/<80
- Hypertension Stage 1: 130-139/80-89
- Hypertension Stage 2: ≥140/≥90
- Crisis: >180/>120
"""
import time
from typing import Optional


class BloodPressureService:
    """Blood pressure tracking, classification, and analysis."""

    def __init__(self):
        self._readings: list[dict] = []

    def log_reading(self, systolic: int, diastolic: int, pulse: Optional[int] = None,
                    context: str = "resting", notes: str = "") -> dict:
        classification = self._classify(systolic, diastolic)
        reading = {
            "id": f"bp_{int(time.time())}", "systolic": systolic, "diastolic": diastolic,
            "pulse": pulse, "classification": classification, "context": context,
            "notes": notes, "timestamp": time.time(),
        }
        self._readings.append(reading)
        return {
            "logged": True, "systolic": systolic, "diastolic": diastolic,
            "classification": classification["label"], "color": classification["color"],
            "message": classification["message"],
        }

    def get_today_readings(self) -> list[dict]:
        today = time.strftime("%Y-%m-%d")
        return [
            {"systolic": r["systolic"], "diastolic": r["diastolic"], "pulse": r["pulse"],
             "classification": r["classification"]["label"], "context": r["context"],
             "time": time.strftime("%H:%M", time.localtime(r["timestamp"]))}
            for r in self._readings if time.strftime("%Y-%m-%d", time.localtime(r["timestamp"])) == today
        ]

    def get_trend(self, days: int = 30) -> dict:
        if not self._readings: return {"trend": "no_data"}
        recent = self._readings[-50:]
        avg_sys = sum(r["systolic"] for r in recent) / len(recent)
        avg_dia = sum(r["diastolic"] for r in recent) / len(recent)
        return {
            "average": {"systolic": round(avg_sys), "diastolic": round(avg_dia)},
            "reading_count": len(recent),
            "latest": {"systolic": recent[-1]["systolic"], "diastolic": recent[-1]["diastolic"]},
            "classification": self._classify(recent[-1]["systolic"], recent[-1]["diastolic"])["label"],
        }

    def get_doctor_report(self) -> dict:
        if not self._readings: return {"message": "No readings yet"}
        readings = self._readings[-100:]
        avg_sys = sum(r["systolic"] for r in readings) / len(readings)
        avg_dia = sum(r["diastolic"] for r in readings) / len(readings)
        max_sys = max(r["systolic"] for r in readings)
        max_dia = max(r["diastolic"] for r in readings)
        return {
            "period": f"Last {len(readings)} readings",
            "average": {"systolic": round(avg_sys), "diastolic": round(avg_dia)},
            "highest": {"systolic": max_sys, "diastolic": max_dia},
            "readings_count": len(readings),
            "classification": self._classify(round(avg_sys), round(avg_dia))["label"],
            "recommendation": "Share this report with your healthcare provider at your next visit.",
        }

    def _classify(self, sys: int, dia: int) -> dict:
        if sys > 180 or dia > 120:
            return {"label": "Hypertensive Crisis", "color": "#DC2626", "message": "⚠️ Seek immediate medical attention! Blood pressure is dangerously high."}
        elif sys >= 140 or dia >= 90:
            return {"label": "Hypertension Stage 2", "color": "#EF4444", "message": "High blood pressure. Consult your doctor about treatment options."}
        elif sys >= 130 or dia >= 80:
            return {"label": "Hypertension Stage 1", "color": "#F97316", "message": "Elevated blood pressure. Lifestyle changes recommended. Monitor regularly."}
        elif sys >= 120 and dia < 80:
            return {"label": "Elevated", "color": "#F59E0B", "message": "Blood pressure is slightly elevated. Focus on healthy lifestyle habits."}
        else:
            return {"label": "Normal", "color": "#10B981", "message": "Blood pressure is in the healthy range. Keep up the good work!"}


blood_pressure_service = BloodPressureService()

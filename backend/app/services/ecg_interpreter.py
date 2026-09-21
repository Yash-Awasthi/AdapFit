"""
ECG interpretation from measured R-R intervals.

This service used to pick a rhythm at random and report it with a confidence
between 0.85 and 0.99 — one roll in five returned "Atrial Fibrillation" and
told the user to see a cardiologist within 24 hours. It now derives what R-R
intervals actually support and refuses when they are missing.

What the intervals support: heart rate, rate-based classification
(bradycardia / normal / tachycardia), and whether the rhythm is regular.
What they do not support is a named arrhythmia — that is a clinical diagnosis
from a full tracing, so an irregular rhythm is reported as irregular, with the
advice to have it looked at, and never labelled.
"""

import statistics
import time
from typing import Any, Dict, List, Optional

from app.services.hrv_analysis import HRVAnalyzer

# Below this many beats the regularity statistics are noise.
MIN_INTERVALS = 10

# Coefficient of variation of R-R above which a rhythm reads as irregular.
# Normal sinus rhythm with respiratory variation sits well under this.
IRREGULAR_CV = 0.12


class ECGInterpreterService:
    """AI-powered ECG interpretation and arrhythmia detection."""

    def __init__(self):
        self.readings: Dict[str, List] = {}

    @staticmethod
    def _intervals(ecg_data: Dict[str, Any]) -> List[float]:
        raw = ecg_data.get("rr_intervals_ms") or ecg_data.get("rr_intervals") or []
        out: List[float] = []
        for value in raw:
            try:
                out.append(float(value))
            except (TypeError, ValueError):
                continue
        return out

    def interpret_ecg(self, user_id: str, ecg_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpret a recording from its R-R intervals.

        Returns an "inconclusive" reading rather than a classification when
        there is not enough signal, which is also what a real single-lead ECG
        does with a poor trace.
        """
        rr = self._intervals(ecg_data)
        if len(rr) < MIN_INTERVALS:
            return {
                "status": "inconclusive",
                "reason": "insufficient_data",
                "needs": f"at least {MIN_INTERVALS} R-R intervals in rr_intervals_ms",
                "received_intervals": len(rr),
                "message": (
                    "Not enough beats to interpret. Record a longer sample from a device "
                    "that reports R-R intervals."
                ),
            }

        report = HRVAnalyzer.analyze(rr)
        if report is None:
            return {
                "status": "inconclusive",
                "reason": "unusable_signal",
                "message": "The intervals could not be analysed — the recording is too noisy.",
            }

        clean = HRVAnalyzer.compute_rri(rr)
        mean_rr = statistics.fmean(clean)
        bpm = round(60000.0 / mean_rr)
        cv = statistics.pstdev(clean) / mean_rr if mean_rr else 0.0
        regular = cv < IRREGULAR_CV

        if not regular:
            classification = "Irregular rhythm"
            description = "The beat-to-beat intervals vary more than a regular rhythm does."
            risk_level = "attention"
            action = (
                "An irregular rhythm has several possible causes and this recording cannot "
                "tell them apart. Show it to a clinician, and seek urgent care if you have "
                "chest pain, fainting or breathlessness."
            )
        elif bpm < 60:
            classification = "Regular rhythm, slow rate"
            description = f"Regular rhythm at {bpm} bpm, below the usual resting range."
            risk_level = "low"
            action = (
                "A low resting rate is common in trained people. Mention it to a clinician "
                "if it comes with dizziness or fatigue."
            )
        elif bpm > 100:
            classification = "Regular rhythm, fast rate"
            description = f"Regular rhythm at {bpm} bpm, above the usual resting range."
            risk_level = "moderate"
            action = (
                "A fast rate is expected after exertion, caffeine or stress. If it persists "
                "at rest, have it checked."
            )
        else:
            classification = "Regular rhythm, normal rate"
            description = f"Regular rhythm at {bpm} bpm."
            risk_level = "low"
            action = "Nothing in this recording needs action."

        reading = {
            "reading_id": f"ecg_{user_id}_{int(time.time())}",
            "user_id": user_id,
            "status": "analyzed",
            "timestamp": time.time(),
            "duration_seconds": round(sum(clean) / 1000.0, 1),
            "classification": classification,
            "heart_rate_bpm": bpm,
            "rhythm": "regular" if regular else "irregular",
            "rr_variation_pct": round(cv * 100, 1),
            "rmssd_ms": round(report.time_domain.rmssd, 1),
            "sdnn_ms": round(report.time_domain.sdnn, 1),
            "signal_quality": round(report.quality_score, 1),
            "interval_count": len(clean),
            "risk_level": risk_level,
            "description": description,
            "action": action,
            # Stated on every reading: the values above are measurements, and a
            # measurement is not a diagnosis.
            "disclaimer": (
                "Derived from R-R intervals only. This is not a diagnosis and does not "
                "identify specific arrhythmias."
            ),
        }

        self.readings.setdefault(user_id, []).append(reading)
        return reading

    def get_ecg_history(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Analysed recordings, most recent last. Inconclusive ones are not stored."""
        readings = self.readings.get(user_id, [])[-limit:]
        return [
            {
                "reading_id": r["reading_id"],
                "timestamp": r["timestamp"],
                "classification": r["classification"],
                "heart_rate_bpm": r["heart_rate_bpm"],
                "rhythm": r["rhythm"],
                "rr_variation_pct": r["rr_variation_pct"],
                "signal_quality": r["signal_quality"],
                "risk_level": r["risk_level"],
            }
            for r in readings
        ]

    def get_irregularity_summary(self, user_id: str) -> Dict[str, Any]:
        """
        How often recordings came back irregular.

        Counts what was measured. It deliberately does not name a condition or
        score a risk: that needs a clinical assessment, not a tally.
        """
        readings = [r for r in self.readings.get(user_id, []) if r.get("status") == "analyzed"]
        irregular_count = sum(1 for r in readings if r.get("rhythm") == "irregular")
        total = len(readings)
        if total == 0:
            return {
                "status": "no_data",
                "message": "No analysed recordings yet.",
                "total_readings": 0,
            }

        return {
            "status": "ok",
            "irregular_readings": irregular_count,
            "total_readings": total,
            "irregular_frequency_pct": round(irregular_count / total * 100, 1),
            "recommendation": (
                "Recordings have come back irregular more than once. Show them to a clinician."
                if irregular_count > 1 else
                "One recording came back irregular. Keep recording and mention it at your next appointment."
                if irregular_count == 1 else
                "Every recording so far has been regular."
            ),
            "lifestyle_tips": ["Limit alcohol", "Exercise regularly", "Manage blood pressure", "Treat sleep apnea"],
            "disclaimer": "A count of irregular recordings, not a diagnosis or a risk score.",
        }

    def get_heart_rate_variability(self, user_id: str) -> Dict[str, Any]:
        """RMSSD across this user's analysed recordings, and how it is moving."""
        values = [
            r["rmssd_ms"] for r in self.readings.get(user_id, [])
            if r.get("status") == "analyzed" and r.get("rmssd_ms") is not None
        ]
        if len(values) < 5:
            return {
                "status": "insufficient_data",
                "readings_available": len(values),
                "message": "Need at least 5 analysed recordings for an HRV picture.",
            }

        hrv = statistics.fmean(values[-5:])
        trend = self._trend(values)
        return {
            "status": "ok",
            "hrv_ms": round(hrv, 1),
            "readings_used": len(values),
            "level": "excellent" if hrv > 60 else "good" if hrv > 40 else "fair" if hrv > 25 else "low",
            "interpretation": (
                "RMSSD is in the higher part of the usual range for this measure."
                if hrv > 50 else
                "RMSSD is in the lower part of the usual range. It moves with sleep, stress and illness."
            ),
            "trend": trend,
            "training_recommendation": (
                "Nothing here argues against a hard session."
                if hrv > 50 else
                "Consider keeping intensity down until this recovers."
            ),
            "disclaimer": "RMSSD varies widely between people; compare it with your own history, not a target.",
        }

    @staticmethod
    def _trend(values: List[float]) -> str:
        """Direction of the recent values against the ones before them."""
        if len(values) < 6:
            return "not_enough_history"
        recent = statistics.fmean(values[-3:])
        earlier = statistics.fmean(values[-6:-3])
        if earlier == 0:
            return "not_enough_history"
        change = (recent - earlier) / earlier
        if change > 0.05:
            return "improving"
        if change < -0.05:
            return "declining"
        return "stable"


ecg_interpreter_service = ECGInterpreterService()

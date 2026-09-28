"""
Sleep audio scoring from events the recorder detected.

Detection happens on the device that has the microphone; this service scores
what it reports. It used to generate the events instead — a random number of
snoring stretches, breathing pauses and gasps per night — which meant a night
could come back "high apnea risk, consult a sleep specialist", or clear
someone who does stop breathing, by chance.

The apnea risk scoring itself is unchanged: it was always real arithmetic over
the events, and it now runs on events that happened.
"""

import time
from typing import Any, Dict, List, Optional


EVENT_KEYS = ("snoring_events", "breathing_pauses", "talking_events", "noise_events")


def _events(audio_data: Dict[str, Any], key: str) -> List[Dict]:
    value = audio_data.get(key)
    return [e for e in value if isinstance(e, dict)] if isinstance(value, list) else []


class SleepAudioAnalyzerService:
    """Analyze sleep audio for health insights."""

    EVENT_KEYS = EVENT_KEYS

    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self._init_apnea_risk_factors()

    def _init_apnea_risk_factors(self):
        self.apnea_risk_factors = {
            "snoring_frequency": {"weight": 3, "threshold": "frequent"},
            "breathing_pause_count": {"weight": 4, "threshold": "5+_per_hour"},
            "gasping_events": {"weight": 4, "threshold": "any"},
            "bmi_over_30": {"weight": 2, "threshold": "yes"},
            "neck_circumference": {"weight": 2, "threshold": ">17in_male_>16in_female"},
            "age_over_50": {"weight": 1, "threshold": "yes"},
            "male": {"weight": 1, "threshold": "yes"},
            "family_history": {"weight": 1, "threshold": "yes"},
        }

    def analyze_night_audio(self, user_id: str, audio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score one night from the events the recorder detected.

        `audio_data` carries `snoring_events`, `breathing_pauses`,
        `talking_events` and `noise_events`, each a list the device produced.
        An empty list means a quiet night; a missing key means the recorder
        did not report that category, which is not the same thing and is why
        the two are distinguished below.
        """
        total_sleep_min = audio_data.get("duration_minutes")
        if not isinstance(total_sleep_min, (int, float)) or total_sleep_min <= 0:
            return {
                "status": "insufficient_data",
                "message": "duration_minutes is needed to score a night.",
            }

        reported = [key for key in self.EVENT_KEYS if key in audio_data]
        if not reported:
            return {
                "status": "insufficient_data",
                "missing": list(self.EVENT_KEYS),
                "message": (
                    "No detected events were supplied. Record a night with the sleep "
                    "audio recorder, which detects these on the device."
                ),
            }

        session_id = f"sa_{user_id}_{int(time.time())}"
        snoring_events = _events(audio_data, "snoring_events")
        breathing_pauses = _events(audio_data, "breathing_pauses")
        talking_events = _events(audio_data, "talking_events")
        noise_events = _events(audio_data, "noise_events")

        # Calculate scores
        snoring_score = len(snoring_events) * 5
        breathing_events_per_hour = len(breathing_pauses) / (total_sleep_min / 60)
        if "breathing_pauses" in audio_data:
            apnea_risk = self._assess_apnea_risk(snoring_events, breathing_pauses, audio_data)
        else:
            # A phone recorder that cannot hear pauses must not report a low risk by their absence.
            apnea_risk = {
                "risk_level": "not_assessed",
                "risk_factors": [],
                "recommendation": ("This recording does not detect breathing pauses. Loud snoring most nights, "
                                   "someone seeing you stop breathing, or sleepiness in the day are worth "
                                   "raising with a doctor."),
            }

        sleep_quality = max(0, 100 - snoring_score - len(breathing_pauses) * 10 - len(noise_events) * 3)

        session = {
            "session_id": session_id,
            "user_id": user_id,
            "status": "scored",
            "categories_reported": reported,
            "date": audio_data.get("date", time.strftime("%Y-%m-%d")),
            "duration_minutes": total_sleep_min,
            "snoring": {
                "detected": len(snoring_events) > 0,
                "total_events": len(snoring_events),
                "total_duration_min": sum(e.get("duration_min", 0) for e in snoring_events),
                "severity": "none" if len(snoring_events) == 0 else "mild" if len(snoring_events) < 5 else "moderate" if len(snoring_events) < 15 else "severe",
                "events": snoring_events[:10],
            },
            "breathing": {
                "pauses_detected": len(breathing_pauses),
                "events_per_hour": round(breathing_events_per_hour, 1),
                "longest_pause_seconds": max((p.get("duration_seconds", 0) for p in breathing_pauses), default=0),
                "gasping_events": sum(1 for p in breathing_pauses if p.get("gasping", False)),
            },
            "talking": {
                "detected": len(talking_events) > 0,
                "events": talking_events[:5],
                "total_events": len(talking_events),
            },
            "environment": {
                # From the recorder's own level measurements, absent when it
                # reported none. A bedroom's noise floor is measured, not guessed.
                "avg_noise_db": audio_data.get("avg_noise_db"),
                "quietest_hour_db": audio_data.get("quietest_hour_db"),
                "noise_events": len(noise_events),
                "environment_score": max(0, 100 - len(noise_events) * 5),
            },
            "apnea_risk": apnea_risk,
            "sleep_quality_score": round(sleep_quality),
            "insights": self._generate_insights(snoring_events, breathing_pauses, talking_events, apnea_risk),
        }

        self.sessions[session_id] = session
        return session

    def get_snoring_trends(self, user_id: str) -> Dict[str, Any]:
        """Get snoring trends over time."""
        user_sessions = [s for s in self.sessions.values() if s["user_id"] == user_id]
        if not user_sessions:
            return {"message": "No sleep audio data yet"}

        recent = user_sessions[-7:] if len(user_sessions) > 7 else user_sessions
        avg_events = sum(s["snoring"]["total_events"] for s in recent) / len(recent)
        avg_quality = sum(s["sleep_quality_score"] for s in recent) / len(recent)

        return {
            "sessions_analyzed": len(recent),
            "avg_snoring_events": round(avg_events, 1),
            "avg_sleep_quality": round(avg_quality),
            "trend": "improving" if len(recent) > 1 and recent[-1]["snoring"]["total_events"] < recent[0]["snoring"]["total_events"] else "stable",
            "position_impact": "Sleeping on your side typically reduces snoring by 50%",
        }

    def get_snoring_remediation(self) -> List[Dict]:
        """Get snoring remediation strategies."""
        return [
            {"category": "Position", "tips": ["Sleep on your side", "Elevate head 4 inches", "Avoid sleeping on back"], "evidence": "strong"},
            {"category": "Lifestyle", "tips": ["Lose weight if overweight", "Avoid alcohol before bed", "Stop smoking", "Exercise regularly"], "evidence": "strong"},
            {"category": "Environment", "tips": ["Use humidifier", "Keep bedroom cool", "Use anti-snoring pillow"], "evidence": "moderate"},
            {"category": "Medical", "tips": ["Try nasal strips or dilators", "Treat nasal congestion", "Consider CPAP if severe", "See ENT specialist"], "evidence": "strong"},
        ]

    def _assess_apnea_risk(self, snoring: List, pauses: List, data: Dict) -> Dict[str, Any]:
        score = 0
        risk_factors = []

        if len(snoring) > 10:
            score += 3
            risk_factors.append("Frequent snoring")
        if len(pauses) > 5:
            score += 4
            risk_factors.append("Frequent breathing pauses")
        if any(p.get("gasping") for p in pauses):
            score += 3
            risk_factors.append("Gasping during sleep")
        if data.get("bmi", 25) > 30:
            score += 2
            risk_factors.append("BMI > 30")
        if data.get("age", 40) > 50:
            score += 1
            risk_factors.append("Age > 50")

        risk_level = "high" if score >= 7 else "moderate" if score >= 4 else "low"

        return {
            "risk_score": min(10, score),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendation": "Consult a sleep specialist for formal evaluation" if risk_level == "high" else "Monitor and consider home sleep study" if risk_level == "moderate" else "Low risk — continue healthy sleep habits",
        }

    def _generate_insights(self, snoring, pauses, talking, apnea_risk) -> List[str]:
        insights = []
        if snoring:
            minutes = sum(e.get("duration_min", 0) for e in snoring)
            insights.append(f"Snoring in {len(snoring)} stretches, about {round(minutes)} min in all. Side sleeping may help")
        if pauses:
            insights.append(f"{len(pauses)} breathing pauses detected")
        if apnea_risk["risk_level"] == "high":
            insights.append("⚠️ Elevated sleep apnea risk — consider medical consultation")
        if talking:
            insights.append(f"Sleep talking detected {len(talking)} times — usually harmless")
        if not insights:
            insights.append("Quiet night with minimal audio events")
        return insights


from app.core.durable import shared  # noqa: E402

sleep_audio_analyzer_service = shared("app.services.sleep_audio_analyzer.sleep_audio_analyzer_service", SleepAudioAnalyzerService())
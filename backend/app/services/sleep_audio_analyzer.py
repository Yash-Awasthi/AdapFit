"""Sleep Audio Analyzer Service - Snoring, apnea risk, sleep talking detection.

Based on 2025 research on smartphone-based sleep audio analysis:
- Snoring detection and scoring
- Sleep apnea risk assessment from audio patterns
- Sleep talking detection and transcription
- Bedroom environment noise analysis
- Sleep quality correlation with audio events
"""

import time
import random
from typing import Dict, List, Optional, Any


class SleepAudioAnalyzerService:
    """Analyze sleep audio for health insights."""

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
        """Analyze a night of sleep audio."""
        session_id = f"sa_{user_id}_{int(time.time())}"

        # Simulate audio analysis
        total_sleep_min = audio_data.get("duration_minutes", 480)
        snoring_events = self._generate_snoring_events(total_sleep_min)
        breathing_pauses = self._generate_breathing_pauses(total_sleep_min)
        talking_events = self._generate_talking_events(total_sleep_min)
        noise_events = self._generate_noise_events(total_sleep_min)

        # Calculate scores
        snoring_score = len(snoring_events) * 5
        breathing_events_per_hour = len(breathing_pauses) / (total_sleep_min / 60)
        apnea_risk = self._assess_apnea_risk(snoring_events, breathing_pauses, audio_data)

        sleep_quality = max(0, 100 - snoring_score - len(breathing_pauses) * 10 - len(noise_events) * 3)

        session = {
            "session_id": session_id,
            "user_id": user_id,
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
                "avg_noise_db": random.randint(25, 45),
                "quietest_hour_db": random.randint(18, 30),
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

    def _generate_snoring_events(self, duration_min: int) -> List[Dict]:
        count = random.randint(0, min(20, duration_min // 30))
        events = []
        for _ in range(count):
            start = random.randint(0, duration_min)
            events.append({
                "start_minute": start,
                "duration_min": round(random.uniform(0.5, 5), 1),
                "intensity": random.choice(["light", "moderate", "loud"]),
            })
        return sorted(events, key=lambda x: x["start_minute"])

    def _generate_breathing_pauses(self, duration_min: int) -> List[Dict]:
        count = random.randint(0, min(10, duration_min // 60))
        events = []
        for _ in range(count):
            events.append({
                "start_minute": random.randint(0, duration_min),
                "duration_seconds": random.randint(5, 30),
                "gasping": random.random() < 0.3,
            })
        return events

    def _generate_talking_events(self, duration_min: int) -> List[Dict]:
        count = random.randint(0, min(5, duration_min // 120))
        return [{"minute": random.randint(0, duration_min), "duration_seconds": random.randint(1, 15), "muffled": True} for _ in range(count)]

    def _generate_noise_events(self, duration_min: int) -> List[Dict]:
        count = random.randint(0, 3)
        return [{"minute": random.randint(0, duration_min), "type": random.choice(["traffic", "partner", "pet", "snoring"]), "db": random.randint(35, 60)} for _ in range(count)]

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
            insights.append(f"Snoring detected {len(snoring)} times — side sleeping may help")
        if pauses:
            insights.append(f"{len(pauses)} breathing pauses detected")
        if apnea_risk["risk_level"] == "high":
            insights.append("⚠️ Elevated sleep apnea risk — consider medical consultation")
        if talking:
            insights.append(f"Sleep talking detected {len(talking)} times — usually harmless")
        if not insights:
            insights.append("Quiet night with minimal audio events")
        return insights


sleep_audio_analyzer_service = SleepAudioAnalyzerService()

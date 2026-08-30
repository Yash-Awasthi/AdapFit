"""
Athlete performance monitoring from monitoring-athletes-performance.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import math


@dataclass
class PerformanceMetrics:
    heart_rate_avg: float = 0.0
    heart_rate_max: float = 0.0
    speed_avg: float = 0.0
    distance_km: float = 0.0
    elevation_gain: float = 0.0
    cadence: float = 0.0
    power: float = 0.0
    vo2_max: float = 0.0
    training_load: float = 0.0
    recovery_score: float = 100.0


@dataclass
class TrainingSession:
    date: str
    duration_minutes: float
    sport: str
    metrics: PerformanceMetrics
    notes: str = ""


@dataclass
class AthleteProfile:
    name: str
    age: int
    weight_kg: float
    max_heart_rate: int = 220
    sessions: List[TrainingSession] = field(default_factory=list)

    @property
    def resting_hr(self) -> float:
        hrs = [s.metrics.heart_rate_avg for s in self.sessions if s.metrics.heart_rate_avg > 0]
        return min(hrs) if hrs else 60.0


def compute_training_stress_score(session: TrainingSession, max_hr: int) -> float:
    if session.metrics.heart_rate_max <= 0 or max_hr <= 0:
        return 0.0
    intensity = session.metrics.heart_rate_avg / max_hr
    return session.duration_minutes * intensity * 1.0


def compute_acwr(sessions: List[TrainingSession], max_hr: int) -> float:
    if len(sessions) < 7:
        return 1.0
    recent_loads = [compute_training_stress_score(s, max_hr) for s in sessions[-7:]]
    chronic_loads = [compute_training_stress_score(s, max_hr) for s in sessions[-28:]]
    acute = sum(recent_loads) / max(1, len(recent_loads))
    chronic = sum(chronic_loads) / max(1, len(chronic_loads))
    return acute / chronic if chronic > 0 else 1.0


def detect_overtraining(athlete: AthleteProfile) -> Dict[str, any]:
    acwr = compute_acwr(athlete.sessions, athlete.max_heart_rate)
    issues = []
    if acwr > 1.5:
        issues.append("ACWR > 1.5 — high injury risk")
    if len(athlete.sessions) >= 2:
        hr_trend = athlete.sessions[-1].metrics.heart_rate_avg - athlete.sessions[-2].metrics.heart_rate_avg
        if hr_trend > 10:
            issues.append("Resting HR trending up — fatigue detected")
    total_volume = sum(s.duration_minutes for s in athlete.sessions[-7:])
    if total_volume > 600:
        issues.append(f"Weekly volume {total_volume:.0f} min — consider recovery week")
    return {"acwr": acwr, "issues": issues, "risk_level": "high" if len(issues) >= 2 else "moderate" if issues else "low"}


def generate_weekly_plan(athlete: AthleteProfile) -> List[Dict]:
    acwr = compute_acwr(athlete.sessions, athlete.max_heart_rate)
    plan = []
    if acwr > 1.3:
        plan = [{"day": "Mon", "type": "rest"}, {"day": "Tue", "type": "easy", "duration": 30},
                {"day": "Wed", "type": "rest"}, {"day": "Thu", "type": "easy", "duration": 30},
                {"day": "Fri", "type": "rest"}, {"day": "Sat", "type": "moderate", "duration": 45},
                {"day": "Sun", "type": "rest"}]
    else:
        plan = [{"day": "Mon", "type": "easy", "duration": 40}, {"day": "Tue", "type": "tempo", "duration": 35},
                {"day": "Wed", "type": "rest"}, {"day": "Thu", "type": "intervals", "duration": 45},
                {"day": "Fri", "type": "easy", "duration": 30}, {"day": "Sat", "type": "long", "duration": 90},
                {"day": "Sun", "type": "rest"}]
    return plan

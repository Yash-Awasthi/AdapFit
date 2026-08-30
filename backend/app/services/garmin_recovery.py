"""
Garmin recovery insights — sleep, stress, HRV analysis.

Extracted from garmin-recovery-insights-agent — research-backed recovery patterns.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict
import math


class RecoveryStatus(Enum):
    OPTIMAL = "optimal"
    GOOD = "good"
    MODERATE = "moderate"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class SleepData:
    deep_minutes: float = 0.0
    light_minutes: float = 0.0
    rem_minutes: float = 0.0
    awake_minutes: float = 0.0
    total_minutes: float = 0.0
    sleep_score: float = 0.0
    sleep_start: str = ""
    sleep_end: str = ""

    @property
    def deep_pct(self) -> float:
        return self.deep_minutes / max(1, self.total_minutes)

    @property
    def rem_pct(self) -> float:
        return self.rem_minutes / max(1, self.total_minutes)


@dataclass
class StressData:
    overall_stress: float = 0.0  # 0-100
    rest_stress: float = 0.0
    medium_stress: float = 0.0
    high_stress: float = 0.0
    stress_resilience: float = 0.0


@dataclass
class HRVData:
    hrv_status: float = 0.0  # 0-100
    last_night: float = 0.0
    baseline: float = 0.0
    seven_day_avg: float = 0.0
    thirty_day_avg: float = 0.0


@dataclass
class BodyBattery:
    current: float = 0.0  # 0-100
    high: float = 0.0
    low: float = 0.0
    charged: float = 0.0
    drained: float = 0.0


@dataclass
class RecoveryInsight:
    status: RecoveryStatus
    score: float  # 0-100
    summary: str
    recommendations: List[str]
    domain_scores: Dict[str, float]


def analyze_sleep(sleep: SleepData) -> Dict[str, float]:
    """Analyze sleep quality against research-backed norms."""
    scores = {}

    # Deep sleep: 15-20% of total is ideal (adults)
    deep_target = 0.17
    scores["deep"] = max(0, 100 - abs(sleep.deep_pct - deep_target) * 500)

    # REM sleep: 20-25% is ideal
    rem_target = 0.22
    scores["rem"] = max(0, 100 - abs(sleep.rem_pct - rem_target) * 400)

    # Total sleep: 7-9 hours is ideal
    hours = sleep.total_minutes / 60
    if 7 <= hours <= 9:
        scores["duration"] = 100
    elif 6 <= hours < 7:
        scores["duration"] = 70
    elif hours > 9:
        scores["duration"] = 80
    else:
        scores["duration"] = max(0, hours / 6 * 100)

    # Sleep efficiency (less awake time = better)
    awake_pct = sleep.awake_minutes / max(1, sleep.total_minutes)
    scores["efficiency"] = max(0, 100 - awake_pct * 200)

    return scores


def analyze_stress(stress: StressData) -> Dict[str, float]:
    """Analyze stress patterns."""
    scores = {}

    # Overall stress: lower is better
    scores["overall"] = max(0, 100 - stress.overall_stress)

    # Resilience: higher is better
    scores["resilience"] = stress.stress_resilience

    # High stress ratio
    total = stress.rest_stress + stress.medium_stress + stress.high_stress
    if total > 0:
        high_ratio = stress.high_stress / total
        scores["high_stress_ratio"] = max(0, 100 - high_ratio * 200)
    else:
        scores["high_stress_ratio"] = 100.0

    return scores


def analyze_hrv(hrv: HRVData) -> Dict[str, float]:
    """Analyze HRV trends."""
    scores = {}

    # HRV status from device
    scores["status"] = hrv.hrv_status

    # Trend: compare 7-day vs 30-day average
    if hrv.thirty_day_avg > 0:
        trend = (hrv.seven_day_avg - hrv.thirty_day_avg) / hrv.thirty_day_avg
        scores["trend"] = max(0, min(100, 50 + trend * 500))
    else:
        scores["trend"] = 50.0

    return scores


def analyze_body_battery(bb: BodyBattery) -> Dict[str, float]:
    """Analyze body battery levels."""
    scores = {}

    scores["current"] = bb.current

    # Recovery rate (how much it charged during sleep)
    if bb.charged > 0:
        scores["recovery_rate"] = min(100, bb.charged)
    else:
        scores["recovery_rate"] = 50.0

    return scores


def generate_recovery_insight(
    sleep: Optional[SleepData] = None,
    stress: Optional[StressData] = None,
    hrv: Optional[HRVData] = None,
    body_battery: Optional[BodyBattery] = None,
) -> RecoveryInsight:
    """Generate comprehensive recovery insight from all data sources."""
    domain_scores = {}
    all_recommendations = []

    if sleep:
        sleep_scores = analyze_sleep(sleep)
        domain_scores["sleep"] = sum(sleep_scores.values()) / len(sleep_scores)

        if sleep_scores["deep"] < 60:
            all_recommendations.append("Improve deep sleep: reduce caffeine after 2pm, keep room cool (65-68°F)")
        if sleep_scores["rem"] < 60:
            all_recommendations.append("Improve REM sleep: maintain consistent sleep schedule, avoid alcohol before bed")
        if sleep_scores["duration"] < 70:
            all_recommendations.append("Aim for 7-9 hours of sleep per night")

    if stress:
        stress_scores = analyze_stress(stress)
        domain_scores["stress"] = sum(stress_scores.values()) / len(stress_scores)

        if stress_scores["overall"] < 50:
            all_recommendations.append("High stress detected: try 5-minute breathing exercises or short walk")
        if stress_scores["resilience"] < 40:
            all_recommendations.append("Low stress resilience: prioritize recovery activities today")

    if hrv:
        hrv_scores = analyze_hrv(hrv)
        domain_scores["hrv"] = sum(hrv_scores.values()) / len(hrv_scores)

        if hrv_scores["trend"] < 40:
            all_recommendations.append("HRV trending down: consider lighter training today")

    if body_battery:
        bb_scores = analyze_body_battery(body_battery)
        domain_scores["body_battery"] = sum(bb_scores.values()) / len(bb_scores)

        if bb_scores["current"] < 30:
            all_recommendations.append("Low body battery: prioritize rest and avoid strenuous activity")
        elif bb_scores["current"] > 70:
            all_recommendations.append("Good energy: ideal time for high-intensity training")

    if not domain_scores:
        return RecoveryInsight(
            status=RecoveryStatus.MODERATE,
            score=50.0,
            summary="Insufficient data for detailed analysis",
            recommendations=["Connect your Garmin device for personalized insights"],
            domain_scores={},
        )

    overall_score = sum(domain_scores.values()) / len(domain_scores)

    if overall_score >= 80:
        status = RecoveryStatus.OPTIMAL
        summary = "Excellent recovery — you're ready for peak performance"
    elif overall_score >= 65:
        status = RecoveryStatus.GOOD
        summary = "Good recovery — ready for moderate to high intensity training"
    elif overall_score >= 50:
        status = RecoveryStatus.MODERATE
        summary = "Moderate recovery — consider lighter training or active recovery"
    elif overall_score >= 35:
        status = RecoveryStatus.POOR
        summary = "Poor recovery — prioritize rest and recovery activities"
    else:
        status = RecoveryStatus.CRITICAL
        summary = "Critical recovery status — rest is strongly recommended"

    if not all_recommendations:
        all_recommendations.append("Maintain current recovery habits — they're working well")

    return RecoveryInsight(
        status=status,
        score=round(overall_score, 1),
        summary=summary,
        recommendations=all_recommendations,
        domain_scores=domain_scores,
    )

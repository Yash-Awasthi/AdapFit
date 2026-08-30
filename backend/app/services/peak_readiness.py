"""Peak readiness score — deterministic 0-100 readiness from recovery metrics.

Extracted from inspiration/ZFIT/peakready.
Pattern: pure function, color zones, daily check-in with sleep hours, workout intensity,
muscle soreness, deterministic score calculation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ReadinessZone(Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


@dataclass(frozen=True)
class RecoveryInput:
    """Daily recovery check-in input."""
    sleep_hours: float          # 0-24
    workout_intensity: int      # 1-10 (RPE)
    muscle_soreness: int         # 1-10
    resting_hr: int | None = None  # optional: resting heart rate
    hrv_ms: float | None = None    # optional: HRV in ms
    stress_level: int | None = None  # optional: 1-10 subjective


@dataclass(frozen=True)
class ReadinessScore:
    score: int  # 0-100
    zone: ReadinessZone
    insight: str
    sleep_component: float
    workout_component: float
    soreness_component: float
    hr_component: float
    hrv_component: float


def _sleep_score(hours: float) -> float:
    """Sleep contribution 0-100."""
    if hours < 4: return 10
    if hours < 5: return 30
    if hours < 6: return 50
    if hours < 7: return 70
    if hours <= 9: return 100
    if hours <= 10: return 90
    if hours <= 11: return 70
    return 50  # oversleeping


def _workout_intensity_score(intensity: int) -> float:
    """Lower intensity yesterday = higher readiness today."""
    if intensity <= 2: return 100
    if intensity <= 4: return 90
    if intensity <= 6: return 70
    if intensity <= 8: return 50
    return 30


def _soreness_score(soreness: int) -> float:
    """Lower soreness = higher readiness."""
    if soreness <= 1: return 100
    if soreness <= 3: return 80
    if soreness <= 5: return 60
    if soreness <= 7: return 40
    return 20


def _hr_deviation_score(resting_hr: int | None, baseline_hr: int = 60) -> float:
    """Score based on HR deviation from baseline."""
    if resting_hr is None: return 70  # neutral if unknown
    delta = abs(resting_hr - baseline_hr)
    if delta == 0: return 100
    if delta <= 2: return 90
    if delta <= 5: return 70
    if delta <= 10: return 50
    return 30


def _hrv_score(hrv_ms: float | None, baseline_hrv: float = 50.0) -> float:
    """Score based on HRV relative to baseline."""
    if hrv_ms is None: return 70
    pct = hrv_ms / baseline_hrv if baseline_hrv > 0 else 1.0
    if pct >= 1.0: return 100
    if pct >= 0.9: return 85
    if pct >= 0.8: return 65
    if pct >= 0.7: return 45
    return 25


def calculate_readiness(data: RecoveryInput) -> ReadinessScore:
    """Calculate deterministic 0-100 readiness score.

    Weighted: sleep 35%, soreness 25%, workout intensity 20%, HR 10%, HRV 10%.
    """
    sleep_s = _sleep_score(data.sleep_hours)
    workout_s = _workout_intensity_score(data.workout_intensity)
    soreness_s = _soreness_score(data.muscle_soreness)
    hr_s = _hr_deviation_score(data.resting_hr)
    hrv_s = _hrv_score(data.hrv_ms)

    total = (
        sleep_s * 0.35 +
        soreness_s * 0.25 +
        workout_s * 0.20 +
        hr_s * 0.10 +
        hrv_s * 0.10
    )
    score = max(0, min(100, int(total)))

    if score >= 75:
        zone = ReadinessZone.GREEN
        insight = "Ready to train hard. Go for it."
    elif score >= 50:
        zone = ReadinessZone.YELLOW
        insight = "Moderate recovery. Light to moderate training recommended."
    else:
        zone = ReadinessZone.RED
        insight = "Low readiness. Focus on recovery — rest or very light activity."

    return ReadinessScore(
        score=score,
        zone=zone,
        insight=insight,
        sleep_component=sleep_s,
        workout_component=workout_s,
        soreness_component=soreness_s,
        hr_component=hr_s,
        hrv_component=hrv_s,
    )

"""Fatigue impairment prediction — bio-mathematical models of fatigue.

Extracted from inspiration/ZFIT/fips.
Pattern: sleep/actigraphy → FIPS data frame → bio-mathematical model → fatigue score.
Implements simplified versions of the Unified Model and Three-Process Model.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class SleepPeriod:
    """A sleep period from actigraphy or self-report."""
    start: datetime
    end: datetime
    quality: float = 1.0  # 0.0-1.0


@dataclass
class FIPSDataFrame:
    """FIPS-format sleep/wake data for BMM simulation."""
    timestamps: list[datetime]
    sleep_state: list[int]  # 0=awake, 1=sleep
    hour_of_day: list[float]  # 0-24


def sleep_periods_to_fips(periods: list[SleepPeriod], start: datetime, end: datetime, interval_min: int = 30) -> FIPSDataFrame:
    """Convert sleep periods to FIPS-format time series."""
    timestamps = []
    sleep_state = []
    hour_of_day = []

    current = start
    while current < end:
        is_sleeping = False
        for p in periods:
            if p.start <= current < p.end:
                is_sleeping = True
                break
        timestamps.append(current)
        sleep_state.append(1 if is_sleeping else 0)
        hour_of_day.append(current.hour + current.minute / 60)
        current += timedelta(minutes=interval_min)

    return FIPSDataFrame(timestamps, sleep_state, hour_of_day)


def circadian_phase(hour: float, chronotype_offset: float = 0) -> float:
    """Circadian phase using a sinusoidal model.

    Peak drive for wakefulness ~2 hours after habitual wake time.
    Trough (sleep drive) ~2 hours before habitual bedtime.
    """
    # Phase relative to midnight
    phase = 2 * math.pi * (hour - 6 - chronotype_offset) / 24
    # Higher = more alertness, lower = more sleep pressure
    return math.sin(phase)


def sleep_homeostat(sleep_state: list[int], decay_rate: float = 0.1, buildup_rate: float = 0.05) -> list[float]:
    """Process S (sleep homeostat) — sleep pressure builds during wake, decays during sleep."""
    pressure = 0.0
    pressures = []
    for state in sleep_state:
        if state == 0:  # awake
            pressure += buildup_rate
        else:  # sleeping
            pressure *= (1 - decay_rate)
        pressure = max(0, min(1, pressure))
        pressures.append(pressure)
    return pressures


def unified_model(fips: FIPSDataFrame, chronotype_offset: float = 0) -> list[float]:
    """Simplified Unified Model of fatigue.

    Fatigue = SleepHomeostat - CircadianAlertness
    Higher = more fatigued
    """
    homeostat = sleep_homeostat(fips.sleep_state)
    fatigue = []
    for i in range(len(fips.timestamps)):
        circadian = circadian_phase(fips.hour_of_day[i], chronotype_offset)
        # Fatigue = homeostatic pressure - circadian alertness
        f = homeostat[i] - (circadian + 1) / 2 * 0.5
        fatigue.append(max(0, min(1, f)))
    return fatigue


def three_process_model(fips: FIPSDataFrame, chronotype_offset: float = 0) -> list[float]:
    """Simplified Three-Process Model.

    Process S: homeostatic sleep pressure
    Process C: circadian rhythm
    Process W: sleep inertia (decays after waking)
    """
    homeostat = sleep_homeostat(fips.sleep_state)
    sleep_inertia = 0.0
    fatigue = []

    for i in range(len(fips.timestamps)):
        # Sleep inertia: spike on waking, decays over ~30 min
        if i > 0 and fips.sleep_state[i] == 0 and fips.sleep_state[i-1] == 1:
            sleep_inertia = 0.3  # wake inertia spike
        sleep_inertia *= 0.95  # decay

        circadian = circadian_phase(fips.hour_of_day[i], chronotype_offset)

        # Total fatigue = S + inertia - C
        f = homeostat[i] + sleep_inertia - (circadian + 1) / 2 * 0.4
        fatigue.append(max(0, min(1, f)))

    return fatigue


@dataclass(frozen=True)
class FatigueAssessment:
    timestamp: datetime
    fatigue_score: float  # 0-1
    risk_level: str  # "low", "moderate", "high", "severe"
    recommendation: str


def assess_fatigue(fatigue_scores: list[float], timestamps: list[datetime]) -> list[FatigueAssessment]:
    """Convert fatigue scores to risk assessments."""
    assessments = []
    for i, score in enumerate(fatigue_scores):
        if score < 0.3:
            risk = "low"
            rec = "Well rested. Normal activity."
        elif score < 0.5:
            risk = "moderate"
            rec = "Some fatigue. Consider lighter tasks."
        elif score < 0.7:
            risk = "high"
            rec = "Significant fatigue. Avoid high-risk activities."
        else:
            risk = "severe"
            rec = "Severe fatigue. Rest required. Do not operate machinery."

        assessments.append(FatigueAssessment(
            timestamp=timestamps[i],
            fatigue_score=round(score, 2),
            risk_level=risk,
            recommendation=rec,
        ))
    return assessments

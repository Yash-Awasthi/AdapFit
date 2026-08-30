"""Smart alarm — wake during light sleep within a time window.

Extracted from inspiration/ZFIT/smartalarm and inspiration/ZFIT/wakeiq.
Pattern: sleep stage detection from accelerometer/HR, find optimal wake moment
in a pre-alarm window (e.g. 30 min before target time), wake during light sleep
to reduce sleep inertia.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import IntEnum


class SleepStage(IntEnum):
    AWAKE = 0
    LIGHT = 1    # N1, N2
    DEEP = 2     # N3
    REM = 3


@dataclass(frozen=True)
class SleepSample:
    timestamp: datetime
    stage: SleepStage
    heart_rate: int | None = None
    movement: float | None = None  # acceleration magnitude


@dataclass(frozen=True)
class SmartAlarmResult:
    should_wake: bool
    wake_time: datetime | None
    target_time: datetime
    window_start: datetime
    window_end: datetime
    current_stage: SleepStage
    reason: str


def detect_sleep_stage_from_sensors(
    movement: float,
    heart_rate: int | None,
    prev_stage: SleepStage = SleepStage.LIGHT,
) -> SleepStage:
    """Heuristic sleep stage detection from accelerometer and HR."""
    # High movement = awake
    if movement > 0.5:
        return SleepStage.AWAKE

    # Low HR + very low movement = deep sleep
    if heart_rate is not None:
        if heart_rate < 55 and movement < 0.05:
            return SleepStage.DEEP
        if heart_rate > 70 and movement < 0.1:
            return SleepStage.REM
        if movement < 0.15:
            return SleepStage.LIGHT

    # Default based on movement
    if movement < 0.05:
        return SleepStage.DEEP
    elif movement < 0.15:
        return SleepStage.LIGHT
    elif movement < 0.3:
        return SleepStage.REM
    return SleepStage.AWAKE


def find_optimal_wake_time(
    samples: list[SleepSample],
    target_time: datetime,
    window_minutes: int = 30,
) -> SmartAlarmResult:
    """Find the optimal wake time within the pre-alarm window.

    Strategy: within the window (target - window_minutes, target),
    find the moment of lightest sleep. If none found, wake at target.

    Priority: AWAKE > LIGHT > REM > DEEP
    """
    window_start = target_time - timedelta(minutes=window_minutes)
    window_end = target_time

    # Filter samples within the window
    window_samples = [
        s for s in samples
        if window_start <= s.timestamp <= window_end
    ]

    if not window_samples:
        return SmartAlarmResult(
            should_wake=False,
            wake_time=None,
            target_time=target_time,
            window_start=window_start,
            window_end=window_end,
            current_stage=SleepStage.LIGHT,
            reason="No sleep data in window",
        )

    # Find best wake moment (lowest stage value = lightest)
    best = min(window_samples, key=lambda s: s.stage)

    # If we found a LIGHT or AWAKE moment, wake now-ish
    if best.stage <= SleepStage.LIGHT:
        return SmartAlarmResult(
            should_wake=True,
            wake_time=best.timestamp,
            target_time=target_time,
            window_start=window_start,
            window_end=window_end,
            current_stage=best.stage,
            reason=f"Light sleep detected at {best.timestamp.strftime('%H:%M')}",
        )

    # Check if current time is near target and stage is REM (acceptable)
    latest = window_samples[-1]
    if latest.timestamp >= target_time - timedelta(minutes=5):
        if latest.stage <= SleepStage.REM:
            return SmartAlarmResult(
                should_wake=True,
                wake_time=target_time,
                target_time=target_time,
                window_start=window_start,
                window_end=window_end,
                current_stage=latest.stage,
                reason="Target time reached, REM stage (acceptable)",
            )

    # Still in deep sleep, wait
    return SmartAlarmResult(
        should_wake=False,
        wake_time=None,
        target_time=target_time,
        window_start=window_start,
        window_end=window_end,
        current_stage=latest.stage,
        reason="Still in deep sleep, waiting for lighter stage",
    )


def calculate_sleep_inertia_risk(wake_stage: SleepStage) -> tuple[str, str]:
    """Estimate sleep inertia risk based on the stage woken from.

    Returns (risk_level, advice).
    """
    if wake_stage == SleepStage.AWAKE:
        return ("none", "Already awake — no inertia risk.")
    elif wake_stage == SleepStage.LIGHT:
        return ("low", "Waking from light sleep — minimal inertia expected.")
    elif wake_stage == SleepStage.REM:
        return ("moderate", "Waking from REM — some grogginess possible, fades quickly.")
    else:  # DEEP
        return ("high", "Waking from deep sleep — significant sleep inertia expected. "
                        "Allow 15-30 min before demanding tasks.")

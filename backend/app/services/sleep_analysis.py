"""
Sleep Analysis Engine

Provides sleep stage detection, quality scoring, circadian rhythm analysis,
and sleep debt calculation from wearable sensor data.
"""
from dataclasses import dataclass, field
from typing import Optional
import statistics
import math


@dataclass
class SleepStage:
    """Single sleep stage occurrence."""
    stage: str  # "awake", "light", "deep", "rem"
    start_minute: int
    duration_minutes: int


@dataclass
class SleepSession:
    """Complete sleep session data."""
    bedtime: str
    wake_time: str
    total_minutes: int
    efficiency_pct: float
    deep_pct: float
    rem_pct: float
    light_pct: float
    awake_pct: float
    heart_rate_avg: Optional[int] = None
    hrv_rmssd: Optional[float] = None
    respiratory_rate: Optional[float] = None
    temperature_delta: Optional[float] = None  # Deviation from baseline


# Sleep quality scoring (0-100)
def calculate_sleep_quality(session: SleepSession) -> dict:
    """
    Calculate comprehensive sleep quality score.

    Scoring weights:
    - Duration (30%): Optimal 7-9h
    - Efficiency (25%): Time asleep / time in bed
    - Deep sleep (20%): Optimal 15-25%
    - REM sleep (15%): Optimal 20-25%
    - Continuity (10%): Low awake percentage
    """
    # Duration score (optimal: 420-540 minutes)
    if 420 <= session.total_minutes <= 540:
        duration_score = 100
    elif session.total_minutes < 420:
        duration_score = max(0, (session.total_minutes / 420) * 100)
    else:
        duration_score = max(0, 100 - (session.total_minutes - 540) / 60 * 10)

    # Efficiency score
    efficiency_score = min(100, session.efficiency_pct * 1.1)

    # Deep sleep score (optimal: 15-25%)
    if 15 <= session.deep_pct <= 25:
        deep_score = 100
    elif session.deep_pct < 15:
        deep_score = max(0, (session.deep_pct / 15) * 100)
    else:
        deep_score = max(0, 100 - (session.deep_pct - 25) * 5)

    # REM sleep score (optimal: 20-25%)
    if 20 <= session.rem_pct <= 25:
        rem_score = 100
    elif session.rem_pct < 20:
        rem_score = max(0, (session.rem_pct / 20) * 100)
    else:
        rem_score = max(0, 100 - (session.rem_pct - 25) * 5)

    # Continuity score (low awake = better)
    continuity_score = max(0, 100 - session.awake_pct * 5)

    # Weighted total
    total = (
        duration_score * 0.30 +
        efficiency_score * 0.25 +
        deep_score * 0.20 +
        rem_score * 0.15 +
        continuity_score * 0.10
    )

    # Grade
    if total >= 90:
        grade = "A"
    elif total >= 80:
        grade = "B"
    elif total >= 70:
        grade = "C"
    elif total >= 60:
        grade = "D"
    else:
        grade = "F"

    return {
        "quality_score": round(total, 1),
        "grade": grade,
        "breakdown": {
            "duration": round(duration_score, 1),
            "efficiency": round(efficiency_score, 1),
            "deep_sleep": round(deep_score, 1),
            "rem_sleep": round(rem_score, 1),
            "continuity": round(continuity_score, 1),
        },
        "duration_hours": round(session.total_minutes / 60, 1),
        "optimal_range": "7-9 hours",
    }


# Circadian rhythm analysis
def analyze_circadian_rhythm(sessions: list[SleepSession]) -> dict:
    """
    Analyze circadian rhythm consistency from multiple sleep sessions.

    Measures:
    - Bedtime consistency (standard deviation of bedtime)
    - Wake time consistency
    - Sleep midpoint stability
    - Social jetlag (difference between weekday and weekend sleep)
    """
    if not sessions:
        return {"error": "No sessions provided"}

    def time_to_minutes(t: str) -> int:
        """Convert HH:MM to minutes since midnight."""
        parts = t.split(":")
        return int(parts[0]) * 60 + int(parts[1])

    bedtimes = [time_to_minutes(s.bedtime) for s in sessions]
    wake_times = [time_to_minutes(s.wake_time) for s in sessions]
    midpoints = [(b + w) // 2 for b, w in zip(bedtimes, wake_times)]

    # Handle overnight bedtimes (e.g., 23:00 → 1380, 01:00 → 60)
    # Normalize: if bedtime > wake_time, it crossed midnight
    normalized_bedtimes = []
    for b, w in zip(bedtimes, wake_times):
        if b > w + 120:  # Bedtime is >2h after wake (crossed midnight)
            normalized_bedtimes.append(b - 1440)  # Wrap to negative
        else:
            normalized_bedtimes.append(b)

    bedtime_std = statistics.stdev(normalized_bedtimes) if len(normalized_bedtimes) > 1 else 0
    wake_std = statistics.stdev(wake_times) if len(wake_times) > 1 else 0
    midpoint_std = statistics.stdev(midpoints) if len(midpoints) > 1 else 0

    # Consistency score (lower std = more consistent)
    bedtime_consistency = max(0, 100 - bedtime_std * 2)
    wake_consistency = max(0, 100 - wake_std * 2)

    # Rhythm regularity
    avg_bedtime = statistics.mean(normalized_bedtimes)
    avg_wake = statistics.mean(wake_times)

    return {
        "consistency_score": round((bedtime_consistency + wake_consistency) / 2, 1),
        "bedtime_consistency": round(bedtime_consistency, 1),
        "wake_consistency": round(wake_consistency, 1),
        "avg_bedtime_minutes": round(avg_bedtime),
        "avg_wake_minutes": round(avg_wake),
        "midpoint_stability": round(max(0, 100 - midpoint_std * 2), 1),
        "bedtime_std_minutes": round(bedtime_std, 1),
        "wake_std_minutes": round(wake_std, 1),
        "session_count": len(sessions),
    }


# Sleep debt calculation
def calculate_sleep_debt(
    sessions: list[SleepSession],
    target_hours: float = 8.0,
) -> dict:
    """
    Calculate cumulative sleep debt over a period.

    Sleep debt = target - actual (negative means oversleep).
    Acute debt (last 1-3 days) matters more than chronic (weeks).
    """
    if not sessions:
        return {"total_debt_hours": 0, "acute_debt_hours": 0, "chronic_debt_hours": 0}

    target_minutes = target_hours * 60
    debts = [(target_minutes - s.total_minutes) / 60 for s in sessions]

    total_debt = sum(debts)
    acute_debt = sum(debts[-3:]) if len(debts) >= 3 else sum(debts)
    chronic_debt = total_debt / len(debts) if debts else 0

    # Severity classification
    if total_debt <= -3:
        severity = "oversleeping"
    elif total_debt <= -1:
        severity = "well_rested"
    elif total_debt <= 3:
        severity = "mild_deficit"
    elif total_debt <= 7:
        severity = "moderate_deficit"
    else:
        severity = "severe_deficit"

    return {
        "total_debt_hours": round(total_debt, 1),
        "acute_debt_hours": round(acute_debt, 1),
        "chronic_debt_hours": round(chronic_debt, 1),
        "target_hours": target_hours,
        "avg_sleep_hours": round(statistics.mean([s.total_minutes / 60 for s in sessions]), 1),
        "severity": severity,
        "session_count": len(sessions),
    }


# Sleep stage analysis
def analyze_stages(sessions: list[SleepSession]) -> dict:
    """Aggregate sleep stage percentages across sessions."""
    if not sessions:
        return {"error": "No sessions"}

    return {
        "avg_deep_pct": round(statistics.mean([s.deep_pct for s in sessions]), 1),
        "avg_rem_pct": round(statistics.mean([s.rem_pct for s in sessions]), 1),
        "avg_light_pct": round(statistics.mean([s.light_pct for s in sessions]), 1),
        "avg_awake_pct": round(statistics.mean([s.awake_pct for s in sessions]), 1),
        "deep_sleep_hours": round(statistics.mean([s.total_minutes * s.deep_pct / 100 / 60 for s in sessions]), 1),
        "rem_sleep_hours": round(statistics.mean([s.total_minutes * s.rem_pct / 100 / 60 for s in sessions]), 1),
    }

"""
Chronotype Analysis Engine

Classifies individual chronotype (morningness/eveningness) from sleep midpoint
data, recommends optimal sleep windows, and provides light exposure guidance.

References: Horne & Östberg Morningness-Eveningness Questionnaire (MEQ),
            Roenneberg et al. Munich ChronoType Questionnaire (MCTQ).
"""
from dataclasses import dataclass
from typing import Optional
import statistics
import math


@dataclass
class SleepRecord:
    """Single night's sleep data for chronotype inference."""
    bedtime: str       # "HH:MM" 24h local time
    wake_time: str     # "HH:MM" 24h local time
    date: str          # "YYYY-MM-DD"


# ── Helpers ────────────────────────────────────────────────────────────────

def _to_minutes(t: str) -> int:
    """Convert HH:MM to minutes since midnight."""
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def _midpoint(bed: str, wake: str) -> float:
    """Sleep midpoint in minutes, handling overnight wrap."""
    b = _to_minutes(bed)
    w = _to_minutes(wake)
    if b > w:
        b -= 1440  # cross midnight
    return (b + w) / 2.0


# ── Core classification ────────────────────────────────────────────────────

# MSF (midpoint of sleep on free days) scoring thresholds.
# Based on MCTQ empirical ranges.  Midpoint is in minutes-since-midnight
# (can be negative for very early sleepers, typically 140–260).
_CHRONOTYPE_BINS = [
    # (label, midpoint_upper_bound, ordinal)
    ("definite_morning",   170.0, 1),
    ("moderate_morning",   190.0, 2),
    ("intermediate",       210.0, 3),
    ("moderate_evening",   230.0, 4),
    ("definite_evening",   math.inf, 5),
]


def classify_chronotype(midpoint_minutes: float) -> dict:
    """
    Classify chronotype from a single sleep midpoint (MSF proxy).

    Parameters
    ----------
    midpoint_minutes : float
        Sleep midpoint expressed as minutes since midnight (0 = midnight).
        Negative values are allowed for very early sleepers.

    Returns
    -------
    dict with classification label, ordinal score (1-5), and description.
    """
    for label, upper, ordinal in _CHRONOTYPE_BINS:
        if midpoint_minutes < upper:
            break
    else:
        label, ordinal = "intermediate", 3

    descriptions = {
        "definite_morning": "Strong morning preference. You naturally wake early and feel most alert in the first half of the day.",
        "moderate_morning": "Leans toward mornings. You're productive before lunch and wind down in the evening.",
        "intermediate":     "Neither strongly morning nor evening. You adapt easily to different schedules.",
        "moderate_evening": "Leans toward evenings. You're more alert later and prefer sleeping in.",
        "definite_evening": "Strong evening preference. Your peak alertness is late afternoon/evening, and you naturally sleep and wake late.",
    }

    return {
        "chronotype": label,
        "ordinal": ordinal,
        "description": descriptions[label],
        "midpoint_minutes": round(midpoint_minutes, 1),
    }


def score_msq(midpoint_minutes: float) -> dict:
    """
    Produce a continuous morningness score (0-100) mirroring the Horne-Östberg
    MEQ scale where higher = more morning-oriented.

    MSF 140 min → score ≈ 95,  MSF 260 min → score ≈ 5.
    Linear mapping with clamping.
    """
    score = 100.0 - ((midpoint_minutes - 140.0) / 120.0) * 100.0
    score = max(0.0, min(100.0, score))

    if score >= 70:
        interpretation = "Morning type"
    elif score >= 42:
        interpretation = "Intermediate type"
    else:
        interpretation = "Evening type"

    return {
        "morningness_score": round(score, 1),
        "interpretation": interpretation,
        "meq_range": "0 (definite evening) – 100 (definite morning)",
    }


# ── Aggregate analysis ────────────────────────────────────────────────────

def analyze_chronotype(records: list[SleepRecord]) -> dict:
    """
    Analyze chronotype from a collection of sleep records.

    Computes:
    - Individual midpoints per record
    - Mean and std of midpoints (free-day proxy)
    - Chronotype classification
    - Morningness score
    - Sleep phase preference (stable vs shifting)
    """
    if not records:
        return {"error": "No sleep records provided"}

    midpoints = [_midpoint(r.bedtime, r.wake_time) for r in records]
    avg_mp = statistics.mean(midpoints)
    std_mp = statistics.stdev(midpoints) if len(midpoints) > 1 else 0.0

    classification = classify_chronotype(avg_mp)
    msq = score_msq(avg_mp)

    # Phase preference: how stable is the midpoint across days?
    if std_mp < 20:
        phase_stability = "stable"
    elif std_mp < 40:
        phase_stability = "moderate_variation"
    else:
        phase_stability = "irregular"

    return {
        **classification,
        "morningness_score": msq["morningness_score"],
        "interpretation": msq["interpretation"],
        "avg_midpoint_minutes": round(avg_mp, 1),
        "midpoint_std_minutes": round(std_mp, 1),
        "phase_stability": phase_stability,
        "record_count": len(records),
    }


# ── Optimal sleep window ──────────────────────────────────────────────────

def recommend_sleep_window(
    chronotype_ordinal: int,
    target_hours: float = 8.0,
    work_wake: Optional[str] = None,
) -> dict:
    """
    Recommend an optimal sleep window based on chronotype.

    Parameters
    ----------
    chronotype_ordinal : int
        1 (definite morning) to 5 (definite_evening).
    target_hours : float
        Desired sleep duration.
    work_wake : str, optional
        Required wake time on work days (e.g., "06:30").
    """
    # Natural sleep onset offset from ordinal (minutes before midnight)
    # ordinal 1 → 21:30, ordinal 5 → 01:30
    natural_bed_offset = {1: 135, 2: 120, 3: 105, 4: 80, 5: 60}
    # Natural wake offset (minutes after midnight)
    natural_wake_offset = {1: 360, 2: 390, 3: 420, 4: 450, 5: 480}

    bed_minutes = 1440 - natural_bed_offset.get(chronotype_ordinal, 105)
    wake_minutes = natural_wake_offset.get(chronotype_ordinal, 420)

    def _fmt(m: int) -> str:
        m = m % 1440
        return f"{m // 60:02d}:{m % 60:02d}"

    window = {
        "optimal_bedtime": _fmt(bed_minutes),
        "optimal_wake": _fmt(wake_minutes),
        "duration_hours": target_hours,
    }

    # Light exposure recommendations
    light_recs = []
    if chronotype_ordinal <= 2:
        light_recs = [
            "Seek bright light immediately upon waking to reinforce morning phase.",
            "Dim lights and avoid blue light after 8 PM.",
            "Morning outdoor walk (10-15 min) before 9 AM.",
        ]
    elif chronotype_ordinal == 3:
        light_recs = [
            "Consistent light exposure at wake time helps stability.",
            "Balance screen time — no strict cutoff needed, but avoid screens within 1 hour of bed.",
        ]
    else:
        light_recs = [
            "Morning light (even 5 min) helps shift phase earlier if desired.",
            "Bright light in the first half of the day prevents excessive phase delay.",
            "Use blue-light filters after sunset; maintain consistent evening dimming.",
        ]

    # Work day adjustment
    if work_wake:
        wake_m = _to_minutes(work_wake)
        recommended_bed = wake_m - int(target_hours * 60)
        window["work_bedtime"] = _fmt(recommended_bed)
        window["work_wake"] = work_wake
        sleep_pressure = wake_minutes - recommended_bed
        if sleep_pressure < int(target_hours * 60) - 60:
            window["warning"] = (
                f"Required wake time ({work_wake}) yields less than "
                f"{target_hours - 1}h sleep at the natural bedtime. "
                f"Consider shifting bedtime earlier."
            )

    window["light_exposure"] = light_recs
    return window


# ── Phase delay / advance estimation ──────────────────────────────────────

def estimate_phase_shift(
    records: list[SleepRecord],
    days: int = 7,
) -> dict:
    """
    Detect whether the user's sleep phase is shifting earlier (advance)
    or later (delay) over the most recent records.
    """
    if len(records) < 3:
        return {"error": "Need at least 3 records for phase shift analysis"}

    sorted_recs = sorted(records, key=lambda r: r.date)[-days:]
    midpoints = [_midpoint(r.bedtime, r.wake_time) for r in sorted_recs]

    # Linear regression on midpoints
    n = len(midpoints)
    x = list(range(n))
    x_mean = statistics.mean(x)
    y_mean = statistics.mean(midpoints)
    num = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, midpoints))
    den = sum((xi - x_mean) ** 2 for xi in x)
    slope = num / den if den > 0 else 0.0  # minutes per day

    if slope < -5:
        direction = "phase_advance"
        description = "Your sleep phase is shifting earlier over recent days."
    elif slope > 5:
        direction = "phase_delay"
        description = "Your sleep phase is shifting later over recent days."
    else:
        direction = "stable"
        description = "Your sleep phase is stable across recent days."

    return {
        "direction": direction,
        "slope_minutes_per_day": round(slope, 2),
        "description": description,
        "days_analyzed": n,
    }

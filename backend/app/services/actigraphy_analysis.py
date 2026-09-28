"""Actigraphy Analysis Service.

Extracted from pyactigraphy (inspiration).
Circadian rhythm analysis: cosinor analysis, activity patterns,
sleep-wake detection, and rhythm metrics.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CosinorResult:
    mesor: float
    amplitude: float
    acrophase: float
    period: float
    goodness_of_fit: float
    rhythm_detected: bool


@dataclass
class ActigraphyMetrics:
    total_counts: int
    active_minutes: int
    sedentary_minutes: int
    sleep_minutes: int
    awake_minutes: int
    sleep_onset: float
    sleep_offset: float
    fragmentation_index: float
    interdaily_stability: float
    intradaily_variability: float


@dataclass
class RhythmAnalysis:
    cosinor: CosinorResult
    peak_time: float
    trough_time: float
    rhythm_strength: str
    is_diurnal: bool


def cosinor_fit(values: list[float], period_minutes: float = 1440.0) -> CosinorResult:
    """Simple cosinor analysis for circadian rhythm detection."""
    n = len(values)
    if n < 10:
        return CosinorResult(0, 0, 0, period_minutes, 0, False)
    mesor = statistics.mean(values)
    min_val = min(values)
    max_val = max(values)
    amplitude = (max_val - min_val) / 2
    if amplitude <= 0:
        return CosinorResult(mesor, 0, 0, period_minutes, 0, False)
    sum_cos = 0.0
    sum_sin = 0.0
    for i, v in enumerate(values):
        angle = 2 * math.pi * i / (n * period_minutes / n)
        sum_cos += (v - mesor) * math.cos(angle)
        sum_sin += (v - mesor) * math.sin(angle)
    acrophase = math.atan2(sum_sin, sum_cos)
    if acrophase < 0:
        acrophase += 2 * math.pi
    ss_res = sum((v - (mesor + amplitude * math.cos(2 * math.pi * i / n + acrophase))) ** 2 for i, v in enumerate(values))
    ss_tot = sum((v - mesor) ** 2 for v in values)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    rhythm_detected = r_squared > 0.3 and amplitude > 10
    return CosinorResult(
        mesor=round(mesor, 2), amplitude=round(amplitude, 2),
        acrophase=round(acrophase, 4), period=period_minutes,
        goodness_of_fit=round(max(0, r_squared), 4),
        rhythm_detected=rhythm_detected,
    )


def detect_actigraphy_metrics(
    counts: list[int],
    sample_rate_minutes: float = 1.0,
    sleep_threshold: float = 100,
) -> ActigraphyMetrics:
    """Compute actigraphy metrics from activity counts."""
    if not counts:
        return ActigraphyMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    total = sum(counts)
    active = sum(1 for c in counts if c > sleep_threshold)
    sedentary = sum(1 for c in counts if 0 < c <= sleep_threshold)
    sleep = sum(1 for c in counts if c == 0)
    awake = len(counts) - sleep
    sleep_onset = _find_sleep_onset(counts, sleep_threshold)
    sleep_offset = _find_sleep_offset(counts, sleep_threshold)
    frag = _calculate_fragmentation(counts, sleep_threshold)
    interdaily_stab = _calculate_interdaily_stability(counts)
    iv = _calculate_intradaily_variability(counts)
    return ActigraphyMetrics(
        total_counts=total, active_minutes=active, sedentary_minutes=sedentary,
        sleep_minutes=sleep, awake_minutes=awake,
        sleep_onset=sleep_onset, sleep_offset=sleep_offset,
        fragmentation_index=frag, interdaily_stability=interdaily_stab, intradaily_variability=iv,
    )


def _find_sleep_onset(counts: list[int], threshold: float) -> float:
    """Find sleep onset time (first 30min below threshold)."""
    window = 30
    for i in range(len(counts) - window):
        if all(c < threshold for c in counts[i:i + window]):
            return i * 1.0
    return 0.0


def _find_sleep_offset(counts: list[int], threshold: float) -> float:
    """Find sleep offset time (last 30min below threshold)."""
    window = 30
    for i in range(len(counts) - window, 0, -1):
        if all(c < threshold for c in counts[i:i + window]):
            return (i + window) * 1.0
    return len(counts) * 1.0


def _calculate_fragmentation(counts: list[int], threshold: float) -> float:
    """Calculate sleep fragmentation index."""
    transitions = 0
    for i in range(1, len(counts)):
        prev_sleep = counts[i - 1] < threshold
        curr_sleep = counts[i] < threshold
        if prev_sleep != curr_sleep:
            transitions += 1
    total = len(counts)
    return round(transitions / total * 100, 2) if total > 0 else 0


def _calculate_interdaily_stability(counts: list[int]) -> float:
    """Calculate interdaily stability (consistency across days)."""
    if len(counts) < 1440:
        return 0.5
    days = len(counts) // 1440
    if days < 2:
        return 0.5
    day_profiles = []
    for d in range(days):
        day_profiles.append(counts[d * 1440:(d + 1) * 1440])
    if not day_profiles:
        return 0.5
    hourly_means = []
    for h in range(24):
        hour_counts = []
        for day in day_profiles:
            start = h * 60
            end = min(start + 60, len(day))
            hour_counts.extend(day[start:end])
        hourly_means.append(statistics.mean(hour_counts) if hour_counts else 0)
    overall_mean = statistics.mean(hourly_means) if hourly_means else 1
    overall_var = statistics.variance(hourly_means) if len(hourly_means) > 1 else 0
    total_var = statistics.variance(counts) if len(counts) > 1 else 1
    if total_var <= 0:
        return 0.5
    return round(min(1.0, max(0, overall_var / total_var)), 4)


def _calculate_intradaily_variability(counts: list[int]) -> float:
    """Calculate intradaily variability (fragmentation)."""
    if len(counts) < 3:
        return 0.0
    diffs = [counts[i] - counts[i - 1] for i in range(1, len(counts))]
    if not diffs:
        return 0.0
    diff_var = statistics.variance(diffs) if len(diffs) > 1 else 0
    data_var = statistics.variance(counts) if len(counts) > 1 else 1
    if data_var <= 0:
        return 0.0
    return round(diff_var / data_var, 4)


def analyze_rhythm(counts: list[int], period_minutes: float = 1440.0) -> RhythmAnalysis:
    """Complete rhythm analysis with cosinor and metrics."""
    cosinor = cosinor_fit([float(c) for c in counts], period_minutes)
    n = len(counts)
    if n == 0 or cosinor.amplitude <= 0:
        return RhythmAnalysis(cosinor, 0, 0, "none", False)
    peak_idx = max(range(n), key=lambda i: counts[i])
    trough_idx = min(range(n), key=lambda i: counts[i])
    peak_time = peak_idx * period_minutes / n
    trough_time = trough_idx * period_minutes / n
    if cosinor.goodness_of_fit > 0.6:
        strength = "strong"
    elif cosinor.goodness_of_fit > 0.3:
        strength = "moderate"
    else:
        strength = "weak"
    is_diurnal = 6 * 60 <= peak_time <= 20 * 60
    return RhythmAnalysis(cosinor, peak_time, trough_time, strength, is_diurnal)


def generate_actigraphy_summary(counts: list[int]) -> dict[str, Any]:
    """Generate complete actigraphy summary."""
    metrics = detect_actigraphy_metrics(counts)
    rhythm = analyze_rhythm(counts)
    return {
        "total_counts": metrics.total_counts,
        "active_minutes": metrics.active_minutes,
        "sedentary_minutes": metrics.sedentary_minutes,
        "sleep_minutes": metrics.sleep_minutes,
        "sleep_onset": metrics.sleep_onset,
        "sleep_offset": metrics.sleep_offset,
        "fragmentation_index": metrics.fragmentation_index,
        "rhythm": {
            "amplitude": rhythm.cosinor.amplitude,
            "acrophase": rhythm.cosinor.acrophase,
            "goodness_of_fit": rhythm.cosinor.goodness_of_fit,
            "strength": rhythm.rhythm_strength,
            "is_diurnal": rhythm.is_diurnal,
        },
    }


def rest_activity_rhythm(hourly_days: list[list[float]]) -> dict[str, Any]:
    """
    Non-parametric rest-activity rhythm (Van Someren 1999) from hourly activity, one list of 24 per day.

    IS near 1 means the same daily pattern every day; IV near 0 a smooth one;
    RA near 1 a clear gap between the most active 10 hours and the quietest 5.
    """
    days = [d for d in hourly_days if len(d) == 24]
    if len(days) < 3:
        return {"status": "insufficient_data", "days": len(days), "needed_days": 3}
    x = [v for d in days for v in d]
    n = len(x)
    mean = sum(x) / n
    total_var = sum((v - mean) ** 2 for v in x)
    if total_var == 0:
        return {"status": "insufficient_data", "days": len(days), "message": "No variation in activity"}
    profile = [sum(d[h] for d in days) / len(days) for h in range(24)]
    interdaily = n * sum((p - mean) ** 2 for p in profile) / (24 * total_var)
    intradaily = n * sum((x[i] - x[i - 1]) ** 2 for i in range(1, n)) / ((n - 1) * total_var)

    def window(size: int, pick):
        means = [(sum(profile[(s + k) % 24] for k in range(size)) / size, s) for s in range(24)]
        return pick(means)

    m10, m10_start = window(10, max)
    l5, l5_start = window(5, min)
    return {
        "status": "ok",
        "days": len(days),
        "interdaily_stability": round(interdaily, 3),
        "intradaily_variability": round(intradaily, 3),
        "m10": round(m10, 1), "m10_onset_hour": m10_start,
        "l5": round(l5, 1), "l5_onset_hour": l5_start,
        "relative_amplitude": round((m10 - l5) / (m10 + l5), 3) if m10 + l5 else 0.0,
        "hourly_profile": [round(p, 1) for p in profile],
    }

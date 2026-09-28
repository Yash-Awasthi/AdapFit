"""CGM (Continuous Glucose Monitor) Analysis Service.

Extracted from dexta-intelligence (inspiration).
Glucose time-series analysis, time-in-range calculations,
hypo/hyperglycemia detection, and glycemic risk assessment.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class GlucoseRange(Enum):
    HYPO = "hypo"            # < 70 mg/dL
    LOW = "low"              # 70-79
    TARGET = "target"        # 80-140
    ELEVATED = "elevated"    # 141-180
    HYPER = "hyper"          # > 180


class RiskLevel(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class GlucoseReading:
    timestamp: datetime
    value: float  # mg/dL
    source: str = "cgm"


@dataclass
class TimeInRangeResult:
    percent_hypo: float
    percent_low: float
    percent_target: float
    percent_elevated: float
    percent_hyper: float
    total_readings: int


@dataclass
class GlycemicEpisode:
    episode_type: str  # "hypo" or "hyper"
    start_index: int
    end_index: int
    start_time: datetime
    end_time: datetime
    duration_minutes: float
    min_or_max_value: float
    severity: str  # "mild", "moderate", "severe"


@dataclass
class GlucoseVariability:
    cv: float  # coefficient of variation
    sd: float  # standard deviation
    iqr: float  # interquartile range
    mean: float
    min_value: float
    max_value: float
    j_index: float  # J-index (glycemic variability index)


@dataclass
class GlycemicRiskIndex:
    gri: float  # Glycemia Risk Index (0-100)
    vgl: float  # Variability-Glucose Level component
    lgl: float  # Low Glucose Level component
    risk_level: RiskLevel
    components: dict[str, float] = field(default_factory=dict)


TARGET_LOW = 70.0
TARGET_HIGH = 180.0
SEVERE_HYPO = 54.0
SEVERE_HYPER = 250.0


def classify_glucose_range(value: float) -> GlucoseRange:
    """Classify a glucose reading into a range."""
    if value < TARGET_LOW:
        return GlucoseRange.HYPO
    elif value < 80:
        return GlucoseRange.LOW
    elif value <= 140:
        return GlucoseRange.TARGET
    elif value <= TARGET_HIGH:
        return GlucoseRange.ELEVATED
    else:
        return GlucoseRange.HYPER


def calculate_time_in_range(readings: list[GlucoseReading]) -> TimeInRangeResult:
    """Calculate percentage of time in each glucose range."""
    if not readings:
        return TimeInRangeResult(0, 0, 0, 0, 0, 0)
    counts = {r: 0 for r in GlucoseRange}
    for reading in readings:
        counts[classify_glucose_range(reading.value)] += 1
    total = len(readings)
    return TimeInRangeResult(
        percent_hypo=counts[GlucoseRange.HYPO] / total * 100,
        percent_low=counts[GlucoseRange.LOW] / total * 100,
        percent_target=counts[GlucoseRange.TARGET] / total * 100,
        percent_elevated=counts[GlucoseRange.ELEVATED] / total * 100,
        percent_hyper=counts[GlucoseRange.HYPER] / total * 100,
        total_readings=total,
    )


def calculate_glucose_variability(readings: list[GlucoseReading]) -> GlucoseVariability:
    """Calculate glucose variability metrics."""
    if len(readings) < 2:
        values = [r.value for r in readings] if readings else [0]
        return GlucoseVariability(0, 0, 0, values[0], values[0], values[0], 0)
    values = [r.value for r in readings]
    mean_val = statistics.mean(values)
    sd_val = statistics.pstdev(values) if len(values) > 1 else 0
    cv = (sd_val / mean_val * 100) if mean_val > 0 else 0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    q1 = sorted_vals[n // 4]
    q3 = sorted_vals[3 * n // 4]
    iqr = q3 - q1
    mean_sq = mean_val ** 2 if mean_val > 0 else 1
    j_index = (mean_val ** 2 + sd_val ** 2) / mean_sq
    return GlucoseVariability(
        cv=cv, sd=sd_val, iqr=iqr, mean=mean_val,
        min_value=min(values), max_value=max(values),
        j_index=j_index,
    )


def detect_episodes(readings: list[GlucoseReading]) -> list[GlycemicEpisode]:
    """Detect hypo and hyperglycemic episodes."""
    if len(readings) < 2:
        return []
    episodes = []
    in_episode = False
    episode_type = ""
    start_idx = 0
    # A sentinel in-range reading closes an episode still open at the end.
    readings = readings + [GlucoseReading(readings[-1].timestamp, (TARGET_LOW + TARGET_HIGH) / 2)]
    for i, reading in enumerate(readings):
        is_hypo = reading.value < TARGET_LOW
        is_hyper = reading.value > TARGET_HIGH
        currently_abnormal = is_hypo or is_hyper
        current_type = "hypo" if is_hypo else ("hyper" if is_hyper else "")
        if currently_abnormal and not in_episode:
            in_episode = True
            episode_type = current_type
            start_idx = i
        elif (not currently_abnormal or current_type != episode_type) and in_episode:
            episode_readings = readings[start_idx:i]
            values = [r.value for r in episode_readings]
            duration = (readings[i - 1].timestamp - readings[start_idx].timestamp).total_seconds() / 60
            if episode_type == "hypo":
                severity = "severe" if min(values) < SEVERE_HYPO else ("moderate" if min(values) < 60 else "mild")
                episodes.append(GlycemicEpisode(
                    episode_type="hypo", start_index=start_idx, end_index=i - 1,
                    start_time=readings[start_idx].timestamp, end_time=readings[i - 1].timestamp,
                    duration_minutes=duration, min_or_max_value=min(values), severity=severity,
                ))
            else:
                severity = "severe" if max(values) > SEVERE_HYPER else ("moderate" if max(values) > 300 else "mild")
                episodes.append(GlycemicEpisode(
                    episode_type="hyper", start_index=start_idx, end_index=i - 1,
                    start_time=readings[start_idx].timestamp, end_time=readings[i - 1].timestamp,
                    duration_minutes=duration, min_or_max_value=max(values), severity=severity,
                ))
            in_episode = False
    return episodes


def calculate_gri(readings: list[GlucoseReading]) -> GlycemicRiskIndex:
    """Calculate Glycemia Risk Index (GRI) per Klonoff et al. 2023."""
    if not readings:
        return GlycemicRiskIndex(0, 0, 0, RiskLevel.LOW, {})
    values = [r.value for r in readings]
    tir = calculate_time_in_range(readings)
    variability = calculate_glucose_variability(readings)
    vgl = min(100, (variability.cv / 36) * 50 + (1 - tir.percent_target / 100) * 50)
    hypo_pct = tir.percent_hypo + tir.percent_low
    lgl = min(100, (hypo_pct / 5) * 50 + (tir.percent_hypo / 1) * 50)
    vgl = min(50, vgl)
    lgl = min(50, lgl)
    gri = vgl + lgl
    if gri < 20:
        risk = RiskLevel.LOW
    elif gri < 40:
        risk = RiskLevel.MODERATE
    elif gri < 60:
        risk = RiskLevel.HIGH
    else:
        risk = RiskLevel.CRITICAL
    return GlycemicRiskIndex(
        gri=gri, vgl=vgl, lgl=lgl, risk_level=risk,
        components={"cv": variability.cv, "tir": tir.percent_target, "hypo_pct": hypo_pct},
    )


def calculate_average_glucose(readings: list[GlucoseReading]) -> float:
    """Calculate mean glucose level."""
    if not readings:
        return 0.0
    return statistics.mean(r.value for r in readings)


def estimate_hba1c(mean_glucose: float) -> float:
    """Glucose Management Indicator (Bergenstal 2018), the consensus estimate from mean CGM glucose."""
    return 3.31 + 0.02392 * mean_glucose


def calculate_mage(readings: list[GlucoseReading]) -> float:
    """Calculate Mean Amplitude of Glycemic Excursions (MAGE)."""
    if len(readings) < 3:
        return 0.0
    values = [r.value for r in readings]
    mean_val = statistics.mean(values)
    excursions = []
    last_peak = None
    last_trough = None
    for v in values:
        if v > mean_val + 1:
            if last_trough is not None:
                excursions.append(v - last_trough)
            last_peak = v
        elif v < mean_val - 1:
            if last_peak is not None:
                excursions.append(last_peak - v)
            last_trough = v
    return statistics.mean(excursions) if excursions else 0.0


def calculate_lABILITY(readings: list[GlucoseReading]) -> float:
    """Calculate lABILITY index (low glucose lability index)."""
    if len(readings) < 2:
        return 0.0
    values = [r.value for r in readings]
    below_target = [v for v in values if v < TARGET_LOW]
    if not below_target:
        return 0.0
    total_area = 0.0
    for i in range(1, len(values)):
        if values[i] < TARGET_LOW:
            total_area += (TARGET_LOW - values[i])
    return total_area / len(values) if values else 0.0


def analyze_daily_patterns(readings: list[GlucoseReading]) -> dict[str, float]:
    """Analyze glucose patterns by time of day."""
    hourly_values: dict[int, list[float]] = {}
    for reading in readings:
        hour = reading.timestamp.hour
        hourly_values.setdefault(hour, []).append(reading.value)
    return {
        f"{h:02d}:00": statistics.mean(vals)
        for h, vals in sorted(hourly_values.items())
    }


def generate_glucose_summary(readings: list[GlucoseReading]) -> dict[str, Any]:
    """Generate comprehensive glucose analysis summary."""
    if not readings:
        return {"error": "No readings provided"}
    tir = calculate_time_in_range(readings)
    variability = calculate_glucose_variability(readings)
    episodes = detect_episodes(readings)
    gri = calculate_gri(readings)
    mean_glucose = calculate_average_glucose(readings)
    hba1c_est = estimate_hba1c(mean_glucose)
    mage = calculate_mage(readings)
    below_70 = tir.percent_hypo + tir.percent_low
    return {
        "readings": len(readings),
        "mean_glucose": round(mean_glucose, 1),
        "gmi": round(hba1c_est, 1),
        # International consensus targets (Battelino et al., Diabetes Care 2019).
        "targets_met": {
            "time_in_range_over_70pct": tir.percent_target > 70,
            "below_70_under_4pct": below_70 < 4,
            "below_54_under_1pct": tir.percent_hypo < 1,
            "cv_36_or_less": variability.cv <= 36,
        },
        "time_in_range": {
            "target": round(tir.percent_target, 1),
            "above_target": round(tir.percent_elevated + tir.percent_hyper, 1),
            "below_target": round(tir.percent_hypo + tir.percent_low, 1),
        },
        "variability": {
            "cv": round(variability.cv, 1),
            "sd": round(variability.sd, 1),
            "j_index": round(variability.j_index, 2),
        },
        "mage": round(mage, 1),
        "episodes": {
            "hypo_count": sum(1 for e in episodes if e.episode_type == "hypo"),
            "hyper_count": sum(1 for e in episodes if e.episode_type == "hyper"),
        },
        "gri": {
            "score": round(gri.gri, 1),
            "risk_level": gri.risk_level.value,
        },
    }

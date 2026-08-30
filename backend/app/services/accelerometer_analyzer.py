"""Accelerometer Analyzer Service.

Extracted from scikit-digital-health (inspiration).
Inertial sensor data analysis: activity classification,
cutpoint-based segmentation, and signal feature extraction.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ActivityLevel(Enum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    VIGOROUS = "vigorous"
    MVPA = "mvpa"


class WristPosition(Enum):
    LEFT_WRIST = "left_wrist"
    RIGHT_WRIST = "right_wrist"
    LUMBAR = "lumbar"
    HIP = "hip"
    ANKLE = "ankle"


@dataclass
class AccelerometerSample:
    timestamp: float
    x: float
    y: float
    z: float


@dataclass
class ActivityMetrics:
    total_counts: float
    sedentary_minutes: float
    light_minutes: float
    moderate_minutes: float
    vigorous_minutes: float
    mvpa_minutes: float
    step_count: int
    avg_enmo: float
    peak_enmo: float


@dataclass
class SignalFeatures:
    mean: float
    std: float
    min_val: float
    max_val: float
    median: float
    iqr: float
    rms: float
    entropy: float
    zero_crossings: int
    peak_count: int


CUTPOINTS = {
    "esliger_lwrist_adult": {
        "wrist": WristPosition.LEFT_WRIST,
        "sedentary": 0.045,
        "light": 0.134,
        "moderate": 0.377,
    },
    "esliger_rwrist_adult": {
        "wrist": WristPosition.RIGHT_WRIST,
        "sedentary": 0.080,
        "light": 0.091,
        "moderate": 0.437,
    },
    "esliger_lumbar_adult": {
        "wrist": WristPosition.LUMBAR,
        "sedentary": 0.063,
        "light": 0.097,
        "moderate": 0.408,
    },
}


def calculate_enmo(x: float, y: float, z: float) -> float:
    """Calculate Euclidean Norm Minus One (ENMO) in g-units."""
    norm = math.sqrt(x**2 + y**2 + z**2)
    return max(0, norm - 1.0)


def calculate_magnitude(x: float, y: float, z: float) -> float:
    """Calculate signal magnitude."""
    return math.sqrt(x**2 + y**2 + z**2)


def calculate_vm(x: float, y: float, z: float) -> float:
    """Vector magnitude for activity counts."""
    return math.sqrt(x**2 + y**2 + z**2)


def classify_activity_level(enmo: float, cutpoint_name: str = "esliger_lwrist_adult") -> ActivityLevel:
    """Classify activity level from ENMO value using cutpoints."""
    cuts = CUTPOINTS.get(cutpoint_name, CUTPOINTS["esliger_lwrist_adult"])
    if enmo < cuts["sedentary"]:
        return ActivityLevel.SEDENTARY
    elif enmo < cuts["light"]:
        return ActivityLevel.LIGHT
    elif enmo < cuts["moderate"]:
        return ActivityLevel.MODERATE
    else:
        return ActivityLevel.VIGOROUS


def calculate_signal_features(values: list[float]) -> SignalFeatures:
    """Calculate signal features from a series of values."""
    if not values:
        return SignalFeatures(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    mean_val = statistics.mean(values)
    std_val = statistics.stdev(values) if len(values) > 1 else 0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    iqr = sorted_vals[3 * n // 4] - sorted_vals[n // 4] if n > 3 else 0
    rms = math.sqrt(sum(v**2 for v in values) / len(values))
    zero_crossings = sum(1 for i in range(1, len(values)) if (values[i] > 0) != (values[i - 1] > 0))
    peaks = sum(1 for i in range(1, len(values) - 1) if values[i] > values[i - 1] and values[i] > values[i + 1])
    entropy = _calculate_entropy(values)
    return SignalFeatures(
        mean=round(mean_val, 4), std=round(std_val, 4),
        min_val=round(min(values), 4), max_val=round(max(values), 4),
        median=round(statistics.median(values), 4), iqr=round(iqr, 4),
        rms=round(rms, 4), entropy=round(entropy, 4),
        zero_crossings=zero_crossings, peak_count=peaks,
    )


def _calculate_entropy(values: list[float]) -> float:
    """Calculate approximate entropy of a signal."""
    if len(values) < 3:
        return 0.0
    bins = min(20, len(values) // 2)
    hist = [0] * bins
    min_val = min(values)
    max_val = max(values)
    rng = max_val - min_val
    if rng == 0:
        return 0.0
    for v in values:
        idx = min(bins - 1, int((v - min_val) / rng * bins))
        hist[idx] += 1
    total = len(values)
    entropy = 0.0
    for count in hist:
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy


def detect_steps(values: list[float], threshold: float = 0.2, min_interval_ms: float = 250) -> int:
    """Simple step detection from accelerometer magnitude."""
    steps = 0
    last_step_index = -min_interval_ms
    for i, v in enumerate(values):
        if v > threshold and (i - last_step_index) >= min_interval_ms:
            steps += 1
            last_step_index = i
    return steps


def analyze_accelerometer_data(
    samples: list[AccelerometerSample],
    cutpoint_name: str = "esliger_lwrist_adult",
    sample_rate_hz: float = 100.0,
) -> ActivityMetrics:
    """Analyze accelerometer data and compute activity metrics."""
    if not samples:
        return ActivityMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0)
    enmo_values = [calculate_enmo(s.x, s.y, s.z) for s in samples]
    total_minutes = len(samples) / sample_rate_hz / 60
    levels = [classify_activity_level(e, cutpoint_name) for e in enmo_values]
    sedentary = sum(1 for l in levels if l == ActivityLevel.SEDENTARY) / sample_rate_hz / 60
    light = sum(1 for l in levels if l == ActivityLevel.LIGHT) / sample_rate_hz / 60
    moderate = sum(1 for l in levels if l == ActivityLevel.MODERATE) / sample_rate_hz / 60
    vigorous = sum(1 for l in levels if l == ActivityLevel.VIGOROUS) / sample_rate_hz / 60
    mvpa = moderate + vigorous
    step_count = detect_steps(enmo_values)
    return ActivityMetrics(
        total_counts=sum(enmo_values),
        sedentary_minutes=round(sedentary, 1),
        light_minutes=round(light, 1),
        moderate_minutes=round(moderate, 1),
        vigorous_minutes=round(vigorous, 1),
        mvpa_minutes=round(mvpa, 1),
        step_count=step_count,
        avg_enmo=round(statistics.mean(enmo_values), 4) if enmo_values else 0,
        peak_enmo=round(max(enmo_values), 4) if enmo_values else 0,
    )


def segment_activity_windows(
    samples: list[AccelerometerSample],
    window_seconds: float = 60.0,
    sample_rate_hz: float = 100.0,
) -> list[dict[str, Any]]:
    """Segment accelerometer data into time windows."""
    window_size = int(window_seconds * sample_rate_hz)
    windows = []
    for i in range(0, len(samples), window_size):
        window_samples = samples[i:i + window_size]
        if len(window_samples) < window_size * 0.5:
            continue
        enmo_values = [calculate_enmo(s.x, s.y, s.z) for s in window_samples]
        levels = [classify_activity_level(e) for e in enmo_values]
        dominant_level = max(set(levels), key=levels.count)
        windows.append({
            "start_index": i,
            "end_index": min(i + window_size, len(samples)),
            "dominant_activity": dominant_level.value,
            "avg_enmo": round(statistics.mean(enmo_values), 4),
            "step_count": detect_steps(enmo_values),
            "duration_seconds": window_seconds,
        })
    return windows


def calculate_daily_activity_summary(
    windows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Calculate daily summary from activity windows."""
    if not windows:
        return {"total_minutes": 0}
    sedentary = sum(1 for w in windows if w["dominant_activity"] == "sedentary")
    light = sum(1 for w in windows if w["dominant_activity"] == "light")
    moderate = sum(1 for w in windows if w["dominant_activity"] == "moderate")
    vigorous = sum(1 for w in windows if w["dominant_activity"] == "vigorous")
    total_steps = sum(w["step_count"] for w in windows)
    return {
        "total_minutes": len(windows) * (windows[0]["duration_seconds"] / 60),
        "sedentary_minutes": sedentary * (windows[0]["duration_seconds"] / 60),
        "light_minutes": light * (windows[0]["duration_seconds"] / 60),
        "moderate_minutes": moderate * (windows[0]["duration_seconds"] / 60),
        "vigorous_minutes": vigorous * (windows[0]["duration_seconds"] / 60),
        "mvpa_minutes": (moderate + vigorous) * (windows[0]["duration_seconds"] / 60),
        "total_steps": total_steps,
        "activity_ratio": round((moderate + vigorous) / max(1, len(windows)), 2),
    }

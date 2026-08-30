"""Sleep Classifier Service.

Extracted from sleep_classifiers (inspiration).
ML-based sleep stage classification from accelerometer and heart rate data.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SleepStage(Enum):
    AWAKE = "awake"
    LIGHT = "light"
    DEEP = "deep"
    REM = "rem"


@dataclass
class SleepEpoch:
    timestamp: float
    accelerometer_magnitude: float
    heart_rate: float
    stage: SleepStage = SleepStage.AWAKE


@dataclass
class SleepClassificationResult:
    stages: list[SleepStage]
    epoch_details: list[SleepEpoch]
    total_sleep_time_minutes: float
    sleep_efficiency: float
    stage_percentages: dict[str, float]
    sleep_latency_minutes: float
    wake_after_sleep_onset_minutes: float


FEATURE_NAMES = [
    "accel_mean", "accel_std", "accel_min", "accel_max",
    "hr_mean", "hr_std", "hr_min", "hr_max",
    "hr_accel_correlation", "movement_count",
]


def extract_epoch_features(epoch: SleepEpoch, next_epochs: list[SleepEpoch]) -> dict[str, float]:
    """Extract features from a sleep epoch."""
    accel_values = [epoch.accelerometer_magnitude] + [e.accelerometer_magnitude for e in next_epochs]
    hr_values = [epoch.heart_rate] + [e.heart_rate for e in next_epochs]
    return {
        "accel_mean": statistics.mean(accel_values),
        "accel_std": statistics.stdev(accel_values) if len(accel_values) > 1 else 0,
        "accel_min": min(accel_values),
        "accel_max": max(accel_values),
        "hr_mean": statistics.mean(hr_values),
        "hr_std": statistics.stdev(hr_values) if len(hr_values) > 1 else 0,
        "hr_min": min(hr_values),
        "hr_max": max(hr_values),
        "hr_accel_correlation": _correlation(hr_values, accel_values),
        "movement_count": sum(1 for v in accel_values if v > 0.1),
    }


def _correlation(x: list[float], y: list[float]) -> float:
    """Calculate Pearson correlation coefficient."""
    n = min(len(x), len(y))
    if n < 2:
        return 0.0
    mean_x = statistics.mean(x[:n])
    mean_y = statistics.mean(y[:n])
    cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    std_x = math.sqrt(sum((x[i] - mean_x) ** 2 for i in range(n)))
    std_y = math.sqrt(sum((y[i] - mean_y) ** 2 for i in range(n)))
    if std_x * std_y == 0:
        return 0.0
    return cov / (std_x * std_y)


def classify_epoch(features: dict[str, float]) -> SleepStage:
    """Classify sleep stage from features using rule-based approach."""
    accel_movement = features.get("accel_mean", 0)
    hr_mean = features.get("hr_mean", 60)
    hr_variability = features.get("hr_std", 0)
    movement_count = features.get("movement_count", 0)
    if accel_movement > 0.15 or movement_count > 3:
        return SleepStage.AWAKE
    if hr_variability < 2 and accel_movement < 0.02:
        return SleepStage.DEEP
    if hr_variability > 5 and accel_movement < 0.05:
        return SleepStage.REM
    return SleepStage.LIGHT


def classify_sleep_epochs(
    epochs: list[SleepEpoch],
    window_size: int = 5,
) -> SleepClassificationResult:
    """Classify sleep stages for a series of epochs."""
    stages = []
    classified_epochs = []
    for i, epoch in enumerate(epochs):
        next_epochs = epochs[i + 1:i + 1 + window_size]
        features = extract_epoch_features(epoch, next_epochs)
        stage = classify_epoch(features)
        stages.append(stage)
        classified_epochs.append(SleepEpoch(
            timestamp=epoch.timestamp,
            accelerometer_magnitude=epoch.accelerometer_magnitude,
            heart_rate=epoch.heart_rate,
            stage=stage,
        ))
    total_epochs = len(stages)
    awake_count = sum(1 for s in stages if s == SleepStage.AWAKE)
    sleep_count = total_epochs - awake_count
    sleep_latency = 0
    for i, s in enumerate(stages):
        if s != SleepStage.AWAKE:
            sleep_latency = i * 30 / 60
            break
    waso = sum(30 for i in range(1, len(stages)) if stages[i] == SleepStage.AWAKE and stages[i - 1] != SleepStage.AWAKE) / 60
    stage_pcts = {}
    for stage in SleepStage:
        count = sum(1 for s in stages if s == stage)
        stage_pcts[stage.value] = round(count / total_epochs * 100, 1) if total_epochs > 0 else 0
    total_sleep = sleep_count * 30 / 60
    efficiency = (sleep_count / total_epochs * 100) if total_epochs > 0 else 0
    return SleepClassificationResult(
        stages=stages, epoch_details=classified_epochs,
        total_sleep_time_minutes=round(total_sleep, 1),
        sleep_efficiency=round(efficiency, 1),
        stage_percentages=stage_pcts,
        sleep_latency_minutes=round(sleep_latency, 1),
        wake_after_sleep_onset_minutes=round(waso, 1),
    )


def calculate_sleep_score(result: SleepClassificationResult) -> int:
    """Calculate a 0-100 sleep quality score."""
    score = 50.0
    if result.total_sleep_time_minutes >= 420:
        score += 15
    elif result.total_sleep_time_minutes >= 360:
        score += 10
    elif result.total_sleep_time_minutes < 300:
        score -= 10
    deep_pct = result.stage_percentages.get("deep", 0)
    if deep_pct >= 15:
        score += 10
    elif deep_pct >= 10:
        score += 5
    elif deep_pct < 5:
        score -= 5
    rem_pct = result.stage_percentages.get("rem", 0)
    if rem_pct >= 20:
        score += 10
    elif rem_pct >= 15:
        score += 5
    if result.sleep_efficiency >= 85:
        score += 10
    elif result.sleep_efficiency >= 70:
        score += 5
    elif result.sleep_efficiency < 50:
        score -= 10
    if result.sleep_latency_minutes <= 15:
        score += 5
    elif result.sleep_latency_minutes > 30:
        score -= 5
    if result.wake_after_sleep_onset_minutes <= 10:
        score += 5
    elif result.wake_after_sleep_onset_minutes > 30:
        score -= 5
    return max(0, min(100, int(score)))


def generate_sleep_report(result: SleepClassificationResult) -> dict[str, Any]:
    """Generate comprehensive sleep report."""
    score = calculate_sleep_score(result)
    return {
        "sleep_score": score,
        "total_sleep_minutes": result.total_sleep_time_minutes,
        "sleep_efficiency": result.sleep_efficiency,
        "stage_percentages": result.stage_percentages,
        "sleep_latency_minutes": result.sleep_latency_minutes,
        "wake_after_sleep_onset_minutes": result.wake_after_sleep_onset_minutes,
        "deep_sleep_percent": result.stage_percentages.get("deep", 0),
        "rem_sleep_percent": result.stage_percentages.get("rem", 0),
    }

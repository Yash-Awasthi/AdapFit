"""Anomaly Detection for Health Time Series.

Extracted from adtk (inspiration).
Implements threshold, persistence, level shift, and aggregate anomaly detectors
for health data time series analysis.

All pure functions — no DB, no async, no pandas dependency.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AnomalyEvent:
    """Detected anomaly event."""
    start_index: int
    end_index: int
    severity: str  # "low", "medium", "high", "critical"
    anomaly_type: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    description: str = ""


@dataclass
class AnomalyResult:
    """Result of anomaly detection."""
    anomalies: list[AnomalyEvent] = field(default_factory=list)
    total_anomalies: int = 0
    anomaly_rate: float = 0.0
    severity_counts: dict = field(default_factory=dict)


# --- Threshold Detector ---

def threshold_detect(
    values: list[float],
    low: Optional[float] = None,
    high: Optional[float] = None,
) -> list[bool]:
    """Detect anomalies based on fixed thresholds.

    Args:
        values: Time series values
        low: Lower threshold (values below are anomalous)
        high: Upper threshold (values above are anomalous)

    Returns:
        Boolean mask where True = anomaly
    """
    result = []
    for v in values:
        is_anomaly = False
        if low is not None and v < low:
            is_anomaly = True
        if high is not None and v > high:
            is_anomaly = True
        result.append(is_anomaly)
    return result


# --- Persistence Detector ---

def persistence_detect(
    anomalies: list[bool],
    min_duration: int = 3,
) -> list[bool]:
    """Filter anomalies by persistence (minimum consecutive duration).

    Args:
        anomalies: Boolean anomaly mask
        min_duration: Minimum consecutive anomalous points

    Returns:
        Filtered anomaly mask
    """
    result = [False] * len(anomalies)
    current_run = 0
    run_start = 0

    for i, is_anom in enumerate(anomalies):
        if is_anom:
            if current_run == 0:
                run_start = i
            current_run += 1
        else:
            if current_run >= min_duration:
                for j in range(run_start, i):
                    result[j] = True
            current_run = 0

    # Handle run at end
    if current_run >= min_duration:
        for j in range(run_start, len(anomalies)):
            result[j] = True

    return result


# --- Level Shift Detector ---

def level_shift_detect(
    values: list[float],
    window: int = 30,
    threshold: float = 2.0,
) -> list[bool]:
    """Detect level shifts using rolling statistics.

    Args:
        values: Time series values
        window: Rolling window size
        threshold: Number of standard deviations for shift detection

    Returns:
        Boolean mask where True = level shift point
    """
    n = len(values)
    if n < window * 2:
        return [False] * n

    result = [False] * n

    for i in range(window, n - window):
        left_window = values[i - window:i]
        right_window = values[i:i + window]

        left_mean = sum(left_window) / window
        right_mean = sum(right_window) / window

        left_var = sum((x - left_mean) ** 2 for x in left_window) / window
        right_var = sum((x - right_mean) ** 2 for x in right_window) / window

        left_std = math.sqrt(left_var) or 1.0
        right_std = math.sqrt(right_var) or 1.0

        # Z-test for mean difference
        z_score = abs(right_mean - left_mean) / math.sqrt(
            left_std ** 2 / window + right_std ** 2 / window
        )

        if z_score > threshold:
            result[i] = True

    return result


# --- Seasonal Anomaly Detector ---

def seasonal_detect(
    values: list[float],
    period: int = 24,
    threshold: float = 2.0,
) -> list[bool]:
    """Detect anomalies relative to seasonal pattern.

    Args:
        values: Time series values
        period: Seasonal period (e.g., 24 for hourly data with daily pattern)
        threshold: Number of standard deviations for anomaly

    Returns:
        Boolean mask where True = seasonal anomaly
    """
    n = len(values)
    if n < period:
        return [False] * n

    # Compute seasonal averages
    seasonal_sums = [0.0] * period
    seasonal_counts = [0] * period

    for i in range(n):
        pos = i % period
        seasonal_sums[pos] += values[i]
        seasonal_counts[pos] += 1

    seasonal_means = [
        seasonal_sums[i] / seasonal_counts[i] if seasonal_counts[i] > 0 else 0
        for i in range(period)
    ]

    # Compute residual standard deviation
    residuals = [values[i] - seasonal_means[i % period] for i in range(n)]
    residual_std = math.sqrt(sum(r ** 2 for r in residuals) / n) or 1.0

    # Detect anomalies
    result = []
    for i in range(n):
        residual = abs(values[i] - seasonal_means[i % period])
        result.append(residual > threshold * residual_std)

    return result


# --- Aggregate Anomaly Detector ---

def aggregate_detect(
    detectors_results: list[list[bool]],
    method: str = "any",
    threshold: int = 1,
) -> list[bool]:
    """Aggregate results from multiple detectors.

    Args:
        detectors_results: List of boolean masks from different detectors
        method: 'any', 'all', or 'majority'
        threshold: Minimum number of detectors for 'majority'

    Returns:
        Aggregated boolean mask
    """
    if not detectors_results:
        return []

    n = len(detectors_results[0])
    result = []

    for i in range(n):
        votes = sum(1 for d in detectors_results if i < len(d) and d[i])

        if method == "any":
            result.append(votes > 0)
        elif method == "all":
            result.append(votes == len(detectors_results))
        elif method == "majority":
            thresh = threshold if threshold > 0 else len(detectors_results) // 2
            result.append(votes >= thresh)
        else:
            result.append(votes > 0)

    return result


# --- Comprehensive Analysis ---

def analyze_anomalies(
    values: list[float],
    low_threshold: Optional[float] = None,
    high_threshold: Optional[float] = None,
    window: int = 30,
    persistence: int = 3,
) -> AnomalyResult:
    """Perform comprehensive anomaly analysis on a time series.

    Combines threshold, persistence, and level shift detection.

    Args:
        values: Time series values
        low_threshold: Low threshold
        high_threshold: High threshold
        window: Window size for level shift
        persistence: Minimum anomaly duration

    Returns:
        AnomalyResult with all detected anomalies
    """
    if not values:
        return AnomalyResult()

    # Run detectors
    threshold_mask = threshold_detect(values, low_threshold, high_threshold)
    persistent_mask = persistence_detect(threshold_mask, persistence)
    level_mask = level_shift_detect(values, window)

    # Aggregate
    combined = aggregate_detect([persistent_mask, level_mask], method="any")

    # Extract anomaly events
    anomalies = []
    in_anomaly = False
    start = 0
    severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}

    for i, is_anom in enumerate(combined):
        if is_anom:
            if not in_anomaly:
                in_anomaly = True
                start = i
        else:
            if in_anomaly:
                # Determine severity
                duration = i - start
                max_val = max(values[start:i]) if values[start:i] else 0
                min_val = min(values[start:i]) if values[start:i] else 0

                if high_threshold and max_val > high_threshold * 1.5:
                    severity = "critical"
                elif high_threshold and max_val > high_threshold * 1.2:
                    severity = "high"
                elif duration > persistence * 2:
                    severity = "medium"
                else:
                    severity = "low"

                anomaly_type = "threshold" if threshold_mask[start] else "level_shift"

                anomalies.append(AnomalyEvent(
                    start_index=start,
                    end_index=i - 1,
                    severity=severity,
                    anomaly_type=anomaly_type,
                    value=max_val,
                    threshold=high_threshold,
                    description=f"{anomaly_type} anomaly: indices {start}-{i-1} ({duration} points)",
                ))
                severity_counts[severity] += 1
                in_anomaly = False

    # Handle trailing anomaly
    if in_anomaly:
        duration = len(values) - start
        anomalies.append(AnomalyEvent(
            start_index=start,
            end_index=len(values) - 1,
            severity="low",
            anomaly_type="threshold",
            description=f"Trailing anomaly at indices {start}-{len(values)-1}",
        ))

    n = len(values)
    return AnomalyResult(
        anomalies=anomalies,
        total_anomalies=len(anomalies),
        anomaly_rate=round(sum(combined) / n, 4) if n > 0 else 0.0,
        severity_counts=severity_counts,
    )

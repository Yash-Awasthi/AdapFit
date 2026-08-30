"""Outlier Detection Service.

Extracted from pyod (inspiration).
Unsupervised outlier detection: histogram-based, KNN-based, and statistical methods.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Any


@dataclass
class OutlierResult:
    index: int
    value: float
    score: float
    is_outlier: bool
    method: str


@dataclass
class OutlierDetectionResult:
    outlier_indices: list[int]
    outlier_scores: list[float]
    threshold: float
    contamination: float
    method: str
    total_samples: int
    total_outliers: int


def histogram_outlier_detection(
    values: list[float],
    contamination: float = 0.1,
    n_bins: int = 10,
) -> OutlierDetectionResult:
    """Histogram-based outlier detection (HBOS)."""
    if not values:
        return OutlierDetectionResult([], [], 0, 0, "hbos", 0, 0)
    min_val = min(values)
    max_val = max(values)
    rng = max_val - min_val if max_val > min_val else 1.0
    bin_width = rng / n_bins
    bins = [0] * n_bins
    for v in values:
        idx = min(n_bins - 1, int((v - min_val) / bin_width))
        bins[idx] += 1
    total = len(values)
    scores = []
    for v in values:
        idx = min(n_bins - 1, int((v - min_val) / bin_width))
        density = bins[idx] / total
        score = 1.0 / max(density, 0.001)
        scores.append(score)
    n_outliers = max(1, int(total * contamination))
    sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    outlier_indices = sorted_indices[:n_outliers]
    threshold = scores[sorted_indices[n_outliers - 1]] if n_outliers <= len(scores) else 0
    return OutlierDetectionResult(
        outlier_indices=outlier_indices,
        outlier_scores=[scores[i] for i in outlier_indices],
        threshold=threshold, contamination=contamination,
        method="hbos", total_samples=total, total_outliers=n_outliers,
    )


def knn_outlier_detection(
    values: list[float],
    k: int = 5,
    contamination: float = 0.1,
) -> OutlierDetectionResult:
    """KNN-based outlier detection."""
    if not values or len(values) < k:
        return OutlierDetectionResult([], [], 0, 0, "knn", len(values), 0)
    sorted_vals = sorted(values)
    scores = []
    for i, v in enumerate(values):
        dists = []
        for j, other in enumerate(values):
            if i != j:
                dists.append(abs(v - other))
        dists.sort()
        avg_dist = statistics.mean(dists[:k])
        scores.append(avg_dist)
    total = len(values)
    n_outliers = max(1, int(total * contamination))
    sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    outlier_indices = sorted_indices[:n_outliers]
    threshold = scores[sorted_indices[n_outliers - 1]] if n_outliers <= len(scores) else 0
    return OutlierDetectionResult(
        outlier_indices=outlier_indices,
        outlier_scores=[scores[i] for i in outlier_indices],
        threshold=threshold, contamination=contamination,
        method="knn", total_samples=total, total_outliers=n_outliers,
    )


def statistical_outlier_detection(
    values: list[float],
    z_threshold: float = 3.0,
) -> OutlierDetectionResult:
    """Statistical outlier detection using Z-score."""
    if not values or len(values) < 3:
        return OutlierDetectionResult([], [], 0, 0, "zscore", len(values), 0)
    mean_val = statistics.mean(values)
    std_val = statistics.stdev(values)
    if std_val <= 0:
        return OutlierDetectionResult([], [], 0, 0, "zscore", len(values), 0)
    scores = [abs(v - mean_val) / std_val for v in values]
    outlier_indices = [i for i, s in enumerate(scores) if s > z_threshold]
    return OutlierDetectionResult(
        outlier_indices=outlier_indices,
        outlier_scores=[scores[i] for i in outlier_indices],
        threshold=z_threshold, contamination=len(outlier_indices) / len(values),
        method="zscore", total_samples=len(values), total_outliers=len(outlier_indices),
    )


def iqr_outlier_detection(
    values: list[float],
    multiplier: float = 1.5,
) -> OutlierDetectionResult:
    """IQR-based outlier detection."""
    if not values:
        return OutlierDetectionResult([], [], 0, 0, "iqr", 0, 0)
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    q1 = sorted_vals[n // 4]
    q3 = sorted_vals[3 * n // 4]
    iqr = q3 - q1
    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr
    scores = []
    for v in values:
        if v < lower:
            scores.append((lower - v) / iqr if iqr > 0 else 0)
        elif v > upper:
            scores.append((v - upper) / iqr if iqr > 0 else 0)
        else:
            scores.append(0)
    outlier_indices = [i for i, v in enumerate(values) if v < lower or v > upper]
    return OutlierDetectionResult(
        outlier_indices=outlier_indices,
        outlier_scores=[scores[i] for i in outlier_indices],
        threshold=multiplier, contamination=len(outlier_indices) / len(values) if values else 0,
        method="iqr", total_samples=len(values), total_outliers=len(outlier_indices),
    )


def detect_anomalies(
    values: list[float],
    method: str = "auto",
    contamination: float = 0.1,
) -> OutlierDetectionResult:
    """Detect anomalies using the best available method."""
    if not values:
        return OutlierDetectionResult([], [], 0, 0, "none", 0, 0)
    if method == "auto":
        if len(values) < 20:
            return statistical_outlier_detection(values)
        return histogram_outlier_detection(values, contamination)
    elif method == "zscore":
        return statistical_outlier_detection(values)
    elif method == "iqr":
        return iqr_outlier_detection(values)
    elif method == "knn":
        return knn_outlier_detection(values)
    elif method == "hbos":
        return histogram_outlier_detection(values, contamination)
    return histogram_outlier_detection(values, contamination)


def detect_health_anomalies(
    heart_rate: list[float] | None = None,
    steps: list[int] | None = None,
    sleep_hours: list[float] | None = None,
    weight: list[float] | None = None,
) -> dict[str, Any]:
    """Detect health metric anomalies."""
    results = {}
    if heart_rate:
        hr_result = detect_anomalies(heart_rate, method="auto")
        results["heart_rate"] = {
            "anomalies": len(hr_result.outlier_indices),
            "indices": hr_result.outlier_indices,
            "method": hr_result.method,
        }
    if steps:
        step_result = detect_anomalies([float(s) for s in steps], method="iqr")
        results["steps"] = {
            "anomalies": len(step_result.outlier_indices),
            "indices": step_result.outlier_indices,
            "method": step_result.method,
        }
    if sleep_hours:
        sleep_result = detect_anomalies(sleep_hours, method="auto")
        results["sleep"] = {
            "anomalies": len(sleep_result.outlier_indices),
            "indices": sleep_result.outlier_indices,
            "method": sleep_result.method,
        }
    if weight:
        weight_result = detect_anomalies(weight, method="zscore")
        results["weight"] = {
            "anomalies": len(weight_result.outlier_indices),
            "indices": weight_result.outlier_indices,
            "method": weight_result.method,
        }
    total_anomalies = sum(r["anomalies"] for r in results.values())
    return {"metrics": results, "total_anomalies": total_anomalies}

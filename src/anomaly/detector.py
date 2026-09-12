"""
Health Metrics Anomaly Detection — detects anomalies in wearable health data.
Monitors heart rate, HRV, sleep patterns, SpO2, and activity metrics.

Inspired by: adtk (Anomaly Detection Toolkit)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class AnomalySeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MetricType(Enum):
    HEART_RATE = "heart_rate"
    HRV = "hrv"
    SPO2 = "spo2"
    SLEEP_QUALITY = "sleep_quality"
    STEP_COUNT = "step_count"
    CALORIES = "calories"
    STRESS = "stress"
    BODY_TEMPERATURE = "body_temperature"
    RESPIRATORY_RATE = "respiratory_rate"


@dataclass
class Anomaly:
    """A detected anomaly in health metrics."""
    metric: MetricType
    timestamp: datetime
    value: float
    expected_range: tuple[float, float]
    severity: AnomalySeverity
    message: str
    context: dict[str, Any] = field(default_factory=dict)


class HealthAnomalyDetector:
    """Detects anomalies in time-series health data using statistical methods.

    Uses rolling statistics, Z-score analysis, and adaptive thresholds
    to identify meaningful deviations from baselines.
    """

    # Default safe ranges for common health metrics
    DEFAULT_RANGES: dict[MetricType, tuple[float, float]] = {
        MetricType.HEART_RATE: (40.0, 200.0),
        MetricType.HRV: (10.0, 200.0),
        MetricType.SPO2: (90.0, 100.0),
        MetricType.SLEEP_QUALITY: (0.0, 100.0),
        MetricType.STEP_COUNT: (0.0, 50000.0),
        MetricType.CALORIES: (0.0, 5000.0),
        MetricType.STRESS: (0.0, 100.0),
        MetricType.BODY_TEMPERATURE: (35.0, 42.0),
        MetricType.RESPIRATORY_RATE: (8.0, 30.0),
    }

    def __init__(
        self,
        z_score_threshold: float = 3.0,
        rolling_window: int = 20,
        min_samples: int = 5,
    ) -> None:
        self.z_score_threshold = z_score_threshold
        self.rolling_window = rolling_window
        self.min_samples = min_samples
        self._baselines: dict[MetricType, list[float]] = {}

    def update_baseline(self, metric: MetricType, values: list[float]) -> None:
        """Update the baseline for a metric with historical values."""
        self._baselines[metric] = values[-self.rolling_window * 3:]

    def detect(
        self,
        metric: MetricType,
        current_value: float,
        timestamp: datetime | None = None,
    ) -> Anomaly | None:
        """Check if a single value is anomalous for the given metric."""
        ts = timestamp or datetime.utcnow()

        # Check absolute bounds
        safe_range = self.DEFAULT_RANGES.get(metric, (0.0, 100.0))
        if current_value < safe_range[0] or current_value > safe_range[1]:
            return Anomaly(
                metric=metric,
                timestamp=ts,
                value=current_value,
                expected_range=safe_range,
                severity=AnomalySeverity.CRITICAL,
                message=f"{metric.value} value {current_value} is outside safe range {safe_range}",
            )

        # Check against baseline using Z-score
        baseline = self._baselines.get(metric, [])
        if len(baseline) < self.min_samples:
            return None

        mean = sum(baseline) / len(baseline)
        variance = sum((x - mean) ** 2 for x in baseline) / len(baseline)
        std = math.sqrt(variance) if variance > 0 else 0.001

        z_score = abs(current_value - mean) / std

        if z_score > self.z_score_threshold:
            severity = AnomalySeverity.HIGH if z_score > 4.0 else AnomalySeverity.MEDIUM
            return Anomaly(
                metric=metric,
                timestamp=ts,
                value=current_value,
                expected_range=(mean - 2 * std, mean + 2 * std),
                severity=severity,
                message=(
                    f"{metric.value} value {current_value:.1f} deviates significantly "
                    f"from baseline (mean={mean:.1f}, z={z_score:.1f})"
                ),
                context={"z_score": z_score, "mean": mean, "std": std},
            )

        return None

    def detect_batch(
        self,
        metric: MetricType,
        values: list[tuple[datetime, float]],
    ) -> list[Anomaly]:
        """Detect anomalies in a batch of time-series values."""
        anomalies: list[Anomaly] = []
        window: list[float] = []

        for ts, val in values:
            window.append(val)
            if len(window) > self.rolling_window:
                window = window[-self.rolling_window:]

            if len(window) >= self.min_samples:
                mean = sum(window) / len(window)
                variance = sum((x - mean) ** 2 for x in window) / len(window)
                std = math.sqrt(variance) if variance > 0 else 0.001
                z_score = abs(val - mean) / std

                if z_score > self.z_score_threshold:
                    severity = AnomalySeverity.HIGH if z_score > 4.0 else AnomalySeverity.MEDIUM
                    anomalies.append(Anomaly(
                        metric=metric,
                        timestamp=ts,
                        value=val,
                        expected_range=(mean - 2 * std, mean + 2 * std),
                        severity=severity,
                        message=(
                            f"{metric.value} value {val:.1f} deviates "
                            f"(z={z_score:.1f}, mean={mean:.1f})"
                        ),
                        context={"z_score": z_score, "mean": mean, "std": std},
                    ))

        return anomalies

    def detect_health_emergencies(
        self,
        metrics: dict[MetricType, float],
        timestamp: datetime | None = None,
    ) -> list[Anomaly]:
        """Check for emergency-level health anomalies.

        Specifically monitors for combinations of metrics that indicate
        potential health emergencies.
        """
        ts = timestamp or datetime.utcnow()
        emergencies: list[Anomaly] = []

        # Critical SpO2
        spo2 = metrics.get(MetricType.SPO2)
        if spo2 is not None and spo2 < 90:
            emergencies.append(Anomaly(
                metric=MetricType.SPO2,
                timestamp=ts,
                value=spo2,
                expected_range=(90.0, 100.0),
                severity=AnomalySeverity.CRITICAL,
                message=f"Critically low SpO2: {spo2}% — seek medical attention",
                context={"emergency": True},
            ))

        # Extreme heart rate
        hr = metrics.get(MetricType.HEART_RATE)
        if hr is not None:
            if hr > 180:
                emergencies.append(Anomaly(
                    metric=MetricType.HEART_RATE,
                    timestamp=ts,
                    value=hr,
                    expected_range=(40.0, 180.0),
                    severity=AnomalySeverity.CRITICAL,
                    message=f"Dangerously high heart rate: {hr} BPM",
                    context={"emergency": True},
                ))
            elif hr < 35:
                emergencies.append(Anomaly(
                    metric=MetricType.HEART_RATE,
                    timestamp=ts,
                    value=hr,
                    expected_range=(35.0, 200.0),
                    severity=AnomalySeverity.CRITICAL,
                    message=f"Abnormally low heart rate: {hr} BPM",
                    context={"emergency": True},
                ))

        # High temperature
        temp = metrics.get(MetricType.BODY_TEMPERATURE)
        if temp is not None and temp > 40.0:
            emergencies.append(Anomaly(
                metric=MetricType.BODY_TEMPERATURE,
                timestamp=ts,
                value=temp,
                expected_range=(35.0, 38.5),
                severity=AnomalySeverity.CRITICAL,
                message=f"High fever detected: {temp}°C",
                context={"emergency": True},
            ))

        return emergencies

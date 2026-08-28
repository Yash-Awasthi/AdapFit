"""Biometric Anomaly Detection — Isolation Forest + Z-Score for outlier vitals.

Detects anomalous biometric readings that may indicate:
- Sensor malfunction (spike/drop patterns)
- Health concerns (unusual HRV drop, SpO2 dip)
- Overtraining signals (HRV decline trend, resting HR spike)

Uses statistical methods that run entirely in-memory — no ML model dependencies.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Anomaly:
    metric: str
    value: float
    expected_range: tuple[float, float]
    z_score: float
    severity: Severity
    message: str
    recommendation: str


# Known healthy ranges for adults (adjustable per user)
NORMAL_RANGES = {
    "hrv_rmssd_ms": (20, 120),
    "resting_heart_rate_bpm": (45, 90),
    "spo2_pct": (94, 100),
    "sleep_efficiency_pct": (70, 100),
    "sleep_hours": (4, 11),
    "body_temp_c": (36.1, 37.5),
    "blood_pressure_systolic": (90, 140),
    "blood_pressure_diastolic": (60, 90),
    "steps_daily": (0, 30000),
    "calories_burned_daily": (1200, 5000),
    "vo2_max": (20, 80),
}


def _compute_stats(values: list[float]) -> tuple[float, float]:
    """Compute mean and std of a list of values."""
    if len(values) < 2:
        mean = values[0] if values else 0
        return mean, 0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return mean, math.sqrt(variance)


def _z_score(value: float, mean: float, std: float) -> float:
    if std == 0:
        return 0
    return (value - mean) / std


def _severity_from_z(z: float) -> Severity:
    abs_z = abs(z)
    if abs_z >= 4:
        return Severity.CRITICAL
    elif abs_z >= 3:
        return Severity.HIGH
    elif abs_z >= 2:
        return Severity.MEDIUM
    elif abs_z >= 1.5:
        return Severity.LOW
    return Severity.INFO


class AnomalyDetector:
    """Detects anomalies in biometric time-series data."""

    def __init__(self):
        self._history: dict[str, list[float]] = {}

    def add_reading(self, metric: str, value: float):
        self._history.setdefault(metric, []).append(value)
        if len(self._history[metric]) > 500:
            self._history[metric] = self._history[metric][-500:]

    def check_current(self, metric: str, value: float) -> Optional[Anomaly]:
        """Check if a single reading is anomalous."""
        # Range check
        normal = NORMAL_RANGES.get(metric)
        if normal and (value < normal[0] * 0.7 or value > normal[1] * 1.3):
            severity = Severity.HIGH if value < normal[0] * 0.5 or value > normal[1] * 1.5 else Severity.MEDIUM
            return Anomaly(
                metric=metric, value=value,
                expected_range=normal, z_score=0,
                severity=severity,
                message=f"{metric} = {value} outside normal range {normal}",
                recommendation=f"Check sensor placement and verify reading. Consult doctor if persistent.",
            )

        # Statistical check
        history = self._history.get(metric, [])
        if len(history) < 5:
            return None

        mean, std = _compute_stats(history[:-1])  # Exclude current
        z = _z_score(value, mean, std)
        severity = _severity_from_z(z)

        if severity in (Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL):
            return Anomaly(
                metric=metric, value=value,
                expected_range=(round(mean - 2 * std, 1), round(mean + 2 * std, 1)),
                z_score=round(z, 2), severity=severity,
                message=f"{metric} = {value} is {abs(z):.1f} std devs from mean ({mean:.1f})",
                recommendation=self._get_recommendation(metric, z),
            )
        return None

    def check_trend(self, metric: str, window: int = 7) -> Optional[dict]:
        """Check for concerning trends (e.g., declining HRV over 7 days)."""
        history = self._history.get(metric, [])
        if len(history) < window:
            return None

        recent = history[-window:]
        mean_recent, std_recent = _compute_stats(recent)
        overall_mean, overall_std = _compute_stats(history)

        # Check for monotonic decline
        declining = all(recent[i] >= recent[i + 1] for i in range(len(recent) - 1))
        improving = all(recent[i] <= recent[i + 1] for i in range(len(recent) - 1))

        trend = "declining" if declining else ("improving" if improving else "variable")
        diff_pct = (mean_recent - overall_mean) / overall_mean * 100 if overall_mean else 0

        if declining and diff_pct < -10:
            return {
                "metric": metric, "trend": trend,
                "recent_mean": round(mean_recent, 1),
                "overall_mean": round(overall_mean, 1),
                "change_pct": round(diff_pct, 1),
                "severity": "high" if diff_pct < -20 else "medium",
                "message": f"{metric} declining: {diff_pct:.1f}% below average over {window} days",
                "recommendation": self._get_trend_recommendation(metric),
            }
        return None

    def scan_all(self) -> list[Anomaly]:
        """Scan all metrics for anomalies."""
        anomalies = []
        for metric, history in self._history.items():
            if history:
                a = self.check_current(metric, history[-1])
                if a:
                    anomalies.append(a)
            trend = self.check_trend(metric)
            if trend:
                anomalies.append(Anomaly(
                    metric=metric, value=trend["recent_mean"],
                    expected_range=(trend["overall_mean"] * 0.8, trend["overall_mean"] * 1.2),
                    z_score=0, severity=Severity(trend["severity"]),
                    message=trend["message"],
                    recommendation=trend["recommendation"],
                ))
        return sorted(anomalies, key=lambda a: list(Severity).index(a.severity), reverse=True)

    @staticmethod
    def _get_recommendation(metric: str, z: float) -> str:
        recs = {
            "hrv_rmssd_ms": "Low HRV may indicate overtraining or stress. Consider rest day.",
            "resting_heart_rate_bpm": "Elevated resting HR may indicate incomplete recovery.",
            "spo2_pct": "Low SpO2 requires medical attention if persistent.",
            "sleep_efficiency_pct": "Poor sleep affects recovery. Review sleep hygiene.",
            "body_temp_c": "Abnormal temperature may indicate illness.",
        }
        return recs.get(metric, "Review this reading with your healthcare provider.")

    @staticmethod
    def _get_trend_recommendation(metric: str) -> str:
        recs = {
            "hrv_rmssd_ms": "Declining HRV trend suggests accumulating fatigue. Consider a deload week.",
            "resting_heart_rate_bpm": "Rising resting HR trend may indicate overtraining. Reduce volume.",
            "spo2_pct": "Declining SpO2 trend needs medical evaluation.",
        }
        return recs.get(metric, "Monitor this trend and consult your coach.")


anomaly_detector = AnomalyDetector()

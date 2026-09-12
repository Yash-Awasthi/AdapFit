"""
Biomarker Tracker — tracks bloodwork biomarkers over time with trend analysis.
Provides reference ranges, flagging of abnormal values, and trend visualization data.

Inspired by: biomarkerdash (bloodwork biomarker dashboard)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class BiomarkerStatus(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL_LOW = "critical_low"
    CRITICAL_HIGH = "critical_high"


class TrendDirection(Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"


@dataclass
class ReferenceRange:
    """Reference range for a biomarker."""
    optimal_low: float
    optimal_high: float
    normal_low: float
    normal_high: float
    critical_low: float | None = None
    critical_high: float | None = None
    unit: str = ""


@dataclass
class BiomarkerReading:
    """A single biomarker measurement."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    lab_name: str = ""
    notes: str = ""


@dataclass
class BiomarkerTrend:
    """Trend analysis for a specific biomarker."""
    name: str
    current_value: float
    previous_value: float | None
    change_pct: float
    direction: TrendDirection
    status: BiomarkerStatus
    reference: ReferenceRange
    readings_count: int
    data_points: list[dict[str, Any]] = field(default_factory=list)


class BiomarkerTracker:
    """Tracks and analyzes bloodwork biomarkers over time."""

    # Common biomarker reference ranges
    DEFAULT_REFERENCES: dict[str, ReferenceRange] = {
        "testosterone_total": ReferenceRange(
            optimal_low=500, optimal_high=900,
            normal_low=264, normal_high=916,
            critical_low=150, critical_high=1200,
            unit="ng/dL",
        ),
        "free_testosterone": ReferenceRange(
            optimal_low=15, optimal_high=25,
            normal_low=5, normal_high=21,
            unit="pg/mL",
        ),
        "cortisol": ReferenceRange(
            optimal_low=6, optimal_high=18,
            normal_low=2.3, normal_high=19.5,
            critical_high=25,
            unit="µg/dL",
        ),
        "tsh": ReferenceRange(
            optimal_low=0.5, optimal_high=2.5,
            normal_low=0.4, normal_high=4.0,
            critical_high=10,
            unit="mIU/L",
        ),
        "fasting_glucose": ReferenceRange(
            optimal_low=70, optimal_high=90,
            normal_low=70, normal_high=100,
            critical_high=126,
            unit="mg/dL",
        ),
        "hba1c": ReferenceRange(
            optimal_low=4.0, optimal_high=5.4,
            normal_low=4.0, normal_high=5.7,
            critical_high=6.5,
            unit="%",
        ),
        "vitamin_d": ReferenceRange(
            optimal_low=40, optimal_high=80,
            normal_low=20, normal_high=100,
            critical_low=10,
            unit="ng/mL",
        ),
        "ferritin": ReferenceRange(
            optimal_low=40, optimal_high=200,
            normal_low=12, normal_high=300,
            critical_low=6,
            unit="ng/mL",
        ),
        "crp": ReferenceRange(
            optimal_low=0, optimal_high=0.5,
            normal_low=0, normal_high=3.0,
            critical_high=10,
            unit="mg/L",
        ),
        "liver_ast": ReferenceRange(
            optimal_low=10, optimal_high=30,
            normal_low=8, normal_high=48,
            critical_high=200,
            unit="U/L",
        ),
        "liver_alt": ReferenceRange(
            optimal_low=10, optimal_high=35,
            normal_low=7, normal_high=56,
            critical_high=200,
            unit="U/L",
        ),
        "total_cholesterol": ReferenceRange(
            optimal_low=125, optimal_high=200,
            normal_low=0, normal_high=200,
            critical_high=240,
            unit="mg/dL",
        ),
        "ldl": ReferenceRange(
            optimal_low=0, optimal_high=100,
            normal_low=0, normal_high=130,
            critical_high=160,
            unit="mg/dL",
        ),
        "hdl": ReferenceRange(
            optimal_low=40, optimal_high=100,
            normal_low=40, normal_high=999,
            critical_low=20,
            unit="mg/dL",
        ),
        "triglycerides": ReferenceRange(
            optimal_low=0, optimal_high=100,
            normal_low=0, normal_high=150,
            critical_high=500,
            unit="mg/dL",
        ),
        "iron": ReferenceRange(
            optimal_low=60, optimal_high=170,
            normal_low=60, normal_high=170,
            critical_low=30, critical_high=450,
            unit="µg/dL",
        ),
        "b12": ReferenceRange(
            optimal_low=400, optimal_high=900,
            normal_low=200, normal_high=900,
            critical_low=100,
            unit="pg/mL",
        ),
    }

    def __init__(self) -> None:
        self._readings: dict[str, list[BiomarkerReading]] = {}
        self._references: dict[str, ReferenceRange] = dict(self.DEFAULT_REFERENCES)

    def register_reference(self, name: str, ref: ReferenceRange) -> None:
        """Register or update a reference range for a biomarker."""
        self._references[name] = ref

    def add_reading(self, reading: BiomarkerReading) -> None:
        """Add a biomarker reading."""
        self._readings.setdefault(reading.name, []).append(reading)
        # Keep sorted by timestamp
        self._readings[reading.name].sort(key=lambda r: r.timestamp)

    def get_status(self, name: str, value: float) -> BiomarkerStatus:
        """Determine the status of a biomarker value."""
        ref = self._references.get(name)
        if not ref:
            return BiomarkerStatus.NORMAL

        if ref.critical_low is not None and value <= ref.critical_low:
            return BiomarkerStatus.CRITICAL_LOW
        if ref.critical_high is not None and value >= ref.critical_high:
            return BiomarkerStatus.CRITICAL_HIGH
        if value < ref.normal_low:
            return BiomarkerStatus.LOW
        if value > ref.normal_high:
            return BiomarkerStatus.HIGH
        return BiomarkerStatus.NORMAL

    def get_trend(self, name: str) -> BiomarkerTrend | None:
        """Get trend analysis for a biomarker."""
        readings = self._readings.get(name, [])
        if not readings:
            return None

        current = readings[-1]
        previous = readings[-2] if len(readings) >= 2 else None

        if previous:
            change_pct = ((current.value - previous.value) / max(abs(previous.value), 0.001)) * 100
        else:
            change_pct = 0

        # Determine trend direction
        if len(readings) >= 3:
            recent = [r.value for r in readings[-3:]]
            diffs = [recent[i+1] - recent[i] for i in range(len(recent)-1)]
            if all(d > 0 for d in diffs):
                direction = TrendDirection.DECLINING if name in ("cortisol", "crp", "hba1c", "fasting_glucose", "ldl") else TrendDirection.IMPROVING
            elif all(d < 0 for d in diffs):
                direction = TrendDirection.IMPROVING if name in ("cortisol", "crp", "hba1c", "fasting_glucose", "ldl") else TrendDirection.DECLINING
            elif max(abs(d) for d in diffs) > abs(sum(diffs) / len(diffs)) * 2:
                direction = TrendDirection.VOLATILE
            else:
                direction = TrendDirection.STABLE
        else:
            direction = TrendDirection.STABLE

        status = self.get_status(name, current.value)
        ref = self._references.get(name, ReferenceRange(0, 100, 0, 100, unit=""))

        data_points = [
            {"timestamp": r.timestamp.isoformat(), "value": r.value, "unit": r.unit}
            for r in readings
        ]

        return BiomarkerTrend(
            name=name,
            current_value=current.value,
            previous_value=previous.value if previous else None,
            change_pct=round(change_pct, 1),
            direction=direction,
            status=status,
            reference=ref,
            readings_count=len(readings),
            data_points=data_points,
        )

    def get_all_trends(self) -> list[BiomarkerTrend]:
        """Get trends for all tracked biomarkers."""
        trends = []
        for name in self._readings:
            trend = self.get_trend(name)
            if trend:
                trends.append(trend)
        return trends

    def get_abnormal_readings(self) -> list[dict[str, Any]]:
        """Get all biomarkers with abnormal status."""
        abnormal = []
        for name in self._readings:
            readings = self._readings[name]
            if readings:
                latest = readings[-1]
                status = self.get_status(name, latest.value)
                if status != BiomarkerStatus.NORMAL:
                    abnormal.append({
                        "name": name,
                        "value": latest.value,
                        "unit": latest.unit,
                        "status": status.value,
                        "timestamp": latest.timestamp.isoformat(),
                    })
        return abnormal

    def get_health_score(self) -> dict[str, Any]:
        """Compute an overall health score from all biomarkers (0-100)."""
        scores = []
        for name, readings in self._readings.items():
            if not readings:
                continue
            ref = self._references.get(name)
            if not ref:
                continue

            value = readings[-1].value
            # Score based on distance from optimal range
            if ref.optimal_low <= value <= ref.optimal_high:
                score = 100
            elif ref.normal_low <= value <= ref.normal_high:
                # Distance from optimal
                if value < ref.optimal_low:
                    dist = (ref.optimal_low - value) / max(ref.optimal_low - ref.normal_low, 1)
                else:
                    dist = (value - ref.optimal_high) / max(ref.normal_high - ref.optimal_high, 1)
                score = max(60, 100 - dist * 40)
            else:
                score = max(0, 40 - abs(value - (ref.optimal_low + ref.optimal_high) / 2) / 10)

            scores.append(score)

        overall = sum(scores) / max(len(scores), 1) if scores else 50

        return {
            "health_score": round(overall, 1),
            "biomarkers_scored": len(scores),
            "status": "excellent" if overall >= 85 else "good" if overall >= 70 else "fair" if overall >= 55 else "needs_attention",
        }

"""
Unified Health Platform Bridge for ZFIT
Extracted from: capacitor-health (cross-platform health data plugin)
Patterns: HealthKit + Health Connect unified API, metric reading/writing,
          cross-platform data types, steps/distance/calories/heart rate/weight
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class HealthPlatform(Enum):
    HEALTHKIT = "healthkit"
    HEALTH_CONNECT = "health_connect"
    WEB = "web"


class MetricType(Enum):
    STEPS = "steps"
    DISTANCE = "distance"
    CALORIES_BURNED = "calories_burned"
    HEART_RATE = "heart_rate"
    WEIGHT = "weight"
    SLEEP_ANALYSIS = "sleep_analysis"
    BLOOD_OXYGEN = "blood_oxygen"
    BLOOD_PRESSURE_SYSTOLIC = "blood_pressure_systolic"
    BLOOD_PRESSURE_DIASTOLIC = "blood_pressure_diastolic"
    RESTING_HEART_RATE = "resting_heart_rate"
    HRV = "heart_rate_variability"
    ACTIVE_ENERGY = "active_energy"
    BASAL_ENERGY = "basal_energy"
    FLIGHTS_CLIMBED = "flights_climbed"
    BODY_TEMPERATURE = "body_temperature"


METRIC_UNITS = {
    MetricType.STEPS: "count",
    MetricType.DISTANCE: "meters",
    MetricType.CALORIES_BURNED: "kcal",
    MetricType.HEART_RATE: "bpm",
    MetricType.WEIGHT: "kg",
    MetricType.SLEEP_ANALYSIS: "hours",
    MetricType.BLOOD_OXYGEN: "%",
    MetricType.BLOOD_PRESSURE_SYSTOLIC: "mmHg",
    MetricType.BLOOD_PRESSURE_DIASTOLIC: "mmHg",
    MetricType.RESTING_HEART_RATE: "bpm",
    MetricType.HRV: "ms",
    MetricType.ACTIVE_ENERGY: "kcal",
    MetricType.BASAL_ENERGY: "kcal",
    MetricType.FLIGHTS_CLIMBED: "count",
    MetricType.BODY_TEMPERATURE: "°C",
}


@dataclass
class HealthDataPoint:
    metric_type: MetricType
    value: float
    unit: str
    start_date: datetime
    end_date: datetime
    source: str = ""
    metadata: dict = None


@dataclass
class HealthQuery:
    metric_types: list[MetricType]
    start_date: datetime
    end_date: datetime
    limit: int = 100
    sort_order: str = "desc"


class HealthPlatformBridge:
    """Unified bridge for reading/writing health data across platforms."""

    def __init__(self, platform: HealthPlatform = HealthPlatform.WEB):
        self.platform = platform
        self.data_store: list[HealthDataPoint] = []

    def request_permissions(self, metric_types: list[MetricType]) -> dict:
        """Request permissions for health data access."""
        permissions = {}
        for mt in metric_types:
            permissions[mt.value] = {
                "read": True,
                "write": True,
                "granted": True,
            }
        return {"platform": self.platform.value, "permissions": permissions}

    def read_data(self, query: HealthQuery) -> list[HealthDataPoint]:
        """Read health data for the given query."""
        results = []
        for dp in self.data_store:
            if dp.metric_type in query.metric_types:
                if query.start_date <= dp.start_date <= query.end_date:
                    results.append(dp)
        results.sort(key=lambda x: x.start_date, reverse=(query.sort_order == "desc"))
        return results[:query.limit]

    def write_data(self, data_point: HealthDataPoint) -> bool:
        """Write a health data point."""
        self.data_store.append(data_point)
        return True

    def write_batch(self, data_points: list[HealthDataPoint]) -> int:
        """Write multiple health data points. Returns count written."""
        self.data_store.extend(data_points)
        return len(data_points)

    def aggregate(self, metric_type: MetricType, start_date: datetime, end_date: datetime) -> dict:
        """Aggregate data for a metric type over a date range."""
        relevant = [
            dp for dp in self.data_store
            if dp.metric_type == metric_type and start_date <= dp.start_date <= end_date
        ]

        if not relevant:
            return {"metric": metric_type.value, "count": 0, "sum": 0, "avg": 0, "min": 0, "max": 0}

        values = [dp.value for dp in relevant]
        return {
            "metric": metric_type.value,
            "unit": METRIC_UNITS.get(metric_type, ""),
            "count": len(values),
            "sum": round(sum(values), 2),
            "avg": round(sum(values) / len(values), 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
        }

    def get_daily_summary(self, date: datetime) -> dict:
        """Get a summary of all metrics for a specific day."""
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(hour=23, minute=59, second=59)

        summary = {}
        for mt in MetricType:
            agg = self.aggregate(mt, start, end)
            if agg["count"] > 0:
                summary[mt.value] = agg

        return {"date": date.date().isoformat(), "metrics": summary}

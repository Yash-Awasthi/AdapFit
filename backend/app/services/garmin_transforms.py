"""Garmin Data Transforms Service.

Extracted from garmin-stats-ai (inspiration).
Pure Garmin JSON → data point transforms with proper timestamp handling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


@dataclass
class DataPoint:
    measurement: str
    time: str
    tags: dict[str, str]
    fields: dict[str, Any]


@dataclass
class DailyStats:
    date: str
    active_calories: int = 0
    bmr_calories: int = 0
    steps: int = 0
    distance_meters: float = 0.0
    floors_climbed: int = 0
    resting_heart_rate: int = 0
    max_heart_rate: int = 0
    avg_heart_rate: int = 0
    stress_score: int = 0
    body_battery_max: int = 0
    body_battery_min: int = 0
    vo2_max: float = 0.0


@dataclass
class SleepSummary:
    date: str
    total_sleep_seconds: int = 0
    deep_sleep_seconds: int = 0
    light_sleep_seconds: int = 0
    rem_sleep_seconds: int = 0
    awake_seconds: int = 0
    sleep_score: int = 0
    sleep_start: str = ""
    sleep_end: str = ""
    respiration_avg: float = 0.0


@dataclass
class HeartRateSample:
    timestamp: str
    heart_rate: int
    activity_type: str = ""


@dataclass
class StressSample:
    timestamp: str
    stress_level: int
    stress_type: str = ""  # "high", "low", "medium"


MENSTRUAL_PHASE_NAMES = {
    1: "menstrual", 2: "follicular", 3: "ovulatory", 4: "luteal"
}


def parse_garmin_timestamp(ts: Any) -> str:
    """Parse Garmin timestamp from various formats."""
    if isinstance(ts, (int, float)):
        return datetime.utcfromtimestamp(ts / 1000).isoformat()
    if isinstance(ts, str):
        try:
            dt = datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")
            return dt.isoformat()
        except ValueError:
            return ts
    return ""


def transform_daily_stats(stats_json: dict, date_str: str, device_name: str = "unknown") -> DataPoint:
    """Transform Garmin daily stats JSON to data point."""
    noon_time = datetime.strptime(date_str, "%Y-%m-%d").replace(hour=12)
    return DataPoint(
        measurement="DailyStats",
        time=noon_time.isoformat(),
        tags={"Device": device_name, "Database_Name": "GarminDB"},
        fields={
            "activeKilocalories": stats_json.get("activeKilocalories", 0),
            "bmrKilocalories": stats_json.get("bmrKilocalories", 0),
            "steps": stats_json.get("steps", 0),
            "distanceMeters": stats_json.get("totalDistanceMeters", 0),
            "floorsAscended": stats_json.get("floorsAscended", 0),
            "restingHeartRateInBpm": stats_json.get("restingHeartRateInBpm", 0),
            "maxHeartRateInBpm": stats_json.get("maxHeartRateInBpm", 0),
            "averageHeartRateInBpm": stats_json.get("averageHeartRateInBpm", 0),
            "averageStressLevel": stats_json.get("averageStressLevel", 0),
            "bodyBatteryChargedValue": stats_json.get("bodyBatteryChargedValue", 0),
            "bodyBatteryDrainedValue": stats_json.get("bodyBatteryDrainedValue", 0),
            "vo2MaxValue": stats_json.get("vo2MaxValue", 0),
        },
    )


def transform_sleep_summary(sleep_json: dict, device_name: str = "unknown") -> DataPoint:
    """Transform Garmin sleep summary JSON to data point."""
    sleep_end_ts = sleep_json.get("sleepEndTimestampGMT", 0)
    time_str = parse_garmin_timestamp(sleep_end_ts)
    return DataPoint(
        measurement="SleepSummary",
        time=time_str,
        tags={"Device": device_name},
        fields={
            "totalSleepSeconds": sleep_json.get("sleepTimeSeconds", 0),
            "deepSleepSeconds": sleep_json.get("deepSleepSeconds", 0),
            "lightSleepSeconds": sleep_json.get("lightSleepSeconds", 0),
            "remSleepSeconds": sleep_json.get("remSleepSeconds", 0),
            "awakeSeconds": sleep_json.get("awakeSleepSeconds", 0),
            "sleepScore": sleep_json.get("sleepScores", {}).get("overall", {}).get("value", 0),
            "respirationAvg": sleep_json.get("averageRespirationValue", 0),
        },
    )


def transform_heart_rate(hr_data: list[dict]) -> list[DataPoint]:
    """Transform Garmin heart rate data to data points."""
    points = []
    for sample in hr_data:
        ts = parse_garmin_timestamp(sample.get("timestamp", 0))
        points.append(DataPoint(
            measurement="HeartRate",
            time=ts,
            tags={"Database_Name": "GarminDB"},
            fields={
                "heartRate": sample.get("heartRate", 0),
                "activityType": sample.get("activityType", ""),
            },
        ))
    return points


def transform_stress(stress_data: list[dict]) -> list[DataPoint]:
    """Transform Garmin stress data to data points."""
    points = []
    for sample in stress_data:
        ts = parse_garmin_timestamp(sample.get("timestamp", 0))
        stress_level = sample.get("stressLevel", 0)
        if stress_level <= 26:
            stress_type = "rest"
        elif stress_level <= 50:
            stress_type = "low"
        elif stress_level <= 75:
            stress_type = "medium"
        else:
            stress_type = "high"
        points.append(DataPoint(
            measurement="Stress",
            time=ts,
            tags={"Database_Name": "GarminDB"},
            fields={
                "stressLevel": stress_level,
                "stressType": stress_type,
            },
        ))
    return points


def transform_body_battery(bb_data: list[dict]) -> list[DataPoint]:
    """Transform Garmin body battery data to data points."""
    points = []
    for sample in bb_data:
        ts = parse_garmin_timestamp(sample.get("timestamp", 0))
        points.append(DataPoint(
            measurement="BodyBattery",
            time=ts,
            tags={"Database_Name": "GarminDB"},
            fields={
                "charged": sample.get("charged", 0),
                "drained": sample.get("drained", 0),
                "level": sample.get("level", 0),
            },
        ))
    return points


def transform_respiration(resp_data: list[dict]) -> list[DataPoint]:
    """Transform Garmin respiration data to data points."""
    points = []
    for sample in resp_data:
        ts = parse_garmin_timestamp(sample.get("timestamp", 0))
        points.append(DataPoint(
            measurement="Respiration",
            time=ts,
            tags={"Database_Name": "GarminDB"},
            fields={
                "respirationValue": sample.get("respirationValue", 0),
                "respirationType": sample.get("respirationType", ""),
            },
        ))
    return points


def transform_pulse_ox(pox_data: list[dict]) -> list[DataPoint]:
    """Transform Garmin Pulse Ox data to data points."""
    points = []
    for sample in pox_data:
        ts = parse_garmin_timestamp(sample.get("timestamp", 0))
        points.append(DataPoint(
            measurement="PulseOx",
            time=ts,
            tags={"Database_Name": "GarminDB"},
            fields={
                "spO2": sample.get("spO2", 0),
            },
        ))
    return points


def aggregate_daily(points: list[DataPoint], measurement: str, date_str: str) -> dict[str, Any]:
    """Aggregate data points into daily summary."""
    day_points = [p for p in points if p.measurement == measurement and p.time.startswith(date_str)]
    if not day_points:
        return {"count": 0}
    all_fields = {}
    for point in day_points:
        for key, value in point.fields.items():
            if key not in all_fields:
                all_fields[key] = []
            all_fields[key].append(value)
    aggregated = {}
    for key, values in all_fields.items():
        if all(isinstance(v, (int, float)) for v in values):
            aggregated[f"avg_{key}"] = round(sum(values) / len(values), 2)
            aggregated[f"min_{key}"] = min(values)
            aggregated[f"max_{key}"] = max(values)
        else:
            aggregated[key] = values[-1] if values else None
    aggregated["count"] = len(day_points)
    return aggregated

"""
Health Data Formatter for ZFIT
Extracted from: apple-health-grafana (Apple Health XML import and visualization)
Patterns: Sleep analysis parsing, stand hour detection, workout route formatting,
          time-series data preparation, InfluxDB-style measurement creation
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class SleepState(Enum):
    DEEP = 0
    CORE = 1
    REM = 2
    IN_BED = 3
    AWAKE = 4
    UNSPECIFIED = 5


class HealthMetricType(Enum):
    HEART_RATE = "HeartRate"
    RESTING_HEART_RATE = "RestingHeartRate"
    HEART_RATE_VARIABILITY = "HeartRateVariabilitySDNN"
    BLOOD_OXYGEN = "OxygenSaturation"
    BODY_TEMPERATURE = "BodyTemperature"
    STEP_COUNT = "StepCount"
    DISTANCE = "DistanceWalkingRunning"
    FLIGHTS_CLIMBED = "FlightsClimbed"
    SLEEP_ANALYSIS = "SleepAnalysis"
    STAND_HOUR = "AppleStandHour"
    WORKOUT = "Workout"
    ACTIVE_ENERGY = "ActiveEnergyBurned"
    BASAL_ENERGY = "BasalEnergyBurned"
    EXERCISE_MINUTES = "AppleExerciseTime"


SLEEP_STATE_NAMES = {
    SleepState.DEEP: "Deep",
    SleepState.CORE: "Core",
    SleepState.REM: "REM",
    SleepState.IN_BED: "InBed",
    SleepState.AWAKE: "Awake",
    SleepState.UNSPECIFIED: "Unspecified",
}

SLEEP_VALUE_MAP = {
    "HKCategoryValueSleepAnalysisAsleepDeep": SleepState.DEEP,
    "HKCategoryValueSleepAnalysisAsleepCore": SleepState.CORE,
    "HKCategoryValueSleepAnalysisAsleepREM": SleepState.REM,
    "HKCategoryValueSleepAnalysisInBed": SleepState.IN_BED,
    "HKCategoryValueSleepAnalysisAwake": SleepState.AWAKE,
}


@dataclass
class HealthRecord:
    measurement: str
    time: int  # unix timestamp
    fields: dict
    tags: dict


def parse_float_safe(value) -> float:
    """Convert value to float or return 0."""
    try:
        return float(value)
    except (ValueError, TypeError):
        try:
            return float(int(value))
        except Exception:
            return 0.0


def parse_timestamp(date_str: str) -> int:
    """Parse ISO date string to unix timestamp."""
    try:
        return int(datetime.fromisoformat(date_str).timestamp())
    except Exception:
        return 0


def format_stand_hour(record: dict) -> list[HealthRecord]:
    """Format Apple Stand Hour data."""
    timestamp = parse_timestamp(record.get("startDate", ""))
    unit = record.get("unit", "unit")
    device = record.get("sourceName", "unknown")
    value = 1 if record.get("value") == "HKCategoryValueAppleStandHourStood" else 0
    return [HealthRecord(
        measurement="AppleStandHour",
        time=timestamp,
        fields={"value": value},
        tags={"unit": unit, "device": device},
    )]


def format_sleep_analysis(record: dict) -> list[HealthRecord]:
    """Format Sleep Analysis data into per-minute records + summary."""
    start_date = datetime.fromisoformat(record["startDate"])
    end_date = datetime.fromisoformat(record["endDate"])
    device = record.get("sourceName", "unknown")
    state = SLEEP_VALUE_MAP.get(record.get("value"), SleepState.UNSPECIFIED)
    state_name = SLEEP_STATE_NAMES.get(state, "Unspecified")

    records = []
    current = start_date
    while current <= end_date:
        records.append(HealthRecord(
            measurement=f"SleepAnalysis-{device}",
            time=int(current.timestamp()),
            fields={"value": state.value},
            tags={"state": state_name, "device": device},
        ))
        current += timedelta(minutes=1)

    records.append(HealthRecord(
        measurement="SleepAnalysis",
        time=int(end_date.timestamp()),
        fields={
            "start": int(start_date.timestamp()),
            "stop": int(end_date.timestamp()),
            "duration_minutes": int((end_date - start_date).total_seconds() / 60),
        },
        tags={"device": device, "state": state_name},
    ))
    return records


def format_heart_rate(record: dict) -> HealthRecord:
    """Format Heart Rate data."""
    return HealthRecord(
        measurement="HeartRate",
        time=parse_timestamp(record.get("startDate", "")),
        fields={"value": parse_float_safe(record.get("value", 0))},
        tags={
            "unit": record.get("unit", "bpm"),
            "device": record.get("sourceName", "unknown"),
        },
    )


def format_step_count(record: dict) -> HealthRecord:
    """Format Step Count data."""
    return HealthRecord(
        measurement="StepCount",
        time=parse_timestamp(record.get("startDate", "")),
        fields={"value": parse_float_safe(record.get("value", 0))},
        tags={
            "unit": record.get("unit", "count"),
            "device": record.get("sourceName", "unknown"),
        },
    )


def format_workout(record: dict) -> HealthRecord:
    """Format Workout data."""
    return HealthRecord(
        measurement="Workout",
        time=parse_timestamp(record.get("startDate", "")),
        fields={
            "duration": parse_float_safe(record.get("duration", 0)),
            "active_energy": parse_float_safe(record.get("activeEnergyBurned", 0)),
            "distance": parse_float_safe(record.get("totalDistance", 0)),
            "avg_heart_rate": parse_float_safe(record.get("averageHeartRate", 0)),
            "max_heart_rate": parse_float_safe(record.get("maximumHeartRate", 0)),
        },
        tags={
            "type": record.get("workoutType", "unknown"),
            "device": record.get("sourceName", "unknown"),
            "unit": record.get("durationUnit", "min"),
        },
    )


def format_blood_oxygen(record: dict) -> HealthRecord:
    """Format Blood Oxygen data."""
    return HealthRecord(
        measurement="OxygenSaturation",
        time=parse_timestamp(record.get("startDate", "")),
        fields={"value": parse_float_safe(record.get("value", 0))},
        tags={
            "unit": record.get("unit", "%"),
            "device": record.get("sourceName", "unknown"),
        },
    )


def format_hrv(record: dict) -> HealthRecord:
    """Format Heart Rate Variability data."""
    return HealthRecord(
        measurement="HeartRateVariabilitySDNN",
        time=parse_timestamp(record.get("startDate", "")),
        fields={"value": parse_float_safe(record.get("value", 0))},
        tags={
            "unit": record.get("unit", "ms"),
            "device": record.get("sourceName", "unknown"),
        },
    )


def aggregate_daily(records: list[HealthRecord], metric: str) -> dict:
    """Aggregate records into daily summaries."""
    daily: dict[int, list[HealthRecord]] = {}
    for r in records:
        if r.measurement == metric:
            day = r.time // 86400 * 86400
            daily.setdefault(day, []).append(r)

    result = []
    for day_ts, day_records in sorted(daily.items()):
        values = [r.fields.get("value", 0) for r in day_records if "value" in r.fields]
        if values:
            result.append({
                "day": day_ts,
                "count": len(values),
                "sum": sum(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
            })
    return {"metric": metric, "daily": result}


def aggregate_weekly(records: list[HealthRecord], metric: str) -> dict:
    """Aggregate records into weekly summaries."""
    daily = aggregate_daily(records, metric)
    weekly: dict[int, list[dict]] = {}
    for day in daily["daily"]:
        week = day["day"] // (7 * 86400) * 7 * 86400
        weekly.setdefault(week, []).append(day)

    result = []
    for week_ts, days in sorted(weekly.items()):
        all_sums = [d["sum"] for d in days]
        all_avgs = [d["avg"] for d in days]
        result.append({
            "week": week_ts,
            "total": sum(all_sums),
            "daily_avg": sum(all_avgs) / len(all_avgs) if all_avgs else 0,
            "days_with_data": len(days),
        })
    return {"metric": metric, "weekly": result}


def generate_health_dashboard(records: list[HealthRecord]) -> dict:
    """Generate a comprehensive health dashboard from raw records."""
    metrics = {}
    for metric_type in HealthMetricType:
        metric_records = [r for r in records if r.measurement == metric_type.value]
        if metric_records:
            values = [r.fields.get("value", 0) for r in metric_records if "value" in r.fields]
            if values:
                metrics[metric_type.value] = {
                    "count": len(values),
                    "latest": values[-1],
                    "avg": round(sum(values) / len(values), 2),
                    "min": min(values),
                    "max": max(values),
                }

    sleep_records = [r for r in records if r.measurement.startswith("SleepAnalysis-")]
    sleep_summary = {}
    if sleep_records:
        states = {}
        for r in sleep_records:
            state = r.tags.get("state", "Unknown")
            states[state] = states.get(state, 0) + 1
        sleep_summary = {
            "total_minutes": len(sleep_records),
            "stages": states,
        }

    return {
        "metrics": metrics,
        "sleep": sleep_summary,
        "total_records": len(records),
    }

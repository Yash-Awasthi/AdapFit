"""Apple Health Data Parser.

Extracted from apple-health-mcp-server (inspiration).
Parses Apple Health XML exports with streaming for memory efficiency.
Classifies health record types, computes statistics, and detects trends.

All pure functions — no database dependencies.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from io import StringIO
from typing import Any, Iterator, Optional


class RecordType(str, Enum):
    """Common Apple Health record types."""
    HEART_RATE = "HKQuantityTypeIdentifierHeartRate"
    RESTING_HEART_RATE = "HKQuantityTypeIdentifierRestingHeartRate"
    HEART_RATE_VARIABILITY = "HKQuantityTypeIdentifierHeartRateVariabilitySDNN"
    BLOOD_OXYGEN = "HKQuantityTypeIdentifierOxygenSaturation"
    BLOOD_PRESSURE_SYSTOLIC = "HKQuantityTypeIdentifierBloodPressureSystolic"
    BLOOD_PRESSURE_DIASTOLIC = "HKQuantityTypeIdentifierBloodPressureDiastolic"
    BODY_TEMPERATURE = "HKQuantityTypeIdentifierBodyTemperature"
    STEP_COUNT = "HKQuantityTypeIdentifierStepCount"
    DISTANCE = "HKQuantityTypeIdentifierDistanceWalkingRunning"
    FLIGHTS_CLIMBED = "HKQuantityTypeIdentifierFlightsClimbed"
    CALORIES_BURNED = "HKQuantityTypeIdentifierActiveEnergyBurned"
    BASAL_CALORIES = "HKQuantityTypeIdentifierBasalEnergyBurned"
    SLEEP_ANALYSIS = "HKCategoryTypeIdentifierSleepAnalysis"
    BODY_MASS = "HKQuantityTypeIdentifierBodyMass"
    BODY_FAT = "HKQuantityTypeIdentifierBodyFatPercentage"
    BMI = "HKQuantityTypeIdentifierBodyMassIndex"
    VO2_MAX = "HKQuantityTypeIdentifierVo2Max"
    WALKING_HEART_RATE = "HKQuantityTypeIdentifierWalkingHeartRateAverage"
    RESPIRATORY_RATE = "HKQuantityTypeIdentifierRespiratoryRate"
    STAIRS_SPEED = "HKQuantityTypeIdentifierStairDescentSpeed"
    WALKING_SPEED = "HKQuantityTypeIdentifierWalkingSpeed"


class WorkoutType(str, Enum):
    """Common Apple Health workout types."""
    RUNNING = "HKWorkoutActivityTypeRunning"
    WALKING = "HKWorkoutActivityTypeWalking"
    CYCLING = "HKWorkoutActivityTypeCycling"
    SWIMMING = "HKWorkoutActivityTypeSwimming"
    YOGA = "HKWorkoutActivityTypeYoga"
    STRENGTH = "HKWorkoutActivityTypeTraditionalStrengthTraining"
    HIIT = "HKWorkoutActivityTypeHighIntensityIntervalTraining"
    DANCE = "HKWorkoutActivityTypeDance"
    HIKING = "HKWorkoutActivityTypeHiking"
    ROWING = "HKWorkoutActivityTypeRowing"


@dataclass
class HealthRecord:
    """Parsed health record from Apple Health."""
    record_type: str
    value: float
    unit: str
    start_date: str
    end_date: str
    source_name: str = ""
    source_version: str = ""
    device: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class WorkoutRecord:
    """Parsed workout record from Apple Health."""
    workout_type: str
    duration: float  # seconds
    duration_unit: str
    start_date: str
    end_date: str
    total_distance: Optional[float] = None
    distance_unit: Optional[str] = None
    total_calories: Optional[float] = None
    calories_unit: Optional[str] = None
    source_name: str = ""


@dataclass
class HealthSummary:
    """Summary of health data in an export."""
    file_size_mb: float = 0.0
    record_types: list[str] = field(default_factory=list)
    workout_types: list[str] = field(default_factory=list)
    total_records: int = 0
    total_workouts: int = 0
    date_range: tuple[str, str] = ("", "")
    sources: list[str] = field(default_factory=list)


def stream_xml_records(xml_content: str, tag: str = "Record") -> Iterator[dict]:
    """Stream XML records without loading entire file into memory.

    Uses iterative parsing for memory efficiency with large exports.

    Args:
        xml_content: XML string content
        tag: XML tag to stream (default "Record")

    Yields:
        Dictionary of element attributes for each matching element
    """
    context = ET.iterparse(StringIO(xml_content), events=("start",))
    for event, elem in context:
        if elem.tag == tag:
            yield dict(elem.attrib)
        elem.clear()


def parse_health_record(elem_dict: dict) -> HealthRecord:
    """Parse a raw XML element dict into a HealthRecord.

    Args:
        elem_dict: Dictionary of XML element attributes

    Returns:
        Parsed HealthRecord
    """
    return HealthRecord(
        record_type=elem_dict.get("type", ""),
        value=float(elem_dict.get("value", "0")),
        unit=elem_dict.get("unit", ""),
        start_date=elem_dict.get("startDate", ""),
        end_date=elem_dict.get("endDate", ""),
        source_name=elem_dict.get("sourceName", ""),
        source_version=elem_dict.get("sourceVersion", ""),
        device=elem_dict.get("device", ""),
    )


def parse_workout_record(elem_dict: dict) -> WorkoutRecord:
    """Parse a raw XML element dict into a WorkoutRecord.

    Args:
        elem_dict: Dictionary of XML element attributes

    Returns:
        Parsed WorkoutRecord
    """
    return WorkoutRecord(
        workout_type=elem_dict.get("workoutActivityType", ""),
        duration=float(elem_dict.get("duration", "0")),
        duration_unit=elem_dict.get("durationUnit", "min"),
        start_date=elem_dict.get("startDate", ""),
        end_date=elem_dict.get("endDate", ""),
        total_distance=float(elem_dict["totalDistance"]) if elem_dict.get("totalDistance") else None,
        distance_unit=elem_dict.get("totalDistanceUnit", None),
        total_calories=float(elem_dict["totalEnergyBurned"]) if elem_dict.get("totalEnergyBurned") else None,
        calories_unit=elem_dict.get("totalEnergyBurnedUnit", None),
        source_name=elem_dict.get("sourceName", ""),
    )


def analyze_structure(xml_content: str) -> HealthSummary:
    """Analyze the structure of an Apple Health XML export.

    Args:
        xml_content: XML string content

    Returns:
        HealthSummary with metadata about the export
    """
    record_types = set()
    workout_types = set()
    sources = set()
    total_records = 0
    total_workouts = 0
    dates = []

    for elem_dict in stream_xml_records(xml_content, "Record"):
        total_records += 1
        rt = elem_dict.get("type", "")
        if rt:
            record_types.add(rt)
        src = elem_dict.get("sourceName", "")
        if src:
            sources.add(src)
        sd = elem_dict.get("startDate", "")
        if sd:
            dates.append(sd)

    for elem_dict in stream_xml_records(xml_content, "Workout"):
        total_workouts += 1
        wt = elem_dict.get("workoutActivityType", "")
        if wt:
            workout_types.add(wt)
        sd = elem_dict.get("startDate", "")
        if sd:
            dates.append(sd)

    return HealthSummary(
        file_size_mb=0.0,
        record_types=sorted(record_types),
        workout_types=sorted(workout_types),
        total_records=total_records,
        total_workouts=total_workouts,
        date_range=(min(dates) if dates else "", max(dates) if dates else ""),
        sources=sorted(sources),
    )


def get_records_by_type(
    xml_content: str,
    record_type: str,
    limit: int = 100,
) -> list[HealthRecord]:
    """Get all records of a specific type from XML content.

    Args:
        xml_content: XML string content
        record_type: HealthKit record type string
        limit: Maximum records to return

    Returns:
        List of HealthRecord objects
    """
    records = []
    for elem_dict in stream_xml_records(xml_content, "Record"):
        if elem_dict.get("type") == record_type:
            records.append(parse_health_record(elem_dict))
            if len(records) >= limit:
                break
    return records


def compute_statistics(records: list[HealthRecord]) -> dict:
    """Compute statistics for a list of health records.

    Args:
        records: List of HealthRecord objects

    Returns:
        Dictionary with count, mean, min, max, std, sum
    """
    if not records:
        return {
            "count": 0, "mean": 0.0, "min": 0.0, "max": 0.0,
            "std": 0.0, "sum": 0.0,
        }

    values = [r.value for r in records]
    n = len(values)
    mean_val = sum(values) / n
    min_val = min(values)
    max_val = max(values)
    sum_val = sum(values)

    if n > 1:
        variance = sum((v - mean_val) ** 2 for v in values) / (n - 1)
        std_val = variance ** 0.5
    else:
        std_val = 0.0

    return {
        "count": n,
        "mean": round(mean_val, 2),
        "min": round(min_val, 2),
        "max": round(max_val, 2),
        "std": round(std_val, 2),
        "sum": round(sum_val, 2),
    }


def compute_daily_statistics(
    records: list[HealthRecord],
) -> dict[str, dict]:
    """Compute per-day statistics for health records.

    Args:
        records: List of HealthRecord objects

    Returns:
        Dictionary mapping date strings to statistics
    """
    by_day: dict[str, list[float]] = defaultdict(list)

    for record in records:
        # Extract date portion from ISO datetime
        date_str = record.start_date[:10] if record.start_date else "unknown"
        by_day[date_str].append(record.value)

    result = {}
    for date, values in sorted(by_day.items()):
        n = len(values)
        result[date] = {
            "count": n,
            "mean": round(sum(values) / n, 2) if n else 0.0,
            "min": round(min(values), 2) if values else 0.0,
            "max": round(max(values), 2) if values else 0.0,
            "sum": round(sum(values), 2) if values else 0.0,
        }

    return result


def compute_weekly_trends(
    records: list[HealthRecord],
    weeks: int = 8,
) -> list[dict]:
    """Compute weekly trend data for health records.

    Args:
        records: List of HealthRecord objects
        weeks: Number of weeks to analyze

    Returns:
        List of weekly statistics dictionaries
    """
    # Group by week
    by_week: dict[str, list[float]] = defaultdict(list)

    for record in records:
        try:
            dt_str = record.start_date[:19]
            if "+" in dt_str or dt_str.endswith("Z"):
                dt_str = dt_str.rstrip("Z").split("+")[0]
            dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
            # ISO week
            week_key = dt.strftime("%Y-W%U")
            by_week[week_key].append(record.value)
        except (ValueError, IndexError):
            continue

    # Take last N weeks
    sorted_weeks = sorted(by_week.keys())[-weeks:]

    trends = []
    for week in sorted_weeks:
        values = by_week[week]
        n = len(values)
        trends.append({
            "week": week,
            "count": n,
            "mean": round(sum(values) / n, 2) if n else 0.0,
            "min": round(min(values), 2) if values else 0.0,
            "max": round(max(values), 2) if values else 0.0,
        })

    return trends


def detect_anomalies(
    records: list[HealthRecord],
    z_threshold: float = 2.0,
) -> list[HealthRecord]:
    """Detect anomalous health records using z-score.

    Args:
        records: List of HealthRecord objects
        z_threshold: Number of standard deviations for anomaly (default 2.0)

    Returns:
        List of anomalous records
    """
    if len(records) < 2:
        return []

    values = [r.value for r in records]
    n = len(values)
    mean_val = sum(values) / n
    variance = sum((v - mean_val) ** 2 for v in values) / max(n - 1, 1)
    std_val = variance ** 0.5

    if std_val == 0:
        return []

    return [
        record for record in records
        if abs((record.value - mean_val) / std_val) > z_threshold
    ]


def classify_sleep_stage(category_value: int) -> str:
    """Classify Apple Health sleep analysis category value.

    Args:
        category_value: HKCategoryValueSleepAnalysis raw value

    Returns:
        Sleep stage string
    """
    stages = {
        0: "inBed",
        1: "asleep",
        2: "awake",
        3: "core",
        4: "deep",
        5: "rem",
    }
    return stages.get(category_value, "unknown")


def compute_sleep_summary(records: list[HealthRecord]) -> dict:
    """Compute sleep summary from sleep analysis records.

    Args:
        records: Sleep analysis records

    Returns:
        Sleep summary with total time, stage breakdown, efficiency
    """
    if not records:
        return {
            "total_minutes": 0, "stages": {}, "efficiency": 0.0,
        }

    stage_minutes: dict[str, float] = defaultdict(float)

    for record in records:
        try:
            start = datetime.fromisoformat(record.start_date.replace("Z", "+00:00"))
            end = datetime.fromisoformat(record.end_date.replace("Z", "+00:00"))
            duration_min = (end - start).total_seconds() / 60.0

            # Parse category value from metadata or use value
            category = int(record.value) if record.value < 10 else 0
            stage = classify_sleep_stage(category)
            stage_minutes[stage] += duration_min
        except (ValueError, TypeError):
            continue

    total = sum(stage_minutes.values())
    sleep_time = sum(
        v for k, v in stage_minutes.items()
        if k in ("asleep", "core", "deep", "rem")
    )
    efficiency = (sleep_time / total * 100.0) if total > 0 else 0.0

    return {
        "total_minutes": round(total, 1),
        "stages": {k: round(v, 1) for k, v in stage_minutes.items()},
        "efficiency": round(efficiency, 1),
    }


def search_records(
    xml_content: str,
    query: str,
    max_results: int = 50,
) -> list[dict]:
    """Search for records matching a query string across all attributes.

    Args:
        xml_content: XML string content
        query: Text to search for (case-insensitive)
        max_results: Maximum results to return

    Returns:
        List of matching record attribute dictionaries
    """
    query_lower = query.lower()
    results = []

    for elem_dict in stream_xml_records(xml_content, "Record"):
        matches = any(
            query_lower in str(v).lower()
            for v in elem_dict.values()
            if v
        )
        if matches:
            results.append(elem_dict)
            if len(results) >= max_results:
                break

    return results

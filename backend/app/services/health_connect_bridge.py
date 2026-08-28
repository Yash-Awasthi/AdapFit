"""Health Connect Bridge — Android Health Connect v2 data type mapping.

Maps Health Connect data types to AdapFit's internal models.
Supports: Steps, HeartRate, HRV, Sleep, BloodOxygen, RestingHeartRate,
VO2Max, Calories, Distance, ActiveMinutes, BloodPressure.

References:
- https://developer.android.com/health-and-fitness/health-connect
- Open Wearables SDK: https://openwearables.io/docs/sdk/android
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class HealthConnectDataType(str, Enum):
    STEPS = "Steps"
    HEART_RATE = "HeartRate"
    HEART_RATE_VARIABILITY = "HeartRateVariabilityRmssd"
    SLEEP_SESSION = "SleepSession"
    BLOOD_OXYGEN = "BloodOxygenSaturation"
    RESTING_HEART_RATE = "RestingHeartRate"
    VO2_MAX = "Vo2Max"
    TOTAL_CALORIES_BURNED = "TotalCaloriesBurned"
    DISTANCE = "Distance"
    ACTIVE_MINUTES = "ActiveMinutes"
    BLOOD_PRESSURE = "BloodPressure"
    WEIGHT = "Weight"
    BODY_FAT = "BodyFat"
    HYDRATION = "Hydration"
    MENSTRUAL_FLOW = "MenstrualFlow"
    SPEED = "Speed"
    ELEVATION_GAIN = "ElevationGain"


class SleepStage(str, Enum):
    AWAKE = "AWAKE"
    SLEEPING = "SLEEPING"
    OUT_OF_BED = "OUT_OF_BED"
    LIGHT = "LIGHT"
    DEEP = "DEEP"
    REM = "REM"
    SLEEPING_UNINTERRUPTIBLE = "SLEEPING_UNINTERRUPTIBLE"


class WorkoutType(str, Enum):
    RUNNING = "Running"
    WALKING = "Walking"
    CYCLING = "Cycling"
    SWIMMING = "Swimming"
    YOGA = "Yoga"
    STRENGTH_TRAINING = "Strength training"
    HIIT = "HIIT"
    OTHER = "Other"


@dataclass
class HealthConnectRecord:
    """Normalized record from any Health Connect data type."""
    data_type: str
    timestamp: str
    value: float
    unit: str
    metadata: dict = field(default_factory=dict)


@dataclass
class StepsRecord:
    count: int
    start_time: str
    end_time: str
    source_app: str = ""


@dataclass
class HeartRateRecord:
    bpm: int
    timestamp: str
    source_app: str = ""


@dataclass
class SleepSessionRecord:
    stages: list[dict]
    start_time: str
    end_time: str
    total_minutes: float = 0
    deep_minutes: float = 0
    rem_minutes: float = 0
    light_minutes: float = 0
    awake_minutes: float = 0


@dataclass
class BloodOxygenRecord:
    saturation_pct: float
    timestamp: str
    source_app: str = ""


# Mapping from Health Connect data types to AdapFit storage keys
HC_TO_ADAPFIT = {
    "Steps": "steps",
    "HeartRate": "heart_rate_bpm",
    "HeartRateVariabilityRmssd": "hrv_rmssd_ms",
    "SleepSession": "sleep_session",
    "BloodOxygenSaturation": "spo2_pct",
    "RestingHeartRate": "resting_heart_rate_bpm",
    "Vo2Max": "vo2_max",
    "TotalCaloriesBurned": "calories_burned",
    "Distance": "distance_meters",
    "ActiveMinutes": "active_minutes",
    "BloodPressure": "blood_pressure",
    "Weight": "weight_kg",
    "BodyFat": "body_fat_pct",
    "Hydration": "hydration_ml",
    "MenstrualFlow": "menstrual_flow",
    "Speed": "speed_ms",
    "ElevationGain": "elevation_gain_m",
}

# Required permissions for each data type
HC_PERMISSIONS = {
    "Steps": ["android.permission.health.READ_STEPS"],
    "HeartRate": ["android.permission.health.READ_HEART_RATE"],
    "HeartRateVariabilityRmssd": ["android.permission.health.READ_HEART_RATE_VARIABILITY"],
    "SleepSession": ["android.permission.health.READ_SLEEP"],
    "BloodOxygenSaturation": ["android.permission.health.READ_BLOOD_OXYGEN"],
    "RestingHeartRate": ["android.permission.health.READ_RESTING_HEART_RATE"],
    "Vo2Max": ["android.permission.health.READ_VO2_MAX"],
    "TotalCaloriesBurned": ["android.permission.health.READ_TOTAL_CALORIES_BURNED"],
    "Distance": ["android.permission.health.READ_DISTANCE"],
    "BloodPressure": ["android.permission.health.READ_BLOOD_PRESSURE"],
    "Weight": ["android.permission.health.READ_WEIGHT"],
    "BodyFat": ["android.permission.health.READ_BODY_FAT"],
    "Hydration": ["android.permission.health.READ_HYDRATION"],
    "MenstrualFlow": ["android.permission.health.READ_MENSTRUATION"],
}

# Write permissions
HC_WRITE_PERMISSIONS = {
    "Steps": ["android.permission.health.WRITE_STEPS"],
    "HeartRate": ["android.permission.health.WRITE_HEART_RATE"],
    "SleepSession": ["android.permission.health.WRITE_SLEEP"],
    "Weight": ["android.permission.health.WRITE_WEIGHT"],
    "TotalCaloriesBurned": ["android.permission.health.WRITE_TOTAL_CALORIES_BURNED"],
    "Hydration": ["android.permission.health.WRITE_HYDRATION"],
    "MenstrualFlow": ["android.permission.health.WRITE_MENSTRUATION"],
}


def normalize_sleep_session(raw_data: dict) -> SleepSessionRecord:
    """Normalize raw Health Connect sleep data to AdapFit format."""
    stages = raw_data.get("stages", [])
    deep = sum(s.get("duration_minutes", 0) for s in stages if s.get("stage") == "DEEP")
    rem = sum(s.get("duration_minutes", 0) for s in stages if s.get("stage") == "REM")
    light = sum(s.get("duration_minutes", 0) for s in stages if s.get("stage") == "LIGHT")
    awake = sum(s.get("duration_minutes", 0) for s in stages if s.get("stage") in ("AWAKE", "OUT_OF_BED"))
    total = deep + rem + light + awake

    return SleepSessionRecord(
        stages=stages,
        start_time=raw_data.get("start_time", ""),
        end_time=raw_data.get("end_time", ""),
        total_minutes=total,
        deep_minutes=deep,
        rem_minutes=rem,
        light_minutes=light,
        awake_minutes=awake,
    )


def normalize_heart_rate_series(raw_readings: list[dict]) -> dict:
    """Normalize a series of heart rate readings."""
    if not raw_readings:
        return {"avg_bpm": 0, "max_bpm": 0, "min_bpm": 0, "readings": []}

    bpms = [r.get("bpm", 0) for r in raw_readings]
    return {
        "avg_bpm": round(sum(bpms) / len(bpms)),
        "max_bpm": max(bpms),
        "min_bpm": min(bpms),
        "readings_count": len(bpms),
        "readings": raw_readings,
    }


def compute_hrv_rmssd(rr_intervals_ms: list[float]) -> float:
    """Compute HRV RMSSD from RR intervals."""
    if len(rr_intervals_ms) < 2:
        return 0.0
    diffs = [rr_intervals_ms[i + 1] - rr_intervals_ms[i] for i in range(len(rr_intervals_ms) - 1)]
    sq_diffs = [d ** 2 for d in diffs]
    return (sum(sq_diffs) / len(sq_diffs)) ** 0.5


def get_all_permissions() -> list[str]:
    """Get all required Health Connect permissions."""
    perms = set()
    for p_list in HC_PERMISSIONS.values():
        perms.update(p_list)
    for p_list in HC_WRITE_PERMISSIONS.values():
        perms.update(p_list)
    return sorted(perms)


def get_read_permissions(data_types: list[str]) -> list[str]:
    """Get read permissions for specific data types."""
    perms = []
    for dt in data_types:
        perms.extend(HC_PERMISSIONS.get(dt, []))
    return sorted(set(perms))

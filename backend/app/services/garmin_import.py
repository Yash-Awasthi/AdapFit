"""
Garmin Connect Data Import

Parses Garmin Connect export format (JSON/CSV), maps fields to ZFIT
internal format, and handles batch import with deduplication.
Pure functions only — no DB.
"""
from dataclasses import dataclass, field
from typing import Optional
import statistics
from datetime import datetime


@dataclass
class GarminDailySummary:
    """One day's summary from Garmin Connect export."""
    date: str  # "YYYY-MM-DD"
    steps: int = 0
    floors_climbed: int = 0
    intensity_minutes: int = 0
    calories_burned: int = 0
    distance_meters: float = 0
    resting_heart_rate: Optional[int] = None
    heart_rate_variability: Optional[float] = None  # ms
    stress_level: Optional[int] = None
    body_battery_high: Optional[int] = None
    body_battery_low: Optional[int] = None
    vo2_max: Optional[float] = None
    sleep_score: Optional[int] = None
    sleep_hours: Optional[float] = None
    deep_sleep_hours: Optional[float] = None
    rem_sleep_hours: Optional[float] = None
    respiration_avg: Optional[float] = None
    spo2_avg: Optional[float] = None
    steps_goal: int = 10000
    floors_goal: int = 10


@dataclass
class GarminWorkout:
    """A single workout session from Garmin Connect."""
    timestamp: str  # ISO 8601
    activity_type: str  # "running", "cycling", "swimming", etc.
    duration_seconds: int = 0
    distance_meters: float = 0
    calories: int = 0
    avg_heart_rate: Optional[int] = None
    max_heart_rate: Optional[int] = None
    avg_speed: Optional[float] = None  # m/s
    max_speed: Optional[float] = None
    elevation_gain: float = 0  # meters
    avg_cadence: Optional[int] = None
    avg_power: Optional[int] = None  # watts
    training_effect_aerobic: Optional[float] = None
    training_effect_anaerobic: Optional[float] = None


@dataclass
class GarminSleepRecord:
    """Detailed sleep record from Garmin Connect."""
    date: str
    sleep_start: str
    sleep_end: str
    total_minutes: int = 0
    deep_minutes: int = 0
    light_minutes: int = 0
    rem_minutes: int = 0
    awake_minutes: int = 0
    sleep_score: Optional[int] = None
    sleep_quality: Optional[str] = None  # "good", "fair", "poor"
    resting_heart_rate: Optional[int] = None
    hrv_status: Optional[str] = None  # "balanced", "unbalanced", "poor"


# ── Activity Type Mapping ──────────────────────────────────────────────────

GARMIN_ACTIVITY_MAP = {
    "running": "run",
    "trail_running": "trail_run",
    "treadmill_running": "treadmill_run",
    "cycling": "cycle",
    "mountain_biking": "mountain_bike",
    "indoor_cycling": "indoor_cycle",
    "swimming": "swim",
    "open_water_swimming": "open_water_swim",
    "walking": "walk",
    "hiking": "hike",
    "strength_training": "strength",
    "cardio": "cardio",
    "yoga": "yoga",
    "elliptical": "elliptical",
    "rowing": "row",
    "golf": "golf",
    "tennis": "tennis",
    "basketball": "basketball",
    "soccer": "soccer",
    "rock_climbing": "climbing",
    "mountaineering": "mountaineering",
    "cross_country_skiing": "cross_country_ski",
    "alpine_skiing": "alpine_ski",
    "snowboarding": "snowboard",
    "paddleboarding": "paddleboard",
    "kayaking": "kayak",
    "surfing": "surf",
}


# ── Field Mapping ──────────────────────────────────────────────────────────

def map_daily_summary(raw: dict) -> Optional[GarminDailySummary]:
    """
    Map a Garmin daily summary dict to GarminDailySummary.

    Handles both Garmin Connect JSON export and ConnectIQ formats.
    """
    try:
        date = raw.get("date") or raw.get("calendarDate") or raw.get("timestamp", "")[:10]
        if not date:
            return None

        return GarminDailySummary(
            date=date,
            steps=int(raw.get("totalSteps", raw.get("steps", 0)) or 0),
            floors_climbed=int(raw.get("floorsAscended", raw.get("floorsClimbed", 0)) or 0),
            intensity_minutes=int(raw.get("moderateIntensityMinutes", 0) or 0) +
                              int(raw.get("vigorousIntensityMinutes", 0) or 0),
            calories_burned=int(raw.get("totalKilocalories", raw.get("calories", 0)) or 0),
            distance_meters=float(raw.get("totalDistanceMeters", raw.get("distance", 0)) or 0),
            resting_heart_rate=_opt_int(raw.get("restingHeartRate")),
            heart_rate_variability=_opt_float(raw.get("hrvValue", raw.get("lastNightHrv"))),
            stress_level=_opt_int(raw.get("overallStressLevel")),
            body_battery_high=_opt_int(raw.get("bodyBatteryHigh")),
            body_battery_low=_opt_int(raw.get("bodyBatteryLow")),
            vo2_max=_opt_float(raw.get("vo2MaxValue")),
            sleep_score=_opt_int(raw.get("sleepScore")),
            sleep_hours=_opt_float(raw.get("sleepTimeSeconds", 0)) and
                        raw.get("sleepTimeSeconds", 0) / 3600 if raw.get("sleepTimeSeconds") else None,
            deep_sleep_hours=_opt_float(raw.get("deepSleepSeconds", 0)) and
                             raw.get("deepSleepSeconds", 0) / 3600 if raw.get("deepSleepSeconds") else None,
            rem_sleep_hours=_opt_float(raw.get("remSleepSeconds", 0)) and
                            raw.get("remSleepSeconds", 0) / 3600 if raw.get("remSleepSeconds") else None,
            respiration_avg=_opt_float(raw.get("avgRespirationValue")),
            spo2_avg=_opt_float(raw.get("pulseOxAverage")),
            steps_goal=int(raw.get("dailyStepGoal", 10000)),
            floors_goal=int(raw.get("floorsAscendedGoal", 10)),
        )
    except (ValueError, TypeError):
        return None


def map_workout(raw: dict) -> Optional[GarminWorkout]:
    """Map a Garmin workout dict to GarminWorkout."""
    try:
        raw_type = raw.get("activityType", raw.get("type", ""))
        if isinstance(raw_type, dict):
            activity_type = raw_type.get("typeKey", "unknown")
        else:
            activity_type = str(raw_type) if raw_type else "unknown"
        if not activity_type or activity_type == "None":
            return None

        return GarminWorkout(
            timestamp=raw.get("startTimeLocal", raw.get("timestamp", "")),
            activity_type=activity_type,
            duration_seconds=int(raw.get("duration", 0) or 0),
            distance_meters=float(raw.get("distance", 0) or 0),
            calories=int(raw.get("calories", 0) or 0),
            avg_heart_rate=_opt_int(raw.get("averageHR")),
            max_heart_rate=_opt_int(raw.get("maxHR")),
            avg_speed=_opt_float(raw.get("averageSpeed")),
            max_speed=_opt_float(raw.get("maxSpeed")),
            elevation_gain=float(raw.get("elevationGain", 0) or 0),
            avg_cadence=_opt_int(raw.get("averageRunningCadenceInStepsPerMinute")),
            avg_power=_opt_int(raw.get("averageWatts")),
            training_effect_aerobic=_opt_float(raw.get("aerobicTrainingEffect")),
            training_effect_anaerobic=_opt_float(raw.get("anaerobicTrainingEffect")),
        )
    except (ValueError, TypeError):
        return None


def map_sleep(raw: dict) -> Optional[GarminSleepRecord]:
    """Map a Garmin sleep dict to GarminSleepRecord."""
    try:
        date = raw.get("date", "") or raw.get("calendarDate", "")
        if not date:
            return None

        deep = raw.get("deepSleepSeconds", 0) or 0
        light = raw.get("lightSleepSeconds", 0) or 0
        rem = raw.get("remSleepSeconds", 0) or 0
        awake = raw.get("awakeSleepSeconds", 0) or 0
        total = (deep + light + rem + awake) // 60

        return GarminSleepRecord(
            date=date,
            sleep_start=raw.get("sleepStartTimestampLocal", ""),
            sleep_end=raw.get("sleepEndTimestampLocal", ""),
            total_minutes=total,
            deep_minutes=deep // 60,
            light_minutes=light // 60,
            rem_minutes=rem // 60,
            awake_minutes=awake // 60,
            sleep_score=_opt_int(raw.get("sleepScore")),
            sleep_quality=raw.get("sleepQuality"),
            resting_heart_rate=_opt_int(raw.get("restingHeartRate")),
            hrv_status=raw.get("hrvStatus"),
        )
    except (ValueError, TypeError):
        return None


# ── Batch Import ───────────────────────────────────────────────────────────

def import_daily_summaries(records: list[dict]) -> dict:
    """Batch import daily summaries with deduplication."""
    imported = []
    skipped = 0
    errors = 0
    seen_dates: set[str] = set()

    for raw in records:
        summary = map_daily_summary(raw)
        if summary is None:
            errors += 1
            continue
        if summary.date in seen_dates:
            skipped += 1
            continue
        seen_dates.add(summary.date)
        imported.append(summary)

    return {
        "imported": len(imported),
        "skipped_duplicates": skipped,
        "errors": errors,
        "date_range": {
            "start": imported[0].date if imported else None,
            "end": imported[-1].date if imported else None,
        },
        "data": imported,
    }


def import_workouts(records: list[dict]) -> dict:
    """Batch import workouts with deduplication by timestamp+type."""
    imported = []
    skipped = 0
    errors = 0
    seen: set[str] = set()

    for raw in records:
        workout = map_workout(raw)
        if workout is None:
            errors += 1
            continue
        key = f"{workout.timestamp}:{workout.activity_type}:{workout.duration_seconds}"
        if key in seen:
            skipped += 1
            continue
        seen.add(key)
        imported.append(workout)

    # Compute training volume summary
    by_type: dict[str, list[GarminWorkout]] = {}
    for w in imported:
        zfit_type = GARMIN_ACTIVITY_MAP.get(w.activity_type, w.activity_type)
        by_type.setdefault(zfit_type, []).append(w)

    volume_summary = {}
    for atype, workouts in by_type.items():
        total_duration = sum(w.duration_seconds for w in workouts)
        total_distance = sum(w.distance_meters for w in workouts)
        total_calories = sum(w.calories for w in workouts)
        avg_hr = statistics.mean([w.avg_heart_rate for w in workouts if w.avg_heart_rate]) if any(w.avg_heart_rate for w in workouts) else None

        volume_summary[atype] = {
            "count": len(workouts),
            "total_duration_minutes": round(total_duration / 60, 1),
            "total_distance_km": round(total_distance / 1000, 2),
            "total_calories": total_calories,
            "avg_heart_rate": round(avg_hr) if avg_hr else None,
        }

    return {
        "imported": len(imported),
        "skipped_duplicates": skipped,
        "errors": errors,
        "volume_summary": volume_summary,
        "data": imported,
    }


def import_sleep_records(records: list[dict]) -> dict:
    """Batch import sleep records with deduplication."""
    imported = []
    skipped = 0
    errors = 0
    seen_dates: set[str] = set()

    for raw in records:
        sleep = map_sleep(raw)
        if sleep is None:
            errors += 1
            continue
        if sleep.date in seen_dates:
            skipped += 1
            continue
        seen_dates.add(sleep.date)
        imported.append(sleep)

    # Compute sleep summary
    if imported:
        avg_total = statistics.mean([s.total_minutes for s in imported])
        avg_deep = statistics.mean([s.deep_minutes for s in imported])
        avg_rem = statistics.mean([s.rem_minutes for s in imported])
        scores = [s.sleep_score for s in imported if s.sleep_score is not None]
    else:
        avg_total = avg_deep = avg_rem = 0
        scores = []

    return {
        "imported": len(imported),
        "skipped_duplicates": skipped,
        "errors": errors,
        "summary": {
            "avg_total_minutes": round(avg_total, 1),
            "avg_deep_minutes": round(avg_deep, 1),
            "avg_rem_minutes": round(avg_rem, 1),
            "avg_sleep_score": round(statistics.mean(scores), 1) if scores else None,
            "nights": len(imported),
        },
        "data": imported,
    }


# ── Helpers ────────────────────────────────────────────────────────────────

def _opt_int(v) -> Optional[int]:
    if v is None:
        return None
    try:
        return int(v)
    except (ValueError, TypeError):
        return None


def _opt_float(v) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None

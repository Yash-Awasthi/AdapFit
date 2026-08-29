"""
HealthKit Bridge — transforms Apple HealthKit sample data into ZFIT format.

Pure functions for data transformation, aggregation, and compatibility checking.
No DB, no async, no external dependencies — just math and dict transforms.

HealthKit provides samples as dictionaries with these common fields:
  - sampleType: e.g. "HKQuantityTypeIdentifierHeartRate"
  - value: numeric value
  - unit: e.g. "count/min", "mg/dL"
  - startDate / endDate: ISO 8601 timestamps
  - metadata: optional dict with device info, source revision, etc.
"""
from dataclasses import dataclass
from typing import Optional
import statistics
from datetime import datetime, timedelta


# ── Sample type mappings ─────────────────────────────────────────────────────

HK_TYPE_MAP = {
    "HKQuantityTypeIdentifierHeartRate": "heart_rate",
    "HKQuantityTypeIdentifierRestingHeartRate": "resting_heart_rate",
    "HKQuantityTypeIdentifierHeartRateVariabilitySDNN": "hrv_rmssd",
    "HKQuantityTypeIdentifierOxygenSaturation": "blood_oxygen",
    "HKQuantityTypeIdentifierBodyTemperature": "body_temperature",
    "HKQuantityTypeIdentifierStepCount": "step_count",
    "HKQuantityTypeIdentifierDistanceWalkingRunning": "distance",
    "HKQuantityTypeIdentifierFlightsClimbed": "flights_climbed",
    "HKCategoryTypeIdentifierSleepAnalysis": "sleep",
    "HKWorkoutTypeIdentifier": "workout",
    "HKQuantityTypeIdentifierActiveEnergyBurned": "active_energy",
    "HKQuantityTypeIdentifierBasalEnergyBurned": "basal_energy",
    "HKQuantityTypeIdentifierDietaryEnergyConsumed": "dietary_energy",
    "HKQuantityTypeIdentifierRespiratoryRate": "respiratory_rate",
    "HKQuantityTypeIdentifierAppleExerciseTime": "exercise_time",
    "HKQuantityTypeIdentifierAppleStandTime": "stand_time",
    "HKQuantityTypeIdentifierVO2Max": "vo2_max",
}

# Unit conversions to ZFIT internal units
UNIT_CONVERSIONS = {
    "count/min": lambda v: v,               # already BPM
    "%": lambda v: v,                        # already percentage
    "°C": lambda v: v,                       # already Celsius
    "°F": lambda v: (v - 32) * 5 / 9,       # F → C
    "count": lambda v: v,                    # steps, flights
    "km": lambda v: v,                       # already km
    "mi": lambda v: v * 1.60934,             # miles → km
    "m": lambda v: v / 1000,                 # meters → km
    "ft": lambda v: v * 0.0003048,           # feet → km
    "kJ": lambda v: v / 4.184,               # kJ → kcal
    "kcal": lambda v: v,
    "breaths/min": lambda v: v,
    "ml/kg*min": lambda v: v,
    "hr": lambda v: v,                       # hours
    "min": lambda v: v / 60,                 # minutes → hours
    "s": lambda v: v / 3600,                 # seconds → hours
}

# Sleep stage mapping from HK values
HK_SLEEP_STAGES = {
    0: "inBed",
    1: "asleep",
    2: "awake",
    3: "deep",      # watchOS 9+
    4: "rem",       # watchOS 9+
    5: "core",      # watchOS 9+ (light)
}


@dataclass
class ZFITSample:
    """Standardized ZFIT data sample."""
    type: str
    value: float
    unit: str
    start: str  # ISO 8601
    end: str    # ISO 8601
    duration_minutes: float = 0
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


def transform_sample(hk_sample: dict) -> Optional[ZFITSample]:
    """
    Transform a single HealthKit sample dict into ZFIT format.

    Returns None if the sample type is unsupported or malformed.
    """
    sample_type = hk_sample.get("sampleType", "")
    zfit_type = HK_TYPE_MAP.get(sample_type)
    if not zfit_type:
        return None

    value = hk_sample.get("value")
    if value is None:
        return None

    unit = hk_sample.get("unit", "")
    convert = UNIT_CONVERSIONS.get(unit, lambda v: v)
    try:
        zfit_value = convert(float(value))
    except (ValueError, TypeError):
        return None

    start = hk_sample.get("startDate", "")
    end = hk_sample.get("endDate", "")

    # Calculate duration
    duration_minutes = 0
    if start and end:
        try:
            t_start = datetime.fromisoformat(start.replace("Z", "+00:00"))
            t_end = datetime.fromisoformat(end.replace("Z", "+00:00"))
            duration_minutes = (t_end - t_start).total_seconds() / 60
        except (ValueError, TypeError):
            pass

    return ZFITSample(
        type=zfit_type,
        value=zfit_value,
        unit=unit,
        start=start,
        end=end,
        duration_minutes=round(duration_minutes, 1),
        metadata=hk_sample.get("metadata", {}),
    )


def transform_batch(samples: list[dict]) -> list[ZFITSample]:
    """Transform a batch of HealthKit samples, filtering unsupported types."""
    results = []
    for s in samples:
        zfit = transform_sample(s)
        if zfit:
            results.append(zfit)
    return results


# ── Aggregation functions ────────────────────────────────────────────────────

def daily_averages(samples: list[ZFITSample], date: str = None) -> dict:
    """
    Compute daily averages for each sample type.

    Args:
        samples: List of ZFITSample objects
        date: ISO date string (YYYY-MM-DD). If None, uses all samples.
    """
    if date:
        samples = [s for s in samples if s.start.startswith(date)]

    by_type = {}
    for s in samples:
        by_type.setdefault(s.type, []).append(s.value)

    result = {}
    for stype, values in by_type.items():
        result[stype] = {
            "avg": round(statistics.mean(values), 1),
            "min": round(min(values), 1),
            "max": round(max(values), 1),
            "count": len(values),
        }
        if len(values) > 1:
            result[stype]["stddev"] = round(statistics.stdev(values), 1)

    return result


def weekly_trends(samples: list[ZFITSample]) -> dict:
    """
    Compute weekly trends — compare this week vs last week.
    """
    now = datetime.now()
    this_week_start = now - timedelta(days=now.weekday())
    last_week_start = this_week_start - timedelta(days=7)

    def in_range(s, start, end):
        try:
            t = datetime.fromisoformat(s.start.replace("Z", "+00:00"))
            return start <= t < end
        except (ValueError, TypeError):
            return False

    this_week = [s for s in samples if in_range(s, this_week_start, now)]
    last_week = [s for s in samples if in_range(s, last_week_start, this_week_start)]

    this_agg = daily_averages(this_week)
    last_agg = daily_averages(last_week)

    trends = {}
    for stype in set(list(this_agg.keys()) + list(last_agg.keys())):
        this_avg = this_agg.get(stype, {}).get("avg", 0)
        last_avg = last_agg.get(stype, {}).get("avg", 0)
        if last_avg > 0:
            change_pct = ((this_avg - last_avg) / last_avg) * 100
        else:
            change_pct = 0 if this_avg == 0 else 100

        direction = "up" if change_pct > 2 else "down" if change_pct < -2 else "stable"
        trends[stype] = {
            "this_week": this_avg,
            "last_week": last_avg,
            "change_pct": round(change_pct, 1),
            "direction": direction,
        }

    return trends


def monthly_summaries(samples: list[ZFITSample]) -> dict:
    """
    Compute monthly summaries — totals and averages per type.
    """
    by_type = {}
    for s in samples:
        by_type.setdefault(s.type, []).append(s)

    result = {}
    for stype, type_samples in by_type.items():
        values = [s.value for s in type_samples]
        total = sum(values)

        # For step_count and distance, report total
        # For heart_rate, report average
        if stype in ("step_count", "flights_climbed", "exercise_time", "stand_time"):
            result[stype] = {"total": round(total, 1), "days": len(set(s.start[:10] for s in type_samples))}
        elif stype in ("active_energy", "basal_energy", "dietary_energy"):
            result[stype] = {"total_kcal": round(total, 1), "days": len(set(s.start[:10] for s in type_samples))}
        elif stype == "distance":
            result[stype] = {"total_km": round(total, 2), "days": len(set(s.start[:10] for s in type_samples))}
        elif stype == "sleep":
            total_hours = sum(s.duration_minutes / 60 for s in type_samples)
            result[stype] = {
                "total_hours": round(total_hours, 1),
                "avg_hours": round(total_hours / max(1, len(type_samples)), 1),
                "nights": len(type_samples),
            }
        else:
            result[stype] = {
                "avg": round(statistics.mean(values), 1),
                "min": round(min(values), 1),
                "max": round(max(values), 1),
                "count": len(values),
            }

    return result


def resting_hr_trend(samples: list[ZFITSample], days: int = 30) -> dict:
    """
    Compute resting heart rate trend over the last N days.
    Returns daily resting HR and linear trend slope.
    """
    hr_samples = [s for s in samples if s.type == "resting_heart_rate"]
    if not hr_samples:
        return {"error": "No resting heart rate data"}

    # Group by date
    daily = {}
    for s in hr_samples:
        date = s.start[:10]
        daily.setdefault(date, []).append(s.value)

    # Average per day
    daily_avg = {d: statistics.mean(vals) for d, vals in daily.items()}
    sorted_days = sorted(daily_avg.items())[-days:]

    if len(sorted_days) < 3:
        return {"error": "Insufficient data", "days_available": len(sorted_days)}

    values = [v for _, v in sorted_days]
    x_vals = list(range(len(values)))
    x_mean = statistics.mean(x_vals)
    y_mean = statistics.mean(values)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, values))
    denominator = sum((x - x_mean) ** 2 for x in x_vals)
    slope = numerator / denominator if denominator > 0 else 0

    trend = "improving" if slope < -0.1 else "declining" if slope > 0.1 else "stable"

    return {
        "avg_resting_hr": round(statistics.mean(values), 1),
        "min": round(min(values), 1),
        "max": round(max(values), 1),
        "slope_per_day": round(slope, 3),
        "trend": trend,
        "days": len(sorted_days),
        "daily": {d: round(v, 1) for d, v in sorted_days},
    }


# ── Compatibility checking ───────────────────────────────────────────────────

COMPATIBILITY_TABLE = {
    "heart_rate":              {"ios": "8.0", "watchos": "2.0", "devices": ["iphone", "watch"]},
    "resting_heart_rate":      {"ios": "11.0", "watchos": "4.0", "devices": ["watch"]},
    "hrv_rmssd":              {"ios": "11.0", "watchos": "4.0", "devices": ["watch"]},
    "blood_oxygen":           {"ios": "14.0", "watchos": "7.0", "devices": ["watch"]},
    "body_temperature":       {"ios": "14.0", "watchos": "7.0", "devices": ["watch"]},
    "step_count":             {"ios": "8.0", "watchos": "2.0", "devices": ["iphone", "watch"]},
    "distance":               {"ios": "8.0", "watchos": "2.0", "devices": ["iphone", "watch"]},
    "flights_climbed":        {"ios": "8.0", "watchos": "2.0", "devices": ["iphone", "watch"]},
    "sleep":                  {"ios": "8.0", "watchos": "2.0", "devices": ["iphone", "watch"]},
    "workout":                {"ios": "8.0", "watchos": "2.0", "devices": ["iphone", "watch"]},
    "active_energy":           {"ios": "8.0", "watchos": "2.0", "devices": ["watch"]},
    "basal_energy":            {"ios": "8.0", "watchos": "2.0", "devices": ["watch"]},
    "dietary_energy":          {"ios": "8.0", "watchos": "2.0", "devices": ["iphone", "watch"]},
    "respiratory_rate":        {"ios": "14.0", "watchos": "7.0", "devices": ["watch"]},
    "exercise_time":           {"ios": "8.0", "watchos": "2.0", "devices": ["watch"]},
    "stand_time":              {"ios": "8.0", "watchos": "2.0", "devices": ["watch"]},
    "vo2_max":                 {"ios": "14.0", "watchos": "7.0", "devices": ["watch"]},
}


def check_healthkit_compatibility(device_type: str = "iphone", ios_version: str = "17.0") -> dict:
    """
    Check which HealthKit data types are available for a given device/OS.

    Args:
        device_type: "iphone" or "watch"
        ios_version: iOS/watchOS version string (e.g. "17.0", "10.0")
    """
    available = []
    unavailable = []

    for data_type, compat in COMPATIBILITY_TABLE.items():
        devices = compat["devices"]
        min_os = compat["ios"] if device_type == "iphone" else compat.get("watchos", compat["ios"])

        if device_type not in devices:
            unavailable.append({"type": data_type, "reason": f"requires {devices[0]}"})
        elif _version_gte(ios_version, min_os):
            available.append(data_type)
        else:
            unavailable.append({"type": data_type, "reason": f"requires iOS {min_os}+"})

    return {
        "device": device_type,
        "os_version": ios_version,
        "available": available,
        "unavailable": unavailable,
        "total_available": len(available),
    }


def _version_gte(current: str, minimum: str) -> bool:
    """Check if current version >= minimum version."""
    try:
        cur_parts = [int(x) for x in current.split(".")[:2]]
        min_parts = [int(x) for x in minimum.split(".")[:2]]
        return cur_parts >= min_parts
    except (ValueError, IndexError):
        return False

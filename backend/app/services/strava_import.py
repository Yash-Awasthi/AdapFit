"""
Strava Data Import

Parses Strava API export format, maps activities to ZFIT internal format,
calculates training load (TSS), and aggregates training volume.
Pure functions only — no DB.
"""
from dataclasses import dataclass
from typing import Optional
import math
import statistics
from datetime import datetime


@dataclass
class StravaActivity:
    """Parsed Strava activity."""
    id: str
    name: str
    activity_type: str       # Strava type: "Run", "Ride", "Swim", etc.
    zfit_type: str           # Mapped to ZFIT: "run", "cycle", "swim", etc.
    start_date: str          # ISO 8601
    distance_meters: float = 0
    moving_time_seconds: int = 0
    elapsed_time_seconds: int = 0
    total_elevation_gain: float = 0
    avg_speed: Optional[float] = None  # m/s
    max_speed: Optional[float] = None
    avg_heart_rate: Optional[int] = None
    max_heart_rate: Optional[int] = None
    avg_cadence: Optional[int] = None
    avg_power: Optional[int] = None
    max_power: Optional[int] = None
    calories: Optional[int] = None
    average_watts: Optional[int] = None
    kilojoules: Optional[float] = None
    trainer: bool = False
    commute: bool = False
    flagged: bool = False


@dataclass
class StravaRoute:
    """GPS route data from a Strava activity."""
    activity_id: str
    coordinates: list[tuple[float, float]] = None  # [(lat, lng), ...]
    elevation_profile: list[float] = None           # meters

    def __post_init__(self):
        if self.coordinates is None:
            self.coordinates = []
        if self.elevation_profile is None:
            self.elevation_profile = []


# ── Activity Type Mapping ──────────────────────────────────────────────────

STRAVA_TYPE_MAP = {
    "Run": "run",
    "TrailRun": "trail_run",
    "Walk": "walk",
    "Hike": "hike",
    "Ride": "cycle",
    "MountainBikeRide": "mountain_bike",
    "VirtualRide": "indoor_cycle",
    "Swim": "swim",
    "OpenWaterSwim": "open_water_swim",
    "Row": "row",
    "Kayak": "kayak",
    "Canoeing": "canoe",
    "StandUpPaddling": "paddleboard",
    "AlpineSki": "alpine_ski",
    "CrossCountrySki": "cross_country_ski",
    "Snowboard": "snowboard",
    "IceSkate": "ice_skate",
    "Wheelchair": "wheelchair",
    "WeightTraining": "strength",
    "Yoga": "yoga",
    "RockClimbing": "climbing",
    "Workout": "workout",
    "Run_commute": "run",
    "Ride_commute": "cycle",
}


# ── Training Load Calculation ──────────────────────────────────────────────

def calculate_tss(
    duration_minutes: float,
    avg_hr: Optional[int] = None,
    max_hr: Optional[int] = None,
    avg_power: Optional[int] = None,
    ftp: Optional[int] = None,
) -> float:
    """
    Calculate Training Stress Score (TSS).

    Three methods (in order of preference):
    1. Power-based (IF² × duration): most accurate
    2. HR-based (TRIMP): moderate accuracy
    3. Duration-based (minutes × intensity): fallback

    Returns TSS as float.
    """
    duration_hours = duration_minutes / 60

    # Method 1: Power-based TSS
    if avg_power and ftp and ftp > 0:
        intensity_factor = avg_power / ftp
        normalized_power = avg_power * 1.05  # approximation
        p_tss = (duration_hours * normalized_power * intensity_factor * 100) / (ftp * 1)
        return round(min(p_tss, 500), 1)  # cap at 500

    # Method 2: HR-based TRIMP
    if avg_hr and max_hr and max_hr > 0:
        hr_reserve_pct = avg_hr / max_hr  # approximation of %HRmax
        # Banister TRIMP: duration × HRratio × 0.64 × e^(1.92 × HRratio)
        trimp = duration_hours * hr_reserve_pct * 0.64 * math.exp(1.92 * hr_reserve_pct)
        return round(min(trimp * 10, 500), 1)  # scale and cap

    # Method 3: Duration-based approximation
    # Rough: 1 TSS per minute at moderate intensity
    return round(min(duration_minutes, 500), 1)


# ── Parsing ────────────────────────────────────────────────────────────────

def parse_activity(raw: dict) -> Optional[StravaActivity]:
    """Parse a single Strava activity dict."""
    try:
        strava_type = raw.get("type", raw.get("sport_type", "Workout"))
        zfit_type = STRAVA_TYPE_MAP.get(strava_type, strava_type.lower())

        tss = calculate_tss(
            duration_minutes=raw.get("moving_time", 0) / 60,
            avg_hr=raw.get("average_heartrate"),
            max_hr=raw.get("max_heartrate"),
            avg_power=raw.get("average_watts"),
        )

        raw_id = raw.get("id")
        if not raw_id and not raw.get("type"):
            return None

        return StravaActivity(
            id=str(raw_id or ""),
            name=raw.get("name", "Untitled"),
            activity_type=strava_type,
            zfit_type=zfit_type,
            start_date=raw.get("start_date", ""),
            distance_meters=float(raw.get("distance", 0) or 0),
            moving_time_seconds=int(raw.get("moving_time", 0) or 0),
            elapsed_time_seconds=int(raw.get("elapsed_time", 0) or 0),
            total_elevation_gain=float(raw.get("total_elevation_gain", 0) or 0),
            avg_speed=_opt_float(raw.get("average_speed")),
            max_speed=_opt_float(raw.get("max_speed")),
            avg_heart_rate=_opt_int(raw.get("average_heartrate")),
            max_heart_rate=_opt_int(raw.get("max_heartrate")),
            avg_cadence=_opt_int(raw.get("average_cadence")),
            avg_power=_opt_int(raw.get("average_watts")),
            max_power=_opt_int(raw.get("max_watts")),
            calories=_opt_int(raw.get("calories")),
            average_watts=_opt_int(raw.get("average_watts")),
            kilojoules=_opt_float(raw.get("kilojoules")),
            trainer=raw.get("trainer", False),
            commute=raw.get("commute", False),
            flagged=raw.get("flagged", False),
        )
    except (ValueError, TypeError):
        return None


def parse_route(raw: dict) -> Optional[StravaRoute]:
    """Parse GPS route data from Strava polyline or coordinate arrays."""
    try:
        activity_id = str(raw.get("activity_id", raw.get("id", "")))

        # Try to extract coordinates from map summary
        map_data = raw.get("map", {})
        summary_polyline = map_data.get("summary_polyline", "")
        coordinates = decode_polyline(summary_polyline) if summary_polyline else []

        # Elevation from altitude data
        elevations = raw.get("altitude_data", [])

        return StravaRoute(
            activity_id=activity_id,
            coordinates=coordinates,
            elevation_profile=elevations,
        )
    except Exception:
        return None


# ── Batch Import ───────────────────────────────────────────────────────────

def import_activities(records: list[dict]) -> dict:
    """Batch import Strava activities with training volume aggregation."""
    imported = []
    skipped = 0
    errors = 0
    seen_ids: set[str] = set()

    for raw in records:
        activity = parse_activity(raw)
        if activity is None:
            errors += 1
            continue
        if activity.id in seen_ids:
            skipped += 1
            continue
        seen_ids.add(activity.id)
        imported.append(activity)

    # Weekly aggregation
    weekly_volume = aggregate_weekly(imported)

    # Type breakdown
    by_type: dict[str, list[StravaActivity]] = {}
    for a in imported:
        by_type.setdefault(a.zfit_type, []).append(a)

    type_summary = {}
    for atype, acts in by_type.items():
        total_distance = sum(a.distance_meters for a in acts)
        total_duration = sum(a.moving_time_seconds for a in acts)
        avg_tss = statistics.mean([
            calculate_tss(a.moving_time_seconds / 60, a.avg_heart_rate, a.max_heart_rate)
            for a in acts
        ]) if acts else 0

        type_summary[atype] = {
            "count": len(acts),
            "total_distance_km": round(total_distance / 1000, 2),
            "total_duration_minutes": round(total_duration / 60, 1),
            "avg_tss": round(avg_tss, 1),
            "total_calories": sum(a.calories or 0 for a in acts),
        }

    return {
        "imported": len(imported),
        "skipped_duplicates": skipped,
        "errors": errors,
        "type_summary": type_summary,
        "weekly_volume": weekly_volume,
        "data": imported,
    }


def aggregate_weekly(activities: list[StravaActivity]) -> list[dict]:
    """Aggregate training volume by ISO week."""
    weeks: dict[str, dict] = {}

    for a in activities:
        try:
            dt = datetime.fromisoformat(a.start_date.replace("Z", "+00:00"))
            iso_year, iso_week, _ = dt.isocalendar()
            week_key = f"{iso_year}-W{iso_week:02d}"
        except (ValueError, TypeError):
            continue

        if week_key not in weeks:
            weeks[week_key] = {
                "week": week_key,
                "total_distance_km": 0,
                "total_duration_minutes": 0,
                "total_tss": 0,
                "total_calories": 0,
                "activity_count": 0,
                "types": set(),
            }

        w = weeks[week_key]
        w["total_distance_km"] += a.distance_meters / 1000
        w["total_duration_minutes"] += a.moving_time_seconds / 60
        w["total_tss"] += calculate_tss(
            a.moving_time_seconds / 60, a.avg_heart_rate, a.max_heart_rate
        )
        w["total_calories"] += a.calories or 0
        w["activity_count"] += 1
        w["types"].add(a.zfit_type)

    # Convert sets to lists for JSON
    result = []
    for week in sorted(weeks.values(), key=lambda w: w["week"]):
        week["types"] = sorted(week["types"])
        week["total_distance_km"] = round(week["total_distance_km"], 2)
        week["total_duration_minutes"] = round(week["total_duration_minutes"], 1)
        week["total_tss"] = round(week["total_tss"], 1)
        result.append(week)

    return result


# ── Helpers ────────────────────────────────────────────────────────────────

def decode_polyline(encoded: str) -> list[tuple[float, float]]:
    """Decode Google polyline encoding to lat/lng coordinates."""
    if not encoded:
        return []

    coords = []
    index = 0
    lat = lng = 0

    while index < len(encoded):
        if index >= len(encoded):
            break
        # Latitude
        shift = result = 0
        while index < len(encoded):
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        lat += (~(result >> 1) if result & 1 else result >> 1)

        if index >= len(encoded):
            break

        # Longitude
        shift = result = 0
        while index < len(encoded):
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        lng += (~(result >> 1) if result & 1 else result >> 1)

        coords.append((lat / 1e5, lng / 1e5))

    return coords


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

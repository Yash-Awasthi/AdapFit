"""Activity Stream Parser Service.

Extracted from endurain (inspiration).
Fitness activity parsing from GPX/TCX/FIT formats,
GPS coordinate processing, distance calculation, and
activity type classification.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class ActivityType(Enum):
    RUN = 1
    TRAIL_RUN = 2
    VIRTUAL_RUN = 3
    RIDE = 4
    GRAVEL_RIDE = 5
    MTB_RIDE = 6
    VIRTUAL_RIDE = 7
    LAP_SWIM = 8
    OPEN_WATER_SWIM = 9
    WORKOUT = 10
    WALK = 11
    HIKE = 12
    ROWING = 13
    YOGA = 14
    ALPINE_SKI = 15
    NORDIC_SKI = 16
    SNOWBOARD = 17
    TRANSITION = 18
    STRENGTH = 19
    CROSSFIT = 20
    TENNIS = 21
    BADMINTON = 22
    SQUASH = 23
    RACQUETBALL = 24


ACTIVITY_NAME_MAP = {
    1: "Run", 2: "Trail run", 3: "Virtual run",
    4: "Ride", 5: "Gravel ride", 6: "MTB ride", 7: "Virtual ride",
    8: "Lap swimming", 9: "Open water swimming",
    10: "Workout", 11: "Walk", 12: "Hike", 13: "Rowing",
    14: "Yoga", 15: "Alpine ski", 16: "Nordic ski", 17: "Snowboard",
    18: "Transition", 19: "Strength training", 20: "Crossfit",
    21: "Tennis", 22: "TableTennis", 23: "Badminton",
    24: "Squash", 25: "Racquetball",
}

NAME_TO_ACTIVITY = {v: k for k, v in ACTIVITY_NAME_MAP.items()}

ACTIVITY_SPEED_RANGES = {
    ActivityType.RUN: (3.0, 7.0),
    ActivityType.TRAIL_RUN: (2.5, 6.0),
    ActivityType.RIDE: (8.0, 30.0),
    ActivityType.WALK: (1.0, 3.0),
    ActivityType.HIKE: (1.5, 4.0),
    ActivityType.LAP_SWIM: (0.5, 2.5),
    ActivityType.ALPINE_SKI: (5.0, 25.0),
}


@dataclass
class GPSPoint:
    latitude: float
    longitude: float
    altitude: float = 0.0
    timestamp: datetime | None = None
    heart_rate: int | None = None
    cadence: int | None = None
    power: float | None = None


@dataclass
class ActivityLap:
    lap_number: int
    start_time: datetime | None = None
    end_time: datetime | None = None
    distance: float = 0.0
    duration_seconds: float = 0.0
    avg_heart_rate: int | None = None
    max_heart_rate: int | None = None
    avg_speed: float = 0.0
    points: list[GPSPoint] = field(default_factory=list)


@dataclass
class Activity:
    activity_type: ActivityType
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    distance: float = 0.0
    duration_seconds: float = 0.0
    elevation_gain: float = 0.0
    elevation_loss: float = 0.0
    avg_heart_rate: int | None = None
    max_heart_rate: int | None = None
    avg_speed: float = 0.0
    max_speed: float = 0.0
    calories: int = 0
    laps: list[ActivityLap] = field(default_factory=list)
    points: list[GPSPoint] = field(default_factory=list)


@dataclass
class ActivityStream:
    time: list[float] = field(default_factory=list)
    latitude: list[float] = field(default_factory=list)
    longitude: list[float] = field(default_factory=list)
    altitude: list[float] = field(default_factory=list)
    heart_rate: list[int] = field(default_factory=list)
    cadence: list[int] = field(default_factory=list)
    power: list[float] = field(default_factory=list)
    speed: list[float] = field(default_factory=list)


EARTH_RADIUS_KM = 6371.0
METERS_PER_FOOT = 0.3048


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two GPS points in meters using haversine formula."""
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return EARTH_RADIUS_KM * c * 1000


def calculate_total_distance(points: list[GPSPoint]) -> float:
    """Calculate total distance from GPS points in meters."""
    if len(points) < 2:
        return 0.0
    total = 0.0
    for i in range(1, len(points)):
        total += haversine_distance(
            points[i - 1].latitude, points[i - 1].longitude,
            points[i].latitude, points[i].longitude,
        )
    return total


def calculate_elevation_stats(points: list[GPSPoint]) -> tuple[float, float]:
    """Calculate elevation gain and loss from GPS points."""
    gain, loss = 0.0, 0.0
    for i in range(1, len(points)):
        diff = points[i].altitude - points[i - 1].altitude
        if diff > 0:
            gain += diff
        else:
            loss += abs(diff)
    return gain, loss


def calculate_speed_from_gps(points: list[GPSPoint]) -> list[float]:
    """Calculate instantaneous speed at each GPS point in m/s."""
    if len(points) < 2:
        return [0.0] * len(points)
    speeds = [0.0]
    for i in range(1, len(points)):
        dist = haversine_distance(
            points[i - 1].latitude, points[i - 1].longitude,
            points[i].latitude, points[i].longitude,
        )
        if points[i].timestamp and points[i - 1].timestamp:
            dt = (points[i].timestamp - points[i - 1].timestamp).total_seconds()
            speeds.append(dist / dt if dt > 0 else 0.0)
        else:
            speeds.append(0.0)
    return speeds


def classify_activity_type(duration_seconds: float, distance_meters: float) -> ActivityType:
    """Classify activity type from duration and distance."""
    if duration_seconds <= 0:
        return ActivityType.WORKOUT
    speed = distance_meters / duration_seconds
    speed_kmh = speed * 3.6
    if speed_kmh > 20:
        return ActivityType.RIDE
    elif speed_kmh > 5:
        return ActivityType.RUN
    elif speed_kmh > 2:
        return ActivityType.WALK
    else:
        return ActivityType.HIKE


def calculate_calories(
    activity_type: ActivityType, duration_seconds: float,
    weight_kg: float = 70.0, avg_heart_rate: int | None = None,
) -> int:
    """Estimate calories burned."""
    met_values = {
        ActivityType.RUN: 9.8, ActivityType.RIDE: 7.5,
        ActivityType.WALK: 3.8, ActivityType.HIKE: 6.0,            ActivityType.LAP_SWIM: 8.0, ActivityType.YOGA: 3.0,
        ActivityType.STRENGTH: 6.0, ActivityType.CROSSFIT: 12.0,
    }
    met = met_values.get(activity_type, 5.0)
    duration_hours = duration_seconds / 3600
    base_calories = met * weight_kg * duration_hours
    if avg_heart_rate and avg_heart_rate > 120:
        hr_factor = 1.0 + (avg_heart_rate - 120) * 0.005
        base_calories *= min(hr_factor, 1.5)
    return int(base_calories)


def calculate_vo2max(distance_meters: float, duration_seconds: float) -> float:
    """Estimate VO2max from running performance using Cooper's formula."""
    if duration_seconds <= 0 or distance_meters <= 0:
        return 0.0
    distance_km = distance_meters / 1000
    duration_min = duration_seconds / 60
    vo2max = (distance_km - 5.0469) / 0.18225 + 3.5
    return max(0, min(vo2max, 85.0))


def calculate_pace(distance_meters: float, duration_seconds: float) -> float:
    """Calculate pace in seconds per kilometer."""
    if distance_meters <= 0:
        return 0.0
    distance_km = distance_meters / 1000
    return duration_seconds / distance_km


def format_pace(pace_seconds_per_km: float) -> str:
    """Format pace as MM:SS string."""
    minutes = int(pace_seconds_per_km // 60)
    seconds = int(pace_seconds_per_km % 60)
    return f"{minutes}:{seconds:02d}"


def calculate_splits(
    points: list[GPSPoint], split_distance_meters: float = 1000.0,
) -> list[dict[str, Any]]:
    """Calculate kilometer splits from GPS points."""
    if not points:
        return []
    splits = []
    current_split_distance = 0.0
    current_split_start = points[0].timestamp
    split_number = 1
    for i in range(1, len(points)):
        seg_dist = haversine_distance(
            points[i - 1].latitude, points[i - 1].longitude,
            points[i].latitude, points[i].longitude,
        )
        current_split_distance += seg_dist
        if current_split_distance >= split_distance_meters:
            duration = 0.0
            if current_split_start and points[i].timestamp:
                duration = (points[i].timestamp - current_split_start).total_seconds()
            pace = duration / (current_split_distance / 1000) if current_split_distance > 0 else 0
            splits.append({
                "split_number": split_number,
                "distance_meters": current_split_distance,
                "duration_seconds": duration,
                "pace_per_km": pace,
            })
            split_number += 1
            current_split_distance = 0.0
            current_split_start = points[i].timestamp
    return splits


def parse_gpx_points(gpx_xml: str) -> list[GPSPoint]:
    """Parse GPX XML string into GPS points (simplified)."""
    points = []
    try:
        # Uploaded XML: defusedxml refuses entity expansion and external entities.
        import defusedxml.ElementTree as ET
        root = ET.fromstring(gpx_xml)
        ns = {"gpx": "http://www.topografix.com/GPX/1/1"}
        for trkpt in root.findall(".//gpx:trkpt", ns):
            lat = float(trkpt.get("lat", 0))
            lon = float(trkpt.get("lon", 0))
            ele_el = trkpt.find("gpx:ele", ns)
            alt = float(ele_el.text) if ele_el is not None else 0.0
            time_el = trkpt.find("gpx:time", ns)
            ts = datetime.fromisoformat(time_el.text.replace("Z", "+00:00")) if time_el is not None else None
            points.append(GPSPoint(latitude=lat, longitude=lon, altitude=alt, timestamp=ts))
    except Exception:
        pass
    return points


def build_activity_from_points(
    points: list[GPSPoint], activity_type: ActivityType,
) -> Activity:
    """Build a complete Activity from GPS points."""
    if not points:
        return Activity(activity_type=activity_type)
    distance = calculate_total_distance(points)
    gain, loss = calculate_elevation_stats(points)
    speeds = calculate_speed_from_gps(points)
    hr_values = [p.heart_rate for p in points if p.heart_rate is not None]
    duration = 0.0
    if points[-1].timestamp and points[0].timestamp:
        duration = (points[-1].timestamp - points[0].timestamp).total_seconds()
    return Activity(
        activity_type=activity_type,
        start_time=points[0].timestamp or datetime.now(),
        end_time=points[-1].timestamp,
        distance=distance,
        duration_seconds=duration,
        elevation_gain=gain,
        elevation_loss=loss,
        avg_heart_rate=int(sum(hr_values) / len(hr_values)) if hr_values else None,
        max_heart_rate=max(hr_values) if hr_values else None,
        avg_speed=distance / duration if duration > 0 else 0.0,
        max_speed=max(speeds) if speeds else 0.0,
        calories=calculate_calories(activity_type, duration, avg_heart_rate=int(sum(hr_values) / len(hr_values)) if hr_values else None),
        points=points,
    )


def create_stream_from_points(points: list[GPSPoint]) -> ActivityStream:
    """Create ActivityStream from GPS points."""
    stream = ActivityStream()
    for i, p in enumerate(points):
        if p.timestamp and points[0].timestamp:
            stream.time.append((p.timestamp - points[0].timestamp).total_seconds())
        else:
            stream.time.append(float(i))
        stream.latitude.append(p.latitude)
        stream.longitude.append(p.longitude)
        stream.altitude.append(p.altitude)
        if p.heart_rate is not None:
            stream.heart_rate.append(p.heart_rate)
        if p.cadence is not None:
            stream.cadence.append(p.cadence)
        if p.power is not None:
            stream.power.append(p.power)
    speeds = calculate_speed_from_gps(points)
    stream.speed = speeds
    return stream

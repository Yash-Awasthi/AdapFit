"""GPS Route Tracking — outdoor workout route recording with pace, elevation, and map overlay.

Records GPS coordinates during outdoor workouts and computes:
- Route distance, elevation gain, average pace
- Split analysis (per-km or per-mile)
- Pace zones and heart rate correlation
"""

from __future__ import annotations
import uuid
import math
from datetime import datetime, timezone
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional
from app.core.durable import durable_dict

router = APIRouter()

_routes = durable_dict("app.api.v1.endpoints.gps_tracking._routes")


class GPSCoordinate(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    altitude: Optional[float] = None
    accuracy_m: Optional[float] = Field(None, ge=0, description="Horizontal accuracy the phone reported")
    timestamp: str = ""
    heart_rate: Optional[int] = None
    pace_seconds_per_km: Optional[float] = None


class RouteStartRequest(BaseModel):
    workout_type: str = Field("running", description="running, cycling, walking, hiking")
    user_notes: str = Field(max_length=300, default="")


class RoutePointRequest(BaseModel):
    coordinates: list[GPSCoordinate] = Field(max_length=5000)


# A fix worse than this is noise, not position.
MAX_ACCURACY_M = 30
# Faster than this between fixes is a GPS jump, not movement (m/s; ~130 km/h covers cycling downhill).
MAX_SPEED_MS = {"running": 12, "walking": 4, "hiking": 4, "cycling": 36}
# Altitude from GPS wanders a few metres; climbs count only past this step.
ELEVATION_STEP_M = 3


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in meters between two GPS coordinates."""
    R = 6371000  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.post("/start")
async def start_route(req: RouteStartRequest, user_id: str = Query("default")):
    """Start recording a GPS route."""
    route_id = str(uuid.uuid4())[:12]
    route = {
        "route_id": route_id,
        "user_id": user_id,
        "workout_type": req.workout_type,
        "user_notes": req.user_notes,
        "coordinates": [],
        "status": "recording",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    _routes.setdefault(user_id, []).append(route)
    return {"route_id": route_id, "status": "recording"}


@router.post("/{route_id}/points")
async def add_route_points(route_id: str, req: RoutePointRequest, user_id: str = Query("default")):
    """Add GPS coordinates to a route."""
    route = _find_route(user_id, route_id)
    if not route:
        return {"error": "Route not found"}

    if route["status"] != "recording":
        return {"error": "Route already finished"}
    for coord in req.coordinates:
        route["coordinates"].append(coord.model_dump())
    route["coordinates"].sort(key=lambda c: c.get("timestamp") or "")

    stats = _compute_route_stats(route["coordinates"], route["workout_type"])
    return {"points_added": len(req.coordinates), "live_stats": stats}


@router.post("/{route_id}/finish")
async def finish_route(route_id: str, user_id: str = Query("default")):
    """Finish recording a GPS route."""
    route = _find_route(user_id, route_id)
    if not route:
        return {"error": "Route not found"}

    stats = _compute_route_stats(route["coordinates"], route["workout_type"])
    first = route["status"] != "completed"
    route["status"] = "completed"
    route["finished_at"] = datetime.now(timezone.utc).isoformat()
    route["final_stats"] = stats

    saved = False
    if first and stats["distance_m"] > 0:
        from app.core.storage import storage
        await storage.add_workout_log(user_id, {
            "completed_at": route["started_at"], "actual_duration_minutes": stats["duration_minutes"],
            "activity_type": route["workout_type"], "distance_km": stats["distance_km"],
            "elevation_gain_m": stats["elevation_gain_m"], "avg_heart_rate": stats.get("avg_hr"),
            "source": "gps", "external_id": f"gps:{route_id}"})
        saved = True
    return {"route_id": route_id, "stats": stats, "saved_to_history": saved}


@router.get("/{route_id}")
async def get_route(route_id: str, user_id: str = Query("default")):
    """Get route details."""
    route = _find_route(user_id, route_id)
    if not route:
        return {"error": "Route not found"}

    stats = _compute_route_stats(route["coordinates"], route["workout_type"])
    splits = _compute_splits(_clean(route["coordinates"], route["workout_type"]))

    return {
        "route_id": route_id,
        "workout_type": route["workout_type"],
        "status": route["status"],
        "stats": stats,
        "splits": splits,
        "coordinates": route["coordinates"][:500],  # Cap for response size
        "started_at": route["started_at"],
    }


@router.get("")
async def list_routes(user_id: str = Query("default"), limit: int = Query(20, ge=1, le=100)):
    """List user's GPS routes."""
    routes = _routes.get(user_id, [])[-limit:]
    return {
        "routes": [
            {
                "route_id": r["route_id"],
                "workout_type": r["workout_type"],
                "status": r["status"],
                "distance_m": r.get("final_stats", {}).get("distance_m", 0),
                "duration_seconds": r.get("final_stats", {}).get("duration_seconds", 0),
                "started_at": r["started_at"],
            }
            for r in reversed(routes)
        ],
        "total": len(_routes.get(user_id, [])),
    }


def _find_route(user_id: str, route_id: str) -> Optional[dict]:
    for r in _routes.get(user_id, []):
        if r["route_id"] == route_id:
            return r
    return None


def _ts(c: dict) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(c["timestamp"]) if c.get("timestamp") else None
    except ValueError:
        return None


def _clean(coords: list[dict], workout_type: str = "running") -> list[dict]:
    """Drop inaccurate fixes and jumps faster than the activity allows."""
    max_speed = MAX_SPEED_MS.get(workout_type, 12)
    kept: list[dict] = []
    for c in coords:
        if c.get("accuracy_m") is not None and c["accuracy_m"] > MAX_ACCURACY_M:
            continue
        if kept:
            prev = kept[-1]
            t0, t1 = _ts(prev), _ts(c)
            d = _haversine(prev["lat"], prev["lon"], c["lat"], c["lon"])
            if t0 and t1:
                dt = (t1 - t0).total_seconds()
                if dt <= 0 or d / dt > max_speed:
                    continue
        kept.append(c)
    return kept


def _compute_route_stats(coords: list[dict], workout_type: str = "running") -> dict:
    """Distance, time, pace and climb from the fixes that survive filtering."""
    raw_count = len(coords)
    coords = _clean(coords, workout_type)
    if len(coords) < 2:
        return {"distance_m": 0, "distance_km": 0, "duration_seconds": 0, "duration_minutes": 0,
                "avg_pace_seconds_per_km": 0, "elevation_gain_m": 0, "coordinates_count": raw_count,
                "coordinates_used": len(coords)}

    total_distance = 0.0
    elevation_gain = 0.0
    base_alt = None
    for i in range(1, len(coords)):
        total_distance += _haversine(coords[i - 1]["lat"], coords[i - 1]["lon"], coords[i]["lat"], coords[i]["lon"])
    for c in coords:
        alt = c.get("altitude")
        if alt is None:
            continue
        if base_alt is None or alt < base_alt:
            base_alt = alt
        elif alt - base_alt >= ELEVATION_STEP_M:
            elevation_gain += alt - base_alt
            base_alt = alt

    # Duration from timestamps
    t0, t1 = _ts(coords[0]), _ts(coords[-1])
    duration = (t1 - t0).total_seconds() if t0 and t1 else 0

    avg_pace = 0
    if duration > 0 and total_distance > 0:
        avg_pace = duration / (total_distance / 1000)  # seconds per km

    # Heart rate stats
    hr_values = [c.get("heart_rate") for c in coords if c.get("heart_rate")]
    hr_stats = {}
    if hr_values:
        hr_stats = {
            "avg_hr": round(sum(hr_values) / len(hr_values)),
            "max_hr": max(hr_values),
            "min_hr": min(hr_values),
        }

    return {
        "distance_m": round(total_distance, 1),
        "distance_km": round(total_distance / 1000, 2),
        "duration_seconds": round(duration),
        "duration_minutes": round(duration / 60, 1),
        "avg_pace_seconds_per_km": round(avg_pace),
        "avg_pace_min_per_km": f"{int(avg_pace // 60)}:{int(avg_pace % 60):02d}",
        "elevation_gain_m": round(elevation_gain, 1),
        "coordinates_count": raw_count,
        "coordinates_used": len(coords),
        **hr_stats,
    }


def _compute_splits(coords: list[dict], split_km: float = 1.0) -> list[dict]:
    """Compute per-km splits."""
    if len(coords) < 2:
        return []

    splits = []
    current_split_distance = 0
    split_start_idx = 0

    for i in range(1, len(coords)):
        d = _haversine(coords[i - 1]["lat"], coords[i - 1]["lon"], coords[i]["lat"], coords[i]["lon"])
        current_split_distance += d

        if current_split_distance >= split_km * 1000:
            # Calculate split time
            split_coords = coords[split_start_idx:i + 1]
            duration = 0
            if split_coords[0].get("timestamp") and split_coords[-1].get("timestamp"):
                try:
                    t0 = datetime.fromisoformat(split_coords[0]["timestamp"])
                    t1 = datetime.fromisoformat(split_coords[-1]["timestamp"])
                    duration = (t1 - t0).total_seconds()
                except Exception:
                    pass

            splits.append({
                "split_number": len(splits) + 1,
                "distance_m": round(current_split_distance),
                "duration_seconds": round(duration),
                "avg_pace": f"{int(duration // 60)}:{int(duration % 60):02d}",
            })

            current_split_distance = 0
            split_start_idx = i

    return splits

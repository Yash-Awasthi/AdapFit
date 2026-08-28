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

router = APIRouter()

_routes: dict[str, list[dict]] = {}


class GPSCoordinate(BaseModel):
    lat: float
    lon: float
    altitude: float = 0
    timestamp: str = ""
    heart_rate: Optional[int] = None
    pace_seconds_per_km: Optional[float] = None


class RouteStartRequest(BaseModel):
    workout_type: str = Field("running", description="running, cycling, walking, hiking")
    user_notes: str = Field(max_length=300, default="")


class RoutePointRequest(BaseModel):
    coordinates: list[GPSCoordinate]


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

    for coord in req.coordinates:
        route["coordinates"].append(coord.model_dump())

    # Compute live stats
    stats = _compute_route_stats(route["coordinates"])
    return {"points_added": len(req.coordinates), "live_stats": stats}


@router.post("/{route_id}/finish")
async def finish_route(route_id: str, user_id: str = Query("default")):
    """Finish recording a GPS route."""
    route = _find_route(user_id, route_id)
    if not route:
        return {"error": "Route not found"}

    route["status"] = "completed"
    route["finished_at"] = datetime.now(timezone.utc).isoformat()
    stats = _compute_route_stats(route["coordinates"])
    route["final_stats"] = stats

    return {"route_id": route_id, "stats": stats}


@router.get("/{route_id}")
async def get_route(route_id: str, user_id: str = Query("default")):
    """Get route details."""
    route = _find_route(user_id, route_id)
    if not route:
        return {"error": "Route not found"}

    stats = _compute_route_stats(route["coordinates"])
    splits = _compute_splits(route["coordinates"])

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


def _compute_route_stats(coords: list[dict]) -> dict:
    """Compute route statistics from coordinates."""
    if len(coords) < 2:
        return {"distance_m": 0, "duration_seconds": 0, "avg_pace": 0, "elevation_gain_m": 0}

    total_distance = 0
    elevation_gain = 0

    for i in range(1, len(coords)):
        d = _haversine(coords[i - 1]["lat"], coords[i - 1]["lon"], coords[i]["lat"], coords[i]["lon"])
        total_distance += d
        alt_diff = coords[i].get("altitude", 0) - coords[i - 1].get("altitude", 0)
        if alt_diff > 0:
            elevation_gain += alt_diff

    # Duration from timestamps
    duration = 0
    if coords[0].get("timestamp") and coords[-1].get("timestamp"):
        try:
            t0 = datetime.fromisoformat(coords[0]["timestamp"])
            t1 = datetime.fromisoformat(coords[-1]["timestamp"])
            duration = (t1 - t0).total_seconds()
        except Exception:
            pass

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
        "coordinates_count": len(coords),
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

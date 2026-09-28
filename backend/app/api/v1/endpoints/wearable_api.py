"""
Wearable imports (Garmin, Strava, GPX) into the caller's own records.

Workouts become workout logs and Garmin nights become sleep-journal entries,
so imported history feeds training form, the briefing and achievements like
anything logged in the app. Re-importing the same file adds nothing twice.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.per_user import current_user_id
from app.core.storage import storage
from app.services.garmin_import import import_sleep_records, import_workouts
from app.services.sleep_tracker import sleep_journal
from app.services.strava_import import import_activities
from app.core.durable import durable_dict

router = APIRouter()
MAX_GPX_BYTES = 5_000_000
_import_log = durable_dict("app.api.v1.endpoints.wearable_api._import_log")


class GarminImportInput(BaseModel):
    workouts: Optional[list[dict]] = Field(None, max_length=5000)
    sleep_records: Optional[list[dict]] = Field(None, max_length=5000)


class StravaImportInput(BaseModel):
    activities: list[dict] = Field(max_length=5000)


class GPXImportInput(BaseModel):
    gpx: str = Field(min_length=20, max_length=MAX_GPX_BYTES)
    activity: str = Field("run", pattern=r"^(run|ride|walk|hike)$")


async def _existing_ids(uid: str) -> set[str]:
    return {w.get("external_id") for w in await storage.get_workout_logs(uid, 3650) if w.get("external_id")}


async def _save_workout(uid: str, seen: set[str], external_id: str, entry: dict) -> bool:
    if external_id in seen:
        return False
    seen.add(external_id)
    await storage.add_workout_log(uid, {**entry, "external_id": external_id})
    return True


def _log(uid: str, source: str, imported: int, skipped: int) -> None:
    _import_log.setdefault(uid, []).append({"source": source, "imported": imported, "skipped": skipped,
                                            "timestamp": datetime.now(timezone.utc).isoformat()})


@router.post("/garmin/import")
async def garmin_import(body: GarminImportInput):
    uid = current_user_id()
    seen = await _existing_ids(uid)
    saved = skipped = 0
    for w in import_workouts(body.workouts or [])["data"]:
        ok = await _save_workout(uid, seen, f"garmin:{w.timestamp}:{w.activity_type}", {
            "completed_at": w.timestamp, "actual_duration_minutes": round(w.duration_seconds / 60, 1),
            "activity_type": w.activity_type, "distance_km": round(w.distance_meters / 1000, 2),
            "avg_heart_rate": w.avg_heart_rate, "max_heart_rate": w.max_heart_rate,
            "elevation_gain_m": w.elevation_gain, "calories": w.calories, "source": "garmin"})
        saved, skipped = saved + ok, skipped + (not ok)
    journal = sleep_journal.instance_for(uid)
    known_nights = {n["date"] for n in journal.nights(3650) if n["source"] == "wearable"}
    nights = 0
    for rec in import_sleep_records(body.sleep_records or [])["data"]:
        try:
            start, end = datetime.fromisoformat(rec.sleep_start), datetime.fromisoformat(rec.sleep_end)
        except ValueError:
            continue
        if rec.date in known_nights:
            continue
        journal.log(start.strftime("%H:%M"), end.strftime("%H:%M"), date=end.strftime("%Y-%m-%d"),
                    total_minutes=rec.total_minutes or None, source="wearable",
                    deep_minutes=rec.deep_minutes, rem_minutes=rec.rem_minutes,
                    light_minutes=rec.light_minutes, awake_minutes=rec.awake_minutes)
        known_nights.add(rec.date)
        nights += 1
    _log(uid, "garmin", saved + nights, skipped)
    return {"source": "garmin", "workouts_saved": saved, "nights_saved": nights, "skipped_duplicates": skipped}


@router.post("/strava/import")
async def strava_import(body: StravaImportInput):
    uid = current_user_id()
    seen = await _existing_ids(uid)
    saved = skipped = 0
    for a in import_activities(body.activities)["data"]:
        ok = await _save_workout(uid, seen, f"strava:{a.id}", {
            "completed_at": a.start_date, "actual_duration_minutes": round(a.moving_time_seconds / 60, 1),
            "activity_type": a.zfit_type, "name": a.name, "distance_km": round(a.distance_meters / 1000, 2),
            "avg_heart_rate": a.avg_heart_rate, "max_heart_rate": a.max_heart_rate,
            "elevation_gain_m": a.total_elevation_gain, "avg_power_w": a.avg_power, "source": "strava"})
        saved, skipped = saved + ok, skipped + (not ok)
    _log(uid, "strava", saved, skipped)
    return {"source": "strava", "workouts_saved": saved, "skipped_duplicates": skipped}


@router.post("/gpx/import")
async def gpx_import(body: GPXImportInput):
    """A GPX track (Strava, Garmin, Komoot, phone apps) as one workout."""
    from app.services.activity_stream_parser import ActivityType, build_activity_from_points, parse_gpx_points

    if "<!DOCTYPE" in body.gpx or "<!ENTITY" in body.gpx:
        raise HTTPException(status_code=422, detail="GPX files do not use DOCTYPE or ENTITY declarations")
    points = parse_gpx_points(body.gpx)
    if len(points) < 2 or not points[0].timestamp:
        raise HTTPException(status_code=422, detail="No timed track points found in this GPX file")
    from app.services.activity_stream_parser import haversine_distance
    from app.services.cycling_analysis import detect_climbs

    kind = {"run": ActivityType.RUN, "ride": ActivityType.RIDE, "walk": ActivityType.WALK, "hike": ActivityType.HIKE}[body.activity]
    a = build_activity_from_points(points, kind)
    uid = current_user_id()
    ok = await _save_workout(uid, await _existing_ids(uid), f"gpx:{a.start_time.isoformat()}", {
        "completed_at": a.start_time.isoformat(), "actual_duration_minutes": round(a.duration_seconds / 60, 1),
        "activity_type": body.activity, "distance_km": round(a.distance / 1000, 2),
        "elevation_gain_m": round(a.elevation_gain), "avg_heart_rate": a.avg_heart_rate, "source": "gpx"})
    _log(uid, "gpx", int(ok), int(not ok))
    cumulative, total = [0.0], 0.0
    for p, q in zip(points, points[1:]):
        total += haversine_distance(p.latitude, p.longitude, q.latitude, q.longitude) / 1000
        cumulative.append(total)
    climbs = detect_climbs(cumulative, [p.altitude for p in points])
    return {"saved": ok, "distance_km": round(a.distance / 1000, 2), "duration_minutes": round(a.duration_seconds / 60, 1),
            "elevation_gain_m": round(a.elevation_gain),
            "climbs": [{"start_km": round(c.start_km, 2), "length_km": round(c.length_km, 2), "gain_m": round(c.elevation_gain_m),
                        "avg_grade_pct": round(c.avg_grade_pct, 1), "category": c.category} for c in climbs]}


@router.get("/status")
async def wearable_status():
    log = _import_log.get(current_user_id(), [])
    out = {}
    for source in ("garmin", "strava", "gpx"):
        entries = [e for e in log if e["source"] == source]
        out[source] = {"imports": len(entries), "records": sum(e["imported"] for e in entries),
                       "last_import": entries[-1]["timestamp"] if entries else None}
    return out


@router.get("/sync-log")
async def sync_log():
    return {"log": list(reversed(_import_log.get(current_user_id(), [])[-50:]))}

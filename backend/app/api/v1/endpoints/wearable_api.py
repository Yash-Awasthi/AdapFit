"""Wearable data import endpoints — Garmin and Strava."""
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.garmin_import import (
    import_daily_summaries, import_workouts, import_sleep_records,
)
from app.services.strava_import import (
    import_activities, aggregate_weekly,
)

router = APIRouter()

# In-memory import log (wire to DB when ready)
_import_log: list[dict] = []


class GarminImportInput(BaseModel):
    daily_summaries: Optional[list[dict]] = None
    workouts: Optional[list[dict]] = None
    sleep_records: Optional[list[dict]] = None


class StravaImportInput(BaseModel):
    activities: list[dict]


@router.post("/garmin/import")
def garmin_import(body: GarminImportInput):
    """Import Garmin Connect data (daily summaries, workouts, sleep)."""
    results = {}
    total_imported = 0

    if body.daily_summaries:
        r = import_daily_summaries(body.daily_summaries)
        results["daily_summaries"] = {k: v for k, v in r.items() if k != "data"}
        total_imported += r["imported"]

    if body.workouts:
        r = import_workouts(body.workouts)
        results["workouts"] = {k: v for k, v in r.items() if k != "data"}
        total_imported += r["imported"]

    if body.sleep_records:
        r = import_sleep_records(body.sleep_records)
        results["sleep"] = {k: v for k, v in r.items() if k != "data"}
        total_imported += r["imported"]

    _import_log.append({
        "source": "garmin",
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        "imported": total_imported,
        "types": list(results.keys()),
    })

    return {"source": "garmin", "total_imported": total_imported, "results": results}


@router.post("/strava/import")
def strava_import(body: StravaImportInput):
    """Import Strava activities with training load calculation."""
    r = import_activities(body.activities)

    _import_log.append({
        "source": "strava",
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        "imported": r["imported"],
        "types": ["activities"],
    })

    return {
        "source": "strava",
        "imported": r["imported"],
        "skipped_duplicates": r["skipped_duplicates"],
        "errors": r["errors"],
        "type_summary": r["type_summary"],
        "weekly_volume": r["weekly_volume"],
    }


@router.get("/status")
def wearable_status():
    """Show imported data summary per source."""
    garmin_imports = [l for l in _import_log if l["source"] == "garmin"]
    strava_imports = [l for l in _import_log if l["source"] == "strava"]

    return {
        "garmin": {
            "total_imports": len(garmin_imports),
            "total_records": sum(l["imported"] for l in garmin_imports),
            "last_import": garmin_imports[-1]["timestamp"] if garmin_imports else None,
        },
        "strava": {
            "total_imports": len(strava_imports),
            "total_records": sum(l["imported"] for l in strava_imports),
            "last_import": strava_imports[-1]["timestamp"] if strava_imports else None,
        },
    }


@router.delete("/data")
def clear_data():
    """Clear all imported data."""
    _import_log.clear()
    return {"status": "cleared", "message": "All imported wearable data cleared"}


@router.get("/sync-log")
def sync_log():
    """Show import history."""
    return {"log": list(reversed(_import_log[-50:]))}  # Last 50 entries

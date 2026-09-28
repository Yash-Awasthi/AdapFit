"""
Data export: each record type as CSV or JSON, or everything held for the user.

`/all` is the portability export: stored records plus every per-user service's
state, so nothing the app keeps about a person is missing from it.
"""
from fastapi import APIRouter, HTTPException, Query, Response

from app.core import per_user
from app.core.export import envelope, to_csv
from app.core.storage import storage
from app.services.sleep_tracker import sleep_journal

router = APIRouter()
ALL_TIME = 3650


async def _workouts(uid: str) -> list[dict]:
    return await storage.get_workout_logs(uid, ALL_TIME)


async def _recovery(uid: str) -> list[dict]:
    return await storage.get_recovery_logs(uid, ALL_TIME)


async def _nutrition(uid: str) -> list[dict]:
    from app.api.v1.endpoints.nutrition import meal_logs
    return list(meal_logs.get(uid, []))


async def _body(uid: str) -> list[dict]:
    from app.api.v1.endpoints.body_composition import measurements
    return list(measurements.get(uid, []))


async def _sleep(uid: str) -> list[dict]:
    return sleep_journal.instance_for(uid).nights(ALL_TIME)


SOURCES = {
    "workouts": ("Workout History", "Completed workouts with sets, RPE and notes", _workouts),
    "recovery": ("Daily Check-ins", "Recovery scores, HRV, sleep and how you felt", _recovery),
    "nutrition": ("Nutrition Log", "Meals with macros", _nutrition),
    "body": ("Body Measurements", "Weight, body fat and circumferences", _body),
    "sleep": ("Sleep Journal", "Nights logged, with stages when a wearable measured them", _sleep),
}


@router.get("/formats")
async def available_formats():
    return {
        "formats": ["csv", "json"],
        "data_types": [{"id": k, "name": n, "description": d} for k, (n, d, _) in SOURCES.items()]
        + [{"id": "all", "name": "Everything", "description": "Every record and setting the app holds for you (JSON)"}],
    }


@router.get("/all")
async def export_all(user_id: str = Query("default")):
    data = {key: await fetch(user_id) for key, (_, _, fetch) in SOURCES.items()}
    data["profile"] = await storage.get_user(user_id)
    data["baseline"] = await storage.get_baseline(user_id)
    data["coach_memory"] = await storage.get_agent_memory(user_id)
    data["feature_data"] = per_user.export_user(user_id)
    return envelope(user_id, data)


@router.get("/{data_type}")
async def export_one(
    data_type: str,
    user_id: str = Query("default"),
    format: str = Query("csv", pattern="^(csv|json)$"),
):
    if data_type not in SOURCES:
        raise HTTPException(status_code=404, detail=f"Unknown data type. Choose from {sorted(SOURCES)} or 'all'.")
    rows = await SOURCES[data_type][2](user_id)
    if format == "csv":
        return Response(content=to_csv(rows), media_type="text/csv",
                        headers={"Content-Disposition": f"attachment; filename=adapfit-{data_type}.csv"})
    return envelope(user_id, {data_type: rows})

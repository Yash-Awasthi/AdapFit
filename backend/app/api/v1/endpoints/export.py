"""Data export: download workout history, health metrics as JSON or CSV."""
from fastapi import APIRouter, Query, Response
from app.core.export import (
    export_workout_history, export_recovery_logs, export_nutrition,
    export_body_measurements, export_sleep_logs, generate_full_export,
)
from app.services.notification_scheduler import get_pending_notifications

router = APIRouter()

# In-memory references to data stores (imported at use time)
# In production these would be database queries


@router.get("/workouts")
async def export_workouts(
    user_id: str = Query("default"),
    format: str = Query("csv", pattern="^(csv|json)$"),
):
    """Export workout history."""
    # Get workouts from the in-memory store
    try:
        from app.api.v1.endpoints.workouts import workout_history
        workouts = workout_history.get(user_id, [])
    except (ImportError, AttributeError):
        workouts = []

    if format == "csv":
        result = export_workout_history(workouts)
        return Response(
            content=result["content"],
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={result['filename']}"},
        )
    return generate_full_export({"workouts": workouts})


@router.get("/recovery")
async def export_recovery(
    user_id: str = Query("default"),
    format: str = Query("csv", pattern="^(csv|json)$"),
):
    """Export recovery logs."""
    try:
        from app.api.v1.endpoints.recovery import recovery_logs
        logs = recovery_logs.get(user_id, [])
    except (ImportError, AttributeError):
        logs = []

    if format == "csv":
        result = export_recovery_logs(logs)
        return Response(
            content=result["content"],
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={result['filename']}"},
        )
    return generate_full_export({"recovery_logs": logs})


@router.get("/nutrition")
async def export_nutrition(
    user_id: str = Query("default"),
    format: str = Query("csv", pattern="^(csv|json)$"),
):
    """Export nutrition logs."""
    try:
        from app.api.v1.endpoints.nutrition import meal_logs
        meals = meal_logs.get(user_id, [])
    except (ImportError, AttributeError):
        meals = []

    if format == "csv":
        result = export_nutrition(meals)
        return Response(
            content=result["content"],
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={result['filename']}"},
        )
    return generate_full_export({"meals": meals})


@router.get("/body")
async def export_body(
    user_id: str = Query("default"),
    format: str = Query("csv", pattern="^(csv|json)$"),
):
    """Export body composition measurements."""
    try:
        from app.api.v1.endpoints.body_composition import measurements
        data = measurements.get(user_id, [])
    except (ImportError, AttributeError):
        data = []

    if format == "csv":
        result = export_body_measurements(data)
        return Response(
            content=result["content"],
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={result['filename']}"},
        )
    return generate_full_export({"body_measurements": data})


@router.get("/sleep")
async def export_sleep(
    user_id: str = Query("default"),
    format: str = Query("csv", pattern="^(csv|json)$"),
):
    """Export sleep logs."""
    try:
        from app.api.v1.endpoints.sleep import sleep_logs
        logs = sleep_logs.get(user_id, [])
    except (ImportError, AttributeError):
        logs = []

    if format == "csv":
        result = export_sleep_logs(logs)
        return Response(
            content=result["content"],
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={result['filename']}"},
        )
    return generate_full_export({"sleep_logs": logs})


@router.get("/all")
async def export_all(user_id: str = Query("default")):
    """Export all user data as a single JSON file."""
    data = {}

    # Gather all data
    for module_name, import_path, attr in [
        ("workouts", "app.api.v1.endpoints.workouts", "workout_history"),
        ("recovery_logs", "app.api.v1.endpoints.recovery", "recovery_logs"),
        ("meals", "app.api.v1.endpoints.nutrition", "meal_logs"),
        ("body_measurements", "app.api.v1.endpoints.body_composition", "measurements"),
        ("sleep_logs", "app.api.v1.endpoints.sleep", "sleep_logs"),
    ]:
        try:
            import importlib
            mod = importlib.import_module(import_path)
            store = getattr(mod, attr, {})
            data[module_name] = store.get(user_id, []) if isinstance(store, dict) else []
        except Exception:
            data[module_name] = []

    # Notifications
    data["notifications"] = [
        n.model_dump() for n in get_pending_notifications(user_id)
    ]

    return generate_full_export(data)


@router.get("/formats")
async def available_formats():
    """List available export formats and data types."""
    return {
        "formats": ["csv", "json"],
        "data_types": [
            {"id": "workouts", "name": "Workout History", "description": "All generated and completed workouts"},
            {"id": "recovery", "name": "Recovery Logs", "description": "Daily recovery scores and metrics"},
            {"id": "nutrition", "name": "Nutrition Log", "description": "Meal entries with macros"},
            {"id": "body", "name": "Body Measurements", "description": "Weight, body fat, circumference measurements"},
            {"id": "sleep", "name": "Sleep Logs", "description": "Sleep duration, efficiency, and stages"},
            {"id": "all", "name": "Complete Export", "description": "All data in a single JSON file (JSON only)"},
        ],
    }

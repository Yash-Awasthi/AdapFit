"""Workout import/export: share workout plans between users as JSON."""
import uuid
import json
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Any

router = APIRouter()


class WorkoutPlanExport(BaseModel):
    """Exportable workout plan format."""
    format_version: str = "1.0"
    app: str = "AdapFit"
    exported_at: str
    exported_by: str
    plan: dict


class WorkoutPlanImport(BaseModel):
    format_version: str = "1.0"
    plan: dict
    name: Optional[str] = None  # Optional rename on import


class ExportedPlanSummary(BaseModel):
    id: str
    name: str
    exercise_count: int
    target_duration: int
    exported_at: str
    exported_by: str


# In-memory exported plans
exported_plans: dict = {}  # plan_id -> plan data
import_history: dict = {}  # user_id -> list of imports


@router.post("/export", response_model=WorkoutPlanExport)
async def export_workout(
    workout_id: str = Query(...),
    user_id: str = Query("default"),
):
    """Export a workout as a shareable JSON plan."""
    try:
        from app.core.storage import storage
        workouts = await storage.get_workouts(user_id, 90)
    except Exception:
        workouts = []

    workout = next((w for w in workouts if w.get("workout_id") == workout_id), None)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    plan = {
        "workout_id": workout.get("workout_id", ""),
        "title": workout.get("title", "Untitled Workout"),
        "readiness_state": workout.get("readiness_state", "MODERATE"),
        "target_duration_minutes": workout.get("target_duration_minutes", 45),
        "warmup": workout.get("warmup", []),
        "exercises": workout.get("exercises", []),
        "cooldown": workout.get("cooldown", []),
        "adaptation_rationale": workout.get("adaptation_rationale", ""),
    }

    exported = WorkoutPlanExport(
        exported_at=datetime.now(timezone.utc).isoformat(),
        exported_by=user_id,
        plan=plan,
    )

    pid = str(uuid.uuid4())[:8]
    exported_plans[pid] = {
        "id": pid,
        "plan": exported.model_dump(),
        "user_id": user_id,
    }

    return exported


@router.post("/import")
async def import_workout(request: WorkoutPlanImport, user_id: str = Query("default")):
    """Import a workout plan from exported JSON."""
    plan = request.plan
    if not plan:
        raise HTTPException(status_code=400, detail="Invalid plan data")

    title = request.name or plan.get("title", "Imported Workout")

    # Create the imported workout
    exercises = plan.get("exercises", [])
    if not exercises:
        raise HTTPException(status_code=400, detail="Plan has no exercises")

    imported = {
        "workout_id": str(uuid.uuid4())[:8],
        "title": title,
        "source": "import",
        "imported_from": plan.get("workout_id", "unknown"),
        "readiness_state": plan.get("readiness_state", "MODERATE"),
        "target_duration_minutes": plan.get("target_duration_minutes", 45),
        "warmup": plan.get("warmup", []),
        "exercises": exercises,
        "cooldown": plan.get("cooldown", []),
        "adaptation_rationale": plan.get("adaptation_rationale", "Imported plan"),
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "imported_by": user_id,
    }

    pid = str(uuid.uuid4())[:8]
    import_history.setdefault(user_id, []).append({
        "id": pid,
        "title": title,
        "exercise_count": len(exercises),
        "imported_at": imported["imported_at"],
    })

    return {
        "message": f"Workout '{title}' imported successfully",
        "workout_id": imported["workout_id"],
        "exercises": len(exercises),
    }


@router.get("/exported", response_model=List[ExportedPlanSummary])
async def list_exported(user_id: str = Query("default")):
    """List workouts you've exported."""
    user_exports = [
        e for e in exported_plans.values() if e["user_id"] == user_id
    ]
    return [
        ExportedPlanSummary(
            id=e["id"],
            name=e["plan"]["plan"].get("title", "Untitled"),
            exercise_count=len(e["plan"]["plan"].get("exercises", [])),
            target_duration=e["plan"]["plan"].get("target_duration_minutes", 0),
            exported_at=e["plan"]["exported_at"],
            exported_by=user_id,
        )
        for e in user_exports
    ]


@router.get("/imported")
async def list_imported(user_id: str = Query("default")):
    """List workouts you've imported."""
    return import_history.get(user_id, [])


@router.get("/shared/{plan_id}")
async def get_shared_plan(plan_id: str):
    """Get an exported plan by its ID (for sharing)."""
    export = exported_plans.get(plan_id)
    if not export:
        raise HTTPException(status_code=404, detail="Plan not found")
    return export["plan"]


@router.post("/quick-export")
async def quick_export(
    name: str = Query(...),
    exercise_ids: List[str] = Query(...),
    user_id: str = Query("default"),
):
    """Quick export a custom workout plan from exercise IDs."""
    from app.services.exercise_service import exercise_service
    all_exercises = {e.id: e for e in exercise_service.get_all()}

    exercises = []
    for eid in exercise_ids:
        if eid in all_exercises:
            ex = all_exercises[eid]
            exercises.append({
                "exercise_id": ex.id,
                "name": ex.name,
                "target_muscle": ex.primary_muscles[0] if ex.primary_muscles else "unknown",
                "sets": 3,
                "target_reps": "8-12",
                "target_rpe": 7,
                "rest_seconds": 90,
            })

    if not exercises:
        raise HTTPException(status_code=400, detail="No valid exercises found")

    plan = {
        "title": name,
        "exercises": exercises,
        "target_duration_minutes": len(exercises) * 8,
    }

    exported = WorkoutPlanExport(
        exported_at=datetime.now(timezone.utc).isoformat(),
        exported_by=user_id,
        plan=plan,
    )

    pid = str(uuid.uuid4())[:8]
    exported_plans[pid] = {"id": pid, "plan": exported.model_dump(), "user_id": user_id}

    return {"id": pid, "name": name, "exercises": len(exercises)}

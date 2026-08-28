"""Personal Best Tracker — track and retrieve personal records for each exercise."""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional
from app.core.storage import storage

router = APIRouter()

# In-memory PR storage
_pr_records: dict[str, list[dict]] = {}  # user_id -> list of PR records


class PRLogRequest(BaseModel):
    exercise_id: str
    exercise_name: str
    weight_kg: float = Field(ge=0)
    reps: int = Field(ge=1)
    sets: int = Field(ge=1, default=1)
    rpe: Optional[float] = None
    date: Optional[str] = None
    notes: str = Field(max_length=300, default="")


@router.post("/log")
async def log_pr(req: PRLogRequest, user_id: str = Query("default")):
    """Log a personal record for an exercise."""
    # Calculate estimated 1RM using Epley formula
    e1rm = req.weight_kg * (1 + req.reps / 30) if req.reps > 1 else req.weight_kg

    record = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "exercise_id": req.exercise_id,
        "exercise_name": req.exercise_name,
        "weight_kg": req.weight_kg,
        "reps": req.reps,
        "sets": req.sets,
        "estimated_1rm": round(e1rm, 1),
        "rpe": req.rpe,
        "date": req.date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "notes": req.notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if user_id not in _pr_records:
        _pr_records[user_id] = []
    _pr_records[user_id].append(record)

    # Check if this is a new PR
    existing = [r for r in _pr_records[user_id]
                if r["exercise_id"] == req.exercise_id and r["id"] != record["id"]]
    is_new_pr = True
    pr_type = "first"

    if existing:
        best_weight = max(r["weight_kg"] for r in existing)
        best_1rm = max(r["estimated_1rm"] for r in existing)
        if req.weight_kg <= best_weight:
            is_new_pr = False
            pr_type = "not_new"
        elif e1rm > best_1rm:
            pr_type = "1rm_improvement"
        else:
            pr_type = "volume_pr"

    return {
        "record": record,
        "is_new_pr": is_new_pr,
        "pr_type": pr_type,
        "estimated_1rm": round(e1rm, 1),
    }


@router.get("")
async def get_prs(
    user_id: str = Query("default"),
    exercise_id: Optional[str] = Query(None),
):
    """Get all personal records for a user."""
    records = _pr_records.get(user_id, [])

    if exercise_id:
        records = [r for r in records if r["exercise_id"] == exercise_id]

    # Group by exercise, keeping best for each
    prs_by_exercise = {}
    for r in records:
        eid = r["exercise_id"]
        if eid not in prs_by_exercise:
            prs_by_exercise[eid] = r
        else:
            if r["estimated_1rm"] > prs_by_exercise[eid]["estimated_1rm"]:
                prs_by_exercise[eid] = r

    # Sort by date descending
    all_records = sorted(records, key=lambda r: r["created_at"], reverse=True)

    return {
        "bests": prs_by_exercise,
        "total_records": len(records),
        "total_exercises": len(prs_by_exercise),
        "recent": all_records[:20],
    }


@router.get("/{exercise_id}/progress")
async def get_pr_progress(
    exercise_id: str,
    user_id: str = Query("default"),
):
    """Get PR progress history for a specific exercise."""
    records = _pr_records.get(user_id, [])
    exercise_records = [r for r in records if r["exercise_id"] == exercise_id]
    exercise_records.sort(key=lambda r: r["created_at"])

    if not exercise_records:
        return {"exercise_id": exercise_id, "records": [], "best_1rm": 0, "improvements": []}

    # Track improvements (new PRs)
    improvements = []
    best_so_far = 0
    for r in exercise_records:
        if r["estimated_1rm"] > best_so_far:
            improvements.append({
                "date": r["date"],
                "weight_kg": r["weight_kg"],
                "reps": r["reps"],
                "estimated_1rm": r["estimated_1rm"],
                "improvement": round(r["estimated_1rm"] - best_so_far, 1),
            })
            best_so_far = r["estimated_1rm"]

    return {
        "exercise_id": exercise_id,
        "records": exercise_records,
        "best_1rm": round(best_so_far, 1),
        "total_attempts": len(exercise_records),
        "improvements": improvements,
        "first_pr_date": exercise_records[0]["date"] if exercise_records else None,
        "latest_pr_date": exercise_records[-1]["date"] if exercise_records else None,
    }


@router.delete("/{record_id}")
async def delete_pr(record_id: str, user_id: str = Query("default")):
    """Delete a PR record."""
    records = _pr_records.get(user_id, [])
    idx = next((i for i, r in enumerate(records) if r["id"] == record_id), None)
    if idx is None:
        return {"error": "Record not found"}
    records.pop(idx)
    return {"deleted": True}

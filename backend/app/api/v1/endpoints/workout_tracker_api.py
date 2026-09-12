"""
Workout Tracker API — workout logging, PR detection, progress analysis.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field

router = APIRouter()


class StartSessionRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    user_id: str = Field(min_length=1, max_length=128)
    workout_type: str = Field(default="", max_length=64)


class LogSetRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    exercise_name: str = Field(min_length=1, max_length=128)
    set_number: int = Field(ge=1, le=50)
    reps: int = Field(ge=0, le=100)
    weight_kg: float = Field(ge=0, le=500)
    rpe: float | None = Field(default=None, ge=1, le=10)
    is_warmup: bool = False


class EndSessionRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    mood_post: int | None = Field(default=None, ge=1, le=10)


@lru_cache(maxsize=1)
def _get_tracker():
    from src.tracker.workout_tracker import WorkoutTracker
    return WorkoutTracker()


@router.post("/session/start", summary="Start a new workout session")
async def start_session(req: StartSessionRequest) -> dict[str, str]:
    tracker = _get_tracker()
    session = tracker.start_session(req.session_id, req.user_id, req.workout_type)
    return {"session_id": session.session_id, "started_at": session.started_at.isoformat()}


@router.post("/session/log-set", summary="Log a set in a workout session")
async def log_set(req: LogSetRequest) -> dict[str, Any]:
    tracker = _get_tracker()
    set_log = tracker.log_set(
        req.session_id, req.exercise_name, req.set_number,
        req.reps, req.weight_kg, req.rpe, req.is_warmup,
    )
    if set_log:
        return {"logged": True, "set": set_log.set_number, "volume": set_log.reps * set_log.weight_kg}
    return {"logged": False, "error": "Session not found"}


@router.post("/session/end", summary="End a workout session and check for PRs")
async def end_session(req: EndSessionRequest) -> dict[str, Any]:
    tracker = _get_tracker()
    session = tracker.end_session(req.session_id, req.mood_post)
    if session:
        return {
            "session_id": session.session_id,
            "duration_min": round(session.duration_minutes, 1),
            "total_volume": round(session.total_volume, 1),
            "exercises": session.exercise_count,
            "sets": session.set_count,
        }
    raise HTTPException(status_code=404, detail="Session not found")


@router.get("/history/{user_id}", summary="Get workout history for a user")
async def get_history(
    user_id: str = Path(min_length=1, max_length=128),
    limit: int = Query(default=10, ge=1, le=100),
) -> list[dict[str, Any]]:
    tracker = _get_tracker()
    return [
        {
            "session_id": s.session_id,
            "started_at": s.started_at.isoformat(),
            "duration_min": round(s.duration_minutes, 1),
            "total_volume": round(s.total_volume, 1),
            "exercises": s.exercise_count,
        }
        for s in tracker.get_user_history(user_id, limit)
    ]


@router.get("/prs/{exercise_name}", summary="Get personal records for an exercise")
async def get_prs(
    exercise_name: str = Path(min_length=1, max_length=128),
) -> dict[str, dict[str, Any]]:
    tracker = _get_tracker()
    prs = tracker.get_prs(exercise_name)
    return {
        exercise_name: {
            k: {"best": v.new_best, "achieved": v.achieved_at.isoformat()}
            for k, v in prs.items()
        }
    }


@router.get("/weekly-summary/{user_id}", summary="Get weekly training summary")
async def weekly_summary(
    user_id: str = Path(min_length=1, max_length=128),
    weeks: int = Query(default=4, ge=1, le=12),
) -> dict[str, Any]:
    return _get_tracker().get_weekly_summary(user_id, weeks)

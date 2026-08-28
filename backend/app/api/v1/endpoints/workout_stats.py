"""Workout statistics dashboard — volume, PRs, muscle distribution, monthly comparison."""

from __future__ import annotations
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Query
from app.core.storage import storage

router = APIRouter()


def _muscle_for(exercise_id: str, fallback: str) -> str:
    """Resolve the primary muscle group for an exercise id."""
    if exercise_id == "unknown" or not exercise_id:
        return fallback
    try:
        from app.services.exercise_service import exercise_service
        ex = exercise_service.get_by_id(exercise_id)
        if ex and ex.primary_muscles:
            return ex.primary_muscles[0]
    except Exception:
        pass
    return fallback


async def _get_workout_data(user_id: str, days: int = 365) -> list[dict]:
    """Fetch workout history for stats computation."""
    try:
        workouts = await storage.get_workouts(user_id, days)
    except Exception:
        workouts = []
    return workouts or []


def _iter_performance_exercises(workouts: list[dict], logs: list[dict]):
    """Yield (exercise_id, target_muscle, weight_kg, reps, sets, date) from both
    generated workout plans and completed workout logs (real performance data)."""
    for w in workouts:
        date_str = w.get("target_date") or (w.get("created_at") or "")[:10]
        for ex in w.get("exercises", []):
            weight = ex.get("actual_weight", 0) or 0
            reps = ex.get("actual_reps", 0) or 0
            sets = ex.get("sets", 0) or 0
            yield ex.get("exercise_id", "unknown"), ex.get("target_muscle", "unknown"), weight, reps, sets, date_str

    for log in logs:
        date_str = (log.get("completed_at") or log.get("created_at") or "")[:10]
        for ex in log.get("logged_exercises", []):
            sets_data = ex.get("sets", []) or []
            if not isinstance(sets_data, list):
                sets_data = []
            sets = len(sets_data)
            weight = 0.0
            reps = 0
            for s in sets_data:
                weight = max(weight, s.get("weight_kg", 0) or 0)
                reps = max(reps, s.get("reps_completed", 0) or 0)
            muscle = _muscle_for(
                ex.get("exercise_id", "unknown"),
                ex.get("target_muscle") or ex.get("muscle") or "unknown",
            )
            yield ex.get("exercise_id", "unknown"), muscle, weight, reps, sets, date_str


@router.get("/{user_id}")
async def get_workout_stats(user_id: str, days: int = Query(365, ge=7, le=730)):
    """Comprehensive workout statistics dashboard."""
    workouts = await _get_workout_data(user_id, days)
    try:
        logs = await storage.get_workout_logs(user_id, days)
    except Exception:
        logs = []

    if not workouts and not logs:
        return {
            "user_id": user_id,
            "period_days": days,
            "total_workouts": 0,
            "total_volume_kg": 0,
            "total_duration_minutes": 0,
            "avg_session_rpe": 0,
            "personal_records": [],
            "muscle_distribution": {},
            "monthly_comparison": [],
            "workout_frequency": {},
            "summary": "No workout data yet. Start training to see your stats!",
        }

    # --- Aggregate stats (plans + completed logs) ---
    total = len(workouts) + len(logs)
    total_duration = sum(w.get("actual_duration_minutes", 0) or 0 for w in workouts)
    total_duration += sum(l.get("actual_duration_minutes", 0) or 0 for l in logs)
    rpes = [w.get("session_rpe", 0) for w in workouts if w.get("session_rpe")]
    rpes += [l.get("session_rpe", 0) for l in logs if l.get("session_rpe")]
    avg_rpe = round(sum(rpes) / len(rpes), 1) if rpes else 0

    total_volume = 0
    exercise_volumes: dict[str, float] = {}
    muscle_volume: dict[str, float] = {}
    exercise_prs: dict[str, dict] = {}

    for eid, muscle, weight, reps, sets, date_str in _iter_performance_exercises(workouts, logs):
        vol = weight * reps * sets
        total_volume += vol
        exercise_volumes[eid] = exercise_volumes.get(eid, 0) + vol
        muscle_volume[muscle] = muscle_volume.get(muscle, 0) + vol
        if weight > 0:
            current = exercise_prs.get(eid, {"weight": 0})
            if weight > current["weight"]:
                exercise_prs[eid] = {"weight": weight, "reps": reps, "date": date_str or ""}

    # Personal records list
    prs = [
        {"exercise_id": eid, "weight_kg": pr["weight"], "reps": pr["reps"], "date": pr["date"]}
        for eid, pr in sorted(exercise_prs.items(), key=lambda x: x[1]["weight"], reverse=True)[:10]
    ]

    # Muscle distribution percentages
    total_muscle_vol = sum(muscle_volume.values()) or 1
    muscle_dist = {
        m: round(v / total_muscle_vol * 100, 1)
        for m, v in sorted(muscle_volume.items(), key=lambda x: x[1], reverse=True)
    }

    # Monthly comparison (last 6 months)
    monthly = {}
    for src in (workouts, logs):
        for w in src:
            date_str = w.get("target_date") or w.get("completed_at") or w.get("created_at", "")
            if not date_str:
                continue
            month_key = date_str[:7]
            if month_key not in monthly:
                monthly[month_key] = {"workouts": 0, "duration": 0, "volume": 0}
            monthly[month_key]["workouts"] += 1
            monthly[month_key]["duration"] += w.get("actual_duration_minutes", 0) or 0
            for ex in w.get("exercises", w.get("logged_exercises", [])):
                sets_data = ex.get("sets", []) or []
                if isinstance(sets_data, list) and sets_data:
                    for s in sets_data:
                        monthly[month_key]["volume"] += (s.get("weight_kg", 0) or 0) * (s.get("reps_completed", 0) or 0)
                else:
                    sets_n = sets_data if isinstance(sets_data, int) else 0
                    monthly[month_key]["volume"] += (
                        (ex.get("actual_weight", 0) or 0) *
                        (ex.get("actual_reps", 0) or 0) *
                        sets_n
                    )

    monthly_list = [
        {"month": k, **v, "avg_rpe": 0}
        for k, v in sorted(monthly.items(), reverse=True)[:6]
    ]

    # Workout frequency (day of week)
    freq: dict[str, int] = {}
    for src in (workouts, logs):
        for w in src:
            date_str = w.get("target_date") or w.get("completed_at") or w.get("created_at", "")
            if not date_str:
                continue
            try:
                dow = datetime.strptime(date_str[:10], "%Y-%m-%d").strftime("%A")
                freq[dow] = freq.get(dow, 0) + 1
            except Exception:
                pass

    return {
        "user_id": user_id,
        "period_days": days,
        "total_workouts": total,
        "total_volume_kg": round(total_volume, 1),
        "total_duration_minutes": total_duration,
        "avg_session_rpe": avg_rpe,
        "personal_records": prs,
        "muscle_distribution": muscle_dist,
        "monthly_comparison": monthly_list,
        "workout_frequency": freq,
        "top_exercises": sorted(
            [{"exercise_id": eid, "total_volume": round(vol, 0)} for eid, vol in exercise_volumes.items()],
            key=lambda x: x["total_volume"],
            reverse=True,
        )[:5],
        "summary": f"{total} workouts, {round(total_volume)}kg total volume, {total_duration}min total time.",
    }


@router.get("/{user_id}/personal-records")
async def get_personal_records(user_id: str):
    """Get personal records across all exercises."""
    workouts = await _get_workout_data(user_id, 730)
    try:
        logs = await storage.get_workout_logs(user_id, 730)
    except Exception:
        logs = []
    prs: dict[str, dict] = {}

    for eid, muscle, weight, reps, sets, date_str in _iter_performance_exercises(workouts, logs):
        if weight > 0:
            current = prs.get(eid, {"weight": 0})
            if weight > current["weight"]:
                prs[eid] = {
                    "weight": weight,
                    "reps": reps,
                    "date": date_str or "",
                    "estimated_1rm": round(weight * (1 + reps / 30), 1) if reps > 1 else weight,
                }

    return {
        "user_id": user_id,
        "personal_records": [
            {"exercise_id": eid, **pr}
            for eid, pr in sorted(prs.items(), key=lambda x: x[1]["weight"], reverse=True)
        ],
        "total_prs": len(prs),
    }

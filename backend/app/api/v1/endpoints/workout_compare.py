"""Workout Comparison — compare workouts side-by-side with metrics delta."""

from __future__ import annotations
from fastapi import APIRouter, Query
from app.core.storage import storage

router = APIRouter()


async def _merge_workout_data(user_id: str, workouts: list[dict]) -> list[dict]:
    """Merge workout generation data with completion logs."""
    logs = await storage.get_workout_logs(user_id, 365)
    log_by_wid = {l.get("workout_id"): l for l in logs if l.get("workout_id")}
    merged = []
    for w in workouts:
        wid = w.get("workout_id")
        log = log_by_wid.get(wid, {})
        merged_w = {**w}
        if log:
            merged_w["actual_duration_minutes"] = log.get("actual_duration_minutes", w.get("target_duration_minutes", 0))
            merged_w["session_rpe"] = log.get("session_rpe", 0)
            merged_w["session_load"] = log.get("session_load", 0)
            if "logged_exercises" in log:
                merged_w["exercises"] = log["logged_exercises"]
        else:
            merged_w.setdefault("actual_duration_minutes", w.get("target_duration_minutes", 0))
        merged.append(merged_w)
    return merged


def _calc_metrics(w: dict) -> dict:
    exercises = w.get("exercises", [])
    total_volume = 0.0
    total_sets = 0
    total_reps = 0
    weights = []
    for e in exercises:
        raw_sets = e.get("sets", 0) or 0
        if isinstance(raw_sets, list):
            # logged_exercises format: sets is a list of set objects
            s = len(raw_sets)
            for st in raw_sets:
                sr = st.get("reps_completed", st.get("reps", 0)) or 0
                sw = st.get("weight_kg", st.get("actual_weight", 0)) or 0
                total_volume += sw * sr
                total_reps += sr
                if sw:
                    weights.append(sw)
        else:
            s = raw_sets or e.get("set_number", 0) or 0
            r = e.get("actual_reps", 0) or 0
            wt = e.get("actual_weight", 0) or 0
            total_volume += wt * r * s
            total_reps += r * s
            if wt:
                weights.append(wt)
        total_sets += s
    avg_weight = sum(weights) / len(weights) if weights else 0

    return {
        "duration_minutes": w.get("actual_duration_minutes", 0) or 0,
        "session_rpe": w.get("session_rpe", 0) or 0,
        "session_load": w.get("session_load", 0) or 0,
        "total_volume_kg": round(total_volume, 1),
        "total_sets": total_sets,
        "total_reps": total_reps,
        "avg_weight_kg": round(avg_weight, 1),
        "exercise_count": len(exercises),
        "readiness_state": w.get("readiness_state"),
        "recovery_score": w.get("recovery_score"),
        "calories_burned": w.get("calories_burned", 0) or 0,
    }


@router.get("/compare")
async def compare_workouts(
    user_id: str = Query("default"),
    workout_id_a: str = Query(..., description="First workout ID"),
    workout_id_b: str = Query(..., description="Second workout ID"),
):
    """Compare two workouts side-by-side."""
    workouts = await storage.get_workouts(user_id, 365)
    workouts = await _merge_workout_data(user_id, workouts)

    wa = next((w for w in workouts if w.get("workout_id") == workout_id_a), None)
    wb = next((w for w in workouts if w.get("workout_id") == workout_id_b), None)

    if not wa:
        return {"error": f"Workout {workout_id_a} not found"}
    if not wb:
        return {"error": f"Workout {workout_id_b} not found"}

    metrics_a = _calc_metrics(wa)
    metrics_b = _calc_metrics(wb)

    # Calculate deltas
    deltas = {}
    for key in metrics_a:
        va = metrics_a.get(key, 0) or 0
        vb = metrics_b.get(key, 0) or 0
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            delta = round(vb - va, 1)
            pct = round(delta / abs(va) * 100, 1) if va != 0 else (0 if delta == 0 else 100)
            deltas[key] = {"delta": delta, "pct_change": pct}
        else:
            deltas[key] = {"from": va, "to": vb}

    # Exercise-level comparison
    ex_a = {e.get("exercise_id") or e.get("name", ""): e for e in wa.get("exercises", [])}
    ex_b = {e.get("exercise_id") or e.get("name", ""): e for e in wb.get("exercises", [])}

    common_exercises = []
    for eid in set(ex_a.keys()) & set(ex_b.keys()):
        ea = ex_a[eid]
        eb = ex_b[eid]
        vol_a = (ea.get("actual_weight", 0) or 0) * (ea.get("actual_reps", 0) or 0)
        vol_b = (eb.get("actual_weight", 0) or 0) * (eb.get("actual_reps", 0) or 0)
        common_exercises.append({
            "exercise_id": eid,
            "name": ea.get("name", eid),
            "weight_delta": (eb.get("actual_weight", 0) or 0) - (ea.get("actual_weight", 0) or 0),
            "reps_delta": (eb.get("actual_reps", 0) or 0) - (ea.get("actual_reps", 0) or 0),
            "volume_delta": round(vol_b - vol_a, 1),
            "sets_a": ea.get("sets", 0),
            "sets_b": eb.get("sets", 0),
        })

    return {
        "workout_a": {"workout_id": workout_id_a, "date": wa.get("target_date"), "metrics": metrics_a},
        "workout_b": {"workout_id": workout_id_b, "date": wb.get("target_date"), "metrics": metrics_b},
        "deltas": deltas,
        "common_exercises": common_exercises,
        "summary": _build_comparison_summary(metrics_a, metrics_b, deltas),
    }


@router.get("/history")
async def workout_history(
    user_id: str = Query("default"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get workout history with basic metrics."""
    workouts = await storage.get_workouts(user_id, 365)
    workouts = await _merge_workout_data(user_id, workouts)

    items = []
    for w in workouts[offset:offset + limit]:
        exercises = w.get("exercises", [])
        items.append({
            "workout_id": w.get("workout_id"),
            "date": w.get("target_date"),
            "title": w.get("title", "Workout"),
            "duration_minutes": w.get("actual_duration_minutes", 0) or 0,
            "session_rpe": w.get("session_rpe", 0) or 0,
            "exercise_count": len(exercises),
            "total_volume_kg": round(
                sum(
                    (e.get("actual_weight", 0) or 0) * (e.get("actual_reps", 0) or 0) * (e.get("sets", 0) or 0)
                    for e in exercises
                ), 1
            ),
        })

    return {"items": items, "total": len(workouts), "has_more": offset + limit < len(workouts)}


def _build_comparison_summary(a: dict, b: dict, deltas: dict) -> str:
    parts = []
    dur_delta = deltas.get("duration_minutes", {}).get("delta", 0)
    if dur_delta > 0:
        parts.append(f"Duration increased by {dur_delta} min")
    elif dur_delta < 0:
        parts.append(f"Duration decreased by {abs(dur_delta)} min")

    vol_delta = deltas.get("total_volume_kg", {}).get("delta", 0)
    if vol_delta > 0:
        parts.append(f"Volume increased by {vol_delta} kg")
    elif vol_delta < 0:
        parts.append(f"Volume decreased by {abs(vol_delta)} kg")

    rpe_a = a.get("session_rpe", 0)
    rpe_b = b.get("session_rpe", 0)
    if rpe_b > rpe_a:
        parts.append(f"RPE increased ({rpe_a} -> {rpe_b})")
    elif rpe_b < rpe_a:
        parts.append(f"RPE decreased ({rpe_a} -> {rpe_b})")

    if not parts:
        return "Both workouts are similar in duration and intensity."
    return ". ".join(parts) + "."

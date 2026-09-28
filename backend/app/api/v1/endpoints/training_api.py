"""
Training analytics over logged sessions: fitness, fatigue and form
(Banister impulse-response on session-RPE load), intensity distribution, and
fuelling plans for long rides.

Only sessions with a recorded RPE count; a session without one would enter the
model at an assumed effort and move every curve by a number nobody measured.
"""
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.core.storage import storage
from app.core.workout_metrics import _first_number, session_duration_minutes
from app.services.cycling_fueling_planner import RideType, generate_fueling_plan
from app.services.endurance_coaching import DailyTrainingLoad, calculate_ctl_atl, classify_tsb
from app.services.training_intensity import classify_distribution

router = APIRouter()


def _day(log: dict) -> str | None:
    raw = log.get("completed_at") or log.get("created_at")
    return str(raw)[:10] if raw else None


def _measured_sessions(logs: list[dict]) -> tuple[list[tuple[str, float, float]], int]:
    """(day, rpe, minutes) for sessions with a recorded RPE, and how many were skipped."""
    out, skipped = [], 0
    for log in logs:
        rpe = _first_number(log, ("session_rpe", "rpe"))
        day = _day(log)
        if rpe is None or day is None:
            skipped += 1
            continue
        out.append((day, max(1.0, min(10.0, rpe)), session_duration_minutes(log)))
    return out, skipped


@router.get("/form")
async def fitness_fatigue_form(user_id: str, days: int = Query(90, ge=14, le=365)):
    logs = await storage.get_workout_logs(user_id, days + 42)
    sessions, skipped = _measured_sessions(logs)
    if not sessions:
        return {"series": [], "today": None, "sessions_used": 0, "sessions_without_rpe": skipped,
                "message": "Log RPE with your workouts to see fitness, fatigue and form."}
    per_day: dict[str, float] = defaultdict(float)
    for day, rpe, minutes in sessions:
        per_day[day] += rpe * minutes
    start = datetime.strptime(min(per_day), "%Y-%m-%d").date()
    loads = []
    d = start
    while d <= date.today():
        key = d.isoformat()
        loads.append(DailyTrainingLoad(date=key, tss=per_day.get(key, 0.0), duration_min=0))
        d += timedelta(days=1)
    series = calculate_ctl_atl(loads)[-days:]
    last = series[-1]
    return {
        "series": [{"date": m.date, "fitness": m.ctl, "fatigue": m.atl, "form": m.tsb, "load": m.tss_today} for m in series],
        "today": {"fitness": last.ctl, "fatigue": last.atl, "form": last.tsb, **classify_tsb(last.tsb)},
        "sessions_used": len(sessions),
        "sessions_without_rpe": skipped,
        "units": "session RPE x minutes",
    }


@router.get("/intensity")
async def intensity_distribution(user_id: str, days: int = Query(28, ge=7, le=180)):
    """Easy / moderate / hard split by session RPE (Foster's three zones), weighted by time."""
    sessions, skipped = _measured_sessions(await storage.get_workout_logs(user_id, days))
    minutes = {"easy": 0.0, "moderate": 0.0, "hard": 0.0}
    for _, rpe, mins in sessions:
        minutes["easy" if rpe <= 4 else "moderate" if rpe <= 6 else "hard"] += mins
    total = sum(minutes.values())
    if total == 0:
        return {"distribution": None, "sessions_used": 0, "sessions_without_rpe": skipped}
    pct = {k: round(v / total * 100, 1) for k, v in minutes.items()}
    c = classify_distribution(pct["easy"], pct["moderate"], pct["hard"])
    return {
        "distribution": pct,
        "pattern": c.label,
        "description": c.description,
        "minutes": {k: round(v) for k, v in minutes.items()},
        "sessions_used": len(sessions),
        "sessions_without_rpe": skipped,
    }


class FuelingRequest(BaseModel):
    duration_hours: float = Field(gt=0, le=12)
    ride_type: Literal["endurance", "long_ride", "threshold", "vo2", "race", "hill", "sprint", "recovery"] = "endurance"
    weight_kg: float = Field(70, ge=30, le=200)


@router.post("/ride-fueling")
async def ride_fueling(req: FuelingRequest):
    plan = generate_fueling_plan(RideType(req.ride_type), req.duration_hours, 0, req.weight_kg)
    return {
        "strategy": plan.strategy.value, "total_carbs_g": round(plan.total_carbs_grams),
        "carbs_per_hour_g": round(plan.carbs_per_hour), "gels": plan.gel_count, "bottles": plan.bottle_count,
        "water_ml": plan.water_ml, "sodium_mg": plan.sodium_mg, "pre_ride_meal": plan.pre_ride_meal,
        "timeline": plan.timeline,
    }

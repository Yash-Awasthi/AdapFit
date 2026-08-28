"""Workout streaks: current streak, best streak, calendar heatmap data."""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List
from app.core.storage import storage

router = APIRouter()


class StreakInfo(BaseModel):
    current_streak: int
    best_streak: int
    total_workouts: int
    workouts_this_week: int
    workouts_this_month: int
    avg_workouts_per_week: float
    last_workout_date: str | None


class CalendarDay(BaseModel):
    date: str
    workout: bool
    workout_type: str | None = None
    intensity: int = 0  # 0-5 scale for heatmap


class HeatmapData(BaseModel):
    year: int
    weeks: List[List[CalendarDay]]


# In-memory: user_id -> list of ISO date strings
workout_dates: dict = {}


def _compute_streaks(dates: list[str]) -> tuple[int, int]:
    """Compute current and best streak from sorted unique dates."""
    if not dates:
        return 0, 0

    unique = sorted(set(dates), reverse=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Current streak
    current = 0
    expected = datetime.strptime(today, "%Y-%m-%d")
    for d in unique:
        actual = datetime.strptime(d, "%Y-%m-%d")
        diff = (expected - actual).days
        if diff <= 1:
            current += 1
            expected = actual - timedelta(days=1)
        else:
            break

    # Best streak
    sorted_asc = sorted(set(dates))
    best = 1
    run = 1
    for i in range(1, len(sorted_asc)):
        prev = datetime.strptime(sorted_asc[i - 1], "%Y-%m-%d")
        curr = datetime.strptime(sorted_asc[i], "%Y-%m-%d")
        if (curr - prev).days == 1:
            run += 1
            best = max(best, run)
        else:
            run = 1

    return current, best


async def _all_workout_dates(user_id: str) -> list[str]:
    """Merge explicit log dates with completed workout logs (single source of truth)."""
    dates = list(workout_dates.get(user_id, []))
    try:
        logs = await storage.get_workout_logs(user_id, 365)
        for log in logs:
            completed = log.get("completed_at") or log.get("created_at")
            if completed:
                dates.append(completed[:10])
        workouts = await storage.get_workouts(user_id, 365)
        for w in workouts:
            d = w.get("target_date") or (w.get("created_at") or "")[:10]
            if d:
                dates.append(d[:10])
    except Exception:
        pass
    return dates


@router.get("", response_model=StreakInfo)
async def get_streaks(user_id: str = Query("default")):
    """Get workout streak information."""
    dates = await _all_workout_dates(user_id)
    today = datetime.now(timezone.utc)
    today_str = today.strftime("%Y-%m-%d")

    unique = sorted(set(dates))
    current, best = _compute_streaks(dates)

    # This week
    week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
    this_week = len([d for d in unique if d >= week_start])

    # This month
    month_start = today.replace(day=1).strftime("%Y-%m-%d")
    this_month = len([d for d in unique if d >= month_start])

    # Avg per week
    if unique:
        first = datetime.strptime(unique[0], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        weeks = max(1, (today - first).days / 7)
        avg = round(len(unique) / weeks, 1)
    else:
        avg = 0

    return StreakInfo(
        current_streak=current,
        best_streak=best,
        total_workouts=len(unique),
        workouts_this_week=this_week,
        workouts_this_month=this_month,
        avg_workouts_per_week=avg,
        last_workout_date=unique[-1] if unique else None,
    )


@router.get("/heatmap", response_model=List[CalendarDay])
async def get_heatmap(user_id: str = Query("default"), months: int = Query(6, ge=1, le=12)):
    """Get calendar heatmap data for the past N months."""
    dates = await _all_workout_dates(user_id)
    today = datetime.now(timezone.utc)
    start = today - timedelta(days=months * 30)
    unique = set(dates)

    days = []
    d = start
    today_date = today.date()
    while d.date() <= today_date:
        ds = d.strftime("%Y-%m-%d")
        days.append(CalendarDay(
            date=ds, workout=ds in unique,
            intensity=3 if ds in unique else 0,
        ))
        d += timedelta(days=1)

    return days


@router.post("/log")
async def log_workout_date(user_id: str = Query("default"), date: str = Query(...)):
    """Log a workout date for streak tracking."""
    workout_dates.setdefault(user_id, []).append(date)
    return {"logged": True, "date": date}

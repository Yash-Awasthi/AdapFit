"""Hydration tracking: log water intake, daily goals, streaks, reminders."""
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter()


class HydrateLogRequest(BaseModel):
    amount_ml: int = Field(ge=10, le=5000, examples=[250])
    drink_type: str = Field(default="water", examples=["water", "tea", "coffee", "sports_drink", "juice"])
    note: Optional[str] = Field(None, max_length=200)


class HydrateGoalUpdate(BaseModel):
    daily_goal_ml: int = Field(ge=500, le=10000, default=3000)
    reminder_interval_minutes: int = Field(ge=15, le=240, default=60)


class HydrateLogResponse(BaseModel):
    id: str
    amount_ml: int
    drink_type: str
    note: Optional[str]
    logged_at: str


class DailyHydration(BaseModel):
    date: str
    total_ml: int
    daily_goal_ml: int
    progress_pct: float
    goal_met: bool
    log_count: int
    drink_breakdown: dict  # type -> ml
    hourly分布: dict  # hour -> ml


class HydrationStats(BaseModel):
    avg_daily_ml: float
    avg_daily_goal_pct: float
    total_logs: int
    goal_met_days: int
    goal_met_rate: float
    current_streak: int
    best_streak: int
    favorite_drink: str
    trend: str  # "improving", "stable", "declining"


# In-memory storage
hydration_logs: dict = {}  # user_id -> list of logs
hydration_goals: dict = {}  # user_id -> {daily_goal_ml, reminder_interval_minutes}


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _update_streak(user_id: str) -> tuple[int, int]:
    """Calculate current and best streak of meeting daily goal."""
    logs = hydration_logs.get(user_id, [])
    goal = hydration_goals.get(user_id, {}).get("daily_goal_ml", 3000)

    # Group by date
    daily_totals: dict[str, int] = {}
    for l in logs:
        d = l["logged_at"][:10]
        daily_totals[d] = daily_totals.get(d, 0) + l["amount_ml"]

    met_dates = sorted([d for d, t in daily_totals.items() if t >= goal], reverse=True)
    if not met_dates:
        return 0, 0

    # Current streak
    current = 0
    expected = datetime.now(timezone.utc).date()
    for d_str in met_dates:
        d = datetime.strptime(d_str, "%Y-%m-%d").date()
        diff = (expected - d).days
        if diff <= 1:
            current += 1
            expected = d - timedelta(days=1)
        else:
            break

    # Best streak
    sorted_asc = sorted(set(met_dates))
    best = 1
    run = 1
    for i in range(1, len(sorted_asc)):
        d1 = datetime.strptime(sorted_asc[i - 1], "%Y-%m-%d").date()
        d2 = datetime.strptime(sorted_asc[i], "%Y-%m-%d").date()
        if (d2 - d1).days == 1:
            run += 1
            best = max(best, run)
        else:
            run = 1

    return current, best


@router.get("/today", response_model=DailyHydration)
async def get_today(user_id: str = Query("default")):
    """Get today's hydration summary."""
    return _get_daily_summary(user_id, _today())


@router.get("/daily/{date}", response_model=DailyHydration)
async def get_daily(user_id: str = Query("default"), date: str = ""):
    """Get hydration for a specific date."""
    return _get_daily_summary(user_id, date)


def _get_daily_summary(user_id: str, date: str) -> DailyHydration:
    logs = hydration_logs.get(user_id, [])
    day_logs = [l for l in logs if l["logged_at"][:10] == date]
    goal = hydration_goals.get(user_id, {}).get("daily_goal_ml", 3000)

    total = sum(l["amount_ml"] for l in day_logs)
    breakdown = {}
    hourly = {}
    for l in day_logs:
        dt = l["drink_type"]
        breakdown[dt] = breakdown.get(dt, 0) + l["amount_ml"]
        hour = l["logged_at"][11:13] if len(l["logged_at"]) > 13 else "00"
        hourly[hour] = hourly.get(hour, 0) + l["amount_ml"]

    return DailyHydration(
        date=date, total_ml=total, daily_goal_ml=goal,
        progress_pct=round(min(100, (total / goal) * 100), 1) if goal else 0,
        goal_met=total >= goal, log_count=len(day_logs),
        drink_breakdown=breakdown, hourly分布=hourly,
    )


@router.post("/log", response_model=HydrateLogResponse, status_code=201)
async def log_hydration(request: HydrateLogRequest, user_id: str = Query("default")):
    """Log a drink."""
    lid = str(uuid.uuid4())[:8]
    entry = {
        "id": lid,
        "amount_ml": request.amount_ml,
        "drink_type": request.drink_type,
        "note": request.note,
        "logged_at": datetime.now(timezone.utc).isoformat(),
    }
    hydration_logs.setdefault(user_id, []).append(entry)
    return HydrateLogResponse(**entry)


@router.delete("/log/{log_id}")
async def delete_log(log_id: str, user_id: str = Query("default")):
    """Delete a hydration log entry."""
    logs = hydration_logs.get(user_id, [])
    for i, l in enumerate(logs):
        if l["id"] == log_id:
            logs.pop(i)
            return {"deleted": True}
    raise HTTPException(status_code=404, detail="Log not found")


@router.get("/logs", response_model=List[HydrateLogResponse])
async def list_logs(user_id: str = Query("default"), date: Optional[str] = Query(None), limit: int = Query(50, ge=1, le=200)):
    """List hydration logs."""
    logs = hydration_logs.get(user_id, [])
    if date:
        logs = [l for l in logs if l["logged_at"][:10] == date]
    logs.sort(key=lambda l: l["logged_at"], reverse=True)
    return [HydrateLogResponse(**l) for l in logs[:limit]]


@router.get("/goal")
async def get_goal(user_id: str = Query("default")):
    """Get hydration goal."""
    return hydration_goals.get(user_id, {"daily_goal_ml": 3000, "reminder_interval_minutes": 60})


@router.put("/goal")
async def update_goal(request: HydrateGoalUpdate, user_id: str = Query("default")):
    """Update hydration goal."""
    hydration_goals[user_id] = {
        "daily_goal_ml": request.daily_goal_ml,
        "reminder_interval_minutes": request.reminder_interval_minutes,
    }
    return hydration_goals[user_id]


@router.get("/stats", response_model=HydrationStats)
async def get_stats(user_id: str = Query("default"), days: int = Query(30, ge=7, le=365)):
    """Get hydration statistics."""
    logs = hydration_logs.get(user_id, [])
    goal = hydration_goals.get(user_id, {}).get("daily_goal_ml", 3000)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    recent = [l for l in logs if l["logged_at"][:10] >= cutoff]

    # Daily totals
    daily: dict[str, int] = {}
    for l in recent:
        d = l["logged_at"][:10]
        daily[d] = daily.get(d, 0) + l["amount_ml"]

    if not daily:
        return HydrationStats(
            avg_daily_ml=0, avg_daily_goal_pct=0, total_logs=0,
            goal_met_days=0, goal_met_rate=0, current_streak=0,
            best_streak=0, favorite_drink="water", trend="stable",
        )

    totals = list(daily.values())
    met_days = sum(1 for t in totals if t >= goal)

    # Favorite drink
    drink_counts: dict[str, int] = {}
    for l in recent:
        drink_counts[l["drink_type"]] = drink_counts.get(l["drink_type"], 0) + 1
    fav = max(drink_counts, key=drink_counts.get) if drink_counts else "water"

    # Trend
    if len(totals) >= 4:
        mid = len(totals) // 2
        recent_avg = sum(totals[:mid]) / mid if mid else 0
        older_avg = sum(totals[mid:]) / (len(totals) - mid) if mid else 0
        if recent_avg > older_avg * 1.1:
            trend = "improving"
        elif recent_avg < older_avg * 0.9:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"

    current, best = _update_streak(user_id)

    return HydrationStats(
        avg_daily_ml=round(sum(totals) / len(totals)),
        avg_daily_goal_pct=round(sum(min(100, (t / goal) * 100) for t in totals) / len(totals), 1),
        total_logs=len(recent),
        goal_met_days=met_days,
        goal_met_rate=round((met_days / len(daily) * 100) if daily else 0, 1),
        current_streak=current, best_streak=best,
        favorite_drink=fav, trend=trend,
    )


@router.get("/quick-add")
async def quick_add_options():
    """Get common quick-add amounts."""
    return {
        "options": [
            {"amount_ml": 150, "label": "Small glass", "icon": "🥛"},
            {"amount_ml": 250, "label": "Regular glass", "icon": "💧"},
            {"amount_ml": 350, "label": "Large glass", "icon": "🥤"},
            {"amount_ml": 500, "label": "Water bottle", "icon": "🍶"},
            {"amount_ml": 750, "label": "Large bottle", "icon": "🧴"},
        ]
    }

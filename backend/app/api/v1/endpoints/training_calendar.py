"""Training plan calendar: schedule workouts, view week plan, manage sessions."""
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter()


class ScheduleWorkoutRequest(BaseModel):
    date: str = Field(examples=["2026-01-15"])
    workout_type: str = Field(default="strength", examples=["strength", "hypertrophy", "endurance", "cardio", "rest", "mobility"])
    title: str = Field(max_length=200, default="")
    duration_minutes: int = Field(ge=10, le=180, default=45)
    focus_muscles: List[str] = Field(default_factory=list)
    template_id: Optional[str] = None
    notes: str = Field(max_length=500, default="")
    priority: str = Field(default="normal", examples=["low", "normal", "high"])


class CalendarEntry(BaseModel):
    id: str
    date: str
    workout_type: str
    title: str
    duration_minutes: int
    focus_muscles: List[str]
    template_id: Optional[str]
    notes: str
    priority: str
    status: str  # "scheduled", "completed", "missed", "skipped"
    scheduled_by: str
    created_at: str


class WeekPlan(BaseModel):
    week_start: str
    week_end: str
    entries: List[CalendarEntry]
    total_duration_minutes: int
    scheduled_days: int
    completed_days: int
    rest_days: int


class MonthOverview(BaseModel):
    year: int
    month: int
    total_scheduled: int
    total_completed: int
    total_minutes: int
    completion_rate: float
    workout_types: dict  # type -> count


# In-memory storage
calendar_entries: dict = {}  # user_id -> list of CalendarEntry dicts


def _get_week_range(date_str: str) -> tuple[str, str]:
    """Get Monday-Sunday range for a given date."""
    d = datetime.strptime(date_str, "%Y-%m-%d")
    monday = d - timedelta(days=d.weekday())
    sunday = monday + timedelta(days=6)
    return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")


@router.get("/week", response_model=WeekPlan)
async def get_week_plan(
    user_id: str = Query("default"),
    date: Optional[str] = Query(None, description="Any date in the target week"),
):
    """Get the weekly training plan."""
    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    week_start, week_end = _get_week_range(date)
    entries = [
        e for e in calendar_entries.get(user_id, [])
        if week_start <= e["date"] <= week_end
    ]
    entries.sort(key=lambda e: e["date"])

    total_duration = sum(e["duration_minutes"] for e in entries)
    scheduled_days = len(set(e["date"] for e in entries))
    completed_days = len(set(e["date"] for e in entries if e["status"] == "completed"))
    rest_days = len([e for e in entries if e["workout_type"] == "rest"])

    return WeekPlan(
        week_start=week_start, week_end=week_end,
        entries=[CalendarEntry(**e) for e in entries],
        total_duration_minutes=total_duration,
        scheduled_days=scheduled_days,
        completed_days=completed_days,
        rest_days=rest_days,
    )


@router.get("/month", response_model=MonthOverview)
async def get_month_overview(
    user_id: str = Query("default"),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
):
    """Get monthly training overview."""
    now = datetime.now(timezone.utc)
    y = year or now.year
    m = month or now.month

    month_entries = [
        e for e in calendar_entries.get(user_id, [])
        if e["date"].startswith(f"{y}-{m:02d}")
    ]

    type_counts = {}
    for e in month_entries:
        t = e["workout_type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    completed = len([e for e in month_entries if e["status"] == "completed"])
    total = len(month_entries)

    return MonthOverview(
        year=y, month=m,
        total_scheduled=total,
        total_completed=completed,
        total_minutes=sum(e["duration_minutes"] for e in month_entries),
        completion_rate=round((completed / total * 100) if total else 0, 1),
        workout_types=type_counts,
    )


@router.get("/date/{date}")
async def get_day_plan(user_id: str = Query("default"), date: str = ""):
    """Get workouts scheduled for a specific date."""
    entries = [
        e for e in calendar_entries.get(user_id, [])
        if e["date"] == date
    ]
    return {
        "date": date,
        "entries": [CalendarEntry(**e) for e in entries],
        "total_duration": sum(e["duration_minutes"] for e in entries),
    }


@router.post("", response_model=CalendarEntry, status_code=201)
async def schedule_workout(request: ScheduleWorkoutRequest, user_id: str = Query("default")):
    """Schedule a workout on a specific date."""
    eid = str(uuid.uuid4())[:8]
    entry = {
        "id": eid,
        "date": request.date,
        "workout_type": request.workout_type,
        "title": request.title or f"{request.workout_type.title()} Day",
        "duration_minutes": request.duration_minutes,
        "focus_muscles": request.focus_muscles,
        "template_id": request.template_id,
        "notes": request.notes,
        "priority": request.priority,
        "status": "scheduled",
        "scheduled_by": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    calendar_entries.setdefault(user_id, []).append(entry)
    return CalendarEntry(**entry)


@router.post("/bulk")
async def bulk_schedule(
    user_id: str = Query("default"),
    plan: str = Query("ppl", description="ppl, upper_lower, full_body"),
    weeks: int = Query(1, ge=1, le=4),
    start_date: Optional[str] = Query(None),
):
    """Bulk schedule a training plan for multiple weeks."""
    if not start_date:
        start_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    start = datetime.strptime(start_date, "%Y-%m-%d")
    plans = {
        "ppl": [
            {"type": "strength", "title": "Push Day", "muscles": ["chest", "shoulders", "triceps"], "dur": 50},
            {"type": "strength", "title": "Pull Day", "muscles": ["back", "biceps"], "dur": 50},
            {"type": "strength", "title": "Leg Day", "muscles": ["quadriceps", "hamstrings", "glutes"], "dur": 55},
        ],
        "upper_lower": [
            {"type": "strength", "title": "Upper Body", "muscles": ["chest", "back", "shoulders"], "dur": 55},
            {"type": "strength", "title": "Lower Body", "muscles": ["quadriceps", "hamstrings", "glutes"], "dur": 55},
        ],
        "full_body": [
            {"type": "strength", "title": "Full Body", "muscles": ["chest", "back", "quadriceps"], "dur": 50},
        ],
    }

    pattern = plans.get(plan, plans["ppl"])
    created = []

    for w in range(weeks):
        week_start = start + timedelta(weeks=w)
        day_offset = 0
        pattern_idx = 0

        for d in range(7):
            current_date = (week_start + timedelta(days=d)).strftime("%Y-%m-%d")

            if d >= 5:  # Sat/Sun = rest
                entry = {
                    "id": str(uuid.uuid4())[:8],
                    "date": current_date, "workout_type": "rest",
                    "title": "Rest Day", "duration_minutes": 0,
                    "focus_muscles": [], "template_id": None,
                    "notes": "Recovery", "priority": "low",
                    "status": "scheduled", "scheduled_by": user_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            elif pattern_idx < len(pattern):
                p = pattern[pattern_idx]
                entry = {
                    "id": str(uuid.uuid4())[:8],
                    "date": current_date, "workout_type": p["type"],
                    "title": p["title"], "duration_minutes": p["dur"],
                    "focus_muscles": p["muscles"], "template_id": None,
                    "notes": "", "priority": "normal",
                    "status": "scheduled", "scheduled_by": user_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                pattern_idx = (pattern_idx + 1) % len(pattern)
            else:
                continue

            calendar_entries.setdefault(user_id, []).append(entry)
            created.append(entry)

    return {"scheduled": len(created), "weeks": weeks, "plan": plan}


@router.patch("/{entry_id}/status")
async def update_status(
    entry_id: str, status: str = Query(..., pattern="^(completed|missed|skipped)$"),
    user_id: str = Query("default"),
):
    """Update workout status (completed, missed, skipped)."""
    for e in calendar_entries.get(user_id, []):
        if e["id"] == entry_id:
            e["status"] = status
            return {"updated": True, "status": status}
    raise HTTPException(status_code=404, detail="Entry not found")


@router.delete("/{entry_id}")
async def remove_entry(entry_id: str, user_id: str = Query("default")):
    """Remove a scheduled workout."""
    entries = calendar_entries.get(user_id, [])
    for i, e in enumerate(entries):
        if e["id"] == entry_id:
            entries.pop(i)
            return {"deleted": True}
    raise HTTPException(status_code=404, detail="Entry not found")


@router.get("/stats")
async def calendar_stats(user_id: str = Query("default"), days: int = Query(30, ge=7, le=365)):
    """Get training calendar statistics."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    entries = [e for e in calendar_entries.get(user_id, []) if e["date"] >= cutoff]

    completed = [e for e in entries if e["status"] == "completed"]
    type_counts = {}
    for e in entries:
        t = e["workout_type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    return {
        "period_days": days,
        "total_scheduled": len(entries),
        "total_completed": len(completed),
        "total_missed": len([e for e in entries if e["status"] == "missed"]),
        "completion_rate": round((len(completed) / len(entries) * 100) if entries else 0, 1),
        "total_minutes": sum(e["duration_minutes"] for e in completed),
        "workout_types": type_counts,
        "avg_duration": round(sum(e["duration_minutes"] for e in completed) / max(len(completed), 1)),
    }

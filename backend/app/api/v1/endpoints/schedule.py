"""Working Hours & Schedule Personalization — adapts workout timing to user's real life.

Tracks: work hours, commute, sleep schedule, meal times, energy peaks,
and generates optimized workout windows that fit the user's actual life.
"""

from __future__ import annotations
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()

_schedules: dict[str, dict] = {}


class ScheduleRequest(BaseModel):
    wake_time: str = Field(description="HH:MM format, e.g. 06:30")
    sleep_time: str = Field(description="HH:MM format, e.g. 23:00")
    work_start: Optional[str] = None
    work_end: Optional[str] = None
    commute_minutes: int = Field(default=0, ge=0, le=180)
    work_days: list[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4], description="0=Mon..6=Sun")
    meal_times: dict[str, str] = Field(default_factory=lambda: {"breakfast": "07:00", "lunch": "12:30", "dinner": "19:00"})
    preferred_workout_time: str = Field(default="any", description="morning, afternoon, evening, any")
    has_children: bool = False
    children_school_start: Optional[str] = None
    children_school_end: Optional[str] = None
    energy_peak: str = Field(default="morning", description="morning, midday, afternoon, evening")


@router.post("")
async def save_schedule(req: ScheduleRequest, user_id: str = Query("default")):
    _schedules[user_id] = req.model_dump()

    windows = _compute_workout_windows(req)

    return {
        "saved": True,
        "schedule": req.model_dump(),
        "workout_windows": windows,
        "recommendation": _get_schedule_recommendation(req, windows),
    }


@router.get("")
async def get_schedule(user_id: str = Query("default")):
    schedule = _schedules.get(user_id)
    if not schedule:
        return {"has_schedule": False, "message": "No schedule configured"}

    windows = _compute_workout_windows(ScheduleRequest(**schedule))
    return {"has_schedule": True, "schedule": schedule, "workout_windows": windows}


@router.get("/windows")
async def get_workout_windows(user_id: str = Query("default")):
    schedule = _schedules.get(user_id)
    if not schedule:
        return {"windows": _default_windows()}
    windows = _compute_workout_windows(ScheduleRequest(**schedule))
    return {"windows": windows}


def _compute_workout_windows(s: ScheduleRequest) -> list[dict]:
    """Find optimal workout windows based on schedule constraints."""
    wake = _time_to_minutes(s.wake_time)
    sleep = _time_to_minutes(s.sleep_time)
    work_start = _time_to_minutes(s.work_start) if s.work_start else None
    work_end = _time_to_minutes(s.work_end) if s.work_end else None
    commute = s.commute_minutes

    windows = []

    # Morning window: wake to work (minus commute)
    if work_start:
        morning_end = work_start - commute - 30  # 30 min buffer
        if morning_end > wake + 30:
            windows.append({
                "period": "morning",
                "start": _minutes_to_time(wake + 30),
                "end": _minutes_to_time(morning_end),
                "duration_minutes": morning_end - wake - 30,
                "score": 9 if s.energy_peak == "morning" else 6,
                "notes": "Pre-work workout. Good for consistency.",
            })

    # Lunch break window
    if work_start and work_end:
        lunch_start = work_start + (work_end - work_start) // 2 - 30
        lunch_end = lunch_start + 60
        windows.append({
            "period": "lunch",
            "start": _minutes_to_time(lunch_start),
            "end": _minutes_to_time(lunch_end),
            "duration_minutes": 60,
            "score": 5,
            "notes": "Lunchtime workout. May need shower facilities.",
        })

    # Evening window: work end to sleep (minus wind-down)
    if work_end:
        evening_start = work_end + commute + 30
        evening_end = sleep - 60  # 1 hour before bed
        if evening_end > evening_start + 30:
            windows.append({
                "period": "evening",
                "start": _minutes_to_time(evening_start),
                "end": _minutes_to_time(evening_end),
                "duration_minutes": evening_end - evening_start,
                "score": 8 if s.energy_peak == "evening" else 5,
                "notes": "After work. May be crowded at gym. Good stress relief.",
            })

    # Weekend flexible window
    windows.append({
        "period": "flexible",
        "start": _minutes_to_time(wake + 60),
        "end": _minutes_to_time(sleep - 120),
        "duration_minutes": max(0, sleep - 120 - wake - 60),
        "score": 7,
        "notes": "Flexible window for rest days or longer sessions.",
    })

    # Sort by score
    windows.sort(key=lambda w: w["score"], reverse=True)
    return windows


def _get_schedule_recommendation(s: ScheduleRequest, windows: list[dict]) -> dict:
    if not windows:
        return {"message": "No optimal windows found. Consider adjusting your schedule."}

    best = windows[0]
    return {
        "best_window": best["period"],
        "best_time": f"{best['start']} - {best['end']}",
        "duration": best["duration_minutes"],
        "reason": best["notes"],
        "tip": f"Your energy peaks in the {s.energy_peak}. Try to align workouts with that.",
    }


def _default_windows() -> list[dict]:
    return [
        {"period": "morning", "start": "06:30", "end": "08:00", "duration_minutes": 90, "score": 7, "notes": "Default morning window"},
        {"period": "evening", "start": "17:30", "end": "19:30", "duration_minutes": 120, "score": 6, "notes": "Default evening window"},
    ]


def _time_to_minutes(t: str) -> int:
    parts = t.split(":")
    return int(parts[0]) * 60 + int(parts[1])


def _minutes_to_time(m: int) -> str:
    m = m % (24 * 60)
    return f"{m // 60:02d}:{m % 60:02d}"

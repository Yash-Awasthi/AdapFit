"""Menstrual Cycle Tracking — phase-aware workout and nutrition recommendations.

Tracks cycle phases (menstrual, follicular, ovulation, luteal) and adjusts
training load, nutrition, and recovery recommendations accordingly.

Based on sports science research on phase-dependent performance.
"""

from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()

# In-memory storage
_cycle_records: dict[str, list[dict]] = {}


class CycleLogRequest(BaseModel):
    start_date: str = Field(..., description="Cycle start date YYYY-MM-DD")
    length_days: int = Field(28, ge=20, le=40, description="Cycle length")
    period_length_days: int = Field(5, ge=2, le=10, description="Period length")
    symptoms: list[str] = Field(default_factory=list)
    mood: Optional[int] = Field(None, ge=1, le=10)
    energy: Optional[int] = Field(None, ge=1, le=10)
    cramping: bool = False
    notes: str = Field(max_length=300, default="")


def _get_phase(day: int, cycle_length: int, period_length: int) -> dict:
    """Determine cycle phase from day number."""
    if day <= period_length:
        return {
            "phase": "menstrual",
            "day": day,
            "days_remaining": period_length - day,
            "hormonal_profile": {"estrogen": "low", "progesterone": "low", "fsh": "rising"},
            "performance_note": "Energy may be low. Listen to your body.",
        }
    elif day <= cycle_length // 2 - 2:
        return {
            "phase": "follicular",
            "day": day,
            "days_remaining": cycle_length // 2 - 2 - day,
            "hormonal_profile": {"estrogen": "rising", "progesterone": "low", "fsh": "steady"},
            "performance_note": "Peak performance window. Estrogen rising — strength and recovery at their best.",
        }
    elif day <= cycle_length // 2 + 2:
        return {
            "phase": "ovulation",
            "day": day,
            "days_remaining": cycle_length // 2 + 2 - day,
            "hormonal_profile": {"estrogen": "peak", "progesterone": "rising", "lh": "peak"},
            "performance_note": "Peak strength and power. Estrogen peaks — push for PRs.",
        }
    else:
        return {
            "phase": "luteal",
            "day": day,
            "days_remaining": cycle_length - day,
            "hormonal_profile": {"estrogen": "declining", "progesterone": "high", "temp": "elevated"},
            "performance_note": "Progesterone rises. May feel more fatigued. Reduce intensity slightly.",
        }


def _get_training_recommendation(phase: str, cramping: bool = False) -> dict:
    """Get phase-specific training recommendation."""
    recommendations = {
        "menstrual": {
            "intensity": "low" if cramping else "moderate",
            "volume_reduction_pct": 20 if cramping else 10,
            "recommended_types": ["yoga", "walking", "light stretching", "swimming"],
            "avoid": ["heavy deadlifts", "high-impact jumping"] if cramping else [],
            "rest_days": 1 if cramping else 0,
            "note": "Listen to your body. Rest if needed. Gentle movement helps cramps.",
        },
        "follicular": {
            "intensity": "high",
            "volume_reduction_pct": 0,
            "recommended_types": ["strength", "HIIT", "powerlifting", "sprints"],
            "avoid": [],
            "rest_days": 0,
            "note": "Estrogen is rising — strength and endurance are improving. Great time to push hard.",
        },
        "ovulation": {
            "intensity": "very_high",
            "volume_reduction_pct": 0,
            "recommended_types": ["max effort lifts", "PR attempts", "sprint intervals", "competition prep"],
            "avoid": [],
            "rest_days": 0,
            "note": "Peak performance. Go for personal records. Injury risk may be slightly elevated.",
        },
        "luteal": {
            "intensity": "moderate",
            "volume_reduction_pct": 15,
            "recommended_types": ["moderate strength", "endurance", "pilates", "steady-state cardio"],
            "avoid": ["max effort lifts", "high-intensity sprints"],
            "rest_days": 1,
            "note": "Progesterone is high. Focus on technique and endurance. May need more recovery.",
        },
    }
    return recommendations.get(phase, recommendations["menstrual"])


def _get_nutrition_recommendation(phase: str) -> dict:
    """Phase-specific nutrition adjustments."""
    nutrition = {
        "menstrual": {
            "calorie_adjustment": 0,
            "focus": ["iron-rich foods", "anti-inflammatory foods", "hydration"],
            "avoid": ["excess caffeine", "alcohol"],
            "supplements": ["iron", "vitamin C", "magnesium"],
        },
        "follicular": {
            "calorie_adjustment": 0,
            "focus": ["lean protein", "complex carbs", "leafy greens"],
            "avoid": [],
            "supplements": ["vitamin D", "B vitamins"],
        },
        "ovulation": {
            "calorie_adjustment": 50,
            "focus": ["high protein", "antioxidant-rich foods", "fermented foods"],
            "avoid": [],
            "supplements": ["zinc", "selenium"],
        },
        "luteal": {
            "calorie_adjustment": 100,
            "focus": ["complex carbs", "magnesium-rich foods", "calcium", "fiber"],
            "avoid": ["excess salt", "refined sugar"],
            "supplements": ["magnesium", "calcium", "B6"],
        },
    }
    return nutrition.get(phase, nutrition["menstrual"])


@router.post("/log")
async def log_cycle(req: CycleLogRequest, user_id: str = Query("default")):
    """Log cycle start date and symptoms."""
    record = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "start_date": req.start_date,
        "length_days": req.length_days,
        "period_length_days": req.period_length_days,
        "symptoms": req.symptoms,
        "mood": req.mood,
        "energy": req.energy,
        "cramping": req.cramping,
        "notes": req.notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if user_id not in _cycle_records:
        _cycle_records[user_id] = []
    _cycle_records[user_id].append(record)

    return {"logged": True, "record": record}


@router.get("/current")
async def get_current_phase(user_id: str = Query("default")):
    """Get current cycle phase and recommendations."""
    records = _cycle_records.get(user_id, [])
    if not records:
        return {"has_cycle_data": False, "message": "No cycle data logged yet"}

    latest = records[-1]
    start = datetime.strptime(latest["start_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    days_since_start = (now - start).days % latest["length_days"] + 1

    phase_info = _get_phase(days_since_start, latest["length_days"], latest["period_length_days"])
    training = _get_training_recommendation(phase_info["phase"], latest.get("cramping", False))
    nutrition = _get_nutrition_recommendation(phase_info["phase"])

    # Predicted next period
    next_start = start + timedelta(days=latest["length_days"])
    days_until_next = (next_start - now).days
    if days_until_next < 0:
        next_start = start + timedelta(days=latest["length_days"] * 2)
        days_until_next = (next_start - now).days

    return {
        "has_cycle_data": True,
        "current_phase": phase_info,
        "training_recommendation": training,
        "nutrition_recommendation": nutrition,
        "predicted_next_period": next_start.strftime("%Y-%m-%d"),
        "days_until_next_period": days_until_next,
        "cycle_length": latest["length_days"],
    }


@router.get("/calendar")
async def get_cycle_calendar(user_id: str = Query("default"), months: int = Query(3, ge=1, le=12)):
    """Get cycle calendar with predicted phases for the next N months."""
    records = _cycle_records.get(user_id, [])
    if not records:
        return {"calendar": []}

    latest = records[-1]
    start = datetime.strptime(latest["start_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    cycle_len = latest["length_days"]
    period_len = latest["period_length_days"]

    calendar = []
    now = datetime.now(timezone.utc)

    for month_offset in range(months):
        for cycle_offset in range(3):
            cycle_start = start + timedelta(days=cycle_len * (month_offset * 3 + cycle_offset))
            if cycle_start < now - timedelta(days=cycle_len):
                continue

            for day in range(cycle_len):
                day_date = cycle_start + timedelta(days=day)
                if day_date < now - timedelta(days=1):
                    continue
                phase_info = _get_phase(day + 1, cycle_len, period_len)
                calendar.append({
                    "date": day_date.strftime("%Y-%m-%d"),
                    "phase": phase_info["phase"],
                    "day_in_cycle": day + 1,
                })

    return {"calendar": calendar[:100]}  # Cap at 100 entries


@router.delete("/log/{record_id}")
async def delete_cycle_log(record_id: str, user_id: str = Query("default")):
    records = _cycle_records.get(user_id, [])
    idx = next((i for i, r in enumerate(records) if r["id"] == record_id), None)
    if idx is None:
        return {"error": "Record not found"}
    records.pop(idx)
    return {"deleted": True}

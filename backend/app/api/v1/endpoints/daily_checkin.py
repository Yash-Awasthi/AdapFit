"""Daily Wellness Check-in — quick morning readiness assessment with recommendations."""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()

# In-memory check-in storage
_checkins: dict[str, list[dict]] = {}


class CheckinRequest(BaseModel):
    sleep_quality: int = Field(ge=1, le=10, description="Sleep quality 1-10")
    energy_level: int = Field(ge=1, le=10, description="Energy level 1-10")
    soreness: int = Field(ge=1, le=10, description="Muscle soreness 1-10")
    stress: int = Field(1, ge=1, le=10, description="Stress level 1-10")
    motivation: int = Field(5, ge=1, le=10, description="Motivation 1-10")
    pain_areas: list[str] = Field(default_factory=list, description="Body areas with pain")
    notes: str = Field(max_length=500, default="")


@router.post("")
async def submit_checkin(req: CheckinRequest, user_id: str = Query("default")):
    """Submit daily wellness check-in."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Check for duplicate
    existing = [c for c in _checkins.get(user_id, []) if c["date"] == today]
    if existing:
        return {"error": "Already checked in today", "existing": existing[0]}

    # Calculate readiness score
    readiness_score = (
        req.sleep_quality * 3
        + req.energy_level * 3
        + (10 - req.soreness) * 2
        + (10 - req.stress) * 1
        + req.motivation * 1
    ) / 10

    # Classify state
    if readiness_score >= 8:
        state = "OPTIMAL"
        recommendation = "You're feeling great! Push for a high-intensity session."
    elif readiness_score >= 6:
        state = "MODERATE"
        recommendation = "Good to go. Moderate intensity recommended."
    elif readiness_score >= 4:
        state = "REDUCED"
        recommendation = "Consider lighter training or active recovery today."
    else:
        state = "DEPLETED"
        recommendation = "Rest day recommended. Focus on recovery and sleep."

    # Suggest focus areas
    suggestions = []
    if req.sleep_quality < 5:
        suggestions.append("Prioritize sleep hygiene tonight")
    if req.soreness > 7:
        suggestions.append("Add extra warmup and consider foam rolling")
    if req.stress > 7:
        suggestions.append("Include a 5-min breathing exercise before training")
    if req.energy_level < 5:
        suggestions.append("Stay hydrated and eat a balanced pre-workout meal")
    if req.pain_areas:
        suggestions.append(f"Avoid heavy loading on {', '.join(req.pain_areas)}")

    checkin = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "date": today,
        "sleep_quality": req.sleep_quality,
        "energy_level": req.energy_level,
        "soreness": req.soreness,
        "stress": req.stress,
        "motivation": req.motivation,
        "pain_areas": req.pain_areas,
        "notes": req.notes,
        "readiness_score": round(readiness_score, 1),
        "readiness_state": state,
        "recommendation": recommendation,
        "suggestions": suggestions,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if user_id not in _checkins:
        _checkins[user_id] = []
    _checkins[user_id].append(checkin)

    return checkin


@router.get("")
async def get_checkins(
    user_id: str = Query("default"),
    days: int = Query(7, ge=1, le=90),
):
    """Get recent check-ins."""
    entries = _checkins.get(user_id, [])[-days:]
    entries.sort(key=lambda c: c["date"], reverse=True)
    return {"checkins": entries, "total": len(entries)}


@router.get("/today")
async def get_today_checkin(user_id: str = Query("default")):
    """Get today's check-in if it exists."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entries = [c for c in _checkins.get(user_id, []) if c["date"] == today]
    if entries:
        return entries[0]
    return {"checked_in": False, "date": today}


@router.get("/trend")
async def checkin_trend(user_id: str = Query("default"), days: int = Query(14, ge=1, le=90)):
    """Get readiness trend over time."""
    entries = _checkins.get(user_id, [])[-days:]
    if not entries:
        return {"trend": "no_data", "avg_readiness": 0, "data_points": []}

    scores = [e["readiness_score"] for e in entries]
    avg = sum(scores) / len(scores)

    if len(scores) >= 3:
        recent = sum(scores[-3:]) / 3
        earlier = sum(scores[:3]) / min(3, len(scores))
        if recent > earlier + 0.5:
            trend = "improving"
        elif recent < earlier - 0.5:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"

    return {
        "trend": trend,
        "avg_readiness": round(avg, 1),
        "min_readiness": round(min(scores), 1),
        "max_readiness": round(max(scores), 1),
        "data_points": [{"date": e["date"], "score": e["readiness_score"], "state": e["readiness_state"]} for e in entries],
        "total_checkins": len(entries),
    }

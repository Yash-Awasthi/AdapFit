"""Illness detection endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.illness_detection import (
    DailyHealthSnapshot, detect_illness, detect_illness_trend,
)

router = APIRouter()


class SnapshotInput(BaseModel):
    date: str
    hrv_rmssd: Optional[float] = None
    resting_hr: Optional[int] = None
    body_temperature: Optional[float] = None
    sleep_quality_score: Optional[float] = None
    sleep_duration_hours: Optional[float] = None
    respiratory_rate: Optional[float] = None
    spo2: Optional[float] = None


@router.post("/illness/detect")
def detect(body: dict):
    """Detect illness risk from health history + today's snapshot."""
    history = [DailyHealthSnapshot(**s) for s in body.get("history", [])]
    today = DailyHealthSnapshot(**body["today"]) if "today" in body else None
    window = body.get("baseline_window", 14)
    return detect_illness(history, today, window)


@router.post("/illness/trend")
def trend(body: dict):
    """Detect illness risk trend over recent days."""
    history = [DailyHealthSnapshot(**s) for s in body.get("history", [])]
    window = body.get("window_days", 7)
    return detect_illness_trend(history, window)

"""Wearable data simulator: generates realistic HRV, sleep, steps for testing."""
import uuid
import random
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter()


class SimulatedDay(BaseModel):
    date: str
    hrv_rmssd: float
    resting_hr: int
    sleep_hours: float
    sleep_efficiency: float
    steps: int
    active_calories: float
    deep_sleep_pct: float
    rem_sleep_pct: float


class SimulateRequest(BaseModel):
    days: int = Field(default=7, ge=1, le=90, examples=[7])
    base_hrv: float = Field(default=45.0, ge=10, le=120, examples=[45])
    base_sleep: float = Field(default=7.5, ge=4, le=12, examples=[7.5])
    trend: str = Field(default="stable", examples=["improving", "stable", "declining"])
    variability: float = Field(default=0.15, ge=0.0, le=0.5, examples=[0.15])


def _simulate_day(
    date: datetime, base_hrv: float, base_sleep: float,
    trend: str, day_index: int, total_days: int,
) -> SimulatedDay:
    """Generate one day of realistic wearable data."""
    # Trend factor
    if trend == "improving":
        factor = 1.0 + (day_index / total_days) * 0.15
    elif trend == "declining":
        factor = 1.0 - (day_index / total_days) * 0.15
    else:
        factor = 1.0

    # Random variation
    hrv = base_hrv * factor * random.uniform(0.85, 1.15)
    sleep = base_sleep * factor * random.uniform(0.85, 1.1)
    rhr = max(45, min(90, int(65 - (hrv - 45) * 0.3 + random.randint(-5, 5))))
    steps = random.randint(4000, 12000)
    cal = steps * 0.04 + random.uniform(50, 200)
    deep_pct = random.uniform(12, 25)
    rem_pct = random.uniform(15, 28)
    efficiency = random.uniform(80, 96)

    return SimulatedDay(
        date=date.strftime("%Y-%m-%d"),
        hrv_rmssd=round(hrv, 1),
        resting_hr=rhr,
        sleep_hours=round(sleep, 1),
        sleep_efficiency=round(efficiency, 1),
        steps=steps,
        active_calories=round(cal, 0),
        deep_sleep_pct=round(deep_pct, 1),
        rem_sleep_pct=round(rem_pct, 1),
    )


@router.post("", response_model=List[SimulatedDay])
async def simulate_data(request: SimulateRequest, user_id: str = Query("default")):
    """Generate simulated wearable data for testing."""
    now = datetime.now(timezone.utc)
    days = []
    for i in range(request.days):
        date = now - timedelta(days=request.days - 1 - i)
        days.append(_simulate_day(
            date, request.base_hrv, request.base_sleep,
            request.trend, i, request.days,
        ))
    return days


@router.get("/quick", response_model=SimulatedDay)
async def quick_simulate(user_id: str = Query("default")):
    """Quick single-day simulation with random parameters."""
    return _simulate_day(datetime.now(timezone.utc), 45.0, 7.5, "stable", 0, 1)

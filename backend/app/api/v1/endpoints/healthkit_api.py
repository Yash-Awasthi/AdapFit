"""HealthKit data import and analysis — transform, query, summarize."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.services.healthkit_bridge import (
    transform_batch, daily_averages, weekly_trends,
    monthly_summaries, resting_hr_trend, check_healthkit_compatibility,
)

router = APIRouter()


class HKSampleInput(BaseModel):
    sampleType: str
    value: float
    unit: str = ""
    startDate: str = ""
    endDate: str = ""
    metadata: dict = {}


class ImportInput(BaseModel):
    samples: list[HKSampleInput]


class CompatibilityInput(BaseModel):
    device_type: str = "iphone"
    ios_version: str = "17.0"


@router.post("/import")
async def import_healthkit(req: ImportInput):
    """Import and transform a batch of HealthKit samples into ZFIT format."""
    raw = [s.model_dump() for s in req.samples]
    transformed = transform_batch(raw)
    return {
        "imported": len(transformed),
        "skipped": len(req.samples) - len(transformed),
        "samples": [
            {"type": s.type, "value": s.value, "start": s.start, "end": s.end, "duration_minutes": s.duration_minutes}
            for s in transformed
        ],
    }


@router.post("/heart-rate")
async def heart_rate_analysis(samples: list[HKSampleInput]):
    """Analyze heart rate data from HealthKit samples."""
    raw = [s.model_dump() for s in samples]
    transformed = transform_batch(raw)
    hr = [s for s in transformed if s.type in ("heart_rate", "resting_heart_rate")]
    if not hr:
        raise HTTPException(status_code=422, detail="No heart rate samples provided")
    return daily_averages(hr)


@router.post("/sleep")
async def sleep_analysis(samples: list[HKSampleInput]):
    """Analyze sleep data from HealthKit sleep analysis samples."""
    raw = [s.model_dump() for s in samples]
    transformed = transform_batch(raw)
    sleep = [s for s in transformed if s.type == "sleep"]
    if not sleep:
        raise HTTPException(status_code=422, detail="No sleep samples provided")

    total_hours = sum(s.duration_minutes / 60 for s in sleep)
    return {
        "nights": len(sleep),
        "total_hours": round(total_hours, 1),
        "avg_hours": round(total_hours / len(sleep), 1),
        "daily_averages": daily_averages(sleep),
    }


@router.post("/workouts")
async def workout_summary(samples: list[HKSampleInput]):
    """Summarize workout data from HealthKit workout samples."""
    raw = [s.model_dump() for s in samples]
    transformed = transform_batch(raw)
    workouts = [s for s in transformed if s.type == "workout"]
    if not workouts:
        raise HTTPException(status_code=422, detail="No workout samples provided")

    total_duration = sum(s.duration_minutes for s in workouts)
    return {
        "workout_count": len(workouts),
        "total_duration_minutes": round(total_duration, 1),
        "avg_duration_minutes": round(total_duration / len(workouts), 1),
    }


@router.post("/summary")
async def healthkit_summary(samples: list[HKSampleInput]):
    """Full HealthKit summary — daily, weekly, monthly, resting HR trend."""
    raw = [s.model_dump() for s in samples]
    transformed = transform_batch(raw)
    if not transformed:
        raise HTTPException(status_code=422, detail="No valid HealthKit samples")

    return {
        "total_samples": len(transformed),
        "types": list(set(s.type for s in transformed)),
        "daily": daily_averages(transformed),
        "weekly": weekly_trends(transformed),
        "monthly": monthly_summaries(transformed),
        "resting_hr_trend": resting_hr_trend(transformed),
    }


@router.post("/compatibility")
async def compatibility(req: CompatibilityInput):
    """Check HealthKit data type compatibility for a device."""
    return check_healthkit_compatibility(req.device_type, req.ios_version)

"""Body composition tracking: weight, measurements, body fat, and trends."""
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter()


class BodyMeasurement(BaseModel):
    weight_kg: Optional[float] = Field(None, ge=20, le=300, examples=[78.5])
    body_fat_pct: Optional[float] = Field(None, ge=1, le=60, examples=[15.2])
    muscle_mass_kg: Optional[float] = Field(None, ge=10, le=150, examples=[35.0])
    chest_cm: Optional[float] = Field(None, ge=40, le=200, examples=[98.0])
    waist_cm: Optional[float] = Field(None, ge=40, le=200, examples=[80.0])
    hips_cm: Optional[float] = Field(None, ge=40, le=200, examples=[95.0])
    bicep_cm: Optional[float] = Field(None, ge=15, le=80, examples=[35.0])
    thigh_cm: Optional[float] = Field(None, ge=25, le=100, examples=[55.0])
    notes: Optional[str] = Field(None, max_length=200)


class MeasurementResponse(BaseModel):
    id: str
    date: str
    weight_kg: Optional[float]
    body_fat_pct: Optional[float]
    muscle_mass_kg: Optional[float]
    measurements: dict
    logged_at: str


class CompositionTrend(BaseModel):
    period: str  # "7d", "30d", "90d"
    weight_change: float
    body_fat_change: float
    muscle_change: float
    waist_change: float
    trend: str  # "improving", "stable", "declining"


# In-memory storage
measurements: dict = {}  # user_id -> list


def _calc_trend(entries: list, days: int) -> CompositionTrend:
    """Calculate trends over a period."""
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=days)).isoformat()
    recent = [e for e in entries if e["logged_at"] >= cutoff]

    if len(recent) < 2:
        return CompositionTrend(
            period=f"{days}d", weight_change=0, body_fat_change=0,
            muscle_change=0, waist_change=0, trend="stable",
        )

    first, last = recent[0], recent[-1]
    weight_chg = (last.get("weight_kg") or 0) - (first.get("weight_kg") or 0)
    bf_chg = (last.get("body_fat_pct") or 0) - (first.get("body_fat_pct") or 0)
    muscle_chg = (last.get("muscle_mass_kg") or 0) - (first.get("muscle_mass_kg") or 0)
    waist_chg = (last.get("measurements", {}).get("waist") or 0) - (first.get("measurements", {}).get("waist") or 0)

    # Improving = losing fat, gaining muscle, waist shrinking
    improving = bf_chg < -0.3 or muscle_chg > 0.2 or waist_chg < -1
    declining = bf_chg > 0.5 or muscle_chg < -0.3 or waist_chg > 1.5

    return CompositionTrend(
        period=f"{days}d",
        weight_change=round(weight_chg, 1),
        body_fat_change=round(bf_chg, 1),
        muscle_change=round(muscle_chg, 1),
        waist_change=round(waist_chg, 1),
        trend="improving" if improving else ("declining" if declining else "stable"),
    )


@router.get("/measurements", response_model=List[MeasurementResponse])
async def list_measurements(user_id: str = Query("default"), days: int = Query(30, ge=1, le=365)):
    """List body measurements."""
    entries = measurements.get(user_id, [])[-days:]
    return [
        MeasurementResponse(
            id=e["id"], date=e["date"],
            weight_kg=e.get("weight_kg"), body_fat_pct=e.get("body_fat_pct"),
            muscle_mass_kg=e.get("muscle_mass_kg"),
            measurements=e.get("measurements", {}),
            logged_at=e["logged_at"],
        )
        for e in entries
    ]


@router.post("/measurements", response_model=MeasurementResponse, status_code=201)
async def log_measurement(m: BodyMeasurement, user_id: str = Query("default")):
    """Log a body measurement."""
    if not any([m.weight_kg, m.body_fat_pct, m.muscle_mass_kg, m.chest_cm, m.waist_cm]):
        raise HTTPException(status_code=400, detail="Provide at least one measurement")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entry = {
        "id": str(uuid.uuid4())[:8],
        "date": today,
        "weight_kg": m.weight_kg,
        "body_fat_pct": m.body_fat_pct,
        "muscle_mass_kg": m.muscle_mass_kg,
        "measurements": {
            k: v for k, v in {
                "chest": m.chest_cm, "waist": m.waist_cm, "hips": m.hips_cm,
                "bicep": m.bicep_cm, "thigh": m.thigh_cm,
            }.items() if v is not None
        },
        "notes": m.notes,
        "logged_at": datetime.now(timezone.utc).isoformat(),
    }
    measurements.setdefault(user_id, []).append(entry)
    return MeasurementResponse(
        id=entry["id"], date=today,
        weight_kg=entry["weight_kg"], body_fat_pct=entry["body_fat_pct"],
        muscle_mass_kg=entry["muscle_mass_kg"],
        measurements=entry["measurements"], logged_at=entry["logged_at"],
    )


@router.get("/trends", response_model=dict)
async def get_trends(user_id: str = Query("default")):
    """Get body composition trends for 7d, 30d, 90d."""
    user_data = measurements.get(user_id, [])
    return {
        "7d": _calc_trend(user_data, 7).model_dump(),
        "30d": _calc_trend(user_data, 30).model_dump(),
        "90d": _calc_trend(user_data, 90).model_dump(),
    }


@router.delete("/measurements/{measurement_id}")
async def delete_measurement(measurement_id: str, user_id: str = Query("default")):
    """Delete a measurement."""
    user_data = measurements.get(user_id, [])
    for i, e in enumerate(user_data):
        if e["id"] == measurement_id:
            user_data.pop(i)
            return {"deleted": True}
    raise HTTPException(status_code=404, detail="Measurement not found")

"""Body metrics dashboard: weight, body fat, measurements trends with chart data."""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from statistics import mean

router = APIRouter()


class TrendPoint(BaseModel):
    date: str
    value: float


class MetricTrend(BaseModel):
    metric: str
    current: Optional[float]
    previous: Optional[float]
    change: float
    change_pct: float
    direction: str  # "up", "down", "stable"
    unit: str
    chart_data: List[TrendPoint]
    min_value: Optional[float]
    max_value: Optional[float]
    avg_value: Optional[float]


class BodyDashboard(BaseModel):
    weight: MetricTrend
    body_fat: MetricTrend
    muscle_mass: MetricTrend
    measurements: dict  # chest, waist, hips, bicep, thigh trends
    bmi: Optional[float]
    bmi_category: Optional[str]
    body_composition_score: float  # 0-100
    summary: str


def _build_trend(values: List[tuple], metric: str, unit: str) -> MetricTrend:
    """Build a metric trend from list of (date, value) tuples."""
    if not values:
        return MetricTrend(
            metric=metric, current=None, previous=None,
            change=0, change_pct=0, direction="stable", unit=unit,
            chart_data=[], min_value=None, max_value=None, avg_value=None,
        )

    vals = [(d, v) for d, v in values if v is not None]
    if not vals:
        return MetricTrend(
            metric=metric, current=None, previous=None,
            change=0, change_pct=0, direction="stable", unit=unit,
            chart_data=[], min_value=None, max_value=None, avg_value=None,
        )

    current = vals[-1][1]
    previous = vals[-2][1] if len(vals) >= 2 else current
    change = current - previous
    change_pct = (change / previous * 100) if previous else 0

    if abs(change_pct) > 0.5:
        direction = "up" if change > 0 else "down"
    else:
        direction = "stable"

    all_vals = [v for _, v in vals]

    return MetricTrend(
        metric=metric, current=current, previous=previous,
        change=round(change, 1), change_pct=round(change_pct, 1),
        direction=direction, unit=unit,
        chart_data=[TrendPoint(date=d, value=v) for d, v in vals[-30:]],
        min_value=round(min(all_vals), 1),
        max_value=round(max(all_vals), 1),
        avg_value=round(mean(all_vals), 1),
    )


def _bmi_category(bmi: float) -> str:
    if bmi < 18.5: return "Underweight"
    elif bmi < 25: return "Normal"
    elif bmi < 30: return "Overweight"
    else: return "Obese"


@router.get("", response_model=BodyDashboard)
async def get_body_dashboard(user_id: str = Query("default"), months: int = Query(3, ge=1, le=12)):
    """Get body metrics dashboard with trends."""
    try:
        from app.api.v1.endpoints.body_composition import measurements
        data = measurements.get(user_id, [])
    except (ImportError, AttributeError):
        data = []

    cutoff = (datetime.now(timezone.utc) - timedelta(days=months * 30)).isoformat()
    recent = [m for m in data if m.get("logged_at", "") >= cutoff]

    # Build trends
    weight_vals = [(m["date"], m.get("weight_kg")) for m in recent if m.get("weight_kg")]
    bf_vals = [(m["date"], m.get("body_fat_pct")) for m in recent if m.get("body_fat_pct")]
    muscle_vals = [(m["date"], m.get("muscle_mass_kg")) for m in recent if m.get("muscle_mass_kg")]

    weight_trend = _build_trend(weight_vals, "weight", "kg")
    bf_trend = _build_trend(bf_vals, "body_fat", "%")
    muscle_trend = _build_trend(muscle_vals, "muscle_mass", "kg")

    # Measurement trends
    measurement_metrics = {
        "chest": ("chest_cm", "cm"),
        "waist": ("waist_cm", "cm"),
        "hips": ("hips_cm", "cm"),
        "bicep": ("bicep_cm", "cm"),
        "thigh": ("thigh_cm", "cm"),
    }
    measurements_trends = {}
    for key, (body_key, unit) in measurement_metrics.items():
        vals = [(m["date"], m.get("measurements", {}).get(key)) for m in recent]
        vals = [(d, v) for d, v in vals if v is not None]
        measurements_trends[key] = _build_trend(vals, key, unit)

    # BMI
    bmi = None
    bmi_cat = None
    if weight_trend.current:
        # Assume average height if not provided (placeholder)
        height_m = 1.75
        bmi = round(weight_trend.current / (height_m ** 2), 1)
        bmi_cat = _bmi_category(bmi)

    # Body composition score
    score = 50
    if bf_trend.current:
        if bf_trend.current < 15:
            score += 20
        elif bf_trend.current < 20:
            score += 10
        elif bf_trend.current > 25:
            score -= 10
    if muscle_trend.current:
        if muscle_trend.current > 35:
            score += 15
        elif muscle_trend.current > 30:
            score += 10
    if weight_trend.direction == "stable":
        score += 5
    score = max(0, min(100, score))

    # Summary
    parts = []
    if weight_trend.current:
        parts.append(f"Weight: {weight_trend.current}kg ({weight_trend.direction})")
    if bf_trend.current:
        parts.append(f"Body fat: {bf_trend.current}% ({bf_trend.direction})")
    if muscle_trend.current:
        parts.append(f"Muscle: {muscle_trend.current}kg ({muscle_trend.direction})")
    summary = ". ".join(parts) if parts else "No body metrics recorded yet."

    return BodyDashboard(
        weight=weight_trend,
        body_fat=bf_trend,
        muscle_mass=muscle_trend,
        measurements=measurements_trends,
        bmi=bmi,
        bmi_category=bmi_cat,
        body_composition_score=score,
        summary=summary,
    )


@router.get("/weight-history")
async def weight_history(user_id: str = Query("default"), days: int = Query(90, ge=7, le=365)):
    """Get weight history for charting."""
    try:
        from app.api.v1.endpoints.body_composition import measurements
        data = measurements.get(user_id, [])
    except (ImportError, AttributeError):
        data = []

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    return [
        {"date": m["date"], "weight_kg": m.get("weight_kg")}
        for m in data
        if m.get("logged_at", "") >= cutoff and m.get("weight_kg")
    ]


@router.get("/body-fat-history")
async def body_fat_history(user_id: str = Query("default"), days: int = Query(90, ge=7, le=365)):
    """Get body fat history for charting."""
    try:
        from app.api.v1.endpoints.body_composition import measurements
        data = measurements.get(user_id, [])
    except (ImportError, AttributeError):
        data = []

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    return [
        {"date": m["date"], "body_fat_pct": m.get("body_fat_pct")}
        for m in data
        if m.get("logged_at", "") >= cutoff and m.get("body_fat_pct")
    ]


@router.get("/summary")
async def metrics_summary(user_id: str = Query("default")):
    """Get a concise body metrics summary."""
    try:
        from app.api.v1.endpoints.body_composition import measurements
        data = measurements.get(user_id, [])
    except (ImportError, AttributeError):
        data = []

    if not data:
        return {"message": "No body metrics recorded. Start tracking to see your progress."}

    latest = data[-1]
    first = data[0]

    return {
        "latest": {
            "date": latest.get("date"),
            "weight_kg": latest.get("weight_kg"),
            "body_fat_pct": latest.get("body_fat_pct"),
            "muscle_mass_kg": latest.get("muscle_mass_kg"),
        },
        "changes": {
            "weight_kg": round((latest.get("weight_kg", 0) or 0) - (first.get("weight_kg", 0) or 0), 1),
            "body_fat_pct": round((latest.get("body_fat_pct", 0) or 0) - (first.get("body_fat_pct", 0) or 0), 1),
            "muscle_mass_kg": round((latest.get("muscle_mass_kg", 0) or 0) - (first.get("muscle_mass_kg", 0) or 0), 1),
        },
        "total_entries": len(data),
        "first_entry": first.get("date"),
    }

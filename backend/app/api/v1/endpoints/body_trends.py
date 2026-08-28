"""Body Metrics Trends — comprehensive trend analysis for weight, body fat, muscle mass."""

from __future__ import annotations
from fastapi import APIRouter, Query
from app.api.v1.endpoints.body_composition import measurements as _body_measurements

router = APIRouter()


@router.get("/trends")
async def body_metrics_trends(
    user_id: str = Query("default"),
    days: int = Query(90, ge=7, le=365),
    metrics: str = Query("weight,body_fat,muscle_mass", description="Comma-separated metric names"),
):
    """Get trend data for body metrics with stats and projections."""
    requested = [m.strip() for m in metrics.split(",") if m.strip()]
    all_entries = _body_measurements.get(user_id, [])
    measurements = all_entries[-days:]

    if not measurements:
        return {"metrics": {m: {"data": [], "stats": {}, "projection": None} for m in requested}}

    result = {}
    for metric in requested:
        data_points = []
        for m in measurements:
            val = m.get(f"{metric}_kg") or m.get(f"{metric}_pct") or m.get(metric)
            if val is not None:
                data_points.append({
                    "date": m.get("created_at", m.get("date", "")),
                    "value": float(val),
                })

        if len(data_points) < 2:
            result[metric] = {"data": data_points, "stats": {}, "projection": None}
            continue

        values = [d["value"] for d in data_points]
        mean_val = sum(values) / len(values)
        std_val = (sum((v - mean_val) ** 2 for v in values) / len(values)) ** 0.5 if len(values) > 1 else 0

        # Linear regression for trend
        n = len(values)
        x_vals = list(range(n))
        x_mean = sum(x_vals) / n
        num = sum((x_vals[i] - x_mean) * (values[i] - mean_val) for i in range(n))
        den = sum((x_vals[i] - x_mean) ** 2 for i in range(n))
        slope = num / den if den > 0 else 0

        # Direction
        if abs(slope) < 0.01:
            direction = "stable"
        elif slope > 0:
            direction = "up"
        else:
            direction = "down"

        # Projection (next 30 days)
        projection = {
            "days_ahead": 30,
            "projected_value": round(values[-1] + slope * 30, 1),
            "confidence": "low" if std_val > abs(slope) * 30 else "medium",
        }

        result[metric] = {
            "data": data_points,
            "stats": {
                "current": round(values[-1], 1),
                "min": round(min(values), 1),
                "max": round(max(values), 1),
                "mean": round(mean_val, 1),
                "std": round(std_val, 2),
                "total_change": round(values[-1] - values[0], 1),
                "pct_change": round((values[-1] - values[0]) / values[0] * 100, 1) if values[0] != 0 else 0,
                "direction": direction,
                "slope_per_day": round(slope, 3),
                "data_points": n,
            },
            "projection": projection,
        }

    return {"metrics": result, "period_days": days}

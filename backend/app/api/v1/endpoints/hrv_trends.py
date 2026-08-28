"""HRV Trend Charts — visualizable HRV data with trend lines and statistics."""

from __future__ import annotations
from fastapi import APIRouter, Query
from typing import Optional
from app.core.storage import storage

router = APIRouter()


@router.get("/trend")
async def hrv_trend(
    user_id: str = Query("default"),
    days: int = Query(30, ge=1, le=365),
):
    """Get HRV trend data with statistics."""
    logs = await storage.get_recovery_logs(user_id, days)

    if not logs:
        return {
            "data_points": [],
            "statistics": {"mean": 0, "std": 0, "min": 0, "max": 0, "trend": "insufficient_data"},
            "trend_line": [],
        }

    # Extract HRV values — storage flattens wearable_data to top-level
    hrv_data = []
    for log in logs:
        hrv = log.get("hrv_rmssd")
        if hrv is None:
            wd = log.get("wearable_data", {})
            hrv = wd.get("hrv_rmssd") if isinstance(wd, dict) else None
        if hrv is not None:
            hrv_data.append({
                "date": log.get("log_date", ""),
                "value": float(hrv),
                "recovery_score": log.get("recovery_score"),
            })

    if not hrv_data:
        return {
            "data_points": [],
            "statistics": {"mean": 0, "std": 0, "min": 0, "max": 0, "trend": "no_hrv_data"},
            "trend_line": [],
        }

    values = [d["value"] for d in hrv_data]
    mean_val = sum(values) / len(values)
    std_val = (sum((v - mean_val) ** 2 for v in values) / len(values)) ** 0.5 if len(values) > 1 else 0

    # Simple linear trend
    n = len(values)
    if n >= 3:
        x_vals = list(range(n))
        x_mean = sum(x_vals) / n
        y_mean = mean_val
        num = sum((x_vals[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        den = sum((x_vals[i] - x_mean) ** 2 for i in range(n))
        slope = num / den if den > 0 else 0
        if slope > 0.5:
            trend = "improving"
        elif slope < -0.5:
            trend = "declining"
        else:
            trend = "stable"

        # Generate trend line
        trend_line = [
            {"date": hrv_data[i]["date"], "value": round(mean_val + slope * (i - x_mean), 1)}
            for i in range(n)
        ]
    else:
        trend = "insufficient_data"
        trend_line = []
        slope = 0

    # Zone classification
    zones = []
    for d in hrv_data:
        z_score = (d["value"] - mean_val) / std_val if std_val > 0 else 0
        if z_score > 1:
            zone = "optimal"
        elif z_score > -0.5:
            zone = "normal"
        elif z_score > -1.5:
            zone = "caution"
        else:
            zone = "stress"
        zones.append({"date": d["date"], "zone": zone, "z_score": round(z_score, 2)})

    return {
        "data_points": hrv_data,
        "statistics": {
            "mean": round(mean_val, 1),
            "std": round(std_val, 1),
            "min": round(min(values), 1),
            "max": round(max(values), 1),
            "trend": trend,
            "slope_per_day": round(slope, 2),
            "data_points_count": n,
        },
        "trend_line": trend_line,
        "zones": zones,
    }


@router.get("/zones")
async def hrv_zones(user_id: str = Query("default"), days: int = Query(14, ge=1, le=365)):
    """Get HRV zone distribution."""
    logs = await storage.get_recovery_logs(user_id, days)

    hrv_values = []
    for log in logs:
        hrv = log.get("hrv_rmssd")
        if hrv is None:
            wd = log.get("wearable_data", {})
            hrv = wd.get("hrv_rmssd") if isinstance(wd, dict) else None
        if hrv is not None:
            hrv_values.append(float(hrv))

    if not hrv_values:
        return {"zones": {}, "total_readings": 0}

    mean_val = sum(hrv_values) / len(hrv_values)
    std_val = (sum((v - mean_val) ** 2 for v in hrv_values) / len(hrv_values)) ** 0.5 if len(hrv_values) > 1 else 0

    zones = {"optimal": 0, "normal": 0, "caution": 0, "stress": 0}
    for v in hrv_values:
        z_score = (v - mean_val) / std_val if std_val > 0 else 0
        if z_score > 1:
            zones["optimal"] += 1
        elif z_score > -0.5:
            zones["normal"] += 1
        elif z_score > -1.5:
            zones["caution"] += 1
        else:
            zones["stress"] += 1

    return {
        "zones": {k: {"count": v, "pct": round(v / len(hrv_values) * 100, 1)} for k, v in zones.items()},
        "total_readings": len(hrv_values),
        "mean_hrv": round(mean_val, 1),
    }

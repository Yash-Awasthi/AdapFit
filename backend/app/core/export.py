"""Data export utilities: generate CSV and JSON files for user health data."""
import csv
import io
import json
from datetime import datetime, timezone
from typing import Any


def to_csv(rows: list[dict], filename: str = "export") -> dict:
    """Convert list of dicts to CSV string with metadata."""
    if not rows:
        return {"filename": f"{filename}.csv", "content": "", "rows": 0, "format": "csv"}

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

    return {
        "filename": f"{filename}.csv",
        "content": output.getvalue(),
        "rows": len(rows),
        "format": "csv",
    }


def to_json(data: Any, filename: str = "export", pretty: bool = True) -> dict:
    """Convert data to formatted JSON string."""
    content = json.dumps(data, indent=2 if pretty else None, default=str)
    return {
        "filename": f"{filename}.json",
        "content": content,
        "rows": len(data) if isinstance(data, list) else 1,
        "format": "json",
    }


def export_workout_history(workouts: list[dict]) -> dict:
    """Export workout history as CSV."""
    rows = []
    for w in workouts:
        exercises = w.get("exercises", [])
        rows.append({
            "date": w.get("target_date", w.get("created_at", "")),
            "workout_id": w.get("workout_id", ""),
            "title": w.get("title", ""),
            "readiness_state": w.get("readiness_state", ""),
            "duration_minutes": w.get("target_duration_minutes", ""),
            "exercise_count": len(exercises),
            "exercises": "; ".join(e.get("name", "") for e in exercises),
            "adaptation_rationale": w.get("adaptation_rationale", ""),
        })
    return to_csv(rows, "workout_history")


def export_recovery_logs(logs: list[dict]) -> dict:
    """Export recovery logs as CSV."""
    rows = []
    for log in logs:
        mb = log.get("metrics_breakdown", {})
        rows.append({
            "date": log.get("log_date", ""),
            "recovery_score": log.get("recovery_score", ""),
            "readiness_state": log.get("readiness_state", ""),
            "hrv_z_score": mb.get("hrv_z_score", ""),
            "sleep_score": mb.get("sleep_score", ""),
            "subjective_score": mb.get("subjective_score", ""),
            "acwr": mb.get("acwr", ""),
            "acwr_status": mb.get("acwr_status", ""),
            "recommendation": log.get("recommendation_directive", ""),
        })
    return to_csv(rows, "recovery_logs")


def export_nutrition(meals: list[dict]) -> dict:
    """Export nutrition logs as CSV."""
    rows = []
    for m in meals:
        rows.append({
            "date": m.get("logged_at", "")[:10],
            "meal_name": m.get("name", ""),
            "meal_type": m.get("meal_type", ""),
            "calories": m.get("calories", 0),
            "protein_g": m.get("protein_g", 0),
            "carbs_g": m.get("carbs_g", 0),
            "fat_g": m.get("fat_g", 0),
            "notes": m.get("notes", ""),
        })
    return to_csv(rows, "nutrition_log")


def export_body_measurements(measurements: list[dict]) -> dict:
    """Export body measurements as CSV."""
    rows = []
    for m in measurements:
        body = m.get("measurements", {})
        rows.append({
            "date": m.get("date", ""),
            "weight_kg": m.get("weight_kg", ""),
            "body_fat_pct": m.get("body_fat_pct", ""),
            "muscle_mass_kg": m.get("muscle_mass_kg", ""),
            "chest_cm": body.get("chest", ""),
            "waist_cm": body.get("waist", ""),
            "hips_cm": body.get("hips", ""),
            "bicep_cm": body.get("bicep", ""),
            "thigh_cm": body.get("thigh", ""),
        })
    return to_csv(rows, "body_measurements")


def export_sleep_logs(logs: list[dict]) -> dict:
    """Export sleep logs as CSV."""
    rows = []
    for l in logs:
        rows.append({
            "date": l.get("date", ""),
            "bedtime": l.get("bedtime", ""),
            "wake_time": l.get("wake_time", ""),
            "total_minutes": l.get("total_minutes", ""),
            "efficiency_pct": l.get("efficiency_pct", ""),
            "deep_pct": l.get("deep_pct", ""),
            "rem_pct": l.get("rem_pct", ""),
            "interruptions": l.get("interruptions", 0),
        })
    return to_csv(rows, "sleep_logs")


def generate_full_export(data: dict) -> dict:
    """Generate a complete JSON export with all user data."""
    return {
        "export_date": datetime.now(timezone.utc).isoformat(),
        "app": "AdapFit",
        "version": "2.0",
        "data": data,
    }

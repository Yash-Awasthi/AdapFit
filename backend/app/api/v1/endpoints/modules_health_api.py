"""
Module Health Check — verifies all extracted modules load correctly.
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", summary="Check that all extracted modules are importable")
async def modules_health() -> dict[str, str]:
    modules = [
        "src.anomaly.detector",
        "src.biometrics.signals", "src.breathing.analyzer",
        "src.medication.tracker", "src.planner.fitness_planner",
        "src.pose.form_checker", "src.rppg.processor", "src.sensors.ble_monitor",
        "src.sleep.classifier", "src.tracker.workout_tracker",
    ]
    status = {}
    for m in modules:
        try:
            __import__(m)
            status[m] = "ok"
        except Exception as e:
            status[m] = f"error: {e}"
    all_ok = all(v == "ok" for v in status.values())
    return {"status": "healthy" if all_ok else "degraded", "modules": status}

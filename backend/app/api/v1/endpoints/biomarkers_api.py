"""
Biomarker Tracking API — bloodwork tracking with trend analysis.
"""
from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


class BiomarkerReadingRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    value: float
    unit: str = Field(min_length=1, max_length=32)
    lab_name: str = Field(default="", max_length=256)
    notes: str = Field(default="", max_length=500)


@lru_cache(maxsize=1)
def _get_tracker():
    from src.biomarkers.tracker import BiomarkerTracker
    return BiomarkerTracker()


@router.post("/readings", summary="Add a biomarker reading")
async def add_reading(req: BiomarkerReadingRequest) -> dict[str, Any]:
    from src.biomarkers.tracker import BiomarkerReading
    tracker = _get_tracker()
    try:
        reading = BiomarkerReading(
            name=req.name, value=req.value, unit=req.unit,
            timestamp=datetime.utcnow(), lab_name=req.lab_name, notes=req.notes,
        )
        tracker.add_reading(reading)
        status = tracker.get_status(req.name, req.value)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"status": status.value, "name": req.name, "value": req.value}


@router.get("/trends", summary="Get all biomarker trends")
async def get_trends() -> dict[str, Any]:
    trends = _get_tracker().get_all_trends()
    return {"trends": len(trends), "message": f"Found {len(trends)} trends" if trends else "Add readings first via POST /readings"}


@router.get("/health-score", summary="Get overall health score from biomarkers")
async def get_health_score() -> dict[str, Any]:
    return _get_tracker().get_health_score()


@router.get("/references", summary="Get reference ranges for all biomarkers")
async def get_references() -> dict[str, dict[str, Any]]:
    tracker = _get_tracker()
    return {
        name: {"optimal": [ref.optimal_low, ref.optimal_high], "normal": [ref.normal_low, ref.normal_high], "unit": ref.unit}
        for name, ref in tracker.DEFAULT_REFERENCES.items()
    }

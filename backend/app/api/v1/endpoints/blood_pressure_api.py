"""Blood pressure: log home readings, see ranges and the 7-day average."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.core.durable import durable_dict
from app.services.blood_pressure import URGENT_SYMPTOMS, classify, summary

router = APIRouter()
_readings = durable_dict("app.api.v1.endpoints.blood_pressure_api.readings")


class BPLog(BaseModel):
    systolic: int = Field(ge=60, le=280)
    diastolic: int = Field(ge=30, le=180)
    pulse: Optional[int] = Field(None, ge=25, le=250)
    arm: str = Field("left", pattern=r"^(left|right)$")


@router.post("/blood-pressure/log", status_code=201)
async def log_bp(r: BPLog, user_id: str = Query("default")):
    band = classify(r.systolic, r.diastolic)
    entry = {**r.model_dump(), "at": datetime.now(timezone.utc).isoformat(), "range": band.key}
    _readings.setdefault(user_id, []).append(entry)
    return {**entry, "label": band.label, "next_step": band.next_step,
            "urgent_symptoms": list(URGENT_SYMPTOMS) if band.key == "very_high" else []}


@router.get("/blood-pressure/log")
async def list_bp(user_id: str = Query("default"), days: int = Query(7, ge=1, le=365)):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    recent = [x for x in _readings.get(user_id, []) if x["at"] >= cutoff]
    return {"readings": list(reversed(recent)), "summary": summary(recent),
            "how_to": "Sit for 5 minutes, back supported, arm at heart level. Take two readings a minute apart, morning and evening."}

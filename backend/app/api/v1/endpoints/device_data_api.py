"""Health Connect sync: the phone posts records it read; summaries and the rest-activity rhythm come back."""
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.services.actigraphy_analysis import rest_activity_rhythm
from app.services.device_data import device_data_service

router = APIRouter()

RecordType = Literal[
    "steps", "sleep", "heart_rate", "resting_heart_rate", "hrv_rmssd", "weight", "body_fat",
    "blood_glucose", "exercise", "active_calories", "distance", "oxygen_saturation",
    "blood_pressure", "body_temperature", "nutrition", "menstruation_flow",
]


class DeviceRecord(BaseModel):
    id: str = Field(min_length=1, max_length=128, description="Health Connect record id")
    type: RecordType
    start: float = Field(gt=946684800, description="Epoch seconds")
    end: float = Field(gt=946684800)
    value: Optional[float] = None
    data: Dict[str, Any] = Field(default_factory=dict, description="Type-specific detail, e.g. systolic/diastolic")
    source: str = Field("", max_length=200, description="App that wrote the record")


class DeviceImport(BaseModel):
    records: List[DeviceRecord] = Field(max_length=20000)
    tz_offset_min: Optional[int] = Field(None, ge=-720, le=840)


@router.post("/import")
async def import_records(body: DeviceImport):
    return device_data_service.import_records([r.model_dump() for r in body.records], body.tz_offset_min)


class DeviceDeletions(BaseModel):
    record_ids: List[str] = Field(max_length=20000)


@router.post("/delete")
async def delete_records(body: DeviceDeletions):
    """Records the user deleted in Health Connect leave the server too."""
    return device_data_service.delete_records(body.record_ids)


@router.get("/daily")
async def daily(days: int = Query(14, ge=1, le=90)):
    return {"days": device_data_service.daily_summary(days)}


@router.get("/rest-activity")
async def rest_activity(days: int = Query(14, ge=3, le=60)):
    grid = device_data_service.hourly_steps(days)
    return {**rest_activity_rhythm(grid["hourly"]), "dates": grid["days"]}


@router.get("/status")
async def status():
    return device_data_service.status()

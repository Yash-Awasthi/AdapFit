"""Wearable device sync: ingest data from WearOS/HealthKit companion apps."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter()


class WearableDataBatch(BaseModel):
    """Batch of wearable data points from a companion device."""
    device_type: str = Field(examples=["wearos", "apple_watch", "garmin", "fitbit"])
    device_id: Optional[str] = Field(None, examples=["Pixel Watch 3"])
    hrv_readings: List[dict] = Field(default_factory=list, description="[{timestamp, value_ms}]")
    sleep_sessions: List[dict] = Field(default_factory=list, description="[{start, end, deep_min, rem_min, light_min}]")
    heart_rate_readings: List[dict] = Field(default_factory=list, description="[{timestamp, bpm}]")
    step_counts: List[dict] = Field(default_factory=list, description="[{date, count}]")
    body_measurements: List[dict] = Field(default_factory=list, description="[{date, weight_kg, body_fat_pct}]")
    stress_readings: List[dict] = Field(default_factory=list, description="[{timestamp, score_0_100}]")


class SyncResponse(BaseModel):
    sync_id: str
    device_type: str
    records_ingested: int
    hrv_count: int
    sleep_count: int
    hr_count: int
    step_count: int
    synced_at: str


class DeviceInfo(BaseModel):
    device_id: str
    device_type: str
    last_sync: str
    records_total: int


# In-memory storage
sync_history: dict = {}  # user_id -> list of sync records
device_registry: dict = {}  # user_id -> {device_id -> info}


@router.post("/sync", response_model=SyncResponse)
async def sync_wearable_data(batch: WearableDataBatch, user_id: str = Query("default")):
    """Sync data from a wearable companion device."""
    now = datetime.now(timezone.utc)
    sync_id = str(uuid.uuid4())[:8]

    total_records = (
        len(batch.hrv_readings) + len(batch.sleep_sessions) +
        len(batch.heart_rate_readings) + len(batch.step_counts) +
        len(batch.body_measurements) + len(batch.stress_readings)
    )

    record = {
        "sync_id": sync_id,
        "device_type": batch.device_type,
        "device_id": batch.device_id,
        "records_ingested": total_records,
        "synced_at": now.isoformat(),
        "hrv_count": len(batch.hrv_readings),
        "sleep_count": len(batch.sleep_sessions),
        "hr_count": len(batch.heart_rate_readings),
        "step_count": len(batch.step_counts),
    }
    sync_history.setdefault(user_id, []).append(record)

    # Register device
    if batch.device_id:
        device_registry.setdefault(user_id, {})[batch.device_id] = {
            "device_id": batch.device_id,
            "device_type": batch.device_type,
            "last_sync": now.isoformat(),
            "records_total": total_records,
        }

    return SyncResponse(
        sync_id=sync_id, device_type=batch.device_type,
        records_ingested=total_records,
        hrv_count=record["hrv_count"], sleep_count=record["sleep_count"],
        hr_count=record["hrv_count"], step_count=record["step_count"],
        synced_at=now.isoformat(),
    )


@router.get("/devices", response_model=List[DeviceInfo])
async def list_devices(user_id: str = Query("default")):
    """List registered companion devices."""
    devices = device_registry.get(user_id, {})
    return [DeviceInfo(**d) for d in devices.values()]


@router.get("/sync-history")
async def sync_history_list(user_id: str = Query("default"), limit: int = Query(10, ge=1, le=50)):
    """List recent sync history."""
    return sync_history.get(user_id, [])[-limit:]


@router.get("/latest")
async def latest_data(user_id: str = Query("default")):
    """Get latest synced wearable data summary."""
    history = sync_history.get(user_id, [])
    if not history:
        return {"message": "No sync data yet", "devices": []}
    latest = history[-1]
    devices = device_registry.get(user_id, {})
    return {
        "latest_sync": latest,
        "total_syncs": len(history),
        "devices": list(devices.keys()),
    }

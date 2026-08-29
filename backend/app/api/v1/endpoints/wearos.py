"""Wearable device sync: ingest data from WearOS/HealthKit companion apps."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional

from app.core import health_validation
from app.core.health_data import health_data_store

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
    records_rejected: int
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


def _parse_ts(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _sleep_duration_hours(session: dict) -> Optional[float]:
    start, end = session.get("start"), session.get("end")
    if start and end:
        try:
            t0 = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
            t1 = datetime.fromisoformat(str(end).replace("Z", "+00:00"))
            hours = (t1 - t0).total_seconds() / 3600
            if hours > 0:
                return hours
        except ValueError:
            pass
    minutes = sum(session.get(k) or 0 for k in ("deep_min", "rem_min", "light_min"))
    return minutes / 60 if minutes else None


def _ingest(
    user_id: str, device_type: str, readings: List[dict],
    value_key: str, physiological_type: str, storage_type: str,
    timestamp_key: str = "timestamp",
) -> tuple[int, int]:
    """Validate each reading against its plausible physiological range, then
    persist survivors with a computed (never client-supplied) confidence.
    """
    accepted = rejected = 0
    for item in readings:
        value = item.get(value_key)
        if value is None:
            rejected += 1
            continue
        ok, normalized, _reason = health_validation.validate(physiological_type, value)
        if not ok:
            rejected += 1
            continue
        confidence = health_validation.compute_confidence(physiological_type, normalized, source="device").value
        result = health_data_store.add_record(
            user_id=user_id, measurement_type=storage_type, value=normalized,
            source="device", device=device_type, confidence=confidence,
            timestamp=_parse_ts(item.get(timestamp_key)),
        )
        if result.get("error"):
            rejected += 1
        else:
            accepted += 1
    return accepted, rejected


def _ingest_stress(user_id: str, device_type: str, readings: List[dict]) -> tuple[int, int]:
    """Stress score has no physiological plausible-range table; only bound-check it."""
    accepted = rejected = 0
    for item in readings:
        value = item.get("score_0_100")
        if not isinstance(value, (int, float)) or not (0 <= value <= 100):
            rejected += 1
            continue
        result = health_data_store.add_record(
            user_id=user_id, measurement_type="stress_score", value=value,
            source="device", device=device_type, confidence="medium",
            timestamp=_parse_ts(item.get("timestamp")),
        )
        if result.get("error"):
            rejected += 1
        else:
            accepted += 1
    return accepted, rejected


@router.post("/sync", response_model=SyncResponse)
async def sync_wearable_data(batch: WearableDataBatch, user_id: str = Query("default")):
    """Sync data from a wearable companion device, validating and persisting each reading."""
    now = datetime.now(timezone.utc)
    sync_id = str(uuid.uuid4())[:8]
    device_type = batch.device_type

    hrv_ok, hrv_rej = _ingest(user_id, device_type, batch.hrv_readings, "value_ms", "hrv_rmssd", "hrv_rmssd")
    hr_ok, hr_rej = _ingest(user_id, device_type, batch.heart_rate_readings, "bpm", "heart_rate", "heart_rate")
    step_ok, step_rej = _ingest(user_id, device_type, batch.step_counts, "count", "steps", "steps")
    weight_ok, weight_rej = _ingest(user_id, device_type, batch.body_measurements, "weight_kg", "weight_kg", "weight", timestamp_key="date")
    stress_ok, stress_rej = _ingest_stress(user_id, device_type, batch.stress_readings)

    sleep_items = []
    sleep_rej = 0
    for session in batch.sleep_sessions:
        hours = _sleep_duration_hours(session)
        if hours is None:
            sleep_rej += 1
            continue
        sleep_items.append({"duration_hours": hours, "timestamp": session.get("start")})
    sleep_ok, extra_sleep_rej = _ingest(user_id, device_type, sleep_items, "duration_hours", "sleep_duration_hours", "sleep_duration")
    sleep_rej += extra_sleep_rej

    total_accepted = hrv_ok + hr_ok + step_ok + weight_ok + stress_ok + sleep_ok
    total_rejected = hrv_rej + hr_rej + step_rej + weight_rej + stress_rej + sleep_rej

    record = {
        "sync_id": sync_id,
        "device_type": device_type,
        "device_id": batch.device_id,
        "records_ingested": total_accepted,
        "records_rejected": total_rejected,
        "synced_at": now.isoformat(),
        "hrv_count": hrv_ok,
        "sleep_count": sleep_ok,
        "hr_count": hr_ok,
        "step_count": step_ok,
    }
    sync_history.setdefault(user_id, []).append(record)

    if batch.device_id:
        device_registry.setdefault(user_id, {})[batch.device_id] = {
            "device_id": batch.device_id,
            "device_type": device_type,
            "last_sync": now.isoformat(),
            "records_total": total_accepted,
        }

    return SyncResponse(
        sync_id=sync_id, device_type=device_type,
        records_ingested=total_accepted, records_rejected=total_rejected,
        hrv_count=hrv_ok, sleep_count=sleep_ok,
        hr_count=hr_ok, step_count=step_ok,
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

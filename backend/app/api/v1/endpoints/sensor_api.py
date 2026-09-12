"""
BLE Sensor API — heart rate monitor and wearable integration.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


class HRFrameRequest(BaseModel):
    raw_data: list[int] = Field(min_length=1, max_length=512)
    session_id: str = Field(default="default", max_length=64)


@lru_cache(maxsize=1)
def _get_monitor():
    from src.sensors.ble_monitor import BLEHeartRateMonitor
    return BLEHeartRateMonitor()


@router.post("/parse-hr", summary="Parse a BLE Heart Rate measurement frame")
async def parse_hr_frame(req: HRFrameRequest) -> dict[str, Any]:
    monitor = _get_monitor()
    try:
        frame = monitor.parse_hr_measurement(bytes(req.raw_data))
    except (ValueError, IndexError) as exc:
        raise HTTPException(status_code=422, detail=f"Invalid BLE frame: {exc}") from exc
    return {
        "heart_rate_bpm": frame.heart_rate_bpm,
        "rr_intervals_ms": frame.rr_intervals_ms,
        "energy_expended_kj": frame.energy_expended_kj,
        "sensor_contact": frame.sensor_contact,
        "timestamp": frame.timestamp.isoformat(),
    }


@router.get("/supported-sensors", summary="List supported BLE sensor types")
async def list_sensors() -> list[dict[str, str]]:
    return [
        {"type": "heart_rate", "protocol": "BLE Heart Rate Service (0x180D)", "devices": "Polar H10/H9, Garmin HRM, Wahoo TICKR"},
        {"type": "ecg", "protocol": "Polar ECG Service", "devices": "Polar H10"},
        {"type": "ppg", "protocol": "Polar PPG Service", "devices": "Polar Verity"},
    ]


@router.get("/ble-uuids", summary="Get BLE service/characteristic UUIDs")
async def get_uuids() -> dict[str, str]:
    return {
        "hr_service": "0000180d-0000-1000-8000-00805f9b34fb",
        "hr_measurement": "00002a37-0000-1000-8000-00805f9b34fb",
        "battery_level": "00002a19-0000-1000-8000-00805f9b34fb",
        "polar_ecg": "0000feea-0000-1000-8000-00805f9b34fb",
        "polar_ppg": "0000fee9-0000-1000-8000-00805f9b34fb",
    }

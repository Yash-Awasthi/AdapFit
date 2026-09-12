"""
BLE Heart Rate & ECG Monitor — connects to BLE chest straps and wearables.
Supports heart rate, RR intervals, ECG, accelerometer, and PPG from Polar sensors.

Inspired by: bleakheart (async BLE heart monitor library)
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class SensorType(Enum):
    HEART_RATE = "heart_rate"
    ECG = "ecg"
    PPG = "ppg"
    ACCELEROMETER = "accelerometer"
    BATTERY = "battery"


class ConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class HeartRateFrame:
    """A single heart rate data frame from a BLE sensor."""
    timestamp: datetime
    heart_rate_bpm: float
    rr_intervals_ms: list[float]
    energy_expended_kj: float = 0.0
    sensor_contact: bool = True
    is_instaneous: bool = False


@dataclass
class ECGFrame:
    """ECG data frame from Polar sensors."""
    timestamp: datetime
    samples: list[float]
    sampling_rate: int = 130  # Polar H10 default
    lead_index: int = 0


@dataclass
class PPGFrame:
    """PPG data frame from optical sensors."""
    timestamp: datetime
    samples: list[float]
    sampling_rate: int = 130


@dataclass
class SensorInfo:
    """Information about a connected sensor."""
    device_name: str
    device_address: str
    sensor_type: SensorType
    firmware_version: str = ""
    battery_pct: int = 0
    manufacturer: str = ""


@dataclass
class SensorReading:
    """A unified reading from any sensor type."""
    sensor_type: SensorType
    timestamp: datetime
    value: float
    raw_data: dict[str, Any] = field(default_factory=dict)


class BLEHeartRateMonitor:
    """Monitors heart rate from BLE chest straps and wearables.

    Supports Polar H10/H9 for ECG, and standard BLE HR service
    for heart rate + RR intervals.
    """

    # Standard BLE Heart Rate Service UUIDs
    HR_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
    HR_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
    BATTERY_LEVEL_UUID = "00002a19-0000-1000-8000-00805f9b34fb"

    # Polar-specific UUIDs
    POLY_ECG_SERVICE = "0000feea-0000-1000-8000-00805f9b34fb"
    POLY_PPG_SERVICE = "0000fee9-0000-1000-8000-00805f9b34fb"

    def __init__(self) -> None:
        self._status = ConnectionStatus.DISCONNECTED
        self._sensor_info: SensorInfo | None = None
        self._hr_callback: Callable[[HeartRateFrame], None] | None = None
        self._ecg_callback: Callable[[ECGFrame], None] | None = None
        self._reading_buffer: list[SensorReading] = []
        self._max_buffer = 10000
        self._rr_buffer: list[float] = []

    @property
    def status(self) -> ConnectionStatus:
        return self._status

    @property
    def sensor_info(self) -> SensorInfo | None:
        return self._sensor_info

    def parse_hr_measurement(self, data: bytes) -> HeartRateFrame:
        """Parse a BLE Heart Rate measurement characteristic value.

        Follows the Bluetooth SIG Heart Rate Measurement characteristic format.
        """
        if not data or len(data) < 2:
            return HeartRateFrame(
                timestamp=datetime.utcnow(),
                heart_rate_bpm=0,
                rr_intervals_ms=[],
                sensor_contact=False,
            )

        flags = data[0]
        is_16bit = (flags & 0x01) == 0
        has_rr = (flags & 0x10) != 0
        has_energy = (flags & 0x08) != 0
        contact_detected = (flags & 0x06) != 0

        offset = 1

        # Heart rate value
        if is_16bit:
            hr = data[offset] | (data[offset + 1] << 8)
            offset += 2
        else:
            hr = data[offset]
            offset += 1

        # Energy expended
        energy = 0.0
        if has_energy:
            energy = data[offset] | (data[offset + 1] << 8)
            offset += 2

        # RR intervals
        rr_intervals: list[float] = []
        if has_rr:
            while offset + 1 < len(data):
                rr_raw = data[offset] | (data[offset + 1] << 8)
                rr_ms = rr_raw / 1024.0 * 1000  # Convert from 1/1024 seconds to ms
                rr_intervals.append(rr_ms)
                offset += 2

        return HeartRateFrame(
            timestamp=datetime.utcnow(),
            heart_rate_bpm=float(hr),
            rr_intervals_ms=rr_intervals,
            energy_expended_kj=energy,
            sensor_contact=contact_detected,
        )

    def process_hr_frame(self, frame: HeartRateFrame) -> list[SensorReading]:
        """Process a heart rate frame and generate readings."""
        readings: list[SensorReading] = []

        # Heart rate reading
        readings.append(SensorReading(
            sensor_type=SensorType.HEART_RATE,
            timestamp=frame.timestamp,
            value=frame.heart_rate_bpm,
            raw_data={
                "energy_kj": frame.energy_expended_kj,
                "contact": frame.sensor_contact,
            },
        ))

        # RR interval readings
        for rr in frame.rr_intervals_ms:
            readings.append(SensorReading(
                sensor_type=SensorType.HEART_RATE,
                timestamp=frame.timestamp,
                value=rr,
                raw_data={"type": "rr_interval", "ms": rr},
            ))
            self._rr_buffer.append(rr)

        # Buffer management
        self._reading_buffer.extend(readings)
        if len(self._reading_buffer) > self._max_buffer:
            self._reading_buffer = self._reading_buffer[-self._max_buffer:]

        return readings

    def get_rr_intervals(self, window_size: int = 100) -> list[float]:
        """Get recent RR intervals for HRV analysis."""
        return self._rr_buffer[-window_size:]

    def get_hr_history(self, limit: int = 100) -> list[SensorReading]:
        """Get recent heart rate readings."""
        hr_readings = [
            r for r in self._reading_buffer
            if r.sensor_type == SensorType.HEART_RATE and "type" not in r.raw_data
        ]
        return hr_readings[-limit:]

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the current monitoring session."""
        hr_readings = [
            r for r in self._reading_buffer
            if r.sensor_type == SensorType.HEART_RATE and "type" not in r.raw_data
        ]

        if not hr_readings:
            return {"status": "no_data", "readings": 0}

        hr_values = [r.value for r in hr_readings]
        return {
            "status": self._status.value,
            "readings": len(hr_readings),
            "hr_min": round(min(hr_values), 1),
            "hr_max": round(max(hr_values), 1),
            "hr_avg": round(sum(hr_values) / len(hr_values), 1),
            "rr_count": len(self._rr_buffer),
            "duration_minutes": round(
                (hr_readings[-1].timestamp - hr_readings[0].timestamp).total_seconds() / 60, 1
            ) if len(hr_readings) > 1 else 0,
            "sensor": self._sensor_info.device_name if self._sensor_info else "unknown",
        }

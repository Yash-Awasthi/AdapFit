"""
BLE Heart Rate Logger for ZFIT
Extracted from: bleheartratelogger (BLE HRM data logger for Linux)
Patterns: Bluetooth Low Energy HRM communication, RR interval logging,
          heart rate data parsing, SQLite storage, device management
"""
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class HRMDeviceType(Enum):
    POLAR_H7 = "polar_h7"
    POLAR_H10 = "polar_h10"
    WAHOO_TICKR = "wahoo_tickr"
    ZEPHYR_HXM = "zephyr_hxm"
    APPLE_WATCH = "apple_watch"
    GARMIN = "garmin"
    UNKNOWN = "unknown"


@dataclass
class HeartRateSample:
    timestamp: datetime
    heart_rate: int  # bpm
    rr_interval: Optional[float] = None  # ms (R-R interval)
    contact_detected: bool = True
    energy_expended: Optional[int] = None  # kJ
    device: str = ""
    device_type: HRMDeviceType = HRMDeviceType.UNKNOWN


@dataclass
class HRMSession:
    id: str
    device: str
    device_type: HRMDeviceType
    start_time: datetime
    end_time: Optional[datetime] = None
    samples: list[HeartRateSample] = field(default_factory=list)
    activity_type: str = "resting"  # resting, exercise, sleep

    @property
    def duration_minutes(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 60
        return 0

    @property
    def avg_heart_rate(self) -> float:
        if not self.samples:
            return 0
        return sum(s.heart_rate for s in self.samples) / len(self.samples)

    @property
    def min_heart_rate(self) -> int:
        return min(s.heart_rate for s in self.samples) if self.samples else 0

    @property
    def max_heart_rate(self) -> int:
        return max(s.heart_rate for s in self.samples) if self.samples else 0

    @property
    def rr_intervals(self) -> list[float]:
        return [s.rr_interval for s in self.samples if s.rr_interval is not None]


# ─── BLE Heart Rate Data Parsing ───────────────────────────────────────

def parse_heart_rate_measurement(data: bytes) -> HeartRateSample:
    """Parse BLE Heart Rate Service measurement characteristic (0x2A37)."""
    if len(data) < 2:
        raise ValueError("Invalid heart rate measurement data")

    flags = data[0]
    is_16bit = (flags & 0x01) == 0
    has_energy = (flags & 0x08) != 0
    has_rr = (flags & 0x10) != 0

    offset = 1
    if is_16bit:
        heart_rate = data[offset] | (data[offset + 1] << 8)
        offset += 2
    else:
        heart_rate = data[offset]
        offset += 1

    energy_expended = None
    if has_energy and offset + 2 <= len(data):
        energy_expended = data[offset] | (data[offset + 1] << 8)
        offset += 2

    rr_interval = None
    if has_rr and offset + 2 <= len(data):
        rr_raw = data[offset] | (data[offset + 1] << 8)
        rr_interval = rr_raw / 1024.0 * 1000  # Convert to ms

    return HeartRateSample(
        timestamp=datetime.now(),
        heart_rate=heart_rate,
        rr_interval=rr_interval,
        contact_detected=True,
        energy_expended=energy_expended,
    )


def parse_heart_rate_from_json(data: dict) -> HeartRateSample:
    """Parse heart rate data from JSON format (watch exports)."""
    return HeartRateSample(
        timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
        heart_rate=int(data.get("heart_rate", 0)),
        rr_interval=data.get("rr_interval"),
        contact_detected=data.get("contact_detected", True),
        energy_expended=data.get("energy_expended"),
        device=data.get("device", ""),
        device_type=HRMDeviceType(data.get("device_type", "unknown")),
    )


# ─── Session Analysis ──────────────────────────────────────────────────

def analyze_session(session: HRMSession) -> dict:
    """Comprehensive analysis of an HRM session."""
    if not session.samples:
        return {"error": "No samples in session"}

    hr_values = [s.heart_rate for s in session.samples]
    rr_intervals = session.rr_intervals

    # Heart rate zones (based on max HR estimation)
    max_hr_est = 220 - 30  # Default age estimate
    zones = {
        "zone1_recovery": sum(1 for hr in hr_values if hr < max_hr_est * 0.5) / len(hr_values) * 100,
        "zone2_aerobic": sum(1 for hr in hr_values if max_hr_est * 0.5 <= hr < max_hr_est * 0.6) / len(hr_values) * 100,
        "zone3_tempo": sum(1 for hr in hr_values if max_hr_est * 0.6 <= hr < max_hr_est * 0.7) / len(hr_values) * 100,
        "zone4_threshold": sum(1 for hr in hr_values if max_hr_est * 0.7 <= hr < max_hr_est * 0.8) / len(hr_values) * 100,
        "zone5_max": sum(1 for hr in hr_values if hr >= max_hr_est * 0.8) / len(hr_values) * 100,
    }

    # HRV metrics from RR intervals
    hrv = {}
    if len(rr_intervals) >= 2:
        diffs = [abs(rr_intervals[i] - rr_intervals[i - 1]) for i in range(1, len(rr_intervals))]
        mean_rr = sum(rr_intervals) / len(rr_intervals)
        hrv = {
            "mean_rr": round(mean_rr, 2),
            "rmssd": round(math.sqrt(sum(d ** 2 for d in diffs) / len(diffs)), 2),
            "sdnn": round(math.sqrt(sum((rr - mean_rr) ** 2 for rr in rr_intervals) / len(rr_intervals)), 2),
            "nn50": sum(1 for d in diffs if d > 50),
            "pnn50": round(sum(1 for d in diffs if d > 50) / len(diffs) * 100, 1),
        }

    return {
        "session_id": session.id,
        "duration_minutes": round(session.duration_minutes, 1),
        "total_samples": len(session.samples),
        "avg_heart_rate": round(session.avg_heart_rate, 1),
        "min_heart_rate": session.min_heart_rate,
        "max_heart_rate": session.max_heart_rate,
        "heart_rate_range": session.max_heart_rate - session.min_heart_rate,
        "zones": {k: round(v, 1) for k, v in zones.items()},
        "hrv": hrv,
        "device": session.device,
        "activity_type": session.activity_type,
    }


# ─── Device Management ─────────────────────────────────────────────────

KNOWN_DEVICES = {
    "Polar H7": HRMDeviceType.POLAR_H7,
    "Polar H10": HRMDeviceType.POLAR_H10,
    "Wahoo TICKR": HRMDeviceType.WAHOO_TICKR,
    "Zephyr HxM": HRMDeviceType.ZEPHYR_HXM,
}

def identify_device(device_name: str) -> HRMDeviceType:
    """Identify HRM device type from name."""
    for name, dtype in KNOWN_DEVICES.items():
        if name.lower() in device_name.lower():
            return dtype
    return HRMDeviceType.UNKNOWN

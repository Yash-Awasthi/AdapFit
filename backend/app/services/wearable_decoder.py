"""Wearable Data Decoder.

Extracted from wearable (inspiration).
Decodes WHOOP protocol frames with category classification
and field extraction for heart rate, RR intervals, and accelerometer data.

All pure functions — no DB, no async.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# --- Categories ---

CATEGORIES = [
    "frame", "cmd", "time", "hr", "rr", "accel", "gyro",
    "ppg", "battery", "event", "meta", "text", "unknown",
]

CATEGORY_DESCRIPTIONS = {
    "frame": "Frame metadata",
    "cmd": "Command data",
    "time": "Timestamp information",
    "hr": "Heart rate data",
    "rr": "RR interval data",
    "accel": "Accelerometer data",
    "gyro": "Gyroscope data",
    "ppg": "Photoplethysmography data",
    "battery": "Battery status",
    "event": "Event information",
    "meta": "Metadata",
    "text": "Text payload",
    "unknown": "Unclassified data",
}


@dataclass
class DecodedFrame:
    """Decoded wearable data frame."""
    category: str
    timestamp: float = 0.0
    heart_rate: Optional[int] = None
    rr_intervals: list[float] = field(default_factory=list)
    accelerometer: Optional[tuple[float, float, float]] = None
    gyroscope: Optional[tuple[float, float, float]] = None
    battery_level: Optional[int] = None
    raw_data: bytes = b""
    metadata: dict = field(default_factory=dict)


@dataclass
class HeartRateData:
    """Processed heart rate data."""
    bpm: int
    timestamp: float
    confidence: float = 1.0
    source: str = "wearable"


@dataclass
class RrIntervalData:
    """RR interval data."""
    intervals_ms: list[float]
    timestamp: float
    rmssd: float = 0.0
    mean_rr: float = 0.0
    sdnn: float = 0.0


# --- Frame Decoding ---

def decode_frame(data: bytes) -> DecodedFrame:
    """Decode a raw wearable frame.

    Args:
        data: Raw frame bytes

    Returns:
        Decoded frame with extracted fields
    """
    if not data or len(data) < 2:
        return DecodedFrame(category="unknown", raw_data=data)

    # First byte is category
    category_id = data[0] & 0x0F
    category = CATEGORIES[category_id] if category_id < len(CATEGORIES) else "unknown"

    frame = DecodedFrame(category=category, raw_data=data)

    # Decode based on category
    if category == "hr":
        frame.heart_rate = _decode_heart_rate(data[1:])
    elif category == "rr":
        frame.rr_intervals = _decode_rr_intervals(data[1:])
    elif category == "accel":
        frame.accelerometer = _decode_accelerometer(data[1:])
    elif category == "gyro":
        frame.gyroscope = _decode_gyroscope(data[1:])
    elif category == "battery":
        frame.battery_level = _decode_battery(data[1:])

    # Extract timestamp if present
    if len(data) >= 5:
        frame.timestamp = int.from_bytes(data[1:5], "big") / 1000.0

    return frame


def _decode_heart_rate(data: bytes) -> Optional[int]:
    """Decode heart rate from data bytes."""
    if len(data) < 1:
        return None
    return data[0]


def _decode_rr_intervals(data: bytes) -> list[float]:
    """Decode RR intervals from data bytes."""
    intervals = []
    for i in range(0, len(data) - 1, 2):
        rr = int.from_bytes(data[i:i + 2], "big") / 1024.0  # Convert to seconds
        intervals.append(round(rr * 1000, 1))  # Convert to ms
    return intervals


def _decode_accelerometer(data: bytes) -> Optional[tuple[float, float, float]]:
    """Decode accelerometer data."""
    if len(data) < 6:
        return None
    x = int.from_bytes(data[0:2], "big", signed=True) / 1000.0
    y = int.from_bytes(data[2:4], "big", signed=True) / 1000.0
    z = int.from_bytes(data[4:6], "big", signed=True) / 1000.0
    return (round(x, 3), round(y, 3), round(z, 3))


def _decode_gyroscope(data: bytes) -> Optional[tuple[float, float, float]]:
    """Decode gyroscope data."""
    if len(data) < 6:
        return None
    x = int.from_bytes(data[0:2], "big", signed=True) / 1000.0
    y = int.from_bytes(data[2:4], "big", signed=True) / 1000.0
    z = int.from_bytes(data[4:6], "big", signed=True) / 1000.0
    return (round(x, 3), round(y, 3), round(z, 3))


def _decode_battery(data: bytes) -> Optional[int]:
    """Decode battery level."""
    if len(data) < 1:
        return None
    return min(100, max(0, data[0]))


# --- HRV Calculation ---

def calculate_rr_metrics(intervals_ms: list[float]) -> RrIntervalData:
    """Calculate HRV metrics from RR intervals.

    Args:
        intervals_ms: List of RR intervals in milliseconds

    Returns:
        RR interval data with HRV metrics
    """
    if not intervals_ms:
        return RrIntervalData(intervals_ms=[], timestamp=0.0)

    import math

    mean_rr = sum(intervals_ms) / len(intervals_ms)

    # RMSSD
    if len(intervals_ms) > 1:
        squared_diffs = [(intervals_ms[i] - intervals_ms[i - 1]) ** 2
                         for i in range(1, len(intervals_ms))]
        rmssd = math.sqrt(sum(squared_diffs) / len(squared_diffs))
    else:
        rmssd = 0.0

    # SDNN
    if len(intervals_ms) > 1:
        variance = sum((rr - mean_rr) ** 2 for rr in intervals_ms) / len(intervals_ms)
        sdnn = math.sqrt(variance)
    else:
        sdnn = 0.0

    return RrIntervalData(
        intervals_ms=intervals_ms,
        timestamp=0.0,
        rmssd=round(rmssd, 2),
        mean_rr=round(mean_rr, 2),
        sdnn=round(sdnn, 2),
    )


# --- Data Aggregation ---

def aggregate_heart_rate(frames: list[DecodedFrame]) -> HeartRateData:
    """Aggregate heart rate from multiple frames.

    Args:
        frames: List of decoded frames with heart rate data

    Returns:
        Aggregated heart rate data
    """
    hr_values = [f.heart_rate for f in frames if f.heart_rate is not None]

    if not hr_values:
        return HeartRateData(bpm=0, timestamp=0.0, confidence=0.0)

    avg_hr = sum(hr_values) / len(hr_values)
    latest_ts = max(f.timestamp for f in frames if f.heart_rate is not None)

    return HeartRateData(
        bpm=round(avg_hr),
        timestamp=latest_ts,
        confidence=min(1.0, len(hr_values) / 5),  # More samples = higher confidence
    )


def classify_hr_zone(hr: int, max_hr: Optional[int] = None, age: int = 30) -> str:
    """Classify heart rate zone.

    Args:
        hr: Current heart rate
        max_hr: Maximum heart rate (default: 220 - age)
        age: User age for max HR calculation

    Returns:
        HR zone name
    """
    if max_hr is None:
        max_hr = 220 - age

    pct = hr / max_hr

    if pct < 0.5:
        return "Rest"
    elif pct < 0.6:
        return "Zone 1 - Warm Up"
    elif pct < 0.7:
        return "Zone 2 - Fat Burn"
    elif pct < 0.8:
        return "Zone 3 - Aerobic"
    elif pct < 0.9:
        return "Zone 4 - Anaerobic"
    else:
        return "Zone 5 - Maximum"


# --- Category Info ---

def get_category_info(category: str) -> dict:
    """Get information about a data category.

    Args:
        category: Category name

    Returns:
        Category information
    """
    return {
        "name": category,
        "description": CATEGORY_DESCRIPTIONS.get(category, "Unknown category"),
        "is_valid": category in CATEGORIES,
    }

"""BLE Heart Rate Data Processor.

Extracted from bleakheart (inspiration).
Processes raw BLE heart rate data frames: RR interval extraction,
instant HR calculation, skin contact detection, timestamp normalization,
and battery monitoring.

All pure functions — no BLE connection code, just data transformation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ContactStatus(Enum):
    """Skin contact detection status."""
    UNKNOWN = "unknown"
    GOOD = "good"
    LOST = "lost"


@dataclass
class HeartRateFrame:
    """Parsed heart rate data frame from BLE."""
    timestamp_ns: int  # nanosecond timestamp
    avg_hr: float  # average heart rate (bpm)
    instant_hr: Optional[float] = None  # computed from RR if available
    rr_intervals_ms: list[float] = field(default_factory=list)
    energy_kj: Optional[float] = None  # energy expenditure in kJ
    contact: ContactStatus = ContactStatus.UNKNOWN
    sensor_skin_contact: bool = False


@dataclass
class BatteryReading:
    """Battery level reading from BLE device."""
    level_percent: int  # 0-100
    timestamp_ns: int


class BLEHRParser:
    """Parse raw BLE Heart Rate characteristic data frames.

    The BLE Heart Rate Service (0x2A37) encodes data as:
    - Byte 0: flags
    - Byte 1+: HR value (1 or 2 bytes depending on flags)
    - Optional: RR intervals (2 bytes each, in 1/1024s units)
    """

    FLAG_HR_FORMAT_16BIT = 0x01
    FLAG_RR_INTERVAL = 0x10
    FLAG_ENERGY_EXPENDED = 0x08
    FLAG_SENSOR_CONTACT = 0x04
    FLAG_SENSOR_CONTACT_SUPPORTED = 0x02

    @staticmethod
    def parse_frame(raw_data: bytes, timestamp_ns: int) -> HeartRateFrame:
        """Parse a raw BLE heart rate characteristic value.

        Args:
            raw_data: Raw bytes from BLE notification
            timestamp_ns: Client timestamp in nanoseconds

        Returns:
            Parsed HeartRateFrame with all available fields
        """
        if len(raw_data) < 2:
            return HeartRateFrame(
                timestamp_ns=timestamp_ns, avg_hr=0.0
            )

        flags = raw_data[0]
        offset = 1

        # Heart rate value
        is_16bit = bool(flags & BLEHRParser.FLAG_HR_FORMAT_16BIT)
        if is_16bit:
            hr = raw_data[offset] | (raw_data[offset + 1] << 8)
            offset += 2
        else:
            hr = raw_data[offset]
            offset += 1

        # Sensor contact
        contact_supported = bool(flags & BLEHRParser.FLAG_SENSOR_CONTACT_SUPPORTED)
        contact_detected = bool(flags & BLEHRParser.FLAG_SENSOR_CONTACT)
        if contact_supported:
            contact = ContactStatus.GOOD if contact_detected else ContactStatus.LOST
        else:
            contact = ContactStatus.UNKNOWN

        # Energy expended
        energy_kj = None
        if flags & BLEHRParser.FLAG_ENERGY_EXPENDED:
            if offset + 2 <= len(raw_data):
                energy_kj = (raw_data[offset] | (raw_data[offset + 1] << 8)) / 1000.0
                offset += 2

        # RR intervals (in 1/1024 second units)
        rr_intervals = []
        if flags & BLEHRParser.FLAG_RR_INTERVAL:
            while offset + 1 < len(raw_data):
                rr_raw = raw_data[offset] | (raw_data[offset + 1] << 8)
                rr_ms = rr_raw * 1000.0 / 1024.0
                rr_intervals.append(rr_ms)
                offset += 2

        return HeartRateFrame(
            timestamp_ns=timestamp_ns,
            avg_hr=float(hr),
            rr_intervals_ms=rr_intervals,
            energy_kj=energy_kj,
            contact=contact,
            sensor_skin_contact=contact_detected,
        )


def compute_instant_hr(rr_interval_ms: float) -> float:
    """Compute instant heart rate from a single RR interval.

    Args:
        rr_interval_ms: RR interval in milliseconds

    Returns:
        Instant heart rate in bpm
    """
    if rr_interval_ms <= 0:
        return 0.0
    return 60000.0 / rr_interval_ms


def normalize_timestamps_to_epoch(
    frames: list[HeartRateFrame],
    reference_epoch_ns: int,
) -> list[HeartRateFrame]:
    """Normalize device timestamps to epoch time.

    Polar devices use a custom time system. This function adjusts
    timestamps relative to a known epoch reference point.

    Args:
        frames: List of heart rate frames with device timestamps
        reference_epoch_ns: Known epoch time (ns) for one reference frame

    Returns:
        Frames with adjusted timestamps
    """
    if not frames:
        return frames

    # Calculate offset from first frame
    first_device_ts = frames[0].timestamp_ns
    offset = reference_epoch_ns - first_device_ts

    return [
        HeartRateFrame(
            timestamp_ns=frame.timestamp_ns + offset,
            avg_hr=frame.avg_hr,
            instant_hr=frame.instant_hr,
            rr_intervals_ms=frame.rr_intervals_ms,
            energy_kj=frame.energy_kj,
            contact=frame.contact,
            sensor_skin_contact=frame.sensor_skin_contact,
        )
        for frame in frames
    ]


def detect_skin_contact_events(
    frames: list[HeartRateFrame],
) -> list[dict]:
    """Detect skin contact establishment and loss events.

    Args:
        frames: Sequence of heart rate frames with contact status

    Returns:
        List of events with type (established/lost), timestamp, and frame index
    """
    events = []
    prev_contact = None

    for i, frame in enumerate(frames):
        current = frame.contact
        if prev_contact is not None and current != prev_contact:
            if current == ContactStatus.GOOD:
                events.append({
                    "type": "established",
                    "timestamp_ns": frame.timestamp_ns,
                    "frame_index": i,
                })
            elif current == ContactStatus.LOST:
                events.append({
                    "type": "lost",
                    "timestamp_ns": frame.timestamp_ns,
                    "frame_index": i,
                })
        prev_contact = current

    return events


def compute_rr_statistics(rr_intervals_ms: list[float]) -> dict:
    """Compute statistics from RR interval series.

    Args:
        rr_intervals_ms: List of RR intervals in milliseconds

    Returns:
        Dictionary with mean_rr, sdnn, rmssd, nn50, pnn50, min_rr, max_rr
    """
    if not rr_intervals_ms or len(rr_intervals_ms) < 2:
        return {
            "mean_rr": 0.0, "sdnn": 0.0, "rmssd": 0.0,
            "nn50": 0, "pnn50": 0.0, "min_rr": 0.0, "max_rr": 0.0,
            "count": len(rr_intervals_ms),
        }

    n = len(rr_intervals_ms)
    mean_rr = sum(rr_intervals_ms) / n

    # SDNN
    variance = sum((rr - mean_rr) ** 2 for rr in rr_intervals_ms) / (n - 1)
    sdnn = math.sqrt(variance)

    # RMSSD
    sq_diffs = [
        (rr_intervals_ms[i + 1] - rr_intervals_ms[i]) ** 2
        for i in range(n - 1)
    ]
    rmssd = math.sqrt(sum(sq_diffs) / (n - 1))

    # NN50 and pNN50
    nn50_count = sum(
        1 for i in range(n - 1)
        if abs(rr_intervals_ms[i + 1] - rr_intervals_ms[i]) > 50.0
    )
    pnn50 = (nn50_count / (n - 1)) * 100.0 if n > 1 else 0.0

    return {
        "mean_rr": mean_rr,
        "sdnn": sdnn,
        "rmssd": rmssd,
        "nn50": nn50_count,
        "pnn50": pnn50,
        "min_rr": min(rr_intervals_ms),
        "max_rr": max(rr_intervals_ms),
        "count": n,
    }


def normalize_battery_level(raw_byte: int) -> int:
    """Normalize battery level from raw BLE byte to percentage.

    Args:
        raw_byte: Raw byte from Battery Level characteristic (0x2A19)

    Returns:
        Battery level as percentage (0-100)
    """
    return max(0, min(100, raw_byte))


def filter_noisy_rr_intervals(
    rr_intervals_ms: list[float],
    min_rr_ms: float = 300.0,
    max_rr_ms: float = 2000.0,
) -> list[float]:
    """Filter out physiologically implausible RR intervals.

    Normal RR intervals are between 300ms (200bpm) and 2000ms (30bpm).

    Args:
        rr_intervals_ms: Raw RR intervals
        min_rr_ms: Minimum plausible RR interval (default 300ms)
        max_rr_ms: Maximum plausible RR interval (default 2000ms)

    Returns:
        Filtered list of RR intervals within plausible range
    """
    return [
        rr for rr in rr_intervals_ms
        if min_rr_ms <= rr <= max_rr_ms
    ]


def estimate_hrv_from_frames(frames: list[HeartRateFrame]) -> dict:
    """Estimate HRV metrics from a sequence of heart rate frames.

    Combines RR interval filtering and statistical analysis.

    Args:
        frames: List of parsed heart rate frames

    Returns:
        HRV statistics dictionary
    """
    all_rr = []
    for frame in frames:
        filtered = filter_noisy_rr_intervals(frame.rr_intervals_ms)
        all_rr.extend(filtered)

    return compute_rr_statistics(all_rr)


def compute_energy_expenditure(frames: list[HeartRateFrame]) -> float:
    """Sum energy expenditure across frames.

    Args:
        frames: Heart rate frames with energy data

    Returns:
        Total energy in kJ
    """
    return sum(
        frame.energy_kj for frame in frames
        if frame.energy_kj is not None
    )


def compute_average_hr(frames: list[HeartRateFrame]) -> float:
    """Compute weighted average heart rate from frames.

    Uses timestamp differences as weights for accurate averaging.

    Args:
        frames: List of heart rate frames sorted by timestamp

    Returns:
        Weighted average heart rate in bpm
    """
    if not frames:
        return 0.0

    total_weighted = 0.0
    total_duration = 0.0

    for i in range(1, len(frames)):
        dt_ns = frames[i].timestamp_ns - frames[i - 1].timestamp_ns
        dt_s = dt_ns / 1e9
        if dt_s > 0 and frames[i - 1].avg_hr > 0:
            total_weighted += frames[i - 1].avg_hr * dt_s
            total_duration += dt_s

    if total_duration == 0:
        return frames[0].avg_hr

    return total_weighted / total_duration


def classify_hr_zone(hr: float, max_hr: float = 190.0) -> dict:
    """Classify heart rate into training zones.

    Uses standard percentage-of-max HR zones.

    Args:
        hr: Current heart rate in bpm
        max_hr: Maximum heart rate (default 190)

    Returns:
        Zone classification with name, intensity, and percentage
    """
    if max_hr <= 0:
        return {"zone": 0, "name": "unknown", "intensity": 0.0}

    pct = (hr / max_hr) * 100.0

    zones = [
        (50, 60, 1, "Recovery", "Very light recovery"),
        (60, 70, 2, "Aerobic", "Base endurance building"),
        (70, 80, 3, "Tempo", "Aerobic/anaerobic threshold"),
        (80, 90, 4, "Threshold", "Lactate threshold training"),
        (90, 100, 5, "VO2max", "Maximum effort"),
    ]

    for low, high, zone, name, desc in zones:
        if pct < high or (zone == 5 and pct <= 100):
            return {
                "zone": zone,
                "name": name,
                "description": desc,
                "intensity": round(pct / 100.0, 3),
            }

    return {"zone": 5, "name": "VO2max", "intensity": 1.0}

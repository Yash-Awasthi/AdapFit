"""Smart Ring Data Parser — BLE Packet Parsing and Data Extraction.

Extracted from colmi_r02_client (inspiration).
Parses BLE packets from smart ring devices (Colmi R02/R06/R10),
extracts HR, SpO2, steps, and sleep data.

All pure functions — no BLE connection, just data transformation.
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional


@dataclass
class HeartRateLog:
    """Heart rate log entry for a single day."""
    heart_rates: list[int] = field(default_factory=list)
    timestamp: Optional[datetime] = None
    interval_minutes: int = 5

    def with_timestamps(self) -> list[tuple[int, datetime]]:
        """Return HR values with timestamps."""
        if not self.timestamp or not self.heart_rates:
            return []
        result = []
        t = self.timestamp
        delta = timedelta(minutes=self.interval_minutes)
        for hr in self.heart_rates:
            result.append((hr, t))
            t += delta
        return result


@dataclass
class SportDetail:
    """Sport/activity detail for a 15-minute interval."""
    year: int = 0
    month: int = 0
    day: int = 0
    time_index: int = 0  # 15-minute intervals (0-95)
    calories: int = 0
    steps: int = 0
    distance_m: int = 0

    @property
    def timestamp(self) -> datetime:
        """Convert time_index to datetime."""
        hour = self.time_index // 4
        minute = (self.time_index % 4) * 15
        return datetime(
            year=self.year, month=self.month, day=self.day,
            hour=hour, minute=minute, tzinfo=timezone.utc,
        )


@dataclass
class DailySummary:
    """Aggregated daily health data from smart ring."""
    date: str = ""
    total_steps: int = 0
    total_calories: int = 0
    total_distance_m: int = 0
    avg_heart_rate: float = 0.0
    min_heart_rate: int = 0
    max_heart_rate: int = 0
    hr_readings: int = 0
    sport_details: list[SportDetail] = field(default_factory=list)


# --- Packet Protocol ---

def calculate_checksum(packet: bytearray) -> int:
    """Calculate packet checksum (sum of bytes mod 255).

    Args:
        packet: Raw packet bytes

    Returns:
        Checksum byte
    """
    return sum(packet) & 255


def make_packet(command: int, sub_data: Optional[bytearray] = None) -> bytearray:
    """Create a well-formed 16-byte packet.

    Args:
        command: Command byte (0-255)
        sub_data: Optional data bytes (max 14)

    Returns:
        16-byte packet with valid checksum
    """
    if not 0 <= command <= 255:
        raise ValueError("Command must be 0-255")

    packet = bytearray(16)
    packet[0] = command

    if sub_data:
        if len(sub_data) > 14:
            raise ValueError("Sub data must be <= 14 bytes")
        for i in range(len(sub_data)):
            packet[i + 1] = sub_data[i]

    packet[-1] = calculate_checksum(packet)
    return packet


def validate_packet(packet: bytearray) -> bool:
    """Validate a received packet's checksum.

    Args:
        packet: 16-byte packet

    Returns:
        True if checksum is valid
    """
    if len(packet) != 16:
        return False
    expected = calculate_checksum(packet[:-1])
    return packet[-1] == expected


def parse_packet_header(packet: bytearray) -> tuple[int, int]:
    """Parse command and sub-type from packet header.

    Args:
        packet: 16-byte packet

    Returns:
        Tuple of (command, sub_type)
    """
    if len(packet) < 2:
        return 0, 0
    return packet[0], packet[1]


# --- Heart Rate Parsing ---

CMD_READ_HEART_RATE = 21  # 0x15

def read_heart_rate_packet(target_date: datetime) -> bytearray:
    """Create packet to request heart rate data for a date.

    Args:
        target_date: Date to query (midnight)

    Returns:
        16-byte command packet
    """
    data = bytearray(struct.pack("<L", int(target_date.timestamp())))
    return make_packet(CMD_READ_HEART_RATE, data)


def parse_heart_rate_log(packet: bytearray, base_timestamp: datetime) -> Optional[HeartRateLog]:
    """Parse a heart rate log packet.

    Heart rate data comes in packets of 288 readings (5-minute intervals).

    Args:
        packet: 16-byte heart rate packet
        base_timestamp: Base timestamp for the data

    Returns:
        HeartRateLog or None if no data
    """
    if len(packet) != 16 or packet[0] != CMD_READ_HEART_RATE:
        return None

    sub_type = packet[1]

    # Sub-type 0 = header with packet count
    if sub_type == 0:
        if packet[2] == 255:  # No data
            return None
        # Return empty log for header
        return HeartRateLog(timestamp=base_timestamp)

    # Sub-type 1+ = data packets
    if sub_type == 1:
        # First data packet contains header info
        size = packet[2]
        index = packet[3]
        return HeartRateLog(
            heart_rates=[packet[i] for i in range(4, 15) if packet[i] > 0],
            timestamp=base_timestamp,
        )

    # Continuation packets
    heart_rates = [packet[i] for i in range(2, 15) if packet[i] > 0]
    return HeartRateLog(
        heart_rates=heart_rates,
        timestamp=base_timestamp,
    )


def aggregate_heart_rates(logs: list[HeartRateLog]) -> dict:
    """Aggregate heart rate data from multiple log entries.

    Args:
        logs: List of HeartRateLog entries

    Returns:
        Aggregated statistics
    """
    all_hr = []
    for log in logs:
        all_hr.extend(log.heart_rates)

    if not all_hr:
        return {"avg": 0, "min": 0, "max": 0, "count": 0}

    # Filter out zeros (no reading)
    valid_hr = [hr for hr in all_hr if hr > 0]

    if not valid_hr:
        return {"avg": 0, "min": 0, "max": 0, "count": 0}

    return {
        "avg": round(sum(valid_hr) / len(valid_hr), 1),
        "min": min(valid_hr),
        "max": max(valid_hr),
        "count": len(valid_hr),
    }


# --- Steps Parsing ---

CMD_GET_STEPS = 67  # 0x43

def read_steps_packet(day_offset: int = 0) -> bytearray:
    """Create packet to request step data.

    Args:
        day_offset: Days offset from today (0=today, -1=yesterday)

    Returns:
        16-byte command packet
    """
    sub_data = bytearray(b"\x00\x0f\x00\x5f\x01")
    sub_data[0] = day_offset & 0xFF
    return make_packet(CMD_GET_STEPS, sub_data)


def parse_sport_detail(packet: bytearray, base_date: datetime) -> Optional[SportDetail]:
    """Parse a sport detail packet (15-minute interval).

    Args:
        packet: 16-byte sport detail packet
        base_date: Base date for the data

    Returns:
        SportDetail or None
    """
    if len(packet) != 16 or packet[0] != CMD_GET_STEPS:
        return None

    if packet[1] == 255:  # No data
        return None

    time_index = packet[2]
    steps = packet[3] | (packet[4] << 8)
    distance = packet[5] | (packet[6] << 8)
    calories = packet[7] | (packet[8] << 8)

    return SportDetail(
        year=base_date.year,
        month=base_date.month,
        day=base_date.day,
        time_index=time_index,
        steps=steps,
        distance_m=distance,
        calories=calories,
    )


def aggregate_sport_details(details: list[SportDetail]) -> dict:
    """Aggregate sport details into daily summary.

    Args:
        details: List of SportDetail entries

    Returns:
        Aggregated daily statistics
    """
    total_steps = sum(d.steps for d in details)
    total_calories = sum(d.calories for d in details)
    total_distance = sum(d.distance_m for d in details)

    return {
        "total_steps": total_steps,
        "total_calories": total_calories,
        "total_distance_m": total_distance,
        "total_distance_km": round(total_distance / 1000, 2),
        "active_minutes": sum(1 for d in details if d.steps > 0) * 15,
        "intervals": len(details),
    }


# --- SpO2 Parsing ---

CMD_READ_SPO2 = 22  # 0x16

def parse_spo2_packet(packet: bytearray) -> Optional[dict]:
    """Parse a SpO2 data packet.

    Args:
        packet: 16-byte SpO2 packet

    Returns:
        SpO2 reading dict or None
    """
    if len(packet) != 16 or packet[0] != CMD_READ_SPO2:
        return None

    if packet[1] == 255:  # No data
        return None

    spo2 = packet[2]
    confidence = packet[3]

    if 0 < spo2 <= 100:
        return {"spo2": spo2, "confidence": confidence}
    return None


# --- Sleep Parsing ---

def detect_sleep_periods(
    hr_log: HeartRateLog,
    low_hr_threshold: int = 60,
    min_duration_hours: float = 1.0,
) -> list[dict]:
    """Detect potential sleep periods from heart rate data.

    Uses low heart rate as a proxy for sleep.

    Args:
        hr_log: Heart rate log for the day
        low_hr_threshold: HR below this suggests sleep
        min_duration_hours: Minimum period duration

    Returns:
        List of detected sleep periods
    """
    if not hr_log.heart_rates:
        return []

    timestamps = hr_log.with_timestamps()
    if not timestamps:
        return []

    periods = []
    in_sleep = False
    sleep_start = None

    for hr, ts in timestamps:
        if hr > 0 and hr < low_hr_threshold:
            if not in_sleep:
                in_sleep = True
                sleep_start = ts
        else:
            if in_sleep and sleep_start:
                duration = (ts - sleep_start).total_seconds() / 3600
                if duration >= min_duration_hours:
                    periods.append({
                        "start": sleep_start.isoformat(),
                        "end": ts.isoformat(),
                        "duration_hours": round(duration, 1),
                        "avg_hr": round(
                            sum(t[0] for t in timestamps
                                if sleep_start <= t[1] <= ts and t[0] > 0)
                            / max(1, sum(1 for t in timestamps
                                         if sleep_start <= t[1] <= ts and t[0] > 0)),
                            1,
                        ),
                    })
                in_sleep = False
                sleep_start = None

    return periods


# --- Full Day Summary ---

def create_daily_summary(
    hr_logs: list[HeartRateLog],
    sport_details: list[SportDetail],
    date_str: str,
) -> DailySummary:
    """Create a complete daily summary from smart ring data.

    Args:
        hr_logs: Heart rate logs for the day
        sport_details: Sport detail entries for the day
        date_str: Date string (YYYY-MM-DD)

    Returns:
        DailySummary with all aggregated data
    """
    hr_stats = aggregate_heart_rates(hr_logs)
    sport_stats = aggregate_sport_details(sport_details)

    return DailySummary(
        date=date_str,
        total_steps=sport_stats["total_steps"],
        total_calories=sport_stats["total_calories"],
        total_distance_m=sport_stats["total_distance_m"],
        avg_heart_rate=hr_stats["avg"],
        min_heart_rate=hr_stats["min"],
        max_heart_rate=hr_stats["max"],
        hr_readings=hr_stats["count"],
        sport_details=sport_details,
    )

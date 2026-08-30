"""BLE wearable device manager — abstraction over Polar, Mi Band, Amazfit, etc.

Extracted from inspiration/ZFIT/polar-ble-sdk and inspiration/ZFIT/gadgetbridge.
Pattern: unified device protocol abstraction for health wearables.
Supports: heart rate, ECG, accelerometer, PPG, steps, sleep, activity.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum


class DeviceType(IntEnum):
    POLAR_H10 = 1
    POLAR_H9 = 2
    POLAR_VERITY = 3
    MI_BAND_5 = 4
    MI_BAND_6 = 5
    MI_BAND_7 = 6
    AMAZFIT_BIP = 7
    AMAZFIT_GTR = 8
    PEBBLE = 9
    HPLUS = 10
    GENERIC_HR = 11  # Any BLE HR monitor using standard HR service


class SensorType(Enum):
    HEART_RATE = "heart_rate"
    ECG = "ecg"
    PPG = "ppg"
    ACCELEROMETER = "accelerometer"
    GYROSCOPE = "gyroscope"
    PEDOMETER = "pedometer"
    SLEEP = "sleep"
    SPO2 = "spo2"
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"  # barometer for altitude


@dataclass
class BLEDevice:
    """A discovered BLE wearable device."""
    address: str
    name: str
    device_type: DeviceType
    battery_level: int | None = None
    firmware_version: str | None = None
    connected: bool = False
    sensors: list[SensorType] = field(default_factory=list)
    last_seen: datetime | None = None


@dataclass
class SensorData:
    """A single data point from a sensor."""
    sensor: SensorType
    timestamp: datetime
    value: float
    unit: str
    metadata: dict = field(default_factory=dict)


# Standard BLE GATT service UUIDs
class BLEService:
    HEART_RATE = "0000180D-0000-1000-8000-00805F9B34FB"
    BATTERY = "0000180F-0000-1000-8000-00805F9B34FB"
    DEVICE_INFO = "0000180A-0000-1000-8000-00805F9B34FB"
    POLAR_PMD = "6E7FXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"  # Polar specific
    POLAR_ECG = "6E7FE9XX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
    MI_BAND_HR = "00002A37-0000-1000-8000-00805F9B34FB"  # HR measurement


# Device capability matrix
DEVICE_CAPABILITIES: dict[DeviceType, list[SensorType]] = {
    DeviceType.POLAR_H10: [
        SensorType.HEART_RATE, SensorType.ECG, SensorType.ACCELEROMETER,
        SensorType.PEDOMETER,
    ],
    DeviceType.POLAR_H9: [
        SensorType.HEART_RATE, SensorType.PEDOMETER,
    ],
    DeviceType.POLAR_VERITY: [
        SensorType.HEART_RATE, SensorType.PPG, SensorType.ACCELEROMETER,
        SensorType.SPO2,
    ],
    DeviceType.MI_BAND_5: [
        SensorType.HEART_RATE, SensorType.PEDOMETER, SensorType.SLEEP,
        SensorType.SPO2,
    ],
    DeviceType.MI_BAND_6: [
        SensorType.HEART_RATE, SensorType.PEDOMETER, SensorType.SLEEP,
        SensorType.SPO2, SensorType.PPG,
    ],
    DeviceType.MI_BAND_7: [
        SensorType.HEART_RATE, SensorType.PEDOMETER, SensorType.SLEEP,
        SensorType.SPO2, SensorType.PPG, SensorType.ACCELEROMETER,
    ],
    DeviceType.AMAZFIT_BIP: [
        SensorType.HEART_RATE, SensorType.PEDOMETER, SensorType.SLEEP,
        SensorType.ACCELEROMETER,
    ],
    DeviceType.AMAZFIT_GTR: [
        SensorType.HEART_RATE, SensorType.PEDOMETER, SensorType.SLEEP,
        SensorType.SPO2, SensorType.ACCELEROMETER,
    ],
    DeviceType.GENERIC_HR: [
        SensorType.HEART_RATE,
    ],
}


def identify_device(name: str, address: str) -> DeviceType:
    """Identify device type from broadcast name."""
    name_lower = name.lower()
    if "polar h10" in name_lower: return DeviceType.POLAR_H10
    if "polar h9" in name_lower: return DeviceType.POLAR_H9
    if "polar verity" in name_lower or "polar oh1" in name_lower: return DeviceType.POLAR_VERITY
    if "mi band 7" in name_lower or "mi band 7" in name_lower: return DeviceType.MI_BAND_7
    if "mi band 6" in name_lower: return DeviceType.MI_BAND_6
    if "mi band 5" in name_lower: return DeviceType.MI_BAND_5
    if "amazfit bip" in name_lower: return DeviceType.AMAZFIT_BIP
    if "amazfit gtr" in name_lower: return DeviceType.AMAZFIT_GTR
    if "pebble" in name_lower: return DeviceType.PEBBLE
    if "hplus" in name_lower: return DeviceType.HPLUS
    return DeviceType.GENERIC_HR


def parse_hr_data(raw: bytes) -> int:
    """Parse heart rate measurement from standard BLE HR service (0x2A37).

    Format:
      Byte 0: flags
        bit 0: 0=8-bit HR, 1=16-bit HR
        bit 1-2: sensor contact
        bit 3: energy expended present
        bit 4: RR-interval present
    """
    if not raw or len(raw) < 2:
        return 0

    flags = raw[0]
    is_16bit = flags & 0x01

    if is_16bit:
        if len(raw) < 3:
            return 0
        return raw[1] | (raw[2] << 8)
    else:
        return raw[1]


def get_device_capabilities(device_type: DeviceType) -> list[SensorType]:
    """Get the list of supported sensors for a device type."""
    return DEVICE_CAPABILITIES.get(device_type, [SensorType.HEART_RATE])


def supports_sensor(device_type: DeviceType, sensor: SensorType) -> bool:
    """Check if a device supports a specific sensor."""
    return sensor in get_device_capabilities(device_type)

"""
Wearable data from wearipedia — unified wearable data access.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class WearableDevice:
    name: str
    type: str  # watch, ring, band, clip
    manufacturer: str
    sensors: List[str] = field(default_factory=list)
    battery_pct: float = 100.0
    is_connected: bool = False


@dataclass
class WearableReading:
    device: str
    sensor: str
    value: float
    unit: str
    timestamp: float
    quality: float = 1.0


class WearableManager:
    def __init__(self):
        self.devices: Dict[str, WearableDevice] = {}
        self.readings: List[WearableReading] = []

    def register_device(self, device: WearableDevice):
        self.devices[device.name] = device

    def add_reading(self, reading: WearableReading):
        self.readings.append(reading)

    def get_readings(self, sensor: Optional[str] = None, device: Optional[str] = None, since: Optional[float] = None) -> List[WearableReading]:
        result = self.readings
        if sensor: result = [r for r in result if r.sensor == sensor]
        if device: result = [r for r in result if r.device == device]
        if since: result = [r for r in result if r.timestamp >= since]
        return sorted(result, key=lambda r: r.timestamp)

    def get_sensor_summary(self, sensor: str) -> Dict:
        readings = self.get_readings(sensor=sensor)
        if not readings: return {"sensor": sensor, "count": 0}
        values = [r.value for r in readings]
        return {"sensor": sensor, "count": len(values), "min": min(values), "max": max(values), "avg": sum(values) / len(values), "latest": values[-1]}

    def get_connected_devices(self) -> List[WearableDevice]:
        return [d for d in self.devices.values() if d.is_connected]

    def get_device_capabilities(self, device_name: str) -> List[str]:
        device = self.devices.get(device_name)
        return device.sensors if device else []

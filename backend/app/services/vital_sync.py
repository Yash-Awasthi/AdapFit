"""
Vital sync from vital-sync — health data synchronization.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import time


@dataclass
class VitalData:
    timestamp: float
    metric: str
    value: float
    unit: str
    source: str = "manual"
    quality: float = 1.0


@dataclass
class SyncState:
    last_sync: float = 0.0
    pending_count: int = 0
    synced_count: int = 0
    error_count: int = 0
    conflicts: List[Dict] = field(default_factory=list)


class VitalSyncManager:
    def __init__(self):
        self.data: List[VitalData] = []
        self.state = SyncState()

    def add_vital(self, vital: VitalData):
        self.data.append(vital)
        self.state.pending_count += 1

    def get_vitals(self, metric: Optional[str] = None, since: Optional[float] = None) -> List[VitalData]:
        result = self.data
        if metric:
            result = [v for v in result if v.metric == metric]
        if since:
            result = [v for v in result if v.timestamp >= since]
        return sorted(result, key=lambda v: v.timestamp)

    def get_latest(self, metric: str) -> Optional[VitalData]:
        vitals = self.get_vitals(metric=metric)
        return vitals[-1] if vitals else None

    def compute_average(self, metric: str, window_seconds: float = 3600) -> Optional[float]:
        now = time.time()
        vitals = self.get_vitals(metric=metric, since=now - window_seconds)
        if not vitals:
            return None
        return sum(v.value for v in vitals) / len(vitals)

    def detect_anomalies(self, metric: str, std_threshold: float = 2.0) -> List[VitalData]:
        vitals = self.get_vitals(metric=metric)
        if len(vitals) < 10:
            return []
        values = [v.value for v in vitals]
        mean = sum(values) / len(values)
        std = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5
        return [v for v in vitals if abs(v.value - mean) > std_threshold * std]

    def sync_complete(self, count: int):
        self.state.pending_count = max(0, self.state.pending_count - count)
        self.state.synced_count += count
        self.state.last_sync = time.time()

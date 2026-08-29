"""
Health Data Model — Normalized health records with source attribution.
"""
import time
import uuid
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class DataSource(Enum):
    MANUAL = "manual"
    DEVICE = "device"
    SENSOR = "sensor"
    IMPORT = "import"
    CALCULATED = "calculated"


class DataConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    ESTIMATED = "estimated"


class PrivacyLevel(Enum):
    PRIVATE = "private"
    FAMILY = "family"
    MEDICAL = "medical"


# Minimal type registry — only types the system actually reads/writes
MEASUREMENT_TYPES = {
    "steps": {"unit": "count", "category": "activity"},
    "heart_rate": {"unit": "bpm", "category": "cardiovascular"},
    "resting_heart_rate": {"unit": "bpm", "category": "cardiovascular"},
    "hrv_rmssd": {"unit": "ms", "category": "cardiovascular"},
    "sleep_duration": {"unit": "hours", "category": "sleep"},
    "sleep_score": {"unit": "score", "category": "sleep"},
    "weight": {"unit": "kg", "category": "body"},
    "calories_consumed": {"unit": "kcal", "category": "nutrition"},
    "water_intake": {"unit": "ml", "category": "nutrition"},
    "stress_score": {"unit": "score", "category": "mental_health"},
    "mood_score": {"unit": "score", "category": "mental_health"},
    "recovery_score": {"unit": "score", "category": "recovery"},
    "training_load": {"unit": "au", "category": "training"},
}


@dataclass
class HealthRecord:
    id: str
    user_id: str
    measurement_type: str
    value: float
    unit: str
    source: DataSource
    confidence: DataConfidence
    timestamp: float
    recorded_at: float
    device: str = ""
    privacy_level: PrivacyLevel = PrivacyLevel.PRIVATE
    metadata: dict = field(default_factory=dict)


class HealthDataStore:
    def __init__(self):
        self._records: dict[str, list[HealthRecord]] = {}

    def add_record(self, user_id: str, measurement_type: str, value: float,
                   source: str = "manual", device: str = "", confidence: str = "medium",
                   timestamp: Optional[float] = None, privacy_level: str = "private",
                   metadata: Optional[dict] = None) -> dict:
        if measurement_type not in MEASUREMENT_TYPES:
            return {"error": f"Unknown type: {measurement_type}"}
        mt = MEASUREMENT_TYPES[measurement_type]
        record = HealthRecord(
            id=f"hr_{uuid.uuid4().hex[:12]}", user_id=user_id,
            measurement_type=measurement_type, value=value, unit=mt["unit"],
            source=DataSource(source), confidence=DataConfidence(confidence),
            timestamp=timestamp or time.time(), recorded_at=time.time(),
            device=device, privacy_level=PrivacyLevel(privacy_level),
            metadata=metadata or {},
        )
        self._records.setdefault(user_id, []).append(record)
        return {"recorded": True, "record_id": record.id, "type": measurement_type, "value": value}

    def get_records(self, user_id: str, measurement_type: Optional[str] = None,
                    days: int = 30, limit: int = 100) -> list[dict]:
        records = self._records.get(user_id, [])
        cutoff = time.time() - days * 86400
        filtered = [r for r in records if r.recorded_at > cutoff
                    and (measurement_type is None or r.measurement_type == measurement_type)]
        filtered.sort(key=lambda r: r.recorded_at, reverse=True)
        return [self._to_dict(r) for r in filtered[:limit]]

    def get_latest(self, user_id: str, measurement_type: str) -> Optional[dict]:
        matching = [r for r in self._records.get(user_id, []) if r.measurement_type == measurement_type]
        if not matching:
            return None
        return self._to_dict(max(matching, key=lambda r: r.recorded_at))

    def get_summary(self, user_id: str, days: int = 7) -> dict:
        records = self._records.get(user_id, [])
        cutoff = time.time() - days * 86400
        recent = [r for r in records if r.recorded_at > cutoff]
        summary = {"days": days, "measurements": {}}
        for r in recent:
            mt = r.measurement_type
            if mt not in summary["measurements"]:
                summary["measurements"][mt] = {"count": 0, "values": [], "sources": set()}
            summary["measurements"][mt]["count"] += 1
            summary["measurements"][mt]["values"].append(r.value)
            summary["measurements"][mt]["sources"].add(r.source.value)
        for mt, data in summary["measurements"].items():
            v = data["values"]
            data["avg"] = round(sum(v) / len(v), 2) if v else 0
            data["min"] = min(v) if v else 0
            data["max"] = max(v) if v else 0
            data["sources"] = list(data.pop("sources"))
            del data["values"]
        return summary

    def _to_dict(self, r: HealthRecord) -> dict:
        return {
            "id": r.id, "user_id": r.user_id, "measurement_type": r.measurement_type,
            "value": r.value, "unit": r.unit, "source": r.source.value,
            "confidence": r.confidence.value, "timestamp": r.timestamp,
            "recorded_at": r.recorded_at, "device": r.device,
            "privacy_level": r.privacy_level.value, "metadata": r.metadata,
        }


health_data_store = HealthDataStore()

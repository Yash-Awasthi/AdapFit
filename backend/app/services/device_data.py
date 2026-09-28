"""
Records synced from the phone's health store (Health Connect on Android).

The app reads Health Connect on the device and posts the records here; this
service keeps them per user, de-duplicated by the record id Health Connect
assigns, and derives daily summaries and the hourly activity profile the
rest-activity rhythm needs. Blood glucose also feeds the CGM summary.
Nothing here is estimated: a day without a record type has no value for it.
"""
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

TYPES = {
    "steps", "sleep", "heart_rate", "resting_heart_rate", "hrv_rmssd", "weight", "body_fat",
    "blood_glucose", "exercise", "active_calories", "distance", "oxygen_saturation",
    "blood_pressure", "body_temperature", "nutrition", "menstruation_flow",
}
RETENTION_DAYS = 400
# India first; days are split at local midnight in the user's zone offset (minutes east of UTC).
DEFAULT_OFFSET_MIN = 330


class DeviceDataService:
    def __init__(self):
        self.records: Dict[str, dict] = {}
        self.last_sync: Optional[float] = None
        self.tz_offset_min: int = DEFAULT_OFFSET_MIN

    def import_records(self, records: List[dict], tz_offset_min: Optional[int] = None) -> dict:
        if tz_offset_min is not None:
            self.tz_offset_min = tz_offset_min
        cutoff = time.time() - RETENTION_DAYS * 86400
        added = updated = skipped = 0
        glucose = []
        for r in records:
            if r["type"] not in TYPES or r["start"] < cutoff:
                skipped += 1
                continue
            key = f"{r['type']}:{r['id']}"
            if key in self.records:
                if self.records[key] == r:
                    skipped += 1
                    continue
                updated += 1
            else:
                added += 1
            self.records[key] = r
            if r["type"] == "blood_glucose" and r.get("value") is not None:
                glucose.append({"timestamp": r["start"], "value_mgdl": float(r["value"])})
        self.records = {k: v for k, v in self.records.items() if v["start"] >= cutoff}
        self.last_sync = time.time()
        result = {"added": added, "updated": updated, "skipped": skipped, "stored": len(self.records)}
        if glucose:
            from app.services.diabetes_manager import diabetes_manager_service
            result["glucose"] = diabetes_manager_service.import_readings(glucose)
        return result

    def _day(self, ts: float) -> str:
        return (datetime.fromtimestamp(ts, tz=timezone.utc) + timedelta(minutes=self.tz_offset_min)).strftime("%Y-%m-%d")

    def daily_summary(self, days: int = 14) -> List[dict]:
        since = time.time() - days * 86400
        by_day: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))
        for r in self.records.values():
            if r["start"] < since:
                continue
            # Sleep counts for the morning it ends on.
            anchor = r["end"] if r["type"] == "sleep" else r["start"]
            by_day[self._day(anchor)][r["type"]].append(r)
        out = []
        for day in sorted(by_day, reverse=True):
            t = by_day[day]
            out.append({k: v for k, v in {
                "date": day,
                "steps": _sum(t["steps"]),
                "sleep_hours": round(sum(r["end"] - r["start"] for r in t["sleep"]) / 3600, 2) if t["sleep"] else None,
                "resting_heart_rate": _latest(t["resting_heart_rate"]),
                "avg_heart_rate": _mean(t["heart_rate"]),
                "hrv_rmssd": _mean(t["hrv_rmssd"]),
                "weight_kg": _latest(t["weight"]),
                "body_fat_pct": _latest(t["body_fat"]),
                "active_calories": _sum(t["active_calories"]),
                "distance_m": _sum(t["distance"]),
                "exercise_minutes": round(sum(r["end"] - r["start"] for r in t["exercise"]) / 60) if t["exercise"] else None,
                "spo2_pct": _mean(t["oxygen_saturation"]),
                "blood_pressure": (t["blood_pressure"] and max(t["blood_pressure"], key=lambda r: r["start"])["data"]) or None,
                "body_temperature_c": _latest(t["body_temperature"]),
                "nutrition_kcal": _sum(t["nutrition"]),
                "glucose_mgdl_avg": _mean(t["blood_glucose"]),
                "menstruation_flow": _latest(t["menstruation_flow"]),
            }.items() if v is not None})
        return out

    def hourly_steps(self, days: int = 14) -> Dict[str, Any]:
        """Steps per local hour for each whole day covered, oldest first; days with no step record are dropped."""
        since = time.time() - days * 86400
        grid: Dict[str, List[float]] = defaultdict(lambda: [0.0] * 24)
        for r in self.records.values():
            if r["type"] != "steps" or r["start"] < since or r.get("value") is None:
                continue
            # A record spanning hours is spread over them in proportion to time.
            start, end = r["start"], max(r["end"], r["start"] + 1)
            t = start
            while t < end:
                local = datetime.fromtimestamp(t, tz=timezone.utc) + timedelta(minutes=self.tz_offset_min)
                hour_end = t + (3600 - (local.minute * 60 + local.second))
                seg_end = min(end, hour_end)
                grid[local.strftime("%Y-%m-%d")][local.hour] += float(r["value"]) * (seg_end - t) / (end - start)
                t = seg_end
        today = self._day(time.time())
        days_sorted = [d for d in sorted(grid) if d != today]
        return {"days": days_sorted, "hourly": [grid[d] for d in days_sorted]}

    def status(self) -> dict:
        counts: Dict[str, int] = defaultdict(int)
        for r in self.records.values():
            counts[r["type"]] += 1
        return {"last_sync": self.last_sync, "records": dict(counts), "tz_offset_min": self.tz_offset_min}


def _values(rs):
    return [float(r["value"]) for r in rs if isinstance(r.get("value"), (int, float))]


def _sum(rs):
    v = _values(rs)
    return round(sum(v), 1) if v else None


def _mean(rs):
    v = _values(rs)
    return round(sum(v) / len(v), 1) if v else None


def _latest(rs):
    rs = [r for r in rs if r.get("value") is not None]
    return max(rs, key=lambda r: r["start"])["value"] if rs else None


from app.core.per_user import per_user, register

device_data_service = register("device_data.device_data_service", per_user(DeviceDataService))

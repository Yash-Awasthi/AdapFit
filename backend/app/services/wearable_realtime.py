"""
Wearable Realtime Service — Live HR streaming, step counting, sleep detection
"""
import time
from typing import Optional
from collections import deque


class WearableRealtimeService:
    """Real-time data streaming from wearables."""

    def __init__(self):
        self._hr_buffer: deque = deque(maxlen=300)  # 5 min at 1Hz
        self._step_buffer: deque = deque(maxlen=3600)  # 1 hour
        self._sleep_data: list[dict] = []
        self._connected = False

    def connect(self, device_type: str) -> dict:
        self._connected = True
        return {"connected": True, "device": device_type, "streaming": True}

    def disconnect(self) -> dict:
        self._connected = False
        return {"disconnected": True}

    def stream_hr(self, bpm: int, confidence: float = 0.9) -> dict:
        if not self._connected: return {"error": "Not connected"}
        self._hr_buffer.append({"bpm": bpm, "confidence": confidence, "timestamp": time.time()})
        avg = sum(h["bpm"] for h in self._hr_buffer) / max(1, len(self._hr_buffer))
        return {"received": True, "current_bpm": bpm, "avg_bpm": round(avg, 1), "samples": len(self._hr_buffer), "zone": self._get_hr_zone(bpm)}

    def stream_steps(self, steps: int, distance_m: float = 0) -> dict:
        self._step_buffer.append({"steps": steps, "timestamp": time.time()})
        total = sum(s["steps"] for s in self._step_buffer)
        return {"total_steps": total, "distance_km": round(total * 0.762 / 1000, 2), "calories_burned": int(total * 0.04)}

    def get_realtime_hr(self) -> dict:
        if not self._hr_buffer: return {"bpm": 0, "zone": "unknown", "buffer_size": 0}
        latest = self._hr_buffer[-1]
        avg = sum(h["bpm"] for h in self._hr_buffer) / len(self._hr_buffer)
        return {"bpm": latest["bpm"], "avg_bpm": round(avg, 1), "zone": self._get_hr_zone(latest["bpm"]), "buffer_size": len(self._hr_buffer), "confidence": latest["confidence"]}

    def get_hr_zones(self) -> dict:
        return {"zone_1_recover": "50-60% max HR", "zone_2_aerobic": "60-70%", "zone_3_tempo": "70-80%", "zone_4_threshold": "80-90%", "zone_5_max": "90-100%"}

    def _get_hr_zone(self, bpm: int) -> str:
        if bpm < 100: return "rest"
        elif bpm < 130: return "zone_1_recover"
        elif bpm < 150: return "zone_2_aerobic"
        elif bpm < 170: return "zone_3_tempo"
        elif bpm < 185: return "zone_4_threshold"
        return "zone_5_max"


wearable_realtime_service = WearableRealtimeService()

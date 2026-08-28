"""Sensor Hub — real-time WebSocket hub for multiple BLE sensor data streams.

Manages concurrent connections from:
- Heart rate monitors (BLE)
- SpO2 sensors
- GPS trackers
- Accelerometers
- Gyroscopes

Aggregates data into unified biometric stream for real-time workout analysis.
"""

from __future__ import annotations
import asyncio
import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Optional

router = APIRouter()

# Active connections: user_id -> {sensor_type -> websocket}
_connections: dict[str, dict[str, WebSocket]] = {}

# Sensor data buffers: user_id -> recent readings
_sensor_buffers: dict[str, dict[str, list[dict]]] = {}

# Aggregated biometrics per user
_user_biometrics: dict[str, dict] = {}


async def _broadcast_to_user(user_id: str, data: dict):
    """Broadcast aggregated data to all of user's sensor connections."""
    connections = _connections.get(user_id, {})
    for ws in connections.values():
        try:
            await ws.send_json(data)
        except Exception:
            pass


@router.websocket("/ws/{user_id}")
async def sensor_websocket(websocket: WebSocket, user_id: str):
    """Main WebSocket endpoint for sensor data streaming.

    Client sends: {"type": "sensor_data", "sensor": "hr", "data": {"bpm": 145}}
    Server responds: {"type": "biometrics", "hr": 145, "hrv": 42, "timestamp": "..."}
    """
    await websocket.accept()

    sensor_type = "unknown"
    try:
        # Register connection
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            msg_type = msg.get("type", "")

            if msg_type == "register":
                sensor_type = msg.get("sensor", "unknown")
                _connections.setdefault(user_id, {})[sensor_type] = websocket
                _sensor_buffers.setdefault(user_id, {}).setdefault(sensor_type, [])
                await websocket.send_json({
                    "type": "registered",
                    "sensor": sensor_type,
                    "message": f"Connected to sensor hub as {sensor_type}",
                })

            elif msg_type == "sensor_data":
                sensor = msg.get("sensor", sensor_type)
                data = msg.get("data", {})

                # Buffer the reading
                reading = {
                    **data,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "sensor": sensor,
                }
                buffer = _sensor_buffers.setdefault(user_id, {}).setdefault(sensor, [])
                buffer.append(reading)
                if len(buffer) > 100:
                    buffer.pop(0)

                # Aggregate biometrics
                aggregated = _aggregate_biometrics(user_id)
                _user_biometrics[user_id] = aggregated

                # Send aggregated response
                await websocket.send_json({
                    "type": "biometrics",
                    "data": aggregated,
                    "timestamp": reading["timestamp"],
                })

                # Broadcast to other connections for same user
                await _broadcast_to_user(user_id, {
                    "type": "biometrics",
                    "data": aggregated,
                    "timestamp": reading["timestamp"],
                })

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "get_history":
                sensor = msg.get("sensor", "hr")
                buffer = _sensor_buffers.get(user_id, {}).get(sensor, [])
                limit = msg.get("limit", 50)
                await websocket.send_json({
                    "type": "history",
                    "sensor": sensor,
                    "data": buffer[-limit:],
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        pass
    finally:
        # Clean up
        if user_id in _connections and sensor_type in _connections[user_id]:
            del _connections[user_id][sensor_type]
            if not _connections[user_id]:
                del _connections[user_id]


def _aggregate_biometrics(user_id: str) -> dict:
    """Aggregate latest readings from all sensors into unified biometrics."""
    buffers = _sensor_buffers.get(user_id, {})
    result = {}

    # Heart rate
    hr_buffer = buffers.get("hr", buffers.get("heart_rate", []))
    if hr_buffer:
        latest = hr_buffer[-1]
        result["heart_rate_bpm"] = latest.get("bpm", latest.get("value", 0))
        if len(hr_buffer) >= 2:
            bpms = [r.get("bpm", r.get("value", 0)) for r in hr_buffer[-10:]]
            result["hr_avg"] = round(sum(bpms) / len(bpms))
            result["hr_min"] = min(bpms)
            result["hr_max"] = max(bpms)

    # HRV
    hrv_buffer = buffers.get("hrv", [])
    if hrv_buffer:
        result["hrv_rmssd"] = hrv_buffer[-1].get("rmssd", hrv_buffer[-1].get("value", 0))

    # SpO2
    spo2_buffer = buffers.get("spo2", [])
    if spo2_buffer:
        result["spo2_pct"] = spo2_buffer[-1].get("saturation", spo2_buffer[-1].get("value", 0))

    # GPS
    gps_buffer = buffers.get("gps", [])
    if gps_buffer:
        latest = gps_buffer[-1]
        result["lat"] = latest.get("lat", 0)
        result["lon"] = latest.get("lon", 0)
        result["altitude"] = latest.get("altitude", 0)
        result["speed_ms"] = latest.get("speed", 0)

    # Accelerometer
    accel_buffer = buffers.get("accel", [])
    if accel_buffer:
        latest = accel_buffer[-1]
        result["accel_x"] = latest.get("x", 0)
        result["accel_y"] = latest.get("y", 0)
        result["accel_z"] = latest.get("z", 0)

    # Temperature
    temp_buffer = buffers.get("temperature", [])
    if temp_buffer:
        result["body_temp_c"] = temp_buffer[-1].get("value", 0)

    result["sensors_connected"] = list(buffers.keys())
    result["last_update"] = datetime.now(timezone.utc).isoformat()

    return result


@router.get("/status/{user_id}")
async def get_sensor_status(user_id: str):
    """Get current sensor connection status and biometrics."""
    connections = _connections.get(user_id, {})
    biometrics = _user_biometrics.get(user_id, {})

    return {
        "connected_sensors": list(connections.keys()),
        "sensor_count": len(connections),
        "biometrics": biometrics,
        "buffer_sizes": {
            sensor: len(buf)
            for sensor, buf in _sensor_buffers.get(user_id, {}).items()
        },
    }


@router.get("/buffer/{user_id}")
async def get_sensor_buffer(user_id: str, sensor: str = "hr", limit: int = 100):
    """Get recent sensor data buffer."""
    buffer = _sensor_buffers.get(user_id, {}).get(sensor, [])
    return {"sensor": sensor, "data": buffer[-limit:], "total": len(buffer)}

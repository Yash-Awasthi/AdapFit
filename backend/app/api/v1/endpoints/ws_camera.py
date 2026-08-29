"""
WebSocket Camera Vitals — Real-time BPM streaming during measurement
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.camera_vitals import camera_vitals_service
import json
import time

router = APIRouter()


@router.websocket("/ws/bpm")
async def websocket_bpm(websocket: WebSocket):
    """
    Real-time BPM streaming via WebSocket.
    
    Client sends frame data, server responds with live BPM updates.
    Protocol:
    Client -> Server: {"type": "start", "measurement_type": "fingertip"}
    Client -> Server: {"type": "frame", "rgb_values": [r, g, b], "confidence": 0.9}
    Client -> Server: {"type": "stop"}
    Server -> Client: {"type": "status", "status": "calibrating"}
    Server -> Client: {"type": "bpm_update", "bpm": 72, "confidence": 0.85, "signal_quality": 0.9}
    Server -> Client: {"type": "result", "bpm": 72, "hrv": 45, "respiratory_rate": 16}
    """
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type", "")
            
            if msg_type == "start":
                result = camera_vitals_service.start_measurement()
                await websocket.send_json({"type": "status", **result})
            
            elif msg_type == "frame":
                frame_data = {
                    "rgb_values": message.get("rgb_values"),
                    "face_detection_confidence": message.get("confidence", 0),
                }
                result = camera_vitals_service.process_frame(frame_data)
                
                # Send live BPM update
                if result.get("current_bpm"):
                    await websocket.send_json({
                        "type": "bpm_update",
                        "bpm": result["current_bpm"],
                        "samples": result.get("samples_collected", 0),
                        "elapsed": result.get("elapsed_seconds", 0),
                    })
                else:
                    await websocket.send_json({"type": "status", **result})
            
            elif msg_type == "stop":
                reading = camera_vitals_service.get_bpm_reading()
                await websocket.send_json({
                    "type": "result",
                    "bpm": reading.bpm,
                    "confidence": reading.confidence,
                    "signal_quality": reading.signal_quality,
                    "hrv_estimate": reading.hrv_estimate,
                    "respiratory_rate": reading.respiratory_rate,
                    "duration": round(reading.measurement_duration, 1),
                })
                break
            
            elif msg_type == "fatigue":
                landmarks = message.get("landmarks", {})
                result = camera_vitals_service.detect_fatigue(landmarks)
                await websocket.send_json({
                    "type": "fatigue_result",
                    "level": result.level.value,
                    "score": result.score,
                    "recommendation": result.recommendation,
                    "micro_sleep_risk": result.micro_sleep_risk,
                })
            
            elif msg_type == "stress":
                result = camera_vitals_service.get_stress_indication()
                await websocket.send_json({"type": "stress_indication", **result})
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass

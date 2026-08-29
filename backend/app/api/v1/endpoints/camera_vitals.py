"""
Camera Vitals API — Heart Rate & Fatigue Detection Endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.services.camera_vitals import camera_vitals_service

router = APIRouter()


class FrameData(BaseModel):
    rgb_values: Optional[list[float]] = None
    face_detection_confidence: float = 0.0
    timestamp: Optional[float] = None


class FacialLandmarks(BaseModel):
    eye_aspect_ratio: float = 0.35
    head_tilt_degrees: float = 5.0
    blinks_per_minute: float = 15.0
    yawn_duration: float = 0.0
    gaze_variance: float = 0.5


class BPMStartRequest(BaseModel):
    measurement_type: str = Field(default="fingertip", description="fingertip or face")


@router.post("/bpm/start")
async def start_bpm_measurement(request: BPMStartRequest = BPMStartRequest()):
    """Start a new heart rate measurement using phone camera."""
    return camera_vitals_service.start_measurement()


@router.post("/bpm/frame")
async def process_frame(frame: FrameData):
    """Process a camera frame for BPM estimation."""
    return camera_vitals_service.process_frame(frame.model_dump(exclude_none=True))


@router.get("/bpm/result")
async def get_bpm_result():
    """Get the current BPM measurement result."""
    reading = camera_vitals_service.get_bpm_reading()
    return {
        "bpm": reading.bpm,
        "confidence": reading.confidence,
        "signal_quality": reading.signal_quality,
        "measurement_duration": round(reading.measurement_duration, 1),
        "samples_count": reading.samples_count,
        "status": reading.status.value,
        "hrv_estimate": reading.hrv_estimate,
        "respiratory_rate": reading.respiratory_rate,
    }


@router.post("/fatigue/detect")
async def detect_fatigue(landmarks: FacialLandmarks):
    """Detect fatigue level from facial landmarks."""
    result = camera_vitals_service.detect_fatigue(landmarks.model_dump())
    return {
        "level": result.level.value,
        "score": result.score,
        "eye_aspect_ratio": result.eye_aspect_ratio,
        "head_tilt_angle": result.head_tilt_angle,
        "blink_rate": result.blink_rate,
        "yawn_detected": result.yawn_detected,
        "micro_sleep_risk": result.micro_sleep_risk,
        "recommendation": result.recommendation,
    }


@router.get("/stress/indication")
async def get_stress_from_camera():
    """Get stress indication from HRV metrics derived from rPPG."""
    return camera_vitals_service.get_stress_indication()


@router.get("/fatigue/trend")
async def get_fatigue_trend(window: int = 10):
    """Get fatigue trend over recent measurements."""
    return camera_vitals_service.get_fatigue_trend(window)


@router.get("/history")
async def get_measurement_history():
    """Get BPM measurement history."""
    return {"history": camera_vitals_service.get_measurement_history()}

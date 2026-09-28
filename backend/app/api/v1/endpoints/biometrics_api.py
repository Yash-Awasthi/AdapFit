"""
Biometrics Signal Processing API — ECG R-peak detection. HRV analysis lives under /hrv.
"""
from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


# --- Response Models ---

class ECGProcessResponse(BaseModel):
    heart_rate_bpm: float
    r_peaks_count: int
    signal_quality: float = Field(ge=0, le=1)
    rr_intervals_count: int
    rr_intervals_ms: list[float]


# --- Input Validation ---

class ECGProcessRequest(BaseModel):
    signal: list[float] = Field(min_length=100, max_length=100000)
    sampling_rate: float = Field(default=250.0, ge=50, le=1000)


# --- Cached singletons ---

@lru_cache(maxsize=1)
def _get_ecg_processor():
    from src.biometrics.signals import ECGProcessor
    return ECGProcessor


# --- Routes ---

@router.post(
    "/ecg/process",
    response_model=ECGProcessResponse,
    summary="Process ECG signal and detect R-peaks",
)
async def process_ecg(req: ECGProcessRequest) -> ECGProcessResponse:
    """Process raw ECG signal data to detect R-peaks and calculate heart rate."""
    try:
        ECGProcessor = _get_ecg_processor()
        processor = ECGProcessor(sampling_rate=req.sampling_rate)
        result = processor.process(req.signal)
    except (ValueError, IndexError) as exc:
        raise HTTPException(status_code=422, detail=f"ECG processing failed: {exc}") from exc

    return ECGProcessResponse(
        heart_rate_bpm=result.heart_rate_bpm,
        r_peaks_count=len(result.r_peaks),
        signal_quality=result.signal_quality,
        rr_intervals_count=len(result.rr_intervals_ms),
        rr_intervals_ms=result.rr_intervals_ms,
    )

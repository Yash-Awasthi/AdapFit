"""
Remote Photoplethysmography (rPPG) API — camera-based heart rate estimation.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


# --- Response Models ---

class RPPGResult(BaseModel):
    heart_rate_bpm: float
    confidence: float = Field(ge=0, le=1)
    signal_quality: float | None = None
    method: str
    snr: float | None = None


class RPPGErrorResponse(BaseModel):
    error: str
    frames_needed: int | None = None


class MethodInfo(BaseModel):
    name: str
    description: str


# --- Input Validation ---

class RGBFrameRequest(BaseModel):
    roi_pixels: list[list[float]] = Field(
        min_length=1, max_length=10000,
        description="RGB pixel values from face ROI",
    )
    timestamp: float = Field(default=0.0, ge=0)


# --- Routes ---

@router.post(
    "/estimate-hr-chrom",
    response_model=RPPGResult,
    summary="Estimate heart rate using CHROM method",
)
async def estimate_hr_chrom(req: RGBFrameRequest) -> RPPGResult:
    """Estimate heart rate from camera RGB data using chrominance-based method."""
    from src.rppg.processor import RPPGProcessor

    processor = RPPGProcessor()
    valid_frames = 0
    for pixel in req.roi_pixels:
        if len(pixel) >= 3:
            processor.add_frame(pixel[0], pixel[1], pixel[2])
            valid_frames += 1

    if valid_frames < 3:
        raise HTTPException(
            status_code=422,
            detail=f"Need at least 3 valid RGB frames, got {valid_frames}",
        )

    result = processor.estimate_hr_chrom(req.timestamp)
    if result:
        return RPPGResult(
            heart_rate_bpm=result.heart_rate_bpm,
            confidence=result.confidence,
            signal_quality=result.signal_quality,
            method=result.method,
            snr=result.snr,
        )
    raise HTTPException(
        status_code=422,
        detail=f"Insufficient data for HR estimation. Need ~{processor.window_size // 2} frames.",
    )


@router.post(
    "/estimate-hr-green",
    response_model=RPPGResult,
    summary="Estimate heart rate using Green channel method",
)
async def estimate_hr_green(req: RGBFrameRequest) -> RPPGResult:
    """Estimate heart rate using the simpler green-channel method."""
    from src.rppg.processor import RPPGProcessor

    processor = RPPGProcessor()
    for pixel in req.roi_pixels:
        if len(pixel) >= 3:
            processor.add_frame(pixel[0], pixel[1], pixel[2])

    result = processor.estimate_hr_green(req.timestamp)
    if result:
        return RPPGResult(
            heart_rate_bpm=result.heart_rate_bpm,
            confidence=result.confidence,
            method=result.method,
        )
    raise HTTPException(status_code=422, detail="Insufficient data for HR estimation")


@router.get(
    "/methods",
    response_model=list[MethodInfo],
    summary="List available rPPG methods",
)
async def list_methods() -> list[MethodInfo]:
    return [
        MethodInfo(name="CHROM", description="Chrominance-based — most accurate, needs good lighting"),
        MethodInfo(name="GREEN", description="Green channel — simplest, works in most conditions"),
    ]

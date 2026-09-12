"""
Biometrics Signal Processing API — ECG, HRV, PPG analysis.
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


class TimeDomainHRV(BaseModel):
    mean_rr_ms: float
    sdnn_ms: float
    rmssd_ms: float
    pnn50_pct: float


class FrequencyDomainHRV(BaseModel):
    lf_power: float
    hf_power: float
    lf_hf_ratio: float


class NonlinearHRV(BaseModel):
    poincare_sd1: float
    poincare_sd2: float
    sample_entropy: float


class HRVAnalysisResponse(BaseModel):
    time_domain: TimeDomainHRV
    frequency_domain: FrequencyDomainHRV
    nonlinear: NonlinearHRV


# --- Input Validation ---

class ECGProcessRequest(BaseModel):
    signal: list[float] = Field(min_length=100, max_length=100000)
    sampling_rate: float = Field(default=250.0, ge=50, le=1000)


class HRVAnalysisRequest(BaseModel):
    rr_intervals_ms: list[float] = Field(min_length=5, max_length=10000)


# --- Cached singletons ---

@lru_cache(maxsize=1)
def _get_ecg_processor():
    from src.biometrics.signals import ECGProcessor
    return ECGProcessor


@lru_cache(maxsize=1)
def _get_hrv_analyzer():
    from src.biometrics.signals import HRVAnalyzer
    return HRVAnalyzer()


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
    )


@router.post(
    "/hrv/analyze",
    response_model=HRVAnalysisResponse,
    summary="Analyze HRV from RR intervals",
)
async def analyze_hrv(req: HRVAnalysisRequest) -> HRVAnalysisResponse:
    """Compute time-domain, frequency-domain, and nonlinear HRV features."""
    try:
        HRVAnalyzer = _get_hrv_analyzer()
        analyzer = HRVAnalyzer()
        features = analyzer.analyze(req.rr_intervals_ms)
    except (ValueError, ZeroDivisionError) as exc:
        raise HTTPException(status_code=422, detail=f"HRV analysis failed: {exc}") from exc

    return HRVAnalysisResponse(
        time_domain=TimeDomainHRV(
            mean_rr_ms=features.mean_rr_ms,
            sdnn_ms=features.sdnn_ms,
            rmssd_ms=features.rmssd_ms,
            pnn50_pct=features.pnn50_pct,
        ),
        frequency_domain=FrequencyDomainHRV(
            lf_power=features.lf_power,
            hf_power=features.hf_power,
            lf_hf_ratio=features.lf_hf_ratio,
        ),
        nonlinear=NonlinearHRV(
            poincare_sd1=features.poincare_sd1,
            poincare_sd2=features.poincare_sd2,
            sample_entropy=features.sample_entropy,
        ),
    )

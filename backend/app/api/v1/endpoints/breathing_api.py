"""
Breathing Analysis API — respiratory pattern analysis and apnea detection.
"""
from __future__ import annotations

from datetime import datetime
from functools import lru_cache

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


# --- Response Models ---

class BreathingAnalysisResponse(BaseModel):
    quality: str
    breath_rate_bpm: float
    ie_ratio: float
    regularity: float = Field(ge=0, le=1)
    ahi: float = Field(ge=0)
    total_breaths: int
    events_count: int
    summary: str


class QualityRange(BaseModel):
    ahi: str
    regularity: str


# --- Input Validation ---

class BreathSampleModel(BaseModel):
    timestamp: str = Field(description="ISO format timestamp")
    flow_rate: float = Field(description="Airflow rate")
    pressure_cmh2o: float = Field(default=0.0)
    spo2: float | None = Field(default=None, ge=0, le=100)


class BreathingAnalysisRequest(BaseModel):
    samples: list[BreathSampleModel] = Field(min_length=10, max_length=50000)


# --- Cached singleton ---

@lru_cache(maxsize=1)
def _get_analyzer():
    from src.breathing.analyzer import BreathingAnalyzer
    return BreathingAnalyzer()


# --- Routes ---

@router.post(
    "/analyze",
    response_model=BreathingAnalysisResponse,
    summary="Analyze breathing patterns",
)
async def analyze_breathing(req: BreathingAnalysisRequest) -> BreathingAnalysisResponse:
    """Analyze respiratory pattern, detect apnea events, and compute quality metrics."""
    from src.breathing.analyzer import BreathSample

    analyzer = _get_analyzer()
    try:
        samples = [
            BreathSample(
                timestamp=datetime.fromisoformat(s.timestamp),
                flow_rate=s.flow_rate,
                pressure_cmh2o=s.pressure_cmh2o,
                spo2=s.spo2,
            )
            for s in req.samples
        ]
        result = analyzer.analyze(samples)
    except (ValueError, IndexError) as exc:
        raise HTTPException(status_code=422, detail=f"Analysis failed: {exc}") from exc

    return BreathingAnalysisResponse(
        quality=result.quality.value,
        breath_rate_bpm=result.avg_breath_rate,
        ie_ratio=result.ie_ratio,
        regularity=result.breath_regularity,
        ahi=result.ahi,
        total_breaths=result.total_breaths,
        events_count=len(result.events),
        summary=result.summary,
    )


@router.get(
    "/quality-scale",
    response_model=dict[str, QualityRange],
    summary="Get breathing quality scale",
)
async def get_quality_scale() -> dict[str, QualityRange]:
    return {
        "excellent": QualityRange(ahi="<1", regularity=">85%"),
        "good": QualityRange(ahi="1-5", regularity="70-85%"),
        "fair": QualityRange(ahi="5-15", regularity="50-70%"),
        "poor": QualityRange(ahi="15-30", regularity="30-50%"),
        "critical": QualityRange(ahi=">30", regularity="<30%"),
    }

"""
Sleep Analysis API — sleep stage classification and architecture analysis.
"""
from __future__ import annotations

from datetime import datetime
from functools import lru_cache

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


# --- Response Models ---

class SleepArchitecture(BaseModel):
    total_sleep_min: float
    sleep_efficiency: float = Field(ge=0, le=1)
    nrem1_pct: float = Field(ge=0, le=100)
    nrem2_pct: float = Field(ge=0, le=100)
    nrem3_pct: float = Field(ge=0, le=100)
    rem_pct: float = Field(ge=0, le=100)
    awakenings: int = Field(ge=0)
    sleep_onset_min: float = Field(ge=0)


class SleepAnalysisResponse(BaseModel):
    quality: str
    quality_score: float = Field(ge=0, le=100)
    summary: str
    architecture: SleepArchitecture
    recommendations: list[str]


class QualityRating(BaseModel):
    score_range: str
    description: str


# --- Input Validation ---

class EpochModel(BaseModel):
    timestamp: str = Field(description="ISO format timestamp")
    acceleration_magnitude: float = Field(ge=0, description="Accelerometer magnitude")
    heart_rate: float | None = Field(default=None, ge=20, le=250)


class SleepAnalysisRequest(BaseModel):
    epochs: list[EpochModel] = Field(min_length=10, max_length=50000)
    time_in_bed_min: float | None = Field(default=None, ge=0, le=1440)


# --- Cached singleton ---

@lru_cache(maxsize=1)
def _get_classifier():
    from src.sleep.classifier import SleepStageClassifier
    return SleepStageClassifier()


# --- Routes ---

@router.post(
    "/analyze",
    response_model=SleepAnalysisResponse,
    summary="Analyze sleep from accelerometer data",
)
async def analyze_sleep(req: SleepAnalysisRequest) -> SleepAnalysisResponse:
    """Classify sleep stages and compute architecture metrics from wearable data."""
    from src.sleep.classifier import Epoch

    classifier = _get_classifier()
    try:
        epochs = [
            Epoch(
                timestamp=datetime.fromisoformat(e.timestamp),
                stage=0,  # Will be classified
                acceleration_magnitude=e.acceleration_magnitude,
                heart_rate=e.heart_rate,
            )
            for e in req.epochs
        ]
        result = classifier.analyze(epochs, req.time_in_bed_min)
    except (ValueError, IndexError) as exc:
        raise HTTPException(status_code=422, detail=f"Analysis failed: {exc}") from exc

    return SleepAnalysisResponse(
        quality=result.quality.value,
        quality_score=result.quality_score,
        summary=result.summary,
        architecture=SleepArchitecture(
            total_sleep_min=result.architecture.total_sleep_time_min,
            sleep_efficiency=result.architecture.sleep_efficiency,
            nrem1_pct=result.architecture.nrem1_pct,
            nrem2_pct=result.architecture.nrem2_pct,
            nrem3_pct=result.architecture.nrem3_pct,
            rem_pct=result.architecture.rem_pct,
            awakenings=result.architecture.num_awakenings,
            sleep_onset_min=result.architecture.sleep_onset_latency_min,
        ),
        recommendations=result.recommendations,
    )


@router.get(
    "/quality-ratings",
    response_model=dict[str, QualityRating],
    summary="Get sleep quality rating scale",
)
async def get_quality_ratings() -> dict[str, QualityRating]:
    return {
        "excellent": QualityRating(score_range="85-100", description="Optimal sleep quality"),
        "good": QualityRating(score_range="70-84", description="Good sleep with minor issues"),
        "fair": QualityRating(score_range="55-69", description="Some sleep issues detected"),
        "poor": QualityRating(score_range="40-54", description="Significant sleep issues"),
        "very_poor": QualityRating(score_range="0-39", description="Severe sleep disruption"),
    }

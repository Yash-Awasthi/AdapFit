"""
Voice analysis API — acoustic measurements and how they move over time.

The disease-screening routes that used to live here reported a risk
percentage per condition from thresholds invented in the service, beside
correlations quoted from published instruments the code does not implement.
They are gone rather than relabelled: there was no measurement behind them.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict

from app.services.voice_biomarker import voice_biomarker_service

router = APIRouter(prefix="/voice-biomarker", tags=["Voice Analysis"])


class VoiceAnalysisRequest(BaseModel):
    user_id: str
    audio_features: Dict[str, Any]


@router.post("/analyze")
async def analyze_voice(req: VoiceAnalysisRequest):
    """Measure a recording and compare it with this user's previous ones."""
    result = voice_biomarker_service.analyze_voice(req.user_id, req.audio_features)
    return {"success": True, "data": result}


@router.get("/trend/{user_id}/{feature}")
async def get_feature_trend(user_id: str, feature: str, limit: int = 30):
    """One acoustic feature across this user's recordings."""
    result = voice_biomarker_service.get_feature_history(user_id, feature, limit)
    return {"success": True, "data": result}


@router.get("/features")
async def list_features():
    """The acoustic measurements a recording must supply."""
    return {"success": True, "data": list(voice_biomarker_service.REQUIRED_FEATURES)}


@router.get("/exercises")
async def get_exercises(target: str = "depression"):
    """Vocal exercises for one training target. A read, so a GET."""
    return {"success": True, "data": voice_biomarker_service.get_voice_exercises(target)}

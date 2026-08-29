"""Sleep Audio Analyzer API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.sleep_audio_analyzer import sleep_audio_analyzer_service

router = APIRouter(prefix="/sleep-audio", tags=["Sleep Audio Analysis"])


class AudioAnalysisRequest(BaseModel):
    user_id: str
    audio_data: Dict[str, Any]


@router.post("/analyze")
async def analyze_night(req: AudioAnalysisRequest):
    result = sleep_audio_analyzer_service.analyze_night_audio(req.user_id, req.audio_data)
    return {"success": True, "data": result}


@router.get("/trends/{user_id}")
async def get_trends(user_id: str):
    result = sleep_audio_analyzer_service.get_snoring_trends(user_id)
    return {"success": True, "data": result}


@router.get("/remediation")
async def get_remediation():
    result = sleep_audio_analyzer_service.get_snoring_remediation()
    return {"success": True, "data": result}

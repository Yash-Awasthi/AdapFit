"""Voice Biomarker Analysis API endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.services.voice_biomarker import voice_biomarker_service

router = APIRouter(prefix="/voice-biomarker", tags=["Voice Biomarker"])


class VoiceAnalysisRequest(BaseModel):
    user_id: str
    audio_features: Dict[str, Any]


class ExerciseRequest(BaseModel):
    target: str


@router.post("/analyze")
async def analyze_voice(req: VoiceAnalysisRequest):
    result = voice_biomarker_service.analyze_voice(req.user_id, req.audio_features)
    return {"success": True, "data": result}


@router.get("/trend/{user_id}/{disease}")
async def get_trend(user_id: str, disease: str):
    result = voice_biomarker_service.get_longitudinal_trend(user_id, disease)
    return {"success": True, "data": result}


@router.post("/exercises")
async def get_exercises(req: ExerciseRequest):
    result = voice_biomarker_service.get_voice_exercises(req.target)
    return {"success": True, "data": result}


@router.get("/diseases")
async def list_diseases():
    diseases = [
        {"id": k, "name": v["name"], "biomarkers": v["biomarkers"]}
        for k, v in voice_biomarker_service.disease_models.items()
    ]
    return {"success": True, "data": diseases}

"""
Voice Workout Logging API endpoints.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field, AliasChoices
from typing import Optional, List, Dict, Any
from app.services.voice_workout import voice_workout_logger

router = APIRouter()


class VoiceTranscriptRequest(BaseModel):
    transcript: str = Field(min_length=3, max_length=3000, validation_alias=AliasChoices("transcript", "text"))
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    user_id: str = "default"

    model_config = {"populate_by_name": True}


class IncrementalRequest(BaseModel):
    partial_transcript: str = Field(min_length=1, max_length=2000)


@router.post("/parse")
async def parse_voice_transcript(req: VoiceTranscriptRequest):
    """Parse a voice transcript into structured workout data."""
    result = voice_workout_logger.parse_voice_input(req.transcript, req.confidence)
    return result


@router.post("/incremental")
async def parse_incremental(req: IncrementalRequest):
    """Process partial transcript during live recording."""
    return voice_workout_logger.process_incremental(req.partial_transcript)


@router.post("/normalize")
async def normalize_transcript(transcript: str):
    """Normalize a raw transcript (correct speech errors)."""
    normalized = voice_workout_logger.normalize_transcript(transcript)
    return {"raw": transcript, "normalized": normalized}


@router.post("/confirm")
async def format_confirmation(data: Dict[str, Any]):
    """Generate spoken confirmation text from parsed data."""
    confirmation = voice_workout_logger.format_confirmation(data)
    return {"confirmation": confirmation}


@router.get("/prompts")
async def get_voice_prompts(partial_parse: Dict[str, Any]):
    """Get follow-up voice prompts for missing data."""
    prompts = voice_workout_logger.generate_voice_prompts(partial_parse)
    return {"prompts": prompts}


@router.get("/status")
async def get_voice_status():
    return voice_workout_logger.get_status()

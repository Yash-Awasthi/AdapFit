"""
AdapFit Voice Engine API
- POST /voice-engine/transcribe  — upload audio → text (faster-whisper)
- POST /voice-engine/speak      — text → audio (edge-tts)
- GET  /voice-engine/voices     — available TTS voices
- GET  /voice-engine/status     — engine status
"""
from __future__ import annotations

import base64
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from app.services.voice_engine import (
    transcribe_audio_bytes,
    synthesize_speech,
    list_voices,
    get_status,
)

router = APIRouter()


class SpeakRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    voice: str = "en-US-JennyNeural"
    rate: str = "+0%"
    pitch: str = "+0Hz"


@router.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
):
    """Transcribe an uploaded audio file to text (faster-whisper, fully local)."""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty audio file")
    result = transcribe_audio_bytes(data, file.filename or "audio.wav")
    if not result.get("available"):
        raise HTTPException(status_code=503, detail=result.get("message", "STT unavailable"))
    return result


@router.post("/transcribe-base64")
async def transcribe_base64(payload: dict):
    """Transcribe base64-encoded audio (mobile-friendly)."""
    b64 = payload.get("audio_base64", "")
    filename = payload.get("filename", "audio.wav")
    language = payload.get("language")
    if not b64:
        raise HTTPException(status_code=400, detail="audio_base64 required")
    try:
        data = base64.b64decode(b64)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid base64") from e
    result = transcribe_audio_bytes(data, filename)
    if not result.get("available"):
        raise HTTPException(status_code=503, detail=result.get("message", "STT unavailable"))
    return result


@router.post("/speak")
async def speak(req: SpeakRequest):
    """Synthesize speech from text, returning base64 mp3."""
    result = await synthesize_speech(req.text, voice=req.voice, rate=req.rate, pitch=req.pitch)
    if not result.get("ok"):
        raise HTTPException(status_code=503, detail=result.get("message", "TTS unavailable"))
    return result


@router.get("/voices")
async def voices():
    return {"voices": list_voices()}


@router.get("/status")
async def status():
    return get_status()
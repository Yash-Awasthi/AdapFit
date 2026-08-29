"""Voice Diary API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.voice_diary import voice_diary_service

router = APIRouter(prefix="/voice-diary", tags=["Voice Diary & Mood"])

class EntryRequest(BaseModel):
    user_id: str
    audio_data: Dict[str, Any]

@router.post("/entry")
async def create_entry(req: EntryRequest):
    result = voice_diary_service.create_entry(req.user_id, req.audio_data)
    return {"success": True, "data": result}

@router.get("/trend/{user_id}")
async def get_mood_trend(user_id: str, days: int = 30):
    result = voice_diary_service.get_mood_trend(user_id, days)
    return {"success": True, "data": result}

@router.get("/weekly/{user_id}")
async def get_weekly_summary(user_id: str):
    result = voice_diary_service.get_weekly_summary(user_id)
    return {"success": True, "data": result}

@router.get("/prompt")
async def get_prompt(mood: str = "neutral"):
    result = voice_diary_service.get_prompt(mood)
    return {"success": True, "data": result}

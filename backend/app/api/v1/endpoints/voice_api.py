"""Voice Assistant API — Hands-free health tracking"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.voice_assistant import voice_assistant_service

router = APIRouter()


class VoiceCommandRequest(BaseModel):
    text: str
    user_context: dict = {}


@router.post("/command")
async def process_command(request: VoiceCommandRequest):
    return voice_assistant_service.process_command(request.text, request.user_context)


@router.get("/commands")
async def get_supported_commands():
    return {"commands": voice_assistant_service.get_supported_commands()}


@router.get("/history")
async def get_history(limit: int = 20):
    return {"history": voice_assistant_service.get_command_history(limit)}

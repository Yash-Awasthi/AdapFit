"""
AI Health Assistant — Natural Language Health Interface API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/ai-assistant", tags=["AI Health Assistant"])


class ChatMessageRequest(BaseModel):
    user_id: str
    message: str
    user_health_data: dict = {}


@router.post("/chat")
async def chat(req: ChatMessageRequest):
    from app.services.ai_health_assistant import ai_health_assistant
    return ai_health_assistant.process_message(req.user_id, req.message, req.user_health_data)


@router.get("/history/{user_id}")
async def get_history(user_id: str, limit: int = 20):
    from app.services.ai_health_assistant import ai_health_assistant
    return ai_health_assistant.get_conversation_history(user_id, limit)


@router.get("/symptoms")
async def get_symptom_database():
    from app.services.ai_health_assistant import ai_health_assistant
    return ai_health_assistant.SYMPTOM_DATABASE


@router.get("/tips")
async def get_health_tips():
    from app.services.ai_health_assistant import ai_health_assistant
    return ai_health_assistant.QUICK_HEALTH_TIPS

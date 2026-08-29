"""AI Companion API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.ai_companion import ai_companion_service

router = APIRouter(prefix="/ai-companion", tags=["AI Health Companion"])

class ChatRequest(BaseModel):
    user_id: str
    message: str
    mood: str = "neutral"

class CheckInRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]

@router.post("/chat")
async def chat(req: ChatRequest):
    return {"success": True, "data": ai_companion_service.chat(req.user_id, req.message, req.mood)}

@router.post("/check-in")
async def daily_check_in(req: CheckInRequest):
    return {"success": True, "data": ai_companion_service.daily_check_in(req.user_id, req.data)}

@router.get("/history/{user_id}")
async def get_history(user_id: str, limit: int = 20):
    return {"success": True, "data": ai_companion_service.get_conversation_history(user_id, limit)}

@router.get("/mood-insights/{user_id}")
async def get_mood_insights(user_id: str):
    return {"success": True, "data": ai_companion_service.get_mood_insights(user_id)}

@router.get("/proactive/{user_id}")
async def proactive_outreach(user_id: str):
    return {"success": True, "data": ai_companion_service.proactive_outreach(user_id)}

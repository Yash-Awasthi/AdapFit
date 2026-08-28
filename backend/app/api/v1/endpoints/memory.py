"""
Conversational Memory API endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.services.conversational_memory import conversational_memory

router = APIRouter()


class SessionStartRequest(BaseModel):
    user_id: str


class TurnRequest(BaseModel):
    session_id: str
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=5000)
    intent: Optional[str] = None


class SessionEndRequest(BaseModel):
    session_id: str
    user_id: str


@router.post("/session/start")
async def start_session(req: SessionStartRequest):
    session_id = conversational_memory.start_session(req.user_id)
    return {"session_id": session_id, "user_id": req.user_id}


@router.post("/session/turn")
async def add_turn(req: TurnRequest):
    conversational_memory.add_turn(
        req.session_id, req.role, req.content, req.intent
    )
    return {"status": "recorded", "session_id": req.session_id}


@router.post("/session/end")
async def end_session(req: SessionEndRequest):
    summary = conversational_memory.end_session(req.session_id, req.user_id)
    return {
        "session_id": summary.session_id,
        "topics": summary.topics,
        "key_decisions": summary.key_decisions,
        "mood": summary.mood,
        "pain_reported": summary.pain_reported,
        "goals_mentioned": summary.goals_mentioned,
        "summary": summary.summary,
        "turn_count": summary.turn_count,
    }


@router.get("/context/{user_id}")
async def get_memory_context(user_id: str, max_tokens: int = 600):
    context = conversational_memory.get_context_for_llm(user_id, max_tokens)
    return {"user_id": user_id, "context": context, "token_estimate": len(context) // 4}


@router.get("/preferences/{user_id}")
async def get_preferences(user_id: str):
    prefs = conversational_memory.get_all_preferences(user_id)
    return {"user_id": user_id, "preferences": prefs}


@router.get("/topics/{user_id}")
async def get_recent_topics(user_id: str):
    topics = conversational_memory.get_last_topics(user_id)
    count = conversational_memory.get_conversation_count(user_id)
    return {"user_id": user_id, "recent_topics": topics, "total_sessions": count}


@router.get("/status")
async def get_memory_status():
    return conversational_memory.get_status()

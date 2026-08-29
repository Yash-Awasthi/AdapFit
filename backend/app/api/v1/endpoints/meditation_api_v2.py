"""Mindfulness & Meditation API — Guided sessions, sound healing, ambient sounds"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.meditation import meditation_service

router = APIRouter()


class StartSessionRequest(BaseModel):
    session_id: str
    user_id: str = "default"


class CompleteSessionRequest(BaseModel):
    session_id: str
    mood_before: int = 5
    mood_after: int = 5


@router.get("/sessions")
async def get_sessions(category: str = "", difficulty: str = "", duration_max: int = 0):
    return {"sessions": meditation_service.get_sessions(category, difficulty, duration_max)}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    session = meditation_service.get_session(session_id)
    if not session:
        return {"error": "Session not found"}
    return {"session": session}


@router.get("/categories")
async def get_categories():
    return {"categories": meditation_service.get_categories()}


@router.post("/session/start")
async def start_session(request: StartSessionRequest):
    return meditation_service.start_session(request.session_id, request.user_id)


@router.post("/session/complete")
async def complete_session(request: CompleteSessionRequest):
    return meditation_service.complete_session(request.session_id, request.mood_before, request.mood_after)


@router.get("/stats")
async def get_stats():
    return meditation_service.get_stats()


@router.get("/ambient-sounds")
async def get_ambient_sounds(category: str = ""):
    return {"sounds": meditation_service.get_ambient_sounds(category)}


@router.get("/recommendations")
async def get_recommendations(mood: str = "neutral"):
    return {"recommendations": meditation_service.get_recommendations(mood)}


@router.get("/history")
async def get_history(limit: int = 10):
    return {"history": meditation_service.get_session_history(limit)}

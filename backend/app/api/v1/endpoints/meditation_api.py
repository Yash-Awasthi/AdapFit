"""Meditation API — guided meditation sessions and recommendations."""

from __future__ import annotations
from fastapi import APIRouter, Query
from app.services.meditation import meditation_service

router = APIRouter()


@router.get("")
async def list_sessions(category: str = "", duration_max: int = 60, difficulty: str = ""):
    return {"sessions": meditation_service.get_sessions(category, difficulty, duration_max)}


@router.get("/{session_id}")
async def get_session_detail(session_id: str):
    s = meditation_service.get_session(session_id)
    if not s:
        return {"error": "Session not found"}
    return s


@router.get("/recommend/quick")
async def recommend(
    stress_level: int = Query(5, ge=1, le=10),
    time_available: int = Query(10, ge=1, le=60),
    time_of_day: str = Query("anytime"),
):
    mood = "stressed" if stress_level > 7 else "anxious" if stress_level > 5 else "neutral"
    return meditation_service.get_recommendations(mood)

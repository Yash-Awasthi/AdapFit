"""Meditation API — guided meditation sessions and recommendations."""

from __future__ import annotations
from fastapi import APIRouter, Query
from app.services.meditation import get_sessions, get_session, recommend_session

router = APIRouter()


@router.get("")
async def list_sessions(category: str = "", duration_max: int = 60, difficulty: str = ""):
    return {"sessions": get_sessions(category, duration_max, difficulty)}


@router.get("/{session_id}")
async def get_session_detail(session_id: str):
    s = get_session(session_id)
    if not s:
        return {"error": "Session not found"}
    return s


@router.get("/recommend/quick")
async def recommend(
    stress_level: int = Query(5, ge=1, le=10),
    time_available: int = Query(10, ge=1, le=60),
    time_of_day: str = Query("anytime"),
):
    return recommend_session(stress_level, time_available, time_of_day)

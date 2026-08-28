"""Breathing exercise endpoints — guided breathing patterns."""

from fastapi import APIRouter, Query
from typing import Optional
from app.services.breathing import get_exercises, get_exercise_detail

router = APIRouter()


@router.get("")
async def list_breathing_exercises(category: Optional[str] = Query(None)):
    """List breathing exercises, optionally by category."""
    return {"exercises": get_exercises(category)}


@router.get("/{exercise_id}")
async def get_breathing_exercise(exercise_id: str):
    """Get full details of a breathing exercise with phase instructions."""
    detail = get_exercise_detail(exercise_id)
    if not detail:
        return {"error": "Exercise not found"}
    return detail

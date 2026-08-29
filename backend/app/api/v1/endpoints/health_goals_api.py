"""Health Goals & Streaks API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.health_goals import health_goals_service

router = APIRouter()

class GoalCreateRequest(BaseModel):
    category: str
    title: str
    target: float
    unit: str
    frequency: str = "daily"

class GoalUpdateRequest(BaseModel):
    goal_id: str
    value: float

@router.post("/create")
async def create_goal(request: GoalCreateRequest):
    """Create a new health goal."""
    return health_goals_service.create_goal(request.category, request.title, request.target, request.unit, request.frequency)

@router.post("/update")
async def update_goal(request: GoalUpdateRequest):
    """Update goal progress."""
    return health_goals_service.update_goal_progress(request.goal_id, request.value)

@router.get("/checklist")
async def get_checklist():
    """Get daily habit checklist."""
    return health_goals_service.get_daily_checklist()

@router.post("/habit/{habit_id}")
async def complete_habit(habit_id: str):
    """Mark a habit as completed."""
    return health_goals_service.complete_habit(habit_id)

@router.get("/stats")
async def get_stats():
    """Get gamification stats (XP, level, streaks)."""
    return health_goals_service.get_gamification_stats()

@router.get("/achievements")
async def get_achievements():
    """Get all achievements."""
    return {"achievements": health_goals_service.get_achievements()}

@router.get("/summary")
async def get_progress_summary():
    """Get overall progress summary."""
    return health_goals_service.get_progress_summary()

"""Gamification API — XP, badges, streaks, leaderboard"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.gamification import gamification_service

router = APIRouter()


class AddXPRequest(BaseModel):
    user_id: str
    amount: int
    reason: str = ""


class BadgeRequest(BaseModel):
    user_id: str
    badge_id: str


class StreakRequest(BaseModel):
    user_id: str
    activity_type: str = "workout"


@router.get("/level/{user_id}")
async def get_user_level(user_id: str):
    return gamification_service.get_user_level(user_id)


@router.post("/xp")
async def add_xp(request: AddXPRequest):
    return gamification_service.add_xp(request.user_id, request.amount, request.reason)


@router.get("/badges/{user_id}")
async def get_user_badges(user_id: str):
    return gamification_service.get_user_badges(user_id)


@router.post("/badges/award")
async def award_badge(request: BadgeRequest):
    return gamification_service.award_badge(request.user_id, request.badge_id)


@router.post("/streak")
async def update_streak(request: StreakRequest):
    return gamification_service.update_streak(request.user_id, request.activity_type)


@router.get("/leaderboard")
async def get_leaderboard(limit: int = 20):
    return {"leaderboard": gamification_service.get_leaderboard(limit)}


@router.get("/achievements")
async def get_achievements(user_id: Optional[str] = None, limit: int = 20):
    return {"achievements": gamification_service.get_achievements_log(user_id, limit)}


@router.get("/all-badges")
async def get_all_badges():
    from app.services.gamification import BADGES
    return {"badges": BADGES, "total": len(BADGES)}

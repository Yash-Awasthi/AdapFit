"""
Health Wellness Hub API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/wellness-hub", tags=["Unified Wellness Hub"])


class LogWellnessRequest(BaseModel):
    user_id: str
    dimension: str
    metric: str
    value: float
    notes: str = ""


class CompleteChallengeRequest(BaseModel):
    user_id: str
    challenge_id: str


@router.post("/log")
async def log_wellness(req: LogWellnessRequest):
    from app.services.health_wellness_hub import wellness_hub
    return wellness_hub.log_wellness(req.user_id, req.dimension, req.metric, req.value, req.notes)


@router.get("/score/{user_id}")
async def get_wellness_score(user_id: str):
    from app.services.health_wellness_hub import wellness_hub
    return wellness_hub.get_wellness_score(user_id)


@router.post("/challenge/complete")
async def complete_challenge(req: CompleteChallengeRequest):
    from app.services.health_wellness_hub import wellness_hub
    return wellness_hub.complete_challenge(req.user_id, req.challenge_id)


@router.get("/challenges/{user_id}")
async def get_daily_challenges(user_id: str, count: int = 5):
    from app.services.health_wellness_hub import wellness_hub
    return wellness_hub.get_daily_challenges(user_id, count)


@router.get("/history/{user_id}")
async def get_history(user_id: str, days: int = 30):
    from app.services.health_wellness_hub import wellness_hub
    return wellness_hub.get_wellness_history(user_id, days)


@router.get("/dimensions")
async def get_dimensions():
    from app.services.health_wellness_hub import wellness_hub
    return wellness_hub.WELLNESS_DIMENSIONS


@router.get("/weekly-theme/{week_number}")
async def get_weekly_theme(week_number: int):
    from app.services.health_wellness_hub import wellness_hub
    return wellness_hub.WEEKLY_THEMES.get(week_number % 8 + 1, "Custom Week")


@router.get("/challenges/all")
async def get_all_challenges():
    from app.services.health_wellness_hub import wellness_hub
    return wellness_hub.DAILY_CHALLENGES

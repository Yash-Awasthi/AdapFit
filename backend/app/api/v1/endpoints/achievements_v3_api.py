"""
Fitness Achievements & Gamification API — badges, streaks, points system.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field

router = APIRouter()


# --- Response Models ---

class AchievementSummary(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    progress: int | None = None
    target: int | None = None
    unlocked: bool = False


class AchievementGrantResult(BaseModel):
    granted: bool
    achievement_id: str | None = None
    reason: str | None = None


class AchievementCheckResult(BaseModel):
    newly_granted: int
    achievements: list[dict[str, str]]


class ProgressResponse(BaseModel):
    user_id: str
    total_achievements: int
    unlocked_count: int
    points: int
    streak: int


# --- Input Validation ---

class AchievementCheckRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    event_type: str = Field(min_length=1, max_length=64, pattern=r"^[a-z_]+$")
    context: dict[str, Any] = Field(default_factory=dict, max_length=50)


class AchievementGrantRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    achievement_id: str = Field(min_length=1, max_length=64)
    context: dict[str, Any] = Field(default_factory=dict, max_length=50)


# --- Cached singleton ---

@lru_cache(maxsize=1)
def _get_engine():
    from src.achievements.engine import AchievementEngine
    return AchievementEngine()


# --- Routes ---

@router.get(
    "/list",
    response_model=list[AchievementSummary],
    summary="List all available achievements",
)
async def list_achievements() -> list[AchievementSummary]:
    engine = _get_engine()
    return engine.list_all()


@router.get(
    "/progress/{user_id}",
    response_model=ProgressResponse,
    summary="Get achievement progress for a user",
)
async def get_progress(
    user_id: str = Path(min_length=1, max_length=128),
) -> ProgressResponse:
    engine = _get_engine()
    return engine.get_progress(user_id)


@router.get(
    "/user/{user_id}",
    response_model=list[AchievementSummary],
    summary="Get all earned achievements for a user",
)
async def get_user_achievements(
    user_id: str = Path(min_length=1, max_length=128),
) -> list[AchievementSummary]:
    engine = _get_engine()
    return engine.get_user_achievements(user_id)


@router.post(
    "/check",
    response_model=AchievementCheckResult,
    summary="Check and grant achievements based on an event",
)
async def check_achievements(req: AchievementCheckRequest) -> AchievementCheckResult:
    engine = _get_engine()
    granted = engine.check_and_grant(req.user_id, req.event_type, req.context)
    return AchievementCheckResult(
        newly_granted=len(granted),
        achievements=[
            {"id": a.achievement_id, "granted_at": a.granted_at.isoformat()}
            for a in granted
        ],
    )


@router.post(
    "/grant",
    response_model=AchievementGrantResult,
    summary="Manually grant an achievement",
)
async def grant_achievement(req: AchievementGrantRequest) -> AchievementGrantResult:
    engine = _get_engine()
    result = engine.force_grant(req.user_id, req.achievement_id, req.context)
    if result:
        return AchievementGrantResult(
            granted=True, achievement_id=result.achievement_id
        )
    return AchievementGrantResult(
        granted=False, reason="Already earned or invalid achievement"
    )

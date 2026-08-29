"""
Health Community V2 API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/community-v2", tags=["Health Community V2"])


class CreateChallengeRequest(BaseModel):
    creator_id: str
    challenge_type: str
    title: str
    description: str
    duration_days: int = 7
    max_participants: int = 50


class JoinChallengeRequest(BaseModel):
    user_id: str
    challenge_id: str


class LogProgressRequest(BaseModel):
    user_id: str
    challenge_id: str
    value: float


class CreatePostRequest(BaseModel):
    user_id: str
    content: str
    post_type: str = "update"
    tags: List[str] = []


class AwardBadgeRequest(BaseModel):
    user_id: str
    badge_id: str


@router.post("/challenge/create")
async def create_challenge(req: CreateChallengeRequest):
    from app.services.health_community_v2 import health_community_v2
    return health_community_v2.create_challenge(req.creator_id, req.challenge_type, req.title, req.description, req.duration_days, req.max_participants)


@router.post("/challenge/join")
async def join_challenge(req: JoinChallengeRequest):
    from app.services.health_community_v2 import health_community_v2
    return health_community_v2.join_challenge(req.user_id, req.challenge_id)


@router.post("/challenge/progress")
async def log_progress(req: LogProgressRequest):
    from app.services.health_community_v2 import health_community_v2
    return health_community_v2.log_progress(req.user_id, req.challenge_id, req.value)


@router.get("/challenge/{challenge_id}/leaderboard")
async def get_leaderboard(challenge_id: str):
    from app.services.health_community_v2 import health_community_v2
    return health_community_v2.get_leaderboard(challenge_id)


@router.get("/challenges/{user_id}")
async def get_user_challenges(user_id: str):
    from app.services.health_community_v2 import health_community_v2
    return health_community_v2.get_user_challenges(user_id)


@router.post("/post")
async def create_post(req: CreatePostRequest):
    from app.services.health_community_v2 import health_community_v2
    return health_community_v2.create_post(req.user_id, req.content, req.post_type, req.tags)


@router.post("/post/like/{post_id}")
async def like_post(post_id: str):
    from app.services.health_community_v2 import health_community_v2
    return health_community_v2.like_post(post_id)


@router.get("/feed")
async def get_feed(limit: int = 20):
    from app.services.health_community_v2 import health_community_v2
    return health_community_v2.get_community_feed(limit)


@router.post("/achievement")
async def award_achievement(req: AwardBadgeRequest):
    from app.services.health_community_v2 import health_community_v2
    return health_community_v2.award_achievement(req.user_id, req.badge_id)


@router.get("/stats/{user_id}")
async def get_user_stats(user_id: str):
    from app.services.health_community_v2 import health_community_v2
    return health_community_v2.get_user_stats(user_id)


@router.get("/badges")
async def get_badges():
    from app.services.health_community_v2 import health_community_v2
    return health_community_v2.ACHIEVEMENT_BADGES


@router.get("/challenge-types")
async def get_challenge_types():
    from app.services.health_community_v2 import health_community_v2
    return health_community_v2.CHALLENGE_TYPES

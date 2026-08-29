"""Social Sharing & Viral Challenges API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.social_sharing import social_sharing_service

router = APIRouter()


class JoinChallengeRequest(BaseModel):
    user_id: str
    challenge_id: str


class ShareCardRequest(BaseModel):
    user_id: str
    card_type: str
    data: dict = {}


class TransformationRequest(BaseModel):
    user_id: str
    before: dict = {}
    after: dict = {}
    summary: str = ""


@router.get("/challenges")
async def get_challenges(type: str = "", trending: bool = False):
    return {"challenges": social_sharing_service.get_challenges(type, trending)}


@router.post("/challenges/join")
async def join_challenge(request: JoinChallengeRequest):
    return social_sharing_service.join_challenge(request.user_id, request.challenge_id)


@router.post("/challenges/log/{challenge_id}")
async def log_challenge_day(challenge_id: str, user_id: str = "default"):
    return social_sharing_service.log_challenge_day(user_id, challenge_id)


@router.get("/challenges/user/{user_id}")
async def get_user_challenges(user_id: str):
    return {"challenges": social_sharing_service.get_user_challenges(user_id)}


@router.post("/share-card")
async def generate_share_card(request: ShareCardRequest):
    return social_sharing_service.generate_share_card(request.user_id, request.card_type, request.data)


@router.get("/share-cards/{user_id}")
async def get_share_cards(user_id: str):
    return {"cards": social_sharing_service.get_share_cards(user_id)}


@router.post("/transformation")
async def create_transformation(request: TransformationRequest):
    return social_sharing_service.create_transformation_story(request.user_id, request.before, request.after, request.summary)


@router.get("/trending")
async def get_trending(limit: int = 5):
    return {"trending": social_sharing_service.get_trending_challenges(limit)}

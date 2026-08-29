"""Community & Social Challenges API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.community import community_service

router = APIRouter()

class ChallengeCreateRequest(BaseModel):
    title: str
    description: str
    challenge_type: str = "steps"
    target: float = 10000
    unit: str = "steps"
    duration_days: int = 7

@router.get("/challenges")
async def get_active_challenges():
    return {"challenges": community_service.get_active_challenges()}

@router.get("/challenges/{challenge_id}/leaderboard")
async def get_leaderboard(challenge_id: str):
    return community_service.get_leaderboard(challenge_id)

@router.post("/challenges/join/{challenge_id}")
async def join_challenge(challenge_id: str):
    return community_service.join_challenge(challenge_id)

@router.post("/challenges/create")
async def create_challenge(request: ChallengeCreateRequest):
    return community_service.create_challenge(
        request.title, request.description, request.challenge_type,
        request.target, request.unit, request.duration_days,
    )

@router.get("/feed")
async def get_feed(limit: int = 20):
    return {"feed": community_service.get_community_feed(limit)}

@router.get("/teams")
async def get_teams():
    return {"teams": community_service.get_team_standings()}

@router.get("/challenge-types")
async def get_challenge_types():
    return {"types": community_service.get_challenge_types()}

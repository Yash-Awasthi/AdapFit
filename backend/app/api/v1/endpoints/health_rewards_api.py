"""Health Rewards API"""
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.health_rewards import health_rewards_service

router = APIRouter()

class AwardXPRequest(BaseModel):
    action: str; multiplier: float = 1.0

class PurchaseRequest(BaseModel):
    reward_id: str

@router.post("/award")
async def award_xp(request: AwardXPRequest):
    return health_rewards_service.award_xp(request.action, request.multiplier)

@router.get("/status")
async def get_status():
    return health_rewards_service.get_status()

@router.get("/catalog")
async def get_catalog():
    return {"rewards": health_rewards_service.get_rewards_catalog()}

@router.post("/purchase")
async def purchase(request: PurchaseRequest):
    return health_rewards_service.purchase_reward(request.reward_id)

@router.get("/leaderboard")
async def get_leaderboard():
    return health_rewards_service.get_leaderboard_position()

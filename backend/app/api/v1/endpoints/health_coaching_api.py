"""Health Coaching API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.health_coaching import health_coaching_service

router = APIRouter(prefix="/health-coaching", tags=["Health Coaching Platform"])

class MatchRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]

class BookRequest(BaseModel):
    user_id: str
    coach_id: str
    slot: str

class MessageRequest(BaseModel):
    user_id: str
    coach_id: str
    message: str

@router.get("/coaches")
async def find_coaches(specialty: str = "", max_price: int = 0):
    return {"success": True, "data": health_coaching_service.find_coach(specialty, max_price)}

@router.post("/match")
async def match_coach(req: MatchRequest):
    return {"success": True, "data": health_coaching_service.match_coach(req.user_id, req.data)}

@router.post("/book")
async def book_session(req: BookRequest):
    return {"success": True, "data": health_coaching_service.book_session(req.user_id, req.coach_id, req.slot)}

@router.get("/sessions/{user_id}")
async def get_sessions(user_id: str):
    return {"success": True, "data": health_coaching_service.get_my_sessions(user_id)}

@router.get("/progress/{user_id}")
async def get_progress(user_id: str):
    return {"success": True, "data": health_coaching_service.get_progress(user_id)}

@router.post("/message")
async def message_coach(req: MessageRequest):
    return {"success": True, "data": health_coaching_service.message_coach(req.user_id, req.coach_id, req.message)}

@router.get("/specialties")
async def get_specialties():
    return {"success": True, "data": health_coaching_service.get_specialties()}

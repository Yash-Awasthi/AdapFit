"""Peer Support API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.peer_support import peer_support_service

router = APIRouter(prefix="/peer-support", tags=["Peer Support & Accountability"])

class ProfileRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]

class CheckInRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]

class CircleRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]

@router.post("/profile")
async def create_profile(req: ProfileRequest):
    return {"success": True, "data": peer_support_service.create_profile(req.user_id, req.data)}

@router.get("/find-peer/{user_id}")
async def find_peer(user_id: str):
    return {"success": True, "data": peer_support_service.find_peer(user_id)}

@router.post("/check-in")
async def check_in(req: CheckInRequest):
    return {"success": True, "data": peer_support_service.check_in(req.user_id, req.data)}

@router.post("/circle")
async def create_circle(req: CircleRequest):
    return {"success": True, "data": peer_support_service.create_circle(req.user_id, req.data)}

@router.post("/circle/{circle_id}/join")
async def join_circle(user_id: str, circle_id: str):
    return {"success": True, "data": peer_support_service.join_circle(user_id, circle_id)}

@router.post("/crisis")
async def escalate_crisis(user_id: str):
    return {"success": True, "data": peer_support_service.escalate_crisis(user_id, {})}

@router.get("/messages/{user_id}")
async def get_messages(user_id: str):
    return {"success": True, "data": peer_support_service.get_partner_messages(user_id)}

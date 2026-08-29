"""Gym Integration API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.gym_integration import gym_integration_service

router = APIRouter(prefix="/gym", tags=["Gym & Fitness Integration"])

@router.get("/search")
async def search_gyms(type: str = "", max_price: int = 0, amenity: str = ""):
    return {"success": True, "data": gym_integration_service.search_gyms(type, max_price, amenity)}

@router.get("/classes")
async def get_classes(gym: str = "", type: str = "", available_only: bool = True):
    return {"success": True, "data": gym_integration_service.get_classes(gym, type, available_only)}

@router.post("/book/{class_id}")
async def book_class(user_id: str, class_id: str):
    return {"success": True, "data": gym_integration_service.book_class(user_id, class_id)}

@router.post("/checkin/{gym_id}")
async def check_in(user_id: str, gym_id: str):
    return {"success": True, "data": gym_integration_service.check_in(user_id, gym_id)}

@router.get("/classpass/{user_id}")
async def get_credits(user_id: str):
    return {"success": True, "data": gym_integration_service.get_classpass_credits(user_id)}

@router.get("/bookings/{user_id}")
async def get_bookings(user_id: str):
    return {"success": True, "data": gym_integration_service.get_my_bookings(user_id)}

"""Fall prevention: STEADI check, home safety and balance exercises."""
from typing import Dict

from fastapi import APIRouter

from app.services.senior_health import BALANCE_EXERCISES, HOME_SAFETY, STEADI, senior_health_service

router = APIRouter()


@router.get("/fall-check")
async def fall_check_questions():
    return [{"id": k, "question": q, "points": p} for k, q, p in STEADI]


@router.post("/fall-check")
async def fall_check(answers: Dict[str, bool]):
    return senior_health_service.fall_check(answers)


@router.get("/home-safety")
async def home_safety():
    return HOME_SAFETY


@router.get("/balance-exercises")
async def balance_exercises():
    return BALANCE_EXERCISES

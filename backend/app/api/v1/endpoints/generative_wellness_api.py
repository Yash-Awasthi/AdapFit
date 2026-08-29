"""
Generative AI Wellness Plan API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/wellness", tags=["AI Wellness Planning"])


class GeneratePlanRequest(BaseModel):
    user_id: str
    goals: List[str]
    fitness_level: str
    health_conditions: List[str] = []
    preferences: dict = {}


class AdjustPlanRequest(BaseModel):
    user_id: str
    plan_id: str
    feedback: str
    completion_rate: float


class WeeklyAdjustmentRequest(BaseModel):
    user_id: str
    plan_id: str
    week_data: dict


@router.post("/plan/generate")
async def generate_wellness_plan(req: GeneratePlanRequest):
    from app.services.generative_wellness import generative_wellness_service
    return generative_wellness_service.generate_plan(req.user_id, req.goals, req.fitness_level, req.health_conditions, req.preferences)


@router.post("/plan/adjust")
async def adjust_plan(req: AdjustPlanRequest):
    from app.services.generative_wellness import generative_wellness_service
    return generative_wellness_service.adjust_plan(req.plan_id, req.feedback, req.completion_rate)


@router.post("/plan/weekly-adjustment")
async def weekly_adjustment(req: WeeklyAdjustmentRequest):
    from app.services.generative_wellness import generative_wellness_service
    return generative_wellness_service.weekly_adjustment(req.plan_id, req.week_data)


@router.get("/plan/{user_id}")
async def get_active_plan(user_id: str):
    from app.services.generative_wellness import generative_wellness_service
    return generative_wellness_service.get_active_plan(user_id)


@router.get("/plans/{user_id}")
async def get_plan_history(user_id: str):
    from app.services.generative_wellness import generative_wellness_service
    return generative_wellness_service.get_plan_history(user_id)


@router.get("/goals")
async def get_available_goals():
    from app.services.generative_wellness import generative_wellness_service
    return generative_wellness_service.GOAL_CATEGORIES


@router.get("/progress/{plan_id}")
async def get_progress(plan_id: str):
    from app.services.generative_wellness import generative_wellness_service
    return generative_wellness_service.get_progress_summary(plan_id)

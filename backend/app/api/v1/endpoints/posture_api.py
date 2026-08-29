"""AI Posture Analysis & Ergonomics API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.posture_analysis import posture_analysis_service

router = APIRouter()


class PostureAnalysisRequest(BaseModel):
    body_landmarks: dict = {}


@router.post("/analyze")
async def analyze_posture(request: PostureAnalysisRequest = PostureAnalysisRequest()):
    return posture_analysis_service.analyze_posture(request.body_landmarks)


@router.get("/ergonomic-tips")
async def get_ergonomic_tips():
    return {"tips": posture_analysis_service.get_ergonomic_tips()}


@router.get("/exercises")
async def get_corrective_exercises(issue: str = ""):
    return {"exercises": posture_analysis_service.get_corrective_exercises(issue)}


@router.get("/score-history")
async def get_score_history(days: int = 7):
    return {"history": posture_analysis_service.get_score_history(days)}


@router.get("/improvement-plan")
async def get_improvement_plan():
    return posture_analysis_service.get_posture_improvement_plan()


@router.post("/monitor/start")
async def start_monitoring(user_id: str = "default"):
    return posture_analysis_service.start_monitoring_session(user_id)


@router.post("/monitor/check")
async def check_posture(user_id: str = "default", current_posture: str = "good"):
    return posture_analysis_service.check_and_alert(user_id, current_posture)

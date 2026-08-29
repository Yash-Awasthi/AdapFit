"""AI Health Coach API"""
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.ai_coach import ai_coach_service

router = APIRouter()

class QuestionRequest(BaseModel):
    question: str

class FeedbackRequest(BaseModel):
    insight_id: str; helpful: bool; comment: str = ""

@router.get("/daily-insight")
async def get_daily_insight():
    return ai_coach_service.get_daily_insight()

@router.get("/weekly-report")
async def get_weekly_report():
    return ai_coach_service.get_weekly_report()

@router.post("/ask")
async def ask_question(request: QuestionRequest):
    return ai_coach_service.ask_question(request.question)

@router.get("/recommendations")
async def get_recommendations():
    return {"recommendations": ai_coach_service.get_recommendations()}

@router.get("/health-risks")
async def get_health_risks():
    return {"risks": ai_coach_service.get_health_risks()}

@router.get("/motivation")
async def get_motivation():
    return ai_coach_service.get_motivation()

@router.post("/feedback")
async def log_feedback(request: FeedbackRequest):
    return ai_coach_service.log_feedback(request.insight_id, request.helpful, request.comment)

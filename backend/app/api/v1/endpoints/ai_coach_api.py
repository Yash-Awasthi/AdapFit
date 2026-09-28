"""Coach briefing and weekly report. Questions go to /chat, which has the safety layer."""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.per_user import current_user_id
from app.services import ai_coach

router = APIRouter()


class FeedbackRequest(BaseModel):
    category: str = Field(min_length=1, max_length=40)
    helpful: bool
    comment: str = Field("", max_length=500)


@router.get("/briefing")
async def get_briefing():
    return await ai_coach.briefing(current_user_id())


@router.get("/weekly-report")
async def get_weekly_report():
    return await ai_coach.weekly_report(current_user_id())


@router.post("/feedback")
async def log_feedback(req: FeedbackRequest):
    return ai_coach.log_feedback(current_user_id(), req.category, req.helpful, req.comment)

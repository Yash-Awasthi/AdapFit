"""
Health Chat Moderation API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/moderation", tags=["Content Moderation"])


class ModerateRequest(BaseModel):
    content: str
    user_id: str


class ReportRequest(BaseModel):
    reporter_id: str
    content_id: str
    reason: str
    details: str = ""


@router.post("/check")
async def moderate_content(req: ModerateRequest):
    from app.services.health_chat_moderation import chat_moderation
    return chat_moderation.moderate_content(req.content, req.user_id)


@router.post("/report")
async def report_content(req: ReportRequest):
    from app.services.health_chat_moderation import chat_moderation
    return chat_moderation.report_content(req.reporter_id, req.content_id, req.reason, req.details)


@router.get("/flagged")
async def get_flagged(limit: int = 50):
    from app.services.health_chat_moderation import chat_moderation
    return chat_moderation.get_flagged_content(limit)


@router.get("/helplines/{country}")
async def get_helplines(country: str = "us"):
    from app.services.health_chat_moderation import chat_moderation
    return chat_moderation.get_helplines(country)

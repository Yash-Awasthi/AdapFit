"""Notifications API — Push notification management"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.notification_service import notification_service

router = APIRouter()


class SendNotificationRequest(BaseModel):
    user_id: str
    title: str
    body: str
    category: str = "general"
    data: dict = {}


class TemplateRequest(BaseModel):
    user_id: str
    template_key: str
    kwargs: dict = {}


class PreferencesUpdate(BaseModel):
    medication_reminders: Optional[bool] = None
    challenge_updates: Optional[bool] = None
    weekly_reports: Optional[bool] = None
    coaching_insights: Optional[bool] = None
    hydration_reminders: Optional[bool] = None
    sleep_reminders: Optional[bool] = None
    workout_reminders: Optional[bool] = None
    emergency_alerts: Optional[bool] = None
    quiet_hours_start: Optional[int] = None
    quiet_hours_end: Optional[int] = None


class ScheduleRequest(BaseModel):
    user_id: str
    title: str
    body: str
    category: str = "general"
    scheduled_at: float


@router.post("/send")
async def send_notification(request: SendNotificationRequest):
    return notification_service.send_notification(
        request.user_id, request.title, request.body,
        request.category, request.data,
    )


@router.post("/send-template")
async def send_from_template(request: TemplateRequest):
    return notification_service.send_from_template(
        request.user_id, request.template_key, **request.kwargs,
    )


@router.get("/list/{user_id}")
async def get_notifications(user_id: str, limit: int = 20, unread_only: bool = False):
    return {"notifications": notification_service.get_notifications(user_id, limit, unread_only)}


@router.post("/read/{notification_id}")
async def mark_read(notification_id: str, user_id: str = "default"):
    return notification_service.mark_read(user_id, notification_id)


@router.post("/read-all/{user_id}")
async def mark_all_read(user_id: str):
    return notification_service.mark_all_read(user_id)


@router.get("/unread/{user_id}")
async def get_unread_count(user_id: str):
    return notification_service.get_unread_count(user_id)


@router.get("/preferences/{user_id}")
async def get_preferences(user_id: str):
    return notification_service.get_preferences(user_id)


@router.put("/preferences/{user_id}")
async def update_preferences(user_id: str, updates: PreferencesUpdate):
    return notification_service.update_preferences(user_id, updates.model_dump(exclude_none=True))


@router.post("/schedule")
async def schedule_notification(request: ScheduleRequest):
    return notification_service.schedule_notification(
        request.user_id, request.title, request.body,
        request.category, request.scheduled_at,
    )


@router.get("/scheduled/{user_id}")
async def get_scheduled(user_id: str):
    return {"scheduled": notification_service.get_scheduled(user_id)}


@router.get("/templates")
async def get_templates():
    return {"templates": notification_service.get_templates()}


@router.get("/stats/{user_id}")
async def get_delivery_stats(user_id: str):
    return notification_service.get_delivery_stats(user_id)

"""Family & Caregiver Mode API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.family_mode import family_mode_service

router = APIRouter()


class CreateGroupRequest(BaseModel):
    owner_id: str
    group_name: str = "My Family"


class AddMemberRequest(BaseModel):
    name: str
    relationship: str
    age: int
    user_id: str = ""


class AlertRequest(BaseModel):
    from_member: str
    alert_type: str
    message: str


class ShareDataRequest(BaseModel):
    member_id: str
    data_type: str
    data: dict = {}


@router.post("/group")
async def create_group(request: CreateGroupRequest):
    return family_mode_service.create_group(request.owner_id, request.group_name)


@router.get("/group/{group_id}/members")
async def get_members(group_id: str):
    return {"members": family_mode_service.get_members(group_id)}


@router.post("/group/{group_id}/member")
async def add_member(group_id: str, request: AddMemberRequest):
    return family_mode_service.add_member(group_id, request.name, request.relationship, request.age, request.user_id)


@router.post("/group/{group_id}/alert")
async def send_alert(group_id: str, request: AlertRequest):
    return family_mode_service.send_family_alert(group_id, request.from_member, request.alert_type, request.message)


@router.get("/group/{group_id}/alerts")
async def get_alerts(group_id: str, unread_only: bool = False):
    return {"alerts": family_mode_service.get_alerts(group_id, unread_only)}


@router.post("/group/{group_id}/share")
async def share_data(group_id: str, request: ShareDataRequest):
    return family_mode_service.share_health_data(group_id, request.member_id, request.data_type, request.data)


@router.get("/group/{group_id}/dashboard")
async def caregiver_dashboard(group_id: str):
    return family_mode_service.get_caregiver_dashboard(group_id)


@router.get("/group/{group_id}/elderly/{member_id}")
async def elderly_monitoring(group_id: str, member_id: str):
    return family_mode_service.get_elderly_monitoring(group_id, member_id)


@router.get("/group/{group_id}/child/{member_id}")
async def child_health(group_id: str, member_id: str):
    return family_mode_service.get_child_health(group_id, member_id)

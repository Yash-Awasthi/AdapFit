"""Chronic Pain Management API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from app.services.chronic_pain import chronic_pain_service

router = APIRouter(prefix="/chronic-pain", tags=["Chronic Pain Management"])


class ProfileRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]


class PainLogRequest(BaseModel):
    user_id: str
    data: Dict[str, Any]


@router.post("/profile")
async def create_profile(req: ProfileRequest):
    result = chronic_pain_service.create_profile(req.user_id, req.data)
    return {"success": True, "data": result}


@router.post("/log")
async def log_pain(req: PainLogRequest):
    result = chronic_pain_service.log_pain(req.user_id, req.data)
    return {"success": True, "data": result}


@router.get("/triggers/{user_id}")
async def analyze_triggers(user_id: str):
    result = chronic_pain_service.analyze_triggers(user_id)
    return {"success": True, "data": result}


@router.get("/treatments/{user_id}")
async def get_treatment_effectiveness(user_id: str):
    result = chronic_pain_service.get_treatment_effectiveness(user_id)
    return {"success": True, "data": result}


@router.get("/flare-management")
async def get_flare_management():
    result = chronic_pain_service.get_flare_management()
    return {"success": True, "data": result}


@router.get("/cbt-techniques")
async def get_cbt_techniques():
    result = chronic_pain_service.get_cbt_techniques()
    return {"success": True, "data": result}


@router.get("/pain-scale")
async def get_pain_scale():
    return {"success": True, "data": chronic_pain_service.pain_scale}


@router.get("/conditions")
async def list_conditions():
    conditions = [{"id": k, "name": v["name"], "symptoms": v["common_symptoms"]} for k, v in chronic_pain_service.pain_conditions.items()]
    return {"success": True, "data": conditions}

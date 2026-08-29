"""Skin Health & Mole Tracking API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.skin_health import skin_health_service

router = APIRouter()


class SkinTypeRequest(BaseModel):
    skin_color: int = 3
    sun_reaction: int = 3
    tanning_ability: int = 3


class MoleRequest(BaseModel):
    name: str
    body_location: str
    size_mm: float
    color: str = "brown"
    notes: str = ""


class UVRequest(BaseModel):
    uv_index: int = 5
    duration_minutes: int = 30
    protection_used: str = "none"


@router.post("/skin-type")
async def assess_skin_type(request: SkinTypeRequest):
    return skin_health_service.assess_skin_type(request.model_dump())


@router.post("/mole")
async def add_mole(request: MoleRequest):
    return skin_health_service.add_mole(request.name, request.body_location, request.size_mm, request.color, request.notes)


@router.get("/moles")
async def get_moles():
    return {"moles": skin_health_service.get_all_moles()}


@router.get("/mole/{mole_id}")
async def get_mole(mole_id: str):
    mole = skin_health_service.get_mole(mole_id)
    if not mole:
        return {"error": "Mole not found"}
    return {"mole": mole}


@router.post("/mole/{mole_id}/analyze")
async def analyze_mole(mole_id: str):
    return skin_health_service.analyze_mole_photo(mole_id)


@router.post("/uv")
async def log_uv(request: UVRequest):
    return skin_health_service.log_uv_exposure(request.uv_index, request.duration_minutes, request.protection_used)


@router.get("/uv-history")
async def get_uv_history(days: int = 7):
    return {"history": skin_health_service.get_uv_history(days)}


@router.get("/cancer-risk")
async def get_cancer_risk():
    return skin_health_service.get_skin_cancer_risk()


@router.get("/dermatology-report")
async def get_report():
    return skin_health_service.get_dermatology_report()

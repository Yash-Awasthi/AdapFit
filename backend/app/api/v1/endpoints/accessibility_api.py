"""
Health Accessibility API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Optional

router = APIRouter(prefix="/accessibility", tags=["Health Accessibility"])


class SetPreferencesRequest(BaseModel):
    user_id: str
    preferences: dict


@router.post("/preferences")
async def set_preferences(req: SetPreferencesRequest):
    from app.services.health_accessibility import health_accessibility
    return health_accessibility.set_preferences(req.user_id, req.preferences)


@router.get("/preferences/{user_id}")
async def get_preferences(user_id: str):
    from app.services.health_accessibility import health_accessibility
    return health_accessibility.get_preferences(user_id)


@router.get("/audit/{screen}")
async def run_audit(screen: str):
    from app.services.health_accessibility import health_accessibility
    return health_accessibility.run_accessibility_audit(screen)


@router.get("/features")
async def get_features():
    from app.services.health_accessibility import health_accessibility
    return health_accessibility.ACCESSIBILITY_FEATURES


@router.get("/voice-commands")
async def get_voice_commands():
    from app.services.health_accessibility import health_accessibility
    return health_accessibility.get_voice_commands()


@router.get("/color-blind-palettes")
async def get_color_blind_palettes():
    from app.services.health_accessibility import health_accessibility
    return health_accessibility.get_color_blind_palettes()

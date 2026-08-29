"""
Substance Use Disorder & MAT Tracking API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/substance-use", tags=["Substance Use & Recovery"])


class CreateRecoveryProfileRequest(BaseModel):
    user_id: str
    substance: str
    start_date: str
    mat_medication: Optional[str] = None


class LogCravingRequest(BaseModel):
    user_id: str
    intensity: int
    trigger: str
    location: str
    duration_min: int
    coping_strategy_used: Optional[str] = None


class LogMATDoseRequest(BaseModel):
    user_id: str
    medication: str
    dosage_mg: float
    taken_at: Optional[str] = None
    side_effects: List[str] = []


class JournalEntryRequest(BaseModel):
    user_id: str
    mood: int
    content: str
    gratitude: List[str] = []


class AddSupportContactRequest(BaseModel):
    user_id: str
    name: str
    relationship: str
    phone: str
    is_sponsor: bool = False


@router.post("/profile/create")
async def create_recovery_profile(req: CreateRecoveryProfileRequest):
    from app.services.substance_use import substance_use_service
    return substance_use_service.create_recovery_profile(req.user_id, req.substance, req.start_date, req.mat_medication)


@router.post("/craving/log")
async def log_craving(req: LogCravingRequest):
    from app.services.substance_use import substance_use_service
    return substance_use_service.log_craving(req.user_id, req.intensity, req.trigger, req.location, req.duration_min, req.coping_strategy_used)


@router.get("/craving/analytics/{user_id}")
async def get_craving_analytics(user_id: str):
    from app.services.substance_use import substance_use_service
    return substance_use_service.get_craving_analytics(user_id)


@router.get("/coping/{intensity}")
async def get_coping_strategies(intensity: int):
    from app.services.substance_use import substance_use_service
    return substance_use_service.get_coping_strategies(intensity)


@router.post("/mat/log")
async def log_mat_dose(req: LogMATDoseRequest):
    from app.services.substance_use import substance_use_service
    return substance_use_service.log_mat_dose(req.user_id, req.medication, req.dosage_mg, req.taken_at, req.side_effects)


@router.post("/journal")
async def add_journal(req: JournalEntryRequest):
    from app.services.substance_use import substance_use_service
    return substance_use_service.add_journal_entry(req.user_id, req.mood, req.content, req.gratitude)


@router.get("/sobriety/{user_id}")
async def get_sobriety_status(user_id: str):
    from app.services.substance_use import substance_use_service
    return substance_use_service.get_sobriety_status(user_id)


@router.post("/support/add")
async def add_support_contact(req: AddSupportContactRequest):
    from app.services.substance_use import substance_use_service
    return substance_use_service.add_support_contact(req.user_id, req.name, req.relationship, req.phone, req.is_sponsor)

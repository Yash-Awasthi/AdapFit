"""Circadian Rhythm Optimizer API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.circadian_rhythm import circadian_rhythm_service

router = APIRouter()


class ChronotypeRequest(BaseModel):
    wake_preference: int = 7
    energy_peak: int = 12
    sleep_preference: int = 23
    sleep_quality: int = 5


class LightExposureRequest(BaseModel):
    lux: int = 5000
    duration_minutes: int = 15
    time_of_day: str = ""


@router.post("/chronotype")
async def assess_chronotype(request: ChronotypeRequest):
    return circadian_rhythm_service.assess_chronotype(request.model_dump())


@router.get("/chronotype/{type}")
async def get_chronotype_info(type: str = ""):
    return circadian_rhythm_service.get_chronotype_info(type)


@router.post("/light-exposure")
async def log_light(request: LightExposureRequest):
    return circadian_rhythm_service.log_light_exposure(request.lux, request.duration_minutes, request.time_of_day)


@router.get("/schedule/{chronotype}")
async def get_daily_schedule(chronotype: str = "bear"):
    return circadian_rhythm_service.get_daily_schedule(chronotype)


@router.get("/energy/{chronotype}")
async def predict_energy(chronotype: str = "bear"):
    return {"energy_curve": circadian_rhythm_service.predict_energy_levels(chronotype)}


@router.post("/jet-lag")
async def get_jet_lag_plan(from_tz: int = 0, to_tz: int = 0):
    return circadian_rhythm_service.get_jet_lag_plan(from_tz, to_tz)


@router.get("/shift-work")
async def get_shift_work_tips(shift_type: str = "night"):
    return circadian_rhythm_service.get_shift_work_tips(shift_type)


@router.post("/energy/log")
async def log_energy(level: int = 5, context: str = ""):
    return circadian_rhythm_service.log_energy(level, context)


@router.get("/rhythm-score")
async def get_rhythm_score():
    return circadian_rhythm_service.get_rhythm_score()

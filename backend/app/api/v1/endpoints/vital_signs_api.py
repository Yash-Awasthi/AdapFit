"""Vital Signs API — ECG, SpO2, Body Temperature"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.vital_signs import vital_signs_service

router = APIRouter()


class TemperatureRequest(BaseModel):
    temperature_celsius: float
    measurement_site: str = "oral"


class SpO2Request(BaseModel):
    red_avg: float = 0.6
    infrared_avg: float = 0.7


@router.post("/ecg/start")
async def start_ecg(user_id: str = "default"):
    return vital_signs_service.start_ecg_measurement(user_id)


@router.post("/ecg/frame")
async def process_ecg_frame(user_id: str = "default"):
    return vital_signs_service.process_ecg_frame(user_id)


@router.get("/ecg/history")
async def get_ecg_history(limit: int = 10):
    return {"readings": vital_signs_service.get_ecg_history(limit=limit)}


@router.post("/ecg/analyze")
async def analyze_rhythm(readings: list[dict] | None = None):
    return vital_signs_service.analyze_rhythm(readings or [])


@router.post("/spo2")
async def estimate_spo2(request: SpO2Request):
    return vital_signs_service.estimate_spo2(request.red_avg, request.infrared_avg)


@router.get("/spo2/history")
async def get_spo2_history(limit: int = 10):
    return {"readings": vital_signs_service.get_spo2_history(limit)}


@router.post("/temperature")
async def log_temperature(request: TemperatureRequest):
    return vital_signs_service.log_temperature(request.temperature_celsius, request.measurement_site)


@router.get("/temperature/history")
async def get_temperature_history(limit: int = 10):
    return {"readings": vital_signs_service.get_temperature_history(limit)}


@router.get("/summary")
async def get_vitals_summary():
    return vital_signs_service.get_vitals_summary()

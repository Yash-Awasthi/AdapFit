"""ME/CFS activity pacing: resting-heart-rate ceiling, daily log and crash log."""
from typing import List, Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.chronic_fatigue import chronic_fatigue_service

router = APIRouter()

DATE = r"^\d{4}-\d{2}-\d{2}$"


class RestingHr(BaseModel):
    bpm: int = Field(ge=30, le=130)


class DayLog(BaseModel):
    date: str = Field(pattern=DATE)
    energy: int = Field(ge=0, le=10)
    activity_minutes: int = Field(ge=0, le=1440)
    peak_hr: Optional[int] = Field(None, ge=30, le=230)
    symptoms: List[str] = Field(default_factory=list, max_length=20)
    notes: str = Field("", max_length=500)


class Crash(BaseModel):
    date: str = Field(pattern=DATE)
    severity: Literal["mild", "moderate", "severe"]
    trigger: str = Field("", max_length=200)
    notes: str = Field("", max_length=500)


@router.get("/summary")
async def summary(days: int = 14):
    return chronic_fatigue_service.summary(days)


@router.put("/resting-hr")
async def set_resting_hr(body: RestingHr):
    return chronic_fatigue_service.set_resting_hr(body.bpm)


@router.post("/day")
async def log_day(body: DayLog):
    return chronic_fatigue_service.log_day(**body.model_dump())


@router.post("/crash")
async def log_crash(body: Crash):
    return chronic_fatigue_service.log_crash(**body.model_dump())

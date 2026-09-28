"""Preventive check-ups due by age and sex, with when each was last done."""
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.preventive_screening import preventive_screening_service

router = APIRouter()


class ProfileRequest(BaseModel):
    age: int = Field(ge=18, le=120)
    sex: Literal["female", "male"]


class LogRequest(BaseModel):
    check_id: str = Field(min_length=2, max_length=40)
    done_on: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    note: str = Field("", max_length=200)


@router.post("/profile")
async def set_profile(req: ProfileRequest):
    return preventive_screening_service.set_profile(req.age, req.sex)


@router.get("/schedule")
async def schedule():
    return preventive_screening_service.schedule()


@router.post("/log")
async def log_check(req: LogRequest):
    try:
        return preventive_screening_service.log(req.check_id, req.done_on, req.note)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

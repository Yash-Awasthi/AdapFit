"""Chronotype analysis endpoints."""
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.chronotype_analysis import (
    SleepRecord, classify_chronotype, score_msq, analyze_chronotype,
    recommend_sleep_window, estimate_phase_shift,
)

router = APIRouter()


class SleepRecordInput(BaseModel):
    bedtime: str
    wake_time: str
    date: str


@router.get("/chronotype/classify")
def classify(midpoint_minutes: float):
    return classify_chronotype(midpoint_minutes)


@router.get("/chronotype/score")
def score(midpoint_minutes: float):
    return score_msq(midpoint_minutes)


@router.post("/chronotype/analyze")
def analyze(body: list[SleepRecordInput]):
    records = [SleepRecord(**r.model_dump()) for r in body]
    return analyze_chronotype(records)


@router.get("/chronotype/sleep-window")
def sleep_window(chronotype_ordinal: int, target_hours: float = 8.0, work_wake: Optional[str] = None):
    return recommend_sleep_window(chronotype_ordinal, target_hours, work_wake)


@router.post("/chronotype/phase-shift")
def phase_shift(body: list[SleepRecordInput], days: int = 7):
    records = [SleepRecord(**r.model_dump()) for r in body]
    return estimate_phase_shift(records, days)

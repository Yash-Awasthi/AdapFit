"""Health predictions and anomaly detection endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.health_predictions import (
    DailyMetric, predict_sleep_score, predict_readiness,
    predict_activity, predict_hrv, detect_anomalies,
)

router = APIRouter(prefix="/predictions")


class DailyMetricInput(BaseModel):
    date: str
    sleep_score: Optional[float] = None
    sleep_hours: Optional[float] = None
    readiness_score: Optional[float] = None
    steps: Optional[int] = None
    hrv_rmssd: Optional[float] = None
    resting_hr: Optional[int] = None


@router.post("/sleep")
def sleep_prediction(body: dict):
    history = [DailyMetric(**m) for m in body.get("history", [])]
    days = body.get("days", 7)
    return predict_sleep_score(history, days)


@router.post("/readiness")
def readiness_prediction(body: dict):
    history = [DailyMetric(**m) for m in body.get("history", [])]
    days = body.get("days", 7)
    return predict_readiness(history, days)


@router.post("/activity")
def activity_prediction(body: dict):
    history = [DailyMetric(**m) for m in body.get("history", [])]
    days = body.get("days", 7)
    return predict_activity(history, days)


@router.post("/hrv")
def hrv_prediction(body: dict):
    history = [DailyMetric(**m) for m in body.get("history", [])]
    days = body.get("days", 7)
    return predict_hrv(history, days)


@router.post("/anomalies/detect")
def anomaly_detection(body: dict):
    history = [DailyMetric(**m) for m in body.get("history", [])]
    sensitivity = body.get("sensitivity", 1.5)
    return detect_anomalies(history, sensitivity)

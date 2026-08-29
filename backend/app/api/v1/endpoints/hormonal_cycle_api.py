"""Hormonal cycle tracking endpoints."""
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.hormonal_cycle import (
    average_cycle_length, calculate_cycle_lengths,
    predict_next_cycle, detect_phase, get_phase_info,
    is_fertile, is_peak_fertility, correlate_symptoms, SymptomEntry,
)

router = APIRouter()


class SymptomInput(BaseModel):
    date: str
    symptom: str
    severity: int = 3


@router.get("/cycle/average-length")
def get_average_cycle_length(period_starts_json: str):
    """Calculate average cycle length. Pass period starts as JSON array of ISO dates."""
    try:
        starts = json.loads(period_starts_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Invalid JSON")
    lengths = calculate_cycle_lengths(starts)
    avg = average_cycle_length(starts)
    return {
        "average_cycle_length": avg,
        "individual_lengths": lengths,
        "data_points": len(lengths),
    }


@router.get("/cycle/predict")
def predict_cycle(period_starts_json: str):
    """Predict next cycle from historical period start dates."""
    try:
        starts = json.loads(period_starts_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Invalid JSON")
    result = predict_next_cycle(starts)
    if result is None:
        raise HTTPException(status_code=422, detail="Need at least 1 period start date")
    return {
        "predicted_start": result.predicted_start,
        "predicted_end": result.predicted_end,
        "predicted_ovulation": result.predicted_ovulation,
        "fertile_window_start": result.fertile_window_start,
        "fertile_window_end": result.fertile_window_end,
        "predicted_cycle_length": result.predicted_cycle_length,
        "confidence": result.confidence,
        "based_on_cycles": result.based_on_cycles,
    }


@router.get("/cycle/phase")
def get_phase(cycle_start: str, cycle_length: int, current_date: str):
    """Detect current cycle phase."""
    phase = detect_phase(cycle_start, cycle_length, current_date)
    info = get_phase_info(phase)
    return {
        "phase": info.phase,
        "day_in_phase": info.day_in_phase,
        "days_remaining": info.days_remaining,
        "description": info.phase_description,
        "recommendations": info.recommendations,
    }


@router.get("/cycle/fertility")
def check_fertility(cycle_start: str, cycle_length: int, check_date: str):
    """Check if a date is in the fertile window."""
    fertile = is_fertile(cycle_start, cycle_length, check_date)
    peak = is_peak_fertility(cycle_start, cycle_length, check_date)
    return {
        "date": check_date,
        "is_fertile": fertile,
        "is_peak_fertility": peak,
    }


@router.post("/cycle/symptoms")
def analyze_symptoms(symptoms: list[SymptomInput], period_starts_json: str):
    """Analyze symptom patterns across cycle phases."""
    try:
        starts = json.loads(period_starts_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Invalid JSON")

    entries = [SymptomEntry(date=s.date, symptom=s.symptom, severity=s.severity) for s in symptoms]
    correlations = correlate_symptoms(entries, starts)
    return {
        "correlations": [
            {
                "symptom": c.symptom,
                "most_common_phase": c.most_common_phase,
                "average_severity_by_phase": c.average_severity_by_phase,
                "correlation_strength": c.correlation_strength,
            }
            for c in correlations
        ],
    }

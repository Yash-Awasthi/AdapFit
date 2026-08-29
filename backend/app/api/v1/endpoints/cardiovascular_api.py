"""Cardiovascular health analysis — HRV, heart rate zones, risk scoring, ECG processing."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.services.cardiovascular import (
    HRVReading,
    analyze_hrv,
    calculate_cv_risk,
    calculate_hr_zones,
    classify_hr_zone,
    ecg_to_hrv,
)

router = APIRouter()


class HRVAnalysisRequest(BaseModel):
    readings: list[dict] = Field(..., description="List of HRV readings with timestamp, hrv_rmssd, heart_rate")


class CVRiskRequest(BaseModel):
    age: int = Field(..., ge=10, le=120)
    resting_hr: int = Field(..., ge=30, le=200)
    avg_hrv: float = Field(..., ge=0, le=300)
    systolic_bp: Optional[int] = Field(None, ge=60, le=300)
    smoker: bool = False
    diabetic: bool = False
    family_history: bool = False


class HRZoneRequest(BaseModel):
    resting_hr: int = Field(..., ge=30, le=200)
    age: int = Field(..., ge=10, le=120)


class ECGRequest(BaseModel):
    signal: list[float] = Field(..., description="ECG signal amplitude values")
    sampling_rate: int = Field(250, ge=50, le=1000)


@router.post("/hrv/analyze")
async def analyze_hrv_data(req: HRVAnalysisRequest):
    """Analyze HRV readings for cardiovascular health indicators."""
    readings = [HRVReading(**r) for r in req.readings]
    return analyze_hrv(readings)


@router.post("/risk-score")
async def cardiovascular_risk(req: CVRiskRequest):
    """Calculate cardiovascular risk score based on multiple factors."""
    profile = calculate_cv_risk(
        age=req.age,
        resting_hr=req.resting_hr,
        avg_hrv=req.avg_hrv,
        systolic_bp=req.systolic_bp,
        smoker=req.smoker,
        diabetic=req.diabetic,
        family_history=req.family_history,
    )
    return {
        "risk_score": profile.cardiovascular_risk_score,
        "risk_category": profile.risk_category,
        "vo2_max_estimate": profile.vo2_max_estimate,
        "hr_zones": {k: {"min": v[0], "max": v[1]} for k, v in profile.hr_zones.items()},
        "max_heart_rate": profile.max_heart_rate,
        "heart_rate_reserve": profile.heart_rate_reserve,
        "recommendations": profile.recommendations,
    }


@router.post("/hr-zones")
async def get_hr_zones(req: HRZoneRequest):
    """Calculate personalized heart rate training zones."""
    from app.services.cardiovascular import max_hr_from_age
    max_hr = max_hr_from_age(req.age)
    zones = calculate_hr_zones(req.resting_hr, max_hr)
    return {
        "resting_hr": req.resting_hr,
        "max_hr": max_hr,
        "zones": {k: {"min": v[0], "max": v[1]} for k, v in zones.items()},
    }


@router.post("/hr-zone/classify")
async def classify_zone(bpm: int, resting_hr: int = 60, age: int = 30):
    """Classify a heart rate value into a training zone."""
    from app.services.cardiovascular import max_hr_from_age
    max_hr = max_hr_from_age(age)
    zones = calculate_hr_zones(resting_hr, max_hr)
    zone = classify_hr_zone(bpm, zones)
    return {"bpm": bpm, "zone": zone, "zones": {k: {"min": v[0], "max": v[1]} for k, v in zones.items()}}


@router.post("/ecg/process")
async def process_ecg(req: ECGRequest):
    """Process raw ECG signal to extract R-peaks and compute HRV."""
    result = ecg_to_hrv(req.signal, req.sampling_rate)
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    return result


@router.get("/zones/presets")
async def zone_presets():
    """Get standard heart rate zone definitions."""
    return {
        "zones": {
            "rest":        {"name": "Rest / Recovery",     "intensity": "50-60% HRR", "benefit": "Active recovery, warm-up"},
            "easy":        {"name": "Easy / Fat Burn",     "intensity": "60-70% HRR", "benefit": "Aerobic base, fat oxidation"},
            "aerobic":     {"name": "Aerobic / Endurance",  "intensity": "70-80% HRR", "benefit": "Cardiovascular endurance"},
            "tempo":       {"name": "Tempo / Threshold",    "intensity": "80-90% HRR", "benefit": "Lactate threshold improvement"},
            "threshold":   {"name": "Threshold / Anaerobic","intensity": "90-100% HRR", "benefit": "Anaerobic capacity"},
            "vo2max":      {"name": "VO2 Max / Sprint",     "intensity": "100%+ HRR",  "benefit": "Maximal oxygen uptake"},
        }
    }

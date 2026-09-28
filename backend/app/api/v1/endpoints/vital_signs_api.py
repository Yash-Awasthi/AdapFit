"""Vital Signs API — ECG, SpO2, Body Temperature"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from app.services.vital_signs import vital_signs_service

router = APIRouter()


class TemperatureRequest(BaseModel):
    temperature_celsius: float
    measurement_site: str = "oral"


class SpO2Request(BaseModel):
    # Required: a default would turn a request carrying no signal into a
    # confident saturation reading.
    red_avg: float
    infrared_avg: float
    pulse_rate: Optional[int] = None


class ECGRecordRequest(BaseModel):
    """An ECG a device measured. Intervals it did not report stay absent."""
    heart_rate: int
    rhythm: str = "normal"
    pr_interval_ms: Optional[float] = None
    qrs_duration_ms: Optional[float] = None
    qt_interval_ms: Optional[float] = None
    abnormalities: list[str] = []


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
    return vital_signs_service.estimate_spo2(request.red_avg, request.infrared_avg, request.pulse_rate)


@router.post("/ecg/record")
async def record_ecg(request: ECGRecordRequest):
    """Store an ECG measured by a device that has the hardware for one."""
    return vital_signs_service.record_ecg(
        request.heart_rate, request.rhythm, request.pr_interval_ms,
        request.qrs_duration_ms, request.qt_interval_ms, request.abnormalities,
    )


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


class NEWS2Request(BaseModel):
    respiratory_rate: int = Field(ge=4, le=60, description="Breaths in 30 seconds x 2")
    oxygen_saturation: int = Field(ge=50, le=100)
    systolic_bp: int = Field(ge=50, le=260)
    pulse_rate: int = Field(ge=20, le=250)
    temperature: float = Field(ge=30, le=43)
    new_confusion: bool = False
    on_oxygen: bool = False
    copd_target_88_92: bool = False


@router.post("/check")
async def when_to_seek_care(req: NEWS2Request):
    """NEWS2 on a full set of home readings, with what to do next."""
    from app.services.early_warning_score import VitalSigns, calculate_news2, home_next_step

    score = calculate_news2(VitalSigns(
        respiratory_rate=req.respiratory_rate, oxygen_saturation=req.oxygen_saturation,
        systolic_bp=req.systolic_bp, pulse_rate=req.pulse_rate,
        consciousness="new confusion" if req.new_confusion else "alert", temperature=req.temperature,
        supplemental_oxygen=req.on_oxygen, hypercapnic_scale=req.copd_target_88_92,
    ))
    return {
        "score": score.total, "band": score.trigger or "none",
        "parameter_scores": {"respiratory_rate": score.respiratory_score, "oxygen_saturation": score.oxygen_sat_score,
                             "systolic_bp": score.systolic_bp_score, "pulse": score.pulse_score,
                             "consciousness": score.consciousness_score, "temperature": score.temp_score,
                             "oxygen_therapy": score.supplemental_o2_score},
        "next_step": home_next_step(score),
        "note": "NEWS2 (Royal College of Physicians). It flags when to get help; it does not diagnose.",
    }

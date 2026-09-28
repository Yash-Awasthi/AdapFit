"""Sleep: the journal, its analysis, and the sensor-based tools built on it."""
from datetime import datetime
from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from app.services import smart_alarm
from app.services.sleep_analyzer import analyze_oximetry, analyze_pap_therapy
from app.services.sleep_architecture import analyze_sleep_architecture, detect_sleep_patterns
from app.services.sleep_tracker import minutes_between, sleep_journal

router = APIRouter()

CLOCK = r"^([01]\d|2[0-3]):[0-5]\d$"


class SleepLogRequest(BaseModel):
    bedtime: str = Field(pattern=CLOCK, examples=["23:30"])
    wake_time: str = Field(pattern=CLOCK, examples=["07:00"])
    date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Morning of waking")
    total_minutes: Optional[int] = Field(None, ge=1, le=1440, description="Minutes asleep, if measured")
    source: Literal["manual", "wearable"] = "manual"
    efficiency_pct: Optional[float] = Field(None, ge=0, le=100)
    deep_minutes: Optional[float] = Field(None, ge=0)
    rem_minutes: Optional[float] = Field(None, ge=0)
    light_minutes: Optional[float] = Field(None, ge=0)
    awake_minutes: Optional[float] = Field(None, ge=0)
    deep_pct: Optional[float] = Field(None, ge=0, le=100)
    rem_pct: Optional[float] = Field(None, ge=0, le=100)
    light_pct: Optional[float] = Field(None, ge=0, le=100)
    awake_pct: Optional[float] = Field(None, ge=0, le=100)
    interruptions: Optional[int] = Field(None, ge=0, le=100)
    minutes_to_fall_asleep: Optional[float] = Field(None, ge=0, le=600)
    quality_rating: Optional[int] = Field(None, ge=1, le=5)
    heart_rate_avg: Optional[float] = Field(None, ge=20, le=250)
    hrv_avg: Optional[float] = Field(None, ge=1, le=500)
    notes: Optional[str] = Field(None, max_length=200)

    @model_validator(mode="after")
    def stages_as_minutes(self):
        total = self.total_minutes or minutes_between(self.bedtime, self.wake_time)
        for stage in ("deep", "rem", "light", "awake"):
            pct = getattr(self, f"{stage}_pct")
            if pct is not None and getattr(self, f"{stage}_minutes") is None:
                setattr(self, f"{stage}_minutes", round(total * pct / 100, 1))
        return self


class ProfileRequest(BaseModel):
    age_group: Literal["teenager", "young_adult", "adult", "older_adult"] = "adult"
    target_bedtime: Optional[str] = Field(None, pattern=CLOCK)
    target_wake: Optional[str] = Field(None, pattern=CLOCK)


@router.post("/logs", status_code=201)
async def log_sleep(log: SleepLogRequest):
    fields = log.model_dump(exclude={"deep_pct", "rem_pct", "light_pct", "awake_pct"})
    try:
        return sleep_journal.log(**fields)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/logs")
async def list_sleep_logs(days: int = Query(7, ge=1, le=90)):
    return sleep_journal.nights(days)


@router.delete("/logs/{log_id}")
async def delete_sleep_log(log_id: str):
    if not sleep_journal.delete(log_id):
        raise HTTPException(status_code=404, detail="Sleep log not found")
    return {"deleted": True}


@router.get("/analysis")
async def get_sleep_analysis(days: int = Query(7, ge=1, le=90)):
    """Score, stages, debt, trend, recommendations and bedtime plan in one call."""
    return sleep_journal.analysis(days)


@router.get("/profile")
async def get_profile():
    return sleep_journal.profile()


@router.put("/profile")
async def set_profile(req: ProfileRequest):
    return sleep_journal.set_profile(req.age_group, req.target_bedtime, req.target_wake)


# --- Sensor tools -----------------------------------------------------------

class SensorSample(BaseModel):
    timestamp: datetime
    movement: float = Field(ge=0, description="Accelerometer magnitude")
    heart_rate: Optional[int] = Field(None, ge=20, le=250)


class SmartAlarmRequest(BaseModel):
    target_time: datetime
    window_minutes: int = Field(30, ge=5, le=90)
    samples: List[SensorSample] = Field(min_length=1, max_length=5000)


@router.post("/smart-alarm")
async def smart_alarm_check(req: SmartAlarmRequest):
    """Wake in the lightest moment of the window before the alarm, from phone or watch sensors."""
    samples, prev = [], smart_alarm.SleepStage.LIGHT
    for s in sorted(req.samples, key=lambda s: s.timestamp):
        prev = smart_alarm.detect_sleep_stage_from_sensors(s.movement, s.heart_rate, prev)
        samples.append(smart_alarm.SleepSample(s.timestamp, prev, s.heart_rate, s.movement))
    result = smart_alarm.find_optimal_wake_time(samples, req.target_time, req.window_minutes)
    inertia, advice = smart_alarm.calculate_sleep_inertia_risk(result.current_stage)
    return {
        "should_wake": result.should_wake,
        "wake_time": result.wake_time,
        "window_start": result.window_start,
        "window_end": result.window_end,
        "current_stage": result.current_stage.name.lower(),
        "reason": result.reason,
        "inertia_risk": inertia,
        "advice": advice,
    }


class HypnogramRequest(BaseModel):
    stages: List[int] = Field(min_length=10, max_length=4000,
                              description="30-second epochs: 0 wake, 1 N1, 2 N2, 3 N3, 4 REM")


@router.post("/architecture")
async def sleep_architecture(req: HypnogramRequest):
    """Architecture of one staged night, from a wearable's hypnogram."""
    if any(s not in (0, 1, 2, 3, 4) for s in req.stages):
        raise HTTPException(status_code=422, detail="Stage codes must be 0-4")
    arch = analyze_sleep_architecture(req.stages)
    return {**arch.__dict__, "patterns": detect_sleep_patterns(req.stages)}


class OximetryRequest(BaseModel):
    readings: List[float] = Field(min_length=2, max_length=50000)
    timestamps: List[datetime] = Field(min_length=2, max_length=50000)

    @model_validator(mode="after")
    def valid(self):
        if len(self.readings) != len(self.timestamps):
            raise ValueError("readings and timestamps must be the same length")
        if any(not 50 <= r <= 100 for r in self.readings):
            raise ValueError("SpO2 readings must be between 50 and 100")
        return self


@router.post("/oximetry")
async def overnight_oximetry(req: OximetryRequest):
    return analyze_oximetry(req.readings, req.timestamps)


class PapRequest(BaseModel):
    events_per_hour: float = Field(ge=0, le=150, description="AHI the machine reports")
    leak_rate: float = Field(ge=0, le=200, description="L/min")
    pressure: float = Field(ge=0, le=30, description="cmH2O")
    usage_hours: float = Field(ge=0, le=24)
    regime: Literal["CPAP", "APAP", "BiPAP"] = "CPAP"


@router.post("/pap")
async def pap_therapy(req: PapRequest):
    return analyze_pap_therapy(**req.model_dump())


class Epoch(BaseModel):
    timestamp: datetime
    acceleration_magnitude: float = Field(ge=0)
    heart_rate: Optional[float] = Field(None, ge=20, le=250)


class StagingRequest(BaseModel):
    epochs: List[Epoch] = Field(min_length=10, max_length=50000)
    time_in_bed_min: Optional[float] = Field(None, ge=0, le=1440)


@router.post("/stages")
async def stage_from_sensors(req: StagingRequest):
    """Estimate stages from 30-second accelerometer and heart-rate epochs."""
    from src.sleep.classifier import Epoch as SensorEpoch, SleepStageClassifier

    epochs = [SensorEpoch(e.timestamp, 0, e.acceleration_magnitude, e.heart_rate) for e in req.epochs]
    try:
        result = SleepStageClassifier().analyze(epochs, req.time_in_bed_min)
    except (ValueError, IndexError) as exc:
        raise HTTPException(status_code=422, detail=f"Analysis failed: {exc}") from exc
    arch = result.architecture
    return {
        "estimated": True,
        "quality": result.quality.value,
        "quality_score": result.quality_score,
        "summary": result.summary,
        "total_sleep_min": arch.total_sleep_time_min,
        "sleep_efficiency": arch.sleep_efficiency,
        "light_pct": arch.nrem1_pct + arch.nrem2_pct,
        "deep_pct": arch.nrem3_pct,
        "rem_pct": arch.rem_pct,
        "awakenings": arch.num_awakenings,
        "sleep_onset_min": arch.sleep_onset_latency_min,
        "recommendations": result.recommendations,
    }


@router.get("/alertness")
async def alertness_today():
    """Today's alertness curve from the two-process model, timed by your own logged nights."""
    from datetime import datetime as dt, timedelta as td

    from app.services.fatigue_prediction import SleepPeriod, alertness_curve, summarise

    nights = sleep_journal.nights(14)
    if len(nights) < 3:
        return {"status": "insufficient_data", "nights_needed": 3 - len(nights),
                "message": "Log at least 3 nights to see your personal alertness curve."}
    periods = []
    for n in nights:
        wake = dt.strptime(f"{n['date']} {n['wake_time']}", "%Y-%m-%d %H:%M")
        periods.append(SleepPeriod(wake - td(minutes=n["total_minutes"]), wake))
    today = dt.now()
    curve = alertness_curve(periods, today)
    return {
        "status": "ok",
        "curve": [{"time": t.strftime("%H:%M"), "alertness": v} for t, v in curve[::4]],
        **summarise(curve),
        "model": "Two-process model (Borbely), body-clock timing from your last nights",
    }

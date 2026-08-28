"""Sleep analysis endpoint: log sleep, get analysis and recommendations."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from app.services.sleep_analyzer import analyze_sleep, SleepAnalysis, SleepEntry

router = APIRouter()


class SleepLogRequest(BaseModel):
    bedtime: str = Field(examples=["23:30"])
    wake_time: str = Field(examples=["07:00"])
    total_minutes: int = Field(ge=0, le=720, examples=[450])
    efficiency_pct: float = Field(ge=0, le=100, default=90, examples=[88])
    interruptions: int = Field(ge=0, default=0, examples=[1])
    deep_pct: float = Field(ge=0, le=100, default=20, examples=[18])
    rem_pct: float = Field(ge=0, le=100, default=25, examples=[22])
    light_pct: float = Field(ge=0, le=100, default=45, examples=[48])
    awake_pct: float = Field(ge=0, le=100, default=10, examples=[12])
    notes: Optional[str] = Field(None, max_length=200)


class SleepLogResponse(BaseModel):
    id: str
    date: str
    total_minutes: int
    efficiency_pct: float
    logged_at: str


# In-memory storage
sleep_logs: dict = {}  # user_id -> list of SleepEntry dicts


@router.get("/analysis", response_model=SleepAnalysis)
async def get_sleep_analysis(
    user_id: str = Query("default"),
    days: int = Query(7, ge=1, le=30),
):
    """Get sleep analysis with recommendations."""
    entries = sleep_logs.get(user_id, [])[-days:]
    sleep_entries = []
    for e in entries:
        stages = []
        total_min = e["total_minutes"]
        for name, pct_key in [("deep", "deep_pct"), ("rem", "rem_pct"), ("light", "light_pct"), ("awake", "awake_pct")]:
            pct = e.get(pct_key, 0)
            stages.append({"name": name, "minutes": round(total_min * pct / 100), "percentage": pct})
        sleep_entries.append(SleepEntry(
            date=e["date"], bedtime=e["bedtime"], wake_time=e["wake_time"],
            total_minutes=total_min, efficiency_pct=e["efficiency_pct"],
            stages=stages, interruptions=e.get("interruptions", 0),
        ))
    return analyze_sleep(sleep_entries)


@router.get("/logs", response_model=List[SleepLogResponse])
async def list_sleep_logs(user_id: str = Query("default"), days: int = Query(7, ge=1, le=30)):
    """List recent sleep logs."""
    return [
        SleepLogResponse(
            id=e["id"], date=e["date"], total_minutes=e["total_minutes"],
            efficiency_pct=e["efficiency_pct"], logged_at=e["logged_at"],
        )
        for e in sleep_logs.get(user_id, [])[-days:]
    ]


@router.post("/logs", response_model=SleepLogResponse, status_code=201)
async def log_sleep(log: SleepLogRequest, user_id: str = Query("default")):
    """Log a sleep session."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entry = {
        "id": str(uuid.uuid4())[:8],
        "date": today,
        "bedtime": log.bedtime,
        "wake_time": log.wake_time,
        "total_minutes": log.total_minutes,
        "efficiency_pct": log.efficiency_pct,
        "interruptions": log.interruptions,
        "deep_pct": log.deep_pct,
        "rem_pct": log.rem_pct,
        "light_pct": log.light_pct,
        "awake_pct": log.awake_pct,
        "notes": log.notes,
        "logged_at": datetime.now(timezone.utc).isoformat(),
    }
    sleep_logs.setdefault(user_id, []).append(entry)
    return SleepLogResponse(
        id=entry["id"], date=today,
        total_minutes=entry["total_minutes"],
        efficiency_pct=entry["efficiency_pct"],
        logged_at=entry["logged_at"],
    )


@router.delete("/logs/{log_id}")
async def delete_sleep_log(log_id: str, user_id: str = Query("default")):
    """Delete a sleep log."""
    user_logs = sleep_logs.get(user_id, [])
    for i, e in enumerate(user_logs):
        if e["id"] == log_id:
            user_logs.pop(i)
            return {"deleted": True}
    raise HTTPException(status_code=404, detail="Sleep log not found")

"""
Medication Tracker API — medication scheduling, adherence tracking, and safety checks.
"""
from __future__ import annotations

from datetime import datetime
from functools import lru_cache

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


# --- Response Models ---

class MedicationRegisterResponse(BaseModel):
    status: str
    medication: str
    id: str


class DoseLogResponse(BaseModel):
    status: str
    record: str


class AdherenceResponse(BaseModel):
    overall_pct: float = Field(ge=0, le=100)
    taken: int
    missed: int
    skipped: int


# --- Input Validation ---

VALID_FREQUENCIES = {"once_daily", "twice_daily", "three_times_daily", "weekly", "as_needed"}
VALID_DOSE_STATUSES = {"taken", "missed", "skipped"}
VALID_CATEGORIES = {"prescription", "otc", "supplement", "vitamin"}


class MedicationRequest(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=256)
    dosage: str = Field(min_length=1, max_length=64)
    frequency: str = Field(default="once_daily")
    times_of_day: list[str] = Field(default_factory=lambda: ["08:00"], max_length=10)
    instructions: str = Field(default="", max_length=500)
    category: str = Field(default="prescription")
    contraindications: list[str] = Field(default_factory=list, max_length=20)

    def model_post_init(self, __context: object) -> None:
        if self.frequency not in VALID_FREQUENCIES:
            raise ValueError(f"Invalid frequency '{self.frequency}'. Valid: {sorted(VALID_FREQUENCIES)}")
        if self.category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category '{self.category}'. Valid: {sorted(VALID_CATEGORIES)}")


class DoseLogRequest(BaseModel):
    medication_id: str = Field(min_length=1, max_length=128)
    scheduled_time: str = Field(description="ISO format datetime")
    status: str = Field(description="taken, missed, or skipped")
    notes: str = Field(default="", max_length=500)

    def model_post_init(self, __context: object) -> None:
        if self.status not in VALID_DOSE_STATUSES:
            raise ValueError(f"Invalid status '{self.status}'. Valid: {sorted(VALID_DOSE_STATUSES)}")


# --- Cached singleton ---

@lru_cache(maxsize=1)
def _get_tracker():
    from src.medication.tracker import MedicationTracker
    return MedicationTracker()


# --- Routes ---

@router.post(
    "/medications",
    response_model=MedicationRegisterResponse,
    summary="Register a medication",
)
async def add_medication(req: MedicationRequest) -> MedicationRegisterResponse:
    from src.medication.tracker import Medication, MedicationFrequency

    tracker = _get_tracker()
    freq = MedicationFrequency(req.frequency)
    med = Medication(
        id=req.id, name=req.name, dosage=req.dosage,
        frequency=freq, times_of_day=req.times_of_day,
        instructions=req.instructions, category=req.category,
        contraindications=req.contraindications,
    )
    tracker.add_medication(med)
    return MedicationRegisterResponse(status="registered", medication=med.name, id=med.id)


@router.get(
    "/schedule/today",
    summary="Get today's medication schedule",
)
async def get_today_schedule() -> list[dict]:
    tracker = _get_tracker()
    return tracker.get_todays_schedule()


@router.post(
    "/dose/log",
    response_model=DoseLogResponse,
    summary="Log a medication dose",
)
async def log_dose(req: DoseLogRequest) -> DoseLogResponse:
    from src.medication.tracker import DoseStatus

    tracker = _get_tracker()
    status = DoseStatus(req.status)
    record = tracker.log_dose(
        req.medication_id,
        datetime.fromisoformat(req.scheduled_time),
        status,
        notes=req.notes,
    )
    return DoseLogResponse(
        status="logged",
        record=record.status.value if record else "not_found",
    )


@router.get(
    "/adherence",
    response_model=AdherenceResponse,
    summary="Get overall medication adherence",
)
async def get_adherence() -> AdherenceResponse:
    tracker = _get_tracker()
    result = tracker.get_overall_adherence()
    return AdherenceResponse(**result)


@router.get(
    "/reminders",
    summary="Get upcoming medication reminders",
)
async def get_reminders() -> list[dict]:
    tracker = _get_tracker()
    return tracker.get_upcoming_reminders(hours_ahead=4)

"""
AdapFit Mental Health Module
Mood tracking, breathing exercises, stress visualization.
"""
import uuid
from typing import List, Literal, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from app.core.limiter import make_limiter

from app.core.storage import storage
from app.core.cache import api_response_cache as cache

router = APIRouter()
limiter = make_limiter()


# --- Schemas ---

class MoodLogRequest(BaseModel):
    user_id: str
    mood: int = Field(ge=1, le=10, description="1 (very low) to 10 (excellent)")
    energy: int = Field(ge=1, le=10, description="1 (exhausted) to 10 (energized)")
    anxiety: int = Field(ge=1, le=10, description="1 (calm) to 10 (very anxious)")
    notes: Optional[str] = Field(None, max_length=500)
    tags: List[str] = []  # e.g., ["work_stress", "good_sleep", "social"]


class MoodLogResponse(BaseModel):
    id: str
    mood: int
    energy: int
    anxiety: int
    notes: Optional[str]
    tags: List[str]
    logged_at: str


class MoodTrendResponse(BaseModel):
    user_id: str
    entries: List[dict]
    avg_mood: float
    avg_energy: float
    avg_anxiety: float
    mood_trend: str  # "improving", "stable", "declining"
    count: int


class BreathingExercise(BaseModel):
    id: str
    name: str
    description: str
    inhale_sec: int
    hold_sec: int
    exhale_sec: int
    rounds: int
    benefit: str


# --- Breathing exercises catalog ---

BREATHING_EXERCISES = [
    BreathingExercise(
        id="box-breathing",
        name="Box Breathing",
        description="Navy SEAL technique for calm focus. Equal inhale, hold, exhale, hold.",
        inhale_sec=4,
        hold_sec=4,
        exhale_sec=4,
        rounds=8,
        benefit="Reduces stress, improves focus, activates parasympathetic nervous system",
    ),
    BreathingExercise(
        id="4-7-8-relaxing",
        name="4-7-8 Relaxing Breath",
        description="Dr. Andrew Weil's natural tranquilizer for the nervous system.",
        inhale_sec=4,
        hold_sec=7,
        exhale_sec=8,
        rounds=6,
        benefit="Promotes sleep, reduces anxiety, lowers heart rate",
    ),
    BreathingExercise(
        id="coherent-breathing",
        name="Coherent Breathing",
        description="5 breaths per minute for heart rate variability optimization.",
        inhale_sec=6,
        hold_sec=0,
        exhale_sec=6,
        rounds=10,
        benefit="Optimizes HRV, balances autonomic nervous system",
    ),
    BreathingExercise(
        id="energizing-breath",
        name="Energizing Breath",
        description="Quick, sharp inhales and exhales to boost alertness.",
        inhale_sec=2,
        hold_sec=0,
        exhale_sec=2,
        rounds=15,
        benefit="Increases energy, improves alertness, stimulates sympathetic system",
    ),
    BreathingExercise(
        id="pre-workout",
        name="Pre-Workout Activation",
        description="Deep diaphragmatic breathing to prepare for intense exercise.",
        inhale_sec=4,
        hold_sec=2,
        exhale_sec=4,
        rounds=5,
        benefit="Increases oxygen flow, primes core stability, mental focus",
    ),
]


# --- Endpoints ---

@router.post("", response_model=MoodLogResponse, status_code=201)
@limiter.limit("20/minute")
async def log_mood(request: Request, req: MoodLogRequest):
    """Log a mood entry with energy and anxiety levels."""
    entry = {
        "id": str(uuid.uuid4()),
        "mood": req.mood,
        "energy": req.energy,
        "anxiety": req.anxiety,
        "notes": req.notes,
        "tags": req.tags,
        "logged_at": datetime.now(timezone.utc).isoformat(),
    }

    # Store in agent_memory under mood_logs key
    memory = await storage.get_agent_memory(req.user_id)
    logs = memory.get("mood_logs", [])
    logs.append(entry)
    # Keep last 90 entries
    if len(logs) > 90:
        logs = logs[-90:]
    await storage.update_agent_memory(req.user_id, {"mood_logs": logs})

    return MoodLogResponse(**entry)


@router.get("", response_model=MoodTrendResponse)
async def get_mood_trend(user_id: str, days: int = 14):
    """Get mood trend over time."""
    memory = await storage.get_agent_memory(user_id)
    logs = memory.get("mood_logs", [])

    if not logs:
        return MoodTrendResponse(
            user_id=user_id,
            entries=[],
            avg_mood=0,
            avg_energy=0,
            avg_anxiety=0,
            mood_trend="insufficient_data",
            count=0,
        )

    recent = logs[-days:] if len(logs) > days else logs

    avg_mood = sum(e["mood"] for e in recent) / len(recent)
    avg_energy = sum(e["energy"] for e in recent) / len(recent)
    avg_anxiety = sum(e["anxiety"] for e in recent) / len(recent)

    # Simple trend: compare first half to second half
    if len(recent) >= 4:
        mid = len(recent) // 2
        first_half_avg = sum(e["mood"] for e in recent[:mid]) / mid
        second_half_avg = sum(e["mood"] for e in recent[mid:]) / (len(recent) - mid)
        diff = second_half_avg - first_half_avg
        trend = "improving" if diff > 0.5 else ("declining" if diff < -0.5 else "stable")
    else:
        trend = "insufficient_data"

    return MoodTrendResponse(
        user_id=user_id,
        entries=recent,
        avg_mood=round(avg_mood, 1),
        avg_energy=round(avg_energy, 1),
        avg_anxiety=round(avg_anxiety, 1),
        mood_trend=trend,
        count=len(recent),
    )


@router.get("/breathing-exercises", response_model=List[BreathingExercise])
async def list_breathing_exercises():
    """List available breathing exercises."""
    cached = cache.get("breathing-exercises")
    if cached is not None:
        return cached
    cache.set("breathing-exercises", BREATHING_EXERCISES, ttl=3600)  # Cache for 1 hour
    return BREATHING_EXERCISES


@router.get("/breathing-exercises/{exercise_id}", response_model=BreathingExercise)
async def get_breathing_exercise(exercise_id: str):
    """Get a specific breathing exercise."""
    for ex in BREATHING_EXERCISES:
        if ex.id == exercise_id:
            return ex
    raise HTTPException(status_code=404, detail=f"Exercise {exercise_id} not found")


# --- Questionnaires (PHQ-9, GAD-7, WHO-5) ---

from app.services import mental_health as questionnaires  # noqa: E402

QuestionnaireId = Literal["phq9", "gad7", "who5"]


class AnswersRequest(BaseModel):
    user_id: str
    answers: List[int] = Field(min_length=5, max_length=9)


@router.get("/questionnaires/{qid}")
async def get_questionnaire(qid: QuestionnaireId):
    return questionnaires.questionnaire(qid)


@router.post("/questionnaires/{qid}", status_code=201)
async def submit_questionnaire(qid: QuestionnaireId, req: AnswersRequest):
    try:
        result = questionnaires.score(qid, req.answers)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    result["taken_at"] = datetime.now(timezone.utc).isoformat()
    memory = await storage.get_agent_memory(req.user_id)
    history = (memory.get("questionnaires", []) + [{k: v for k, v in result.items() if k != "crisis"}])[-60:]
    await storage.update_agent_memory(req.user_id, {"questionnaires": history})
    return result


@router.get("/questionnaires")
async def questionnaire_history(user_id: str):
    """Latest result per questionnaire, and the full history."""
    history = (await storage.get_agent_memory(user_id)).get("questionnaires", [])
    latest = {}
    for entry in history:
        latest[entry["questionnaire"]] = entry
    return {"latest": latest, "history": history}


# --- CBT thought records ---

class ThoughtRecordRequest(BaseModel):
    user_id: str
    situation: str = Field(min_length=1, max_length=500)
    thought: str = Field(min_length=1, max_length=500)
    emotion: str = Field(min_length=1, max_length=60)
    intensity_before: int = Field(ge=0, le=100)
    evidence_for: str = Field("", max_length=1000)
    evidence_against: str = Field("", max_length=1000)
    balanced_thought: str = Field("", max_length=500)
    intensity_after: int = Field(ge=0, le=100)


@router.post("/thought-records", status_code=201)
async def add_thought_record(req: ThoughtRecordRequest):
    record = {"id": str(uuid.uuid4()), **req.model_dump(exclude={"user_id"}),
              "created_at": datetime.now(timezone.utc).isoformat()}
    memory = await storage.get_agent_memory(req.user_id)
    records = (memory.get("thought_records", []) + [record])[-200:]
    await storage.update_agent_memory(req.user_id, {"thought_records": records})
    return {**record, "change": req.intensity_before - req.intensity_after}


@router.get("/thought-records")
async def list_thought_records(user_id: str, limit: int = 20):
    return list(reversed((await storage.get_agent_memory(user_id)).get("thought_records", [])))[:limit]

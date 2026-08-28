"""
AdapFit Mental Health Module
Mood tracking, breathing exercises, stress visualization.
"""
import uuid
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.storage import storage
from app.core.cache import api_response_cache as cache

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


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

"""Workout timer: session control, rest timer, audio cues, set tracking."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from app.services.workout_timer import workout_timer, TimerSession, AudioCue, SetInfo

router = APIRouter()


class StartSessionRequest(BaseModel):
    workout_id: Optional[str] = None
    exercises: List[dict] = Field(default_factory=list)


class RestRequest(BaseModel):
    duration_seconds: int = Field(ge=10, le=600, default=90)


class CueResponse(BaseModel):
    cue_type: str
    message: str
    time_seconds: Optional[float]
    priority: int


@router.post("/start", response_model=TimerSession)
async def start_timer(request: StartSessionRequest, user_id: str = Query("default")):
    """Start a workout timer session."""
    import uuid
    session_id = str(uuid.uuid4())[:8]

    exercises = request.exercises
    if not exercises and request.workout_id:
        # Try to load exercises from workout
        try:
            from app.core.storage import storage
            workouts = await storage.get_workouts(user_id, 30)
            workout = next((w for w in workouts if w.get("workout_id") == request.workout_id), None)
            if workout:
                exercises = workout.get("exercises", [])
        except Exception:
            pass

    if not exercises:
        exercises = [{"name": "Custom Exercise", "sets": 3, "target_reps": "8-12", "target_rpe": 7, "rest_seconds": 90}]

    return workout_timer.start_session(session_id, exercises)


@router.get("/{session_id}", response_model=TimerSession)
async def get_timer_state(session_id: str):
    """Get current timer state."""
    session = workout_timer.get_state(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{session_id}/rest", response_model=TimerSession)
async def start_rest(session_id: str, request: RestRequest):
    """Start rest timer."""
    session = workout_timer.start_rest(session_id, request.duration_seconds)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{session_id}/complete-set", response_model=TimerSession)
async def complete_set(session_id: str):
    """Complete current set and advance."""
    session = workout_timer.complete_set(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{session_id}/pause", response_model=TimerSession)
async def pause_timer(session_id: str):
    """Pause the timer."""
    session = workout_timer.pause(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{session_id}/resume", response_model=TimerSession)
async def resume_timer(session_id: str):
    """Resume the timer."""
    session = workout_timer.resume(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{session_id}/end")
async def end_timer(session_id: str):
    """End the timer session."""
    result = workout_timer.end_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@router.get("/{session_id}/cues", response_model=List[CueResponse])
async def get_cues(session_id: str):
    """Get pending audio cues."""
    session = workout_timer.get_state(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return [CueResponse(**c.model_dump()) for c in session.cues]


@router.delete("/{session_id}/cues")
async def clear_cues(session_id: str):
    """Clear consumed audio cues."""
    session = workout_timer.get_state(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.cues = []
    return {"cleared": True}

"""
Workout timer service: manages workout sessions with audio cues,
rest timers, set tracking, and exercise transitions.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class TimerState(str, Enum):
    IDLE = "idle"
    WARMUP = "warmup"
    EXERCISE = "exercise"
    REST = "rest"
    COOLDOWN = "cooldown"
    PAUSED = "paused"
    COMPLETED = "completed"


class AudioCue(BaseModel):
    cue_type: str  # "start", "rest", "halfway", "countdown", "complete", "next_exercise"
    message: str
    time_seconds: Optional[float] = None
    priority: int = 0  # Higher = more important


class SetInfo(BaseModel):
    set_number: int
    exercise_name: str
    target_reps: str
    target_rpe: float
    rest_seconds: int
    status: str = "pending"  # pending, active, completed


class TimerSession(BaseModel):
    session_id: str
    state: TimerState
    exercise_index: int = 0
    set_index: int = 0
    elapsed_seconds: float = 0
    remaining_seconds: float = 0
    total_exercises: int = 0
    completed_sets: int = 0
    total_sets: int = 0
    current_exercise: Optional[str] = None
    current_set: Optional[SetInfo] = None
    cues: list[AudioCue] = []
    started_at: Optional[str] = None


# Audio cue templates
CUE_TEMPLATES = {
    "workout_start": AudioCue(cue_type="start", message="Workout started. Let's go!", priority=2),
    "warmup_start": AudioCue(cue_type="start", message="Starting warm-up. Get your body ready.", priority=1),
    "exercise_start": AudioCue(cue_type="start", message="", priority=1),
    "set_complete": AudioCue(cue_type="complete", message="", priority=1),
    "rest_start": AudioCue(cue_type="rest", message="", priority=1),
    "rest_30s": AudioCue(cue_type="countdown", message="30 seconds rest remaining.", priority=0),
    "rest_10s": AudioCue(cue_type="countdown", message="10 seconds. Get ready!", priority=1),
    "rest_3s": AudioCue(cue_type="countdown", message="3, 2, 1...", priority=2),
    "halfway": AudioCue(cue_type="halfway", message="Halfway through!", priority=0),
    "next_exercise": AudioCue(cue_type="next_exercise", message="", priority=1),
    "workout_complete": AudioCue(cue_type="complete", message="Workout complete! Great work!", priority=2),
    "pause": AudioCue(cue_type="start", message="Timer paused.", priority=1),
    "resume": AudioCue(cue_type="start", message="Timer resumed. Let's continue!", priority=1),
}


class WorkoutTimer:
    def __init__(self):
        self.sessions: dict[str, TimerSession] = {}

    def start_session(self, session_id: str, exercises: list[dict]) -> TimerSession:
        """Start a new timer session with exercises."""
        total_sets = sum(ex.get("sets", 3) for ex in exercises)

        cues = [CUE_TEMPLATES["workout_start"].model_copy()]

        session = TimerSession(
            session_id=session_id,
            state=TimerState.WARMUP,
            total_exercises=len(exercises),
            total_sets=total_sets,
            current_exercise=exercises[0].get("name", "Warm-up") if exercises else "Warm-up",
            started_at=datetime.now(timezone.utc).isoformat(),
            cues=cues,
        )
        self.sessions[session_id] = session
        return session

    def get_state(self, session_id: str) -> Optional[TimerSession]:
        return self.sessions.get(session_id)

    def start_rest(self, session_id: str, duration_seconds: int = 90) -> TimerSession:
        """Start rest timer."""
        session = self.sessions.get(session_id)
        if not session:
            return None

        session.state = TimerState.REST
        session.remaining_seconds = duration_seconds

        cues = []
        set_num = session.set_index + 1
        total = session.current_set.target_reps if session.current_set else "8-12"
        rest_cue = CUE_TEMPLATES["rest_start"].model_copy()
        rest_cue.message = f"Rest for {duration_seconds} seconds. Set {set_num} complete."
        cues.append(rest_cue)

        session.cues = cues
        return session

    def complete_set(self, session_id: str) -> TimerSession:
        """Mark current set as complete, advance to next set or exercise."""
        session = self.sessions.get(session_id)
        if not session:
            return None

        session.completed_sets += 1
        cues = []

        # Check if more sets in current exercise
        if session.current_set and session.set_index < (session.current_set.set_number):
            session.set_index += 1
            set_cue = CUE_TEMPLATES["set_complete"].model_copy()
            set_cue.message = f"Set {session.set_index} complete!"
            cues.append(set_cue)
        else:
            # Move to next exercise
            session.exercise_index += 1
            session.set_index = 0

            if session.exercise_index >= session.total_exercises:
                session.state = TimerState.COMPLETED
                cues.append(CUE_TEMPLATES["workout_complete"].model_copy())
            else:
                session.state = TimerState.EXERCISE
                next_cue = CUE_TEMPLATES["next_exercise"].model_copy()
                next_cue.message = f"Next exercise. Let's go!"
                cues.append(next_cue)

        session.cues = cues
        return session

    def pause(self, session_id: str) -> Optional[TimerSession]:
        session = self.sessions.get(session_id)
        if session and session.state != TimerState.COMPLETED:
            session.state = TimerState.PAUSED
            session.cues = [CUE_TEMPLATES["pause"].model_copy()]
        return session

    def resume(self, session_id: str) -> Optional[TimerSession]:
        session = self.sessions.get(session_id)
        if session and session.state == TimerState.PAUSED:
            session.state = TimerState.EXERCISE
            session.cues = [CUE_TEMPLATES["resume"].model_copy()]
        return session

    def end_session(self, session_id: str) -> Optional[dict]:
        session = self.sessions.get(session_id)
        if not session:
            return None

        started = datetime.fromisoformat(session.started_at) if session.started_at else datetime.now(timezone.utc)
        duration = (datetime.now(timezone.utc) - started).total_seconds()

        return {
            "session_id": session_id,
            "duration_seconds": round(duration),
            "total_exercises": session.total_exercises,
            "completed_sets": session.completed_sets,
            "total_sets": session.total_sets,
            "completion_pct": round((session.completed_sets / session.total_sets * 100) if session.total_sets else 0, 1),
        }


# Singleton
workout_timer = WorkoutTimer()

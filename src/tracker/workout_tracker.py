"""
Workout Tracker — logs workouts, tracks progress, and detects personal records.
Supports real-time set tracking, rest timers, and PR detection.

Inspired by: ai-workout-tracker (React Native workout tracker)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


@dataclass
class SetLog:
    """A single set in a workout."""
    set_number: int
    reps: int
    weight_kg: float
    rpe: float | None = None  # Rate of Perceived Exertion (1-10)
    is_drop_set: bool = False
    is_warmup: bool = False
    is_failure: bool = False
    notes: str = ""
    timestamp: datetime | None = None


@dataclass
class ExerciseLog:
    """All sets for a single exercise within a workout."""
    exercise_name: str
    sets: list[SetLog] = field(default_factory=list)
    notes: str = ""

    @property
    def total_volume(self) -> float:
        """Total volume (sets × reps × weight)."""
        return sum(s.reps * s.weight_kg for s in self.sets if not s.is_warmup)

    @property
    def top_set(self) -> SetLog | None:
        """The heaviest working set."""
        working = [s for s in self.sets if not s.is_warmup]
        return max(working, key=lambda s: s.weight_kg) if working else None

    @property
    def estimated_1rm(self) -> float:
        """Estimated 1RM using Epley formula: weight × (1 + reps/30)."""
        top = self.top_set
        if not top or top.reps < 2:
            return top.weight_kg if top else 0
        return round(top.weight_kg * (1 + top.reps / 30), 1)


@dataclass
class WorkoutSession:
    """A complete workout session."""
    session_id: str
    user_id: str
    started_at: datetime
    ended_at: datetime | None = None
    exercise_logs: list[ExerciseLog] = field(default_factory=list)
    workout_type: str = ""  # full_body, upper, lower, etc.
    notes: str = ""
    mood_pre: int | None = None  # 1-5 pre-workout mood
    mood_post: int | None = None  # 1-5 post-workout mood
    energy_level: int | None = None  # 1-5

    @property
    def duration_minutes(self) -> float:
        """Workout duration in minutes."""
        if self.ended_at:
            return (self.ended_at - self.started_at).total_seconds() / 60
        return 0

    @property
    def total_volume(self) -> float:
        """Total volume across all exercises."""
        return sum(el.total_volume for el in self.exercise_logs)

    @property
    def exercise_count(self) -> int:
        return len(self.exercise_logs)

    @property
    def set_count(self) -> int:
        return sum(len(el.sets) for el in self.exercise_logs)


@dataclass
class PersonalRecord:
    """A detected personal record."""
    exercise_name: str
    record_type: str  # "weight", "volume", "1rm", "reps"
    previous_best: float
    new_best: float
    achieved_at: datetime
    session_id: str


class WorkoutTracker:
    """Tracks workouts, detects PRs, and analyzes training progress."""

    def __init__(self) -> None:
        self._sessions: dict[str, WorkoutSession] = {}
        self._pr_history: dict[str, dict[str, PersonalRecord]] = {}  # exercise -> {type -> PR}
        self._user_sessions: dict[str, list[str]] = {}  # user_id -> session_ids

    def start_session(self, session_id: str, user_id: str, workout_type: str = "") -> WorkoutSession:
        """Start a new workout session."""
        session = WorkoutSession(
            session_id=session_id,
            user_id=user_id,
            started_at=datetime.utcnow(),
            workout_type=workout_type,
        )
        self._sessions[session_id] = session
        self._user_sessions.setdefault(user_id, []).append(session_id)
        return session

    def log_set(
        self,
        session_id: str,
        exercise_name: str,
        set_number: int,
        reps: int,
        weight_kg: float,
        rpe: float | None = None,
        is_warmup: bool = False,
        is_failure: bool = False,
    ) -> SetLog | None:
        """Log a single set for an exercise."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        # Find or create exercise log
        exercise_log = None
        for el in session.exercise_logs:
            if el.exercise_name == exercise_name:
                exercise_log = el
                break

        if not exercise_log:
            exercise_log = ExerciseLog(exercise_name=exercise_name)
            session.exercise_logs.append(exercise_log)

        set_log = SetLog(
            set_number=set_number,
            reps=reps,
            weight_kg=weight_kg,
            rpe=rpe,
            is_warmup=is_warmup,
            is_failure=is_failure,
            timestamp=datetime.utcnow(),
        )
        exercise_log.sets.append(set_log)

        return set_log

    def end_session(self, session_id: str, mood_post: int | None = None) -> WorkoutSession | None:
        """End a workout session and check for PRs."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        session.ended_at = datetime.utcnow()
        session.mood_post = mood_post

        # Check for PRs
        for el in session.exercise_logs:
            self._check_prs(el, session)

        return session

    def _check_prs(self, exercise_log: ExerciseLog, session: WorkoutSession) -> list[PersonalRecord]:
        """Check for personal records in an exercise log."""
        detected: list[PersonalRecord] = []
        name = exercise_log.exercise_name
        user_prs = self._pr_history.setdefault(name, {})

        # Check weight PR
        top = exercise_log.top_set
        if top:
            prev = user_prs.get("weight")
            if not prev or top.weight_kg > prev.new_best:
                pr = PersonalRecord(
                    exercise_name=name,
                    record_type="weight",
                    previous_best=prev.new_best if prev else 0,
                    new_best=top.weight_kg,
                    achieved_at=session.started_at,
                    session_id=session.session_id,
                )
                user_prs["weight"] = pr
                detected.append(pr)

        # Check volume PR
        vol = exercise_log.total_volume
        if vol > 0:
            prev = user_prs.get("volume")
            if not prev or vol > prev.new_best:
                pr = PersonalRecord(
                    exercise_name=name,
                    record_type="volume",
                    previous_best=prev.new_best if prev else 0,
                    new_best=vol,
                    achieved_at=session.started_at,
                    session_id=session.session_id,
                )
                user_prs["volume"] = pr
                detected.append(pr)

        # Check estimated 1RM PR
        e1rm = exercise_log.estimated_1rm
        if e1rm > 0:
            prev = user_prs.get("1rm")
            if not prev or e1rm > prev.new_best:
                pr = PersonalRecord(
                    exercise_name=name,
                    record_type="1rm",
                    previous_best=prev.new_best if prev else 0,
                    new_best=e1rm,
                    achieved_at=session.started_at,
                    session_id=session.session_id,
                )
                user_prs["1rm"] = pr
                detected.append(pr)

        return detected

    def get_user_history(self, user_id: str, limit: int = 10) -> list[WorkoutSession]:
        """Get recent workout history for a user."""
        session_ids = self._user_sessions.get(user_id, [])[-limit:]
        return [self._sessions[sid] for sid in session_ids if sid in self._sessions]

    def get_exercise_history(
        self, user_id: str, exercise_name: str, limit: int = 20
    ) -> list[ExerciseLog]:
        """Get history for a specific exercise."""
        history: list[ExerciseLog] = []
        for session in self.get_user_history(user_id, limit=50):
            for el in session.exercise_logs:
                if el.exercise_name == exercise_name:
                    history.append(el)
        return history[-limit:]

    def get_prs(self, exercise_name: str) -> dict[str, PersonalRecord]:
        """Get all PRs for an exercise."""
        return dict(self._pr_history.get(exercise_name, {}))

    def get_weekly_summary(self, user_id: str, weeks: int = 4) -> dict[str, Any]:
        """Get a weekly training summary."""
        now = datetime.utcnow()
        cutoff = now - timedelta(weeks=weeks)

        sessions = [
            s for s in self.get_user_history(user_id, limit=weeks * 7)
            if s.started_at >= cutoff
        ]

        weekly: dict[int, dict[str, Any]] = {}
        for session in sessions:
            week_num = (now - session.started_at).days // 7
            if week_num not in weekly:
                weekly[week_num] = {
                    "sessions": 0,
                    "total_volume": 0,
                    "total_sets": 0,
                    "total_duration": 0,
                }
            weekly[week_num]["sessions"] += 1
            weekly[week_num]["total_volume"] += session.total_volume
            weekly[week_num]["total_sets"] += session.set_count
            weekly[week_num]["total_duration"] += session.duration_minutes

        return {
            "weeks": weeks,
            "weekly_data": weekly,
            "avg_sessions_per_week": round(
                len(sessions) / max(weeks, 1), 1
            ),
            "total_volume": sum(s.total_volume for s in sessions),
        }

"""Self-Evolving Personalization Engine — tracks user patterns and adapts recommendations.

Inspired by EvoAgentX self-evolving agent patterns. This engine:
- Records user preferences, acceptance/rejection of recommendations
- Builds a personalization vector that evolves over time
- Adjusts workout intensity, exercise selection, and scheduling
- Implements a feedback loop: recommendation → user response → adaptation

References:
- EvoAgentX/Awesome-Self-Evolving-Agents
- RL-style reward shaping from user behavior signals
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone
import json


@dataclass
class PersonalizationProfile:
    user_id: str
    exercise_preferences: dict[str, float] = field(default_factory=dict)  # exercise_id -> preference score 0-1
    intensity_preference: float = 0.6  # 0 = very light, 1 = very heavy
    volume_preference: float = 0.5  # 0 = low volume, 1 = high volume
    workout_duration_preference: float = 45  # minutes
    rest_day_preference: float = 2  # rest days per week
    time_of_day_preference: str = "any"  # morning, afternoon, evening, any
    equipment_preferences: list[str] = field(default_factory=list)
    avoided_exercises: list[str] = field(default_factory=list)
    preferred_movement_patterns: list[str] = field(default_factory=list)
    accepted_workouts: int = 0
    rejected_workouts: int = 0
    total_feedback_signals: int = 0
    avg_session_rpe: float = 7.0
    avg_workout_duration: float = 45.0
    avg_rest_between_sets: float = 90.0
    last_updated: str = ""
    # Learning rate: how fast we adapt (decreases with more data)
    _learning_rate: float = 0.15

    @property
    def confidence(self) -> float:
        """How confident we are in this profile (0-1)."""
        signals = min(self.total_feedback_signals, 100)
        return round(signals / 100, 2)

    @property
    def acceptance_rate(self) -> float:
        total = self.accepted_workouts + self.rejected_workouts
        return self.accepted_workouts / total if total > 0 else 0.5


# In-memory profiles
_profiles: dict[str, PersonalizationProfile] = {}


def get_profile(user_id: str) -> PersonalizationProfile:
    """Get or create a personalization profile."""
    if user_id not in _profiles:
        _profiles[user_id] = PersonalizationProfile(user_id=user_id)
    return _profiles[user_id]


def _adapt(profile: PersonalizationProfile, signal: str, value: float):
    """Adapt profile based on a feedback signal."""
    lr = profile._learning_rate
    # Decrease learning rate as we get more data
    profile._learning_rate = max(0.03, lr * 0.99)

    if signal == "workout_accepted":
        profile.accepted_workouts += 1
        profile.intensity_preference = min(1.0, profile.intensity_preference + lr * 0.1)
    elif signal == "workout_rejected":
        profile.rejected_workouts += 1
        profile.intensity_preference = max(0.0, profile.intensity_preference - lr * 0.2)
    elif signal == "session_rpe_high":
        # User rated session hard → reduce intensity next time
        profile.intensity_preference = max(0.0, profile.intensity_preference - lr * 0.1)
    elif signal == "session_rpe_low":
        # User rated session easy → increase intensity
        profile.intensity_preference = min(1.0, profile.intensity_preference + lr * 0.05)
    elif signal == "exercise_loved":
        profile.exercise_preferences[value] = min(1.0, profile.exercise_preferences.get(value, 0.5) + lr * 0.2)
    elif signal == "exercise_disliked":
        profile.exercise_preferences[value] = max(0.0, profile.exercise_preferences.get(value, 0.5) - lr * 0.3)
    elif signal == "workout_duration_short":
        profile.workout_duration_preference = max(15, profile.workout_duration_preference - 5)
    elif signal == "workout_duration_long":
        profile.workout_duration_preference = min(120, profile.workout_duration_preference + 5)

    profile.total_feedback_signals += 1
    profile.last_updated = datetime.now(timezone.utc).isoformat()


def record_workout_accepted(user_id: str, exercise_ids: list[str]):
    """Record that user accepted a workout."""
    profile = get_profile(user_id)
    _adapt(profile, "workout_accepted", 0)
    for eid in exercise_ids:
        _adapt(profile, "exercise_loved", eid)


def record_workout_rejected(user_id: str, exercise_ids: list[str]):
    """Record that user rejected a workout."""
    profile = get_profile(user_id)
    _adapt(profile, "workout_rejected", 0)
    for eid in exercise_ids:
        _adapt(profile, "exercise_disliked", eid)


def record_session_feedback(user_id: str, rpe: float, duration_minutes: float, exercise_ids: list[str]):
    """Record post-workout feedback."""
    profile = get_profile(user_id)
    profile.avg_session_rpe = (profile.avg_session_rpe * 0.8 + rpe * 0.2)
    profile.avg_workout_duration = (profile.avg_workout_duration * 0.8 + duration_minutes * 0.2)

    if rpe >= 9:
        _adapt(profile, "session_rpe_high", rpe)
    elif rpe <= 4:
        _adapt(profile, "session_rpe_low", rpe)

    if duration_minutes < 30:
        _adapt(profile, "workout_duration_short", duration_minutes)
    elif duration_minutes > 75:
        _adapt(profile, "workout_duration_long", duration_minutes)


def get_recommendations(user_id: str) -> dict:
    """Get personalized recommendations based on evolved profile."""
    profile = get_profile(user_id)

    # Determine recommended intensity
    if profile.intensity_preference > 0.7:
        intensity = "high"
        rpe_range = (7.5, 9)
    elif profile.intensity_preference > 0.4:
        intensity = "moderate"
        rpe_range = (6, 8)
    else:
        intensity = "light"
        rpe_range = (4, 6)

    # Top exercises
    top_exercises = sorted(
        profile.exercise_preferences.items(),
        key=lambda x: x[1], reverse=True
    )[:5]

    # Avoided exercises to exclude
    avoided = profile.avoided_exercises[:]

    # Recommended workout structure
    if profile.confidence < 0.3:
        source = "default"
        note = "Still learning your preferences. Rate your workouts to improve!"
    else:
        source = "personalized"
        note = f"Based on {profile.total_feedback_signals} feedback signals ({profile.confidence:.0%} confidence)"

    return {
        "intensity": intensity,
        "rpe_range": rpe_range,
        "recommended_duration_minutes": round(profile.workout_duration_preference),
        "top_exercises": [{"exercise_id": eid, "preference": round(score, 2)} for eid, score in top_exercises],
        "avoided_exercises": avoided,
        "acceptance_rate": round(profile.acceptance_rate * 100, 1),
        "confidence": profile.confidence,
        "source": source,
        "note": note,
        "total_signals": profile.total_feedback_signals,
    }


def get_profile_stats(user_id: str) -> dict:
    """Get profile statistics."""
    profile = get_profile(user_id)
    return {
        "user_id": user_id,
        "intensity_preference": round(profile.intensity_preference, 2),
        "volume_preference": round(profile.volume_preference, 2),
        "workout_duration_preference": round(profile.workout_duration_preference),
        "accepted_workouts": profile.accepted_workouts,
        "rejected_workouts": profile.rejected_workouts,
        "acceptance_rate": round(profile.acceptance_rate * 100, 1),
        "total_feedback_signals": profile.total_feedback_signals,
        "avg_session_rpe": round(profile.avg_session_rpe, 1),
        "avg_workout_duration": round(profile.avg_workout_duration, 1),
        "exercise_count": len(profile.exercise_preferences),
        "confidence": profile.confidence,
        "learning_rate": round(profile._learning_rate, 4),
        "last_updated": profile.last_updated,
    }

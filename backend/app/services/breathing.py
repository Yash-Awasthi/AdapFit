"""Guided breathing exercise engine.

Provides structured breathing patterns for:
- Recovery optimization (box breathing, 4-7-8)
- Pre-workout activation (energizing breath)
- Post-workout cooldown (calming breath)
- Stress relief (extended exhale)
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class BreathingPhase:
    name: str
    duration_seconds: int
    instruction: str


@dataclass
class BreathingExercise:
    id: str
    name: str
    description: str
    category: str  # recovery, energizing, calming, stress
    phases: list[BreathingPhase]
    total_duration_seconds: int
    repeat_cycles: int
    benefits: list[str]


BREATHING_EXERCISES: list[BreathingExercise] = [
    BreathingExercise(
        id="box_breathing",
        name="Box Breathing",
        description="Equal inhale, hold, exhale, hold pattern. Used by Navy SEALs for focus and calm.",
        category="recovery",
        phases=[
            BreathingPhase("Inhale", 4, "Breathe in through your nose"),
            BreathingPhase("Hold", 4, "Hold your breath"),
            BreathingPhase("Exhale", 4, "Breathe out through your mouth"),
            BreathingPhase("Hold", 4, "Hold empty"),
        ],
        total_duration_seconds=64,
        repeat_cycles=4,
        benefits=["Reduces cortisol", "Improves focus", "Regulates heart rate"],
    ),
    BreathingExercise(
        id="4_7_8",
        name="4-7-8 Relaxing Breath",
        description="Dr. Andrew Weil's technique for deep relaxation and sleep preparation.",
        category="calming",
        phases=[
            BreathingPhase("Inhale", 4, "Breathe in quietly through your nose"),
            BreathingPhase("Hold", 7, "Hold your breath"),
            BreathingPhase("Exhale", 8, "Exhale completely through mouth, making a whoosh"),
        ],
        total_duration_seconds=76,
        repeat_cycles=4,
        benefits=["Promotes sleep", "Reduces anxiety", "Lowers blood pressure"],
    ),
    BreathingExercise(
        id="energizing_breath",
        name="Energizing Breath",
        description="Quick, rhythmic breathing to activate the sympathetic nervous system before training.",
        category="energizing",
        phases=[
            BreathingPhase("Inhale", 2, "Quick, sharp inhale through nose"),
            BreathingPhase("Exhale", 2, "Forceful exhale through mouth"),
        ],
        total_duration_seconds=40,
        repeat_cycles=10,
        benefits=["Increases alertness", "Boosts energy", "Primes nervous system"],
    ),
    BreathingExercise(
        id="extended_exhale",
        name="Extended Exhale",
        description="Longer exhale than inhale activates parasympathetic nervous system for stress relief.",
        category="stress",
        phases=[
            BreathingPhase("Inhale", 4, "Breathe in through your nose"),
            BreathingPhase("Exhale", 8, "Slowly exhale through pursed lips"),
        ],
        total_duration_seconds=96,
        repeat_cycles=6,
        benefits=["Activates parasympathetic", "Reduces stress", "Lowers heart rate"],
    ),
    BreathingExercise(
        id="coherent_breathing",
        name="Coherent Breathing",
        description="5.5 breaths per minute for heart rate variability optimization.",
        category="recovery",
        phases=[
            BreathingPhase("Inhale", 5.5, "Breathe in smoothly"),
            BreathingPhase("Exhale", 5.5, "Breathe out smoothly"),
        ],
        total_duration_seconds=330,
        repeat_cycles=10,
        benefits=["Optimizes HRV", "Balances autonomic nervous system", "Improves coherence"],
    ),
    BreathingExercise(
        id="pre_sleep",
        name="Pre-Sleep Wind Down",
        description="Gentle pattern to transition into sleep mode.",
        category="calming",
        phases=[
            BreathingPhase("Inhale", 4, "Gentle breath in"),
            BreathingPhase("Hold", 2, "Brief pause"),
            BreathingPhase("Exhale", 6, "Long, slow release"),
            BreathingPhase("Hold", 2, "Rest"),
        ],
        total_duration_seconds=120,
        repeat_cycles=6,
        benefits=["Prepares for sleep", "Releases tension", "Slows mind"],
    ),
]


def get_exercises(category: str | None = None) -> list[dict]:
    """Get breathing exercises, optionally filtered by category."""
    exercises = BREATHING_EXERCISES
    if category:
        exercises = [e for e in exercises if e.category == category]
    return [
        {
            "id": e.id,
            "name": e.name,
            "description": e.description,
            "category": e.category,
            "total_duration_seconds": e.total_duration_seconds,
            "repeat_cycles": e.repeat_cycles,
            "benefits": e.benefits,
            "phase_count": len(e.phases),
        }
        for e in exercises
    ]


def get_exercise_detail(exercise_id: str) -> dict | None:
    """Get full details of a specific breathing exercise."""
    exercise = next((e for e in BREATHING_EXERCISES if e.id == exercise_id), None)
    if not exercise:
        return None
    return {
        "id": exercise.id,
        "name": exercise.name,
        "description": exercise.description,
        "category": exercise.category,
        "total_duration_seconds": exercise.total_duration_seconds,
        "repeat_cycles": exercise.repeat_cycles,
        "benefits": exercise.benefits,
        "phases": [
            {"name": p.name, "duration_seconds": p.duration_seconds, "instruction": p.instruction}
            for p in exercise.phases
        ],
        "total_phases": len(exercise.phases),
    }


breathing_engine = __import__(__name__)

"""
Core Training Assessment Service — Pull-up tracking, grip analysis, progression
Inspired by athlete-core: pull-up system, wellness scoring, energy level calculation

Patterns extracted:
- Pull-up tracking (grip types, volume, 1RM estimation via Epley)
- Personal best detection
- Progression rate calculation
- Grip distribution analysis
- Wellness composite score (mental + mood + energy + stress)
- Energy level calculation (sleep + wellness + workouts)
- Breathing exercise configurations
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class GripType(Enum):
    OVERHAND = "overhand"
    UNDERHAND = "underhand"
    NEUTRAL = "neutral"
    WIDE = "wide"
    CLOSE = "close"
    ARCHER = "archer"
    TYPEWRITER = "typewriter"
    MIXED = "mixed"


@dataclass
class PullupRecord:
    date: str
    sets: int
    max_reps: int
    total_reps: int
    grip_type: GripType = GripType.OVERHAND
    body_weight_kg: float = 70.0
    added_weight_kg: float = 0.0
    notes: str = ""


@dataclass
class PullupSession:
    records: List[PullupRecord]
    date: str = ""


@dataclass
class ProgressionRate:
    reps_gained_per_week: float
    total_gain: int
    weeks_tracked: int
    trend: str  # "improving", "plateauing", "declining"


@dataclass
class WellnessEntry:
    mood: float = 5.0  # 1-10
    energy: float = 5.0  # 1-10
    stress: float = 5.0  # 1-10 (10 = max stress)
    sleep_hours: float = 7.0
    relationships: float = 5.0
    stress_management: float = 5.0
    self_confidence: float = 5.0
    emotional_balance: float = 5.0
    mental_resilience: float = 5.0
    focus_clarity: float = 5.0


@dataclass
class WellnessResult:
    wellness_score: float  # 1-10
    energy_level: float  # 1-10
    mental_score: float
    mood_contribution: float
    energy_contribution: float
    stress_contribution: float
    recommendations: List[str]


@dataclass
class BreathingExercise:
    name: str
    description: str
    inhale_seconds: float
    hold_seconds: float
    exhale_seconds: float
    hold_out_seconds: float
    cycles: int
    bpm: float


GRIP_DESCRIPTIONS = {
    GripType.OVERHAND: "Standard pronated grip — targets lats and upper back",
    GripType.UNDERHAND: "Chin-up grip — more bicep involvement",
    GripType.NEUTRAL: "Parallel / hammer grip — easier on shoulders",
    GripType.WIDE: "Wide pronated — maximises lat stretch",
    GripType.CLOSE: "Close grip — increases tricep and inner-lat work",
    GripType.ARCHER: "One arm bears most load — builds toward one-arm pull-up",
    GripType.TYPEWRITER: "Lateral shift at the top — advanced lat isolation",
    GripType.MIXED: "One overhand, one underhand — grip strength focus",
}


class CoreTrainingAnalyzer:
    """Pure function core training assessment and pull-up tracking."""

    # ── Pull-Up Tracking ──────────────────────────────────────────────────

    @staticmethod
    def validate_record(record: PullupRecord) -> Tuple[bool, List[str]]:
        errors = []
        if record.sets < 1:
            errors.append("Sets must be at least 1")
        if record.max_reps < 1:
            errors.append("Max reps must be at least 1")
        if record.total_reps < 1:
            errors.append("Total reps must be at least 1")
        if record.total_reps < record.max_reps:
            errors.append("Total reps cannot be less than max reps")
        return len(errors) == 0, errors

    @staticmethod
    def is_new_personal_best(new_max: int, previous: List[PullupRecord]) -> bool:
        if not previous:
            return True
        return new_max > max(r.max_reps for r in previous)

    @staticmethod
    def total_volume(records: List[PullupRecord]) -> int:
        return sum(r.total_reps for r in records)

    @staticmethod
    def avg_reps_per_set(record: PullupRecord) -> float:
        if record.sets <= 0:
            return 0.0
        return round(record.total_reps / record.sets, 1)

    @staticmethod
    def total_sets(records: List[PullupRecord]) -> int:
        return sum(r.sets for r in records)

    @staticmethod
    def volume_in_range(records: List[PullupRecord],
                       start_date: str, end_date: str) -> int:
        return sum(r.total_reps for r in records
                  if start_date <= r.date <= end_date)

    @staticmethod
    def estimate_1rm(max_reps: int) -> float:
        """Epley formula: 1RM ≈ reps × (1 + reps / 30)."""
        if max_reps <= 0:
            return 0.0
        return round(max_reps * (1 + max_reps / 30), 1)

    @staticmethod
    def calculate_progression_rate(records: List[PullupRecord]) -> ProgressionRate:
        if len(records) < 2:
            return ProgressionRate(0.0, 0, 0, "insufficient_data")
        sorted_records = sorted(records, key=lambda r: r.date)
        first_reps = sorted_records[0].max_reps
        last_reps = sorted_records[-1].max_reps
        total_gain = last_reps - first_reps
        # Estimate weeks from date range
        weeks = max(1, len(sorted_records) // 3)
        rate = total_gain / weeks if weeks > 0 else 0.0
        if rate > 0.1:
            trend = "improving"
        elif rate < -0.1:
            trend = "declining"
        else:
            trend = "plateauing"
        return ProgressionRate(
            reps_gained_per_week=round(rate, 2),
            total_gain=total_gain,
            weeks_tracked=weeks,
            trend=trend,
        )

    @staticmethod
    def grip_distribution(records: List[PullupRecord]) -> List[Dict]:
        counts: Dict[GripType, int] = {}
        for r in records:
            counts[r.grip_type] = counts.get(r.grip_type, 0) + r.total_reps
        total = sum(counts.values()) or 1
        return [
            {
                "grip": grip.value,
                "description": GRIP_DESCRIPTIONS.get(grip, ""),
                "total_reps": reps,
                "percent": round(reps / total * 100, 1),
            }
            for grip, reps in sorted(counts.items(), key=lambda x: -x[1])
        ]

    @classmethod
    def recommend_next_session(cls, current_max: int, goal: str = "strength") -> Dict:
        if goal == "strength":
            return {
                "target_sets": 5,
                "target_reps_per_set": max(1, int(current_max * 0.8)),
                "rest_seconds": 180,
                "focus": "Heavy sets close to max",
            }
        elif goal == "endurance":
            return {
                "target_sets": 4,
                "target_reps_per_set": max(1, int(current_max * 0.6)),
                "rest_seconds": 60,
                "focus": "High reps with short rest",
            }
        else:  # hypertrophy
            return {
                "target_sets": 4,
                "target_reps_per_set": max(1, int(current_max * 0.7)),
                "rest_seconds": 90,
                "focus": "Moderate reps, controlled tempo",
            }

    # ── Wellness Scoring ──────────────────────────────────────────────────

    @staticmethod
    def calculate_mental_score(entry: WellnessEntry) -> float:
        """Average of 6 mental wellness metrics."""
        metrics = [
            entry.relationships,
            entry.stress_management,
            entry.self_confidence,
            entry.emotional_balance,
            entry.mental_resilience,
            entry.focus_clarity,
        ]
        return round(sum(metrics) / len(metrics), 1)

    @classmethod
    def calculate_wellness_score(cls, entry: WellnessEntry) -> WellnessResult:
        """Composite wellness score: mental 40%, mood 20%, energy 20%, stress(inverted) 20%."""
        mental_avg = cls.calculate_mental_score(entry)
        stress_inverted = 11 - entry.stress  # 10 = no stress, 1 = max stress
        composite = (
            mental_avg * 0.4 +
            entry.mood * 0.2 +
            entry.energy * 0.2 +
            stress_inverted * 0.2
        )
        wellness_score = max(1.0, min(10.0, round(composite, 1)))
        recs = []
        if wellness_score < 4:
            recs.append("Wellness score is low — consider rest and self-care")
        if entry.stress > 7:
            recs.append("High stress detected — try breathing exercises")
        if entry.sleep_hours < 6:
            recs.append("Sleep debt — prioritize 7-9 hours tonight")
        if entry.mood < 4:
            recs.append("Low mood — consider social connection or activity")
        if not recs:
            recs.append("✅ Wellness looks good — keep it up")
        return WellnessResult(
            wellness_score=wellness_score,
            energy_level=entry.energy,
            mental_score=mental_avg,
            mood_contribution=round(entry.mood * 0.2, 1),
            energy_contribution=round(entry.energy * 0.2, 1),
            stress_contribution=round(stress_inverted * 0.2, 1),
            recommendations=recs,
        )

    @staticmethod
    def calculate_energy_level(entry: WellnessEntry,
                              recent_workout_count: int = 0,
                              recent_high_intensity: int = 0) -> float:
        """Energy level from sleep, mental wellness, and workout activity."""
        score = 5.0
        # Sleep (25%)
        if entry.sleep_hours >= 8:
            score += 1.5
        elif entry.sleep_hours >= 7:
            score += 1.0
        elif entry.sleep_hours >= 6:
            score += 0.5
        elif entry.sleep_hours < 5:
            score -= 2.0
        else:
            score -= 1.0
        # Mental wellness (30%)
        mental = (entry.relationships + entry.stress_management +
                 entry.self_confidence + entry.emotional_balance +
                 entry.mental_resilience + entry.focus_clarity) / 6
        score += ((mental - 5.5) / 4.5) * 1.5
        # Recent workouts (25%)
        if recent_workout_count >= 3:
            score += 1.0
        elif recent_workout_count == 2:
            score += 0.5
        elif recent_workout_count == 0:
            score -= 0.5
        if recent_high_intensity > 2:
            score -= 0.8
        return max(1.0, min(10.0, round(score, 1)))

    # ── Breathing Exercises ───────────────────────────────────────────────

    @staticmethod
    def get_breathing_exercises() -> List[BreathingExercise]:
        return [
            BreathingExercise(
                name="Box Breathing",
                description="Navy SEAL technique for focus and calm",
                inhale_seconds=4, hold_seconds=4, exhale_seconds=4,
                hold_out_seconds=4, cycles=10, bpm=6.0,
            ),
            BreathingExercise(
                name="4-7-8 Relaxing Breath",
                description="Dr. Weil's technique for sleep and anxiety",
                inhale_seconds=4, hold_seconds=7, exhale_seconds=8,
                hold_out_seconds=0, cycles=8, bpm=4.6,
            ),
            BreathingExercise(
                name="Wim Hof Method",
                description="Power breathing for energy and immune boost",
                inhale_seconds=2, hold_seconds=0, exhale_seconds=2,
                hold_out_seconds=0, cycles=30, bpm=15.0,
            ),
            BreathingExercise(
                name="Resonance Breathing",
                description="5.5 BPM coherence breathing for HRV optimization",
                inhale_seconds=5.5, hold_seconds=0, exhale_seconds=5.5,
                hold_out_seconds=0, cycles=10, bpm=5.5,
            ),
            BreathingExercise(
                name="Energizing Breath",
                description="Quick breathing for morning energy",
                inhale_seconds=1, hold_seconds=0, exhale_seconds=1,
                hold_out_seconds=0, cycles=20, bpm=30.0,
            ),
        ]

    @staticmethod
    def get_exercise_library() -> List[Dict]:
        """Core exercise library with muscle groups and difficulty."""
        return [
            {"name": "Pull-up", "muscle_group": "back", "difficulty": "intermediate", "type": "compound"},
            {"name": "Chin-up", "muscle_group": "back", "difficulty": "intermediate", "type": "compound"},
            {"name": "Push-up", "muscle_group": "chest", "difficulty": "beginner", "type": "compound"},
            {"name": "Squat", "muscle_group": "legs", "difficulty": "intermediate", "type": "compound"},
            {"name": "Plank", "muscle_group": "core", "difficulty": "beginner", "type": "isometric"},
            {"name": "Dead Hang", "muscle_group": "grip", "difficulty": "beginner", "type": "isometric"},
            {"name": "Hanging Leg Raise", "muscle_group": "core", "difficulty": "intermediate", "type": "compound"},
            {"name": "Dip", "muscle_group": "chest", "difficulty": "intermediate", "type": "compound"},
            {"name": "Lunges", "muscle_group": "legs", "difficulty": "beginner", "type": "compound"},
            {"name": "Burpee", "muscle_group": "full_body", "difficulty": "intermediate", "type": "compound"},
        ]

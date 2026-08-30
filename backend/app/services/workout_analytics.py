"""
Workout Analytics Service — Workout tracking, progress analytics, exercise library
Inspired by ai-workout-tracker: Sanity CMS schemas for workout/exercise data models

Patterns extracted:
- Workout data model (exercises with sets/reps/weight)
- Exercise library with difficulty levels
- Progress analytics (volume, intensity, consistency)
- Personal records tracking
- Workout streak calculation
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class Difficulty(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class WorkoutType(Enum):
    STRENGTH = "strength"
    CARDIO = "cardio"
    FLEXIBILITY = "flexibility"
    MIXED = "mixed"


@dataclass
class ExerciseSet:
    reps: int
    weight: float = 0.0
    weight_unit: str = "kg"
    rest_seconds: int = 90
    rpe: Optional[float] = None  # Rate of Perceived Exertion (1-10)
    notes: str = ""


@dataclass
class WorkoutExercise:
    exercise_name: str
    muscle_group: str
    sets: List[ExerciseSet]
    notes: str = ""


@dataclass
class WorkoutSession:
    session_id: str
    user_id: str
    date: float
    duration_seconds: int
    exercises: List[WorkoutExercise]
    workout_type: WorkoutType = WorkoutType.STRENGTH
    notes: str = ""


@dataclass
class PersonalRecord:
    exercise_name: str
    weight: float
    reps: int
    date: float
    estimated_1rm: float


@dataclass
class WorkoutStats:
    total_workouts: int
    total_duration_minutes: int
    total_sets: int
    total_reps: int
    total_volume_kg: float
    avg_duration_minutes: float
    avg_sets_per_workout: float
    workout_frequency_per_week: float
    consistency_score: float


@dataclass
class ProgressReport:
    period: str
    workout_count: int
    volume_change: float
    intensity_change: float
    personal_records: List[PersonalRecord]
    muscle_group_balance: Dict[str, int]
    recommendations: List[str]


class WorkoutAnalytics:
    """Pure function workout tracking and analytics."""

    # ── Volume & Intensity Calculations ───────────────────────────────────

    @staticmethod
    def calculate_set_volume(exercise_set: ExerciseSet) -> float:
        """Volume for a single set (reps × weight)."""
        return exercise_set.reps * exercise_set.weight

    @staticmethod
    def calculate_exercise_volume(exercise: WorkoutExercise) -> float:
        """Total volume for an exercise (sum of all sets)."""
        return sum(WorkoutAnalytics.calculate_set_volume(s) for s in exercise.sets)

    @staticmethod
    def calculate_workout_volume(session: WorkoutSession) -> float:
        """Total volume for a workout session."""
        return sum(WorkoutAnalytics.calculate_exercise_volume(e) for e in session.exercises)

    @staticmethod
    def calculate_volume_load(session: WorkoutSession) -> float:
        """Total reps × weight across all exercises."""
        total = 0.0
        for exercise in session.exercises:
            for s in exercise.sets:
                total += s.reps * s.weight
        return total

    @staticmethod
    def calculate_intensity(session: WorkoutSession) -> float:
        """Average intensity as percentage of estimated 1RM."""
        all_weights = []
        for exercise in session.exercises:
            for s in exercise.sets:
                if s.weight > 0:
                    all_weights.append(s.weight)
        if not all_weights:
            return 0.0
        # Simple intensity estimate based on weight distribution
        avg_weight = sum(all_weights) / len(all_weights)
        max_weight = max(all_weights)
        if max_weight == 0:
            return 0.0
        return round(avg_weight / max_weight * 100, 1)

    # ── Personal Records ──────────────────────────────────────────────────

    @staticmethod
    def estimate_1rm(weight: float, reps: int) -> float:
        """Estimate 1RM using Epley formula: weight × (1 + reps/30)."""
        if reps <= 0:
            return weight
        return round(weight * (1 + reps / 30), 1)

    @classmethod
    def find_personal_records(cls, sessions: List[WorkoutSession]) -> List[PersonalRecord]:
        """Find personal records for each exercise across all sessions."""
        best_by_exercise: Dict[str, PersonalRecord] = {}
        for session in sessions:
            for exercise in session.exercises:
                for s in exercise.sets:
                    if s.weight <= 0:
                        continue
                    est_1rm = cls.estimate_1rm(s.weight, s.reps)
                    existing = best_by_exercise.get(exercise.exercise_name)
                    if existing is None or est_1rm > existing.estimated_1rm:
                        best_by_exercise[exercise.exercise_name] = PersonalRecord(
                            exercise_name=exercise.exercise_name,
                            weight=s.weight,
                            reps=s.reps,
                            date=session.date,
                            estimated_1rm=est_1rm,
                        )
        return sorted(best_by_exercise.values(), key=lambda pr: -pr.estimated_1rm)

    # ── Workout Statistics ────────────────────────────────────────────────

    @classmethod
    def calculate_stats(cls, sessions: List[WorkoutSession]) -> WorkoutStats:
        """Calculate overall workout statistics."""
        if not sessions:
            return WorkoutStats(0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0)
        total_duration = sum(s.duration_seconds for s in sessions)
        total_sets = sum(len(e.sets) for s in sessions for e in s.exercises)
        total_reps = sum(
            sr.reps for s in sessions for e in s.exercises for sr in e.sets
        )
        total_volume = sum(cls.calculate_workout_volume(s) for s in sessions)
        # Frequency: workouts per week
        if len(sessions) >= 2:
            date_range = sessions[-1].date - sessions[0].date
            weeks = max(1, date_range / (7 * 24 * 3600))
            frequency = len(sessions) / weeks
        else:
            frequency = 0.0
        # Consistency: coefficient of variation of gaps between workouts
        if len(sessions) >= 3:
            dates = sorted(s.date for s in sessions)
            gaps = [dates[i + 1] - dates[i] for i in range(len(dates) - 1)]
            avg_gap = sum(gaps) / len(gaps)
            if avg_gap > 0:
                variance = sum((g - avg_gap) ** 2 for g in gaps) / len(gaps)
                cv = math.sqrt(variance) / avg_gap
                consistency = max(0, 1 - cv)
            else:
                consistency = 1.0
        else:
            consistency = 0.5
        return WorkoutStats(
            total_workouts=len(sessions),
            total_duration_minutes=round(total_duration / 60),
            total_sets=total_sets,
            total_reps=total_reps,
            total_volume_kg=round(total_volume, 1),
            avg_duration_minutes=round(total_duration / 60 / len(sessions), 1),
            avg_sets_per_workout=round(total_sets / len(sessions), 1),
            workout_frequency_per_week=round(frequency, 1),
            consistency_score=round(consistency, 2),
        )

    # ── Muscle Group Balance ──────────────────────────────────────────────

    @staticmethod
    def calculate_muscle_balance(sessions: List[WorkoutSession]) -> Dict[str, int]:
        """Count total sets per muscle group."""
        balance = defaultdict(int)
        for session in sessions:
            for exercise in session.exercises:
                balance[exercise.muscle_group] += len(exercise.sets)
        return dict(sorted(balance.items(), key=lambda x: -x[1]))

    @staticmethod
    def assess_muscle_balance(balance: Dict[str, int]) -> List[str]:
        """Identify muscle group imbalances."""
        recs = []
        if not balance:
            return ["No workout data available"]
        avg = sum(balance.values()) / len(balance)
        for muscle, sets in balance.items():
            if sets < avg * 0.5:
                recs.append(f"Undertrained: {muscle} ({sets} sets vs avg {avg:.0f})")
            elif sets > avg * 2:
                recs.append(f"Overtrained: {muscle} ({sets} sets vs avg {avg:.0f})")
        if not recs:
            recs.append("Muscle group balance looks good!")
        return recs

    # ── Progress Tracking ─────────────────────────────────────────────────

    @classmethod
    def compare_periods(cls, period1: List[WorkoutSession],
                        period2: List[WorkoutSession]) -> Dict:
        """Compare two training periods."""
        stats1 = cls.calculate_stats(period1)
        stats2 = cls.calculate_stats(period2)
        volume_change = 0.0
        if stats1.total_volume_kg > 0:
            volume_change = ((stats2.total_volume_kg - stats1.total_volume_kg)
                           / stats1.total_volume_kg * 100)
        return {
            "period1": {"workouts": stats1.total_workouts, "volume": stats1.total_volume_kg},
            "period2": {"workouts": stats2.total_workouts, "volume": stats2.total_volume_kg},
            "volume_change_pct": round(volume_change, 1),
            "frequency_change": round(stats2.workout_frequency_per_week - stats1.workout_frequency_per_week, 1),
        }

    # ── Streak Calculation ────────────────────────────────────────────────

    @staticmethod
    def calculate_streaks(sessions: List[WorkoutSession]) -> Dict:
        """Calculate current and best workout streaks."""
        if not sessions:
            return {"current_streak": 0, "best_streak": 0, "total_workout_days": 0}
        dates = sorted(set(
            int(s.date // (24 * 3600)) for s in sessions
        ))
        if not dates:
            return {"current_streak": 0, "best_streak": 0, "total_workout_days": 0}
        current_streak = 1
        best_streak = 1
        streak = 1
        for i in range(1, len(dates)):
            if dates[i] - dates[i - 1] <= 2:  # Allow 1 rest day
                streak += 1
                best_streak = max(best_streak, streak)
            else:
                streak = 1
        # Current streak: count from end
        current_streak = 1
        for i in range(len(dates) - 1, 0, -1):
            if dates[i] - dates[i - 1] <= 2:
                current_streak += 1
            else:
                break
        return {
            "current_streak": current_streak,
            "best_streak": best_streak,
            "total_workout_days": len(dates),
        }

    # ── Recommendations ───────────────────────────────────────────────────

    @classmethod
    def generate_recommendations(cls, sessions: List[WorkoutSession]) -> List[str]:
        """Generate workout recommendations based on history."""
        recs = []
        if not sessions:
            recs.append("Start logging workouts to get personalized recommendations")
            return recs
        stats = cls.calculate_stats(sessions)
        balance = cls.calculate_muscle_balance(sessions)
        if stats.workout_frequency_per_week < 3:
            recs.append("Try to work out at least 3 times per week for optimal results")
        if stats.consistency_score < 0.5:
            recs.append("Improve consistency — regular training beats sporadic intense sessions")
        balance_recs = cls.assess_muscle_balance(balance)
        recs.extend([r for r in balance_recs if "Undertrained" in r or "Overtrained" in r])
        if stats.avg_duration_minutes < 30:
            recs.append("Consider extending workouts to 45-60 minutes for better stimulus")
        if not recs:
            recs.append("Great job! Keep up the consistent training")
        return recs

    # ── Exercise Library ──────────────────────────────────────────────────

    @staticmethod
    def get_exercise_library() -> List[Dict]:
        """Return a curated exercise library."""
        return [
            {"name": "Barbell Squat", "muscle_group": "legs", "difficulty": "intermediate", "equipment": ["barbell", "squat_rack"]},
            {"name": "Bench Press", "muscle_group": "chest", "difficulty": "intermediate", "equipment": ["barbell", "bench"]},
            {"name": "Deadlift", "muscle_group": "back", "difficulty": "advanced", "equipment": ["barbell"]},
            {"name": "Pull-ups", "muscle_group": "back", "difficulty": "intermediate", "equipment": ["pull_up_bar"]},
            {"name": "Overhead Press", "muscle_group": "shoulders", "difficulty": "intermediate", "equipment": ["barbell"]},
            {"name": "Barbell Row", "muscle_group": "back", "difficulty": "intermediate", "equipment": ["barbell"]},
            {"name": "Lunges", "muscle_group": "legs", "difficulty": "beginner", "equipment": ["dumbbells"]},
            {"name": "Push-ups", "muscle_group": "chest", "difficulty": "beginner", "equipment": ["none"]},
            {"name": "Plank", "muscle_group": "core", "difficulty": "beginner", "equipment": ["none"]},
            {"name": "Dumbbell Curl", "muscle_group": "arms", "difficulty": "beginner", "equipment": ["dumbbells"]},
        ]

    @staticmethod
    def filter_exercises(exercises: List[Dict], difficulty: Optional[str] = None,
                         muscle_group: Optional[str] = None,
                         equipment: Optional[List[str]] = None) -> List[Dict]:
        """Filter exercises by criteria."""
        result = exercises
        if difficulty:
            result = [e for e in result if e["difficulty"] == difficulty]
        if muscle_group:
            result = [e for e in result if e["muscle_group"] == muscle_group]
        if equipment:
            result = [e for e in result
                     if any(eq in equipment for eq in e["equipment"]) or "none" in e["equipment"]]
        return result


# ── Additional Models for API Compatibility ──────────────────────────────

from pydantic import BaseModel as PydanticBaseModel


class VolumeTrend(PydanticBaseModel):
    muscle_group: str
    current_volume: float
    previous_volume: float
    change_pct: float
    direction: str  # "increasing", "decreasing", "stable"
    recommendation: str


class MuscleBalance(PydanticBaseModel):
    muscle_group: str
    set_count: int
    balance_score: float
    status: str  # "balanced", "overtrained", "undertrained"
    recommendation: str


class PeriodizationInsight(PydanticBaseModel):
    current_phase: str
    phase_duration_weeks: int
    fatigue_accumulation: float
    readiness_score: float
    recommendation: str


class TrendPrediction(PydanticBaseModel):
    metric: str
    current_value: float
    predicted_value: float
    confidence: float
    trend: str


class WorkoutAnalyticsResponse(PydanticBaseModel):
    summary: Dict
    volume_trends: List[VolumeTrend]
    muscle_balance: List[MuscleBalance]
    periodization_insights: PeriodizationInsight
    predictions: List[TrendPrediction]
    overall_score: float
    actionable_insights: List[str]


# ── Standalone Functions for API Endpoint ─────────────────────────────────


def analyze_volume_trends(workouts: List[Dict]) -> List[VolumeTrend]:
    """Analyze volume trends per muscle group from raw workout dicts."""
    muscle_volumes: Dict[str, List[float]] = {}
    for w in workouts:
        for ex in w.get("exercises", []):
            muscle = ex.get("target_muscle", "unknown")
            vol = sum(s.get("weight_kg", 0) * s.get("reps_completed", 0) for s in ex.get("sets", []))
            muscle_volumes.setdefault(muscle, []).append(vol)
    trends = []
    for muscle, vols in muscle_volumes.items():
        if len(vols) < 2:
            avg = vols[0] if vols else 0
            trends.append(VolumeTrend(
                muscle_group=muscle, current_volume=avg, previous_volume=avg,
                change_pct=0.0, direction="stable", recommendation="Keep consistent"
            ))
            continue
        mid = len(vols) // 2
        prev = sum(vols[:mid]) / max(mid, 1)
        curr = sum(vols[mid:]) / max(len(vols) - mid, 1)
        change = ((curr - prev) / prev * 100) if prev > 0 else 0
        direction = "increasing" if change > 10 else "decreasing" if change < -10 else "stable"
        rec = ("Good progression" if direction == "increasing" else
               "Consider reducing load" if direction == "decreasing" else "Maintain current volume")
        trends.append(VolumeTrend(
            muscle_group=muscle, current_volume=round(curr, 1), previous_volume=round(prev, 1),
            change_pct=round(change, 1), direction=direction, recommendation=rec,
        ))
    return trends


def analyze_muscle_balance(workouts: List[Dict]) -> List[MuscleBalance]:
    """Analyze muscle group balance from raw workout dicts."""
    counts: Dict[str, int] = {}
    for w in workouts:
        for ex in w.get("exercises", []):
            muscle = ex.get("target_muscle", "unknown")
            counts[muscle] = counts.get(muscle, 0) + len(ex.get("sets", []))
    if not counts:
        return []
    avg = sum(counts.values()) / len(counts)
    results = []
    for muscle, count in sorted(counts.items(), key=lambda x: -x[1]):
        score = count / avg * 100 if avg > 0 else 50
        status = "balanced" if 70 <= score <= 130 else ("overtrained" if score > 130 else "undertrained")
        rec = ("Well trained" if status == "balanced" else
               "Reduce volume" if status == "overtrained" else "Increase volume")
        results.append(MuscleBalance(
            muscle_group=muscle, set_count=count, balance_score=round(score, 1),
            status=status, recommendation=rec,
        ))
    return results


def generate_periodization_insight(workouts: List[Dict], logs: List[Dict]) -> PeriodizationInsight:
    """Generate periodization insight from workout and recovery data."""
    total_volume = sum(
        sum(s.get("weight_kg", 0) * s.get("reps_completed", 0) for ex in w.get("exercises", []) for s in ex.get("sets", []))
        for w in workouts
    )
    n = len(workouts) or 1
    avg_volume = total_volume / n
    fatigue = min(100, max(0, avg_volume / 100))
    readiness = max(0, 100 - fatigue)
    if fatigue > 70:
        phase = "overreaching"
        rec = "Consider a deload week to allow recovery"
    elif fatigue > 40:
        phase = "build"
        rec = "Good training stimulus — maintain progressive overload"
    else:
        phase = "accumulation"
        rec = "Gradually increase training volume"
    return PeriodizationInsight(
        current_phase=phase, phase_duration_weeks=max(1, n // 3),
        fatigue_accumulation=round(fatigue, 1), readiness_score=round(readiness, 1),
        recommendation=rec,
    )


def generate_predictions(workouts: List[Dict]) -> List[TrendPrediction]:
    """Generate simple trend predictions from workout history."""
    predictions = []
    volumes = []
    for w in workouts:
        vol = sum(
            s.get("weight_kg", 0) * s.get("reps_completed", 0)
            for ex in w.get("exercises", []) for s in ex.get("sets", [])
        )
        volumes.append(vol)
    if len(volumes) >= 3:
        avg_recent = sum(volumes[-3:]) / 3
        avg_older = sum(volumes[:-3]) / max(len(volumes) - 3, 1) if len(volumes) > 3 else avg_recent
        change = avg_recent - avg_older
        predictions.append(TrendPrediction(
            metric="volume_load", current_value=round(avg_recent, 1),
            predicted_value=round(avg_recent + change, 1), confidence=0.7,
            trend="increasing" if change > 0 else "decreasing",
        ))
    return predictions

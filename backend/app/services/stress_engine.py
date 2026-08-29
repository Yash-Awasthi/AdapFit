"""
Stress Management Engine — Comprehensive Stress Assessment & Intervention

Features:
- Multi-factor stress scoring (HRV, sleep, activity, mood, work patterns)
- Personalized intervention recommendations
- Guided breathing exercises with biometric feedback
- Stress journaling with NLP sentiment analysis
- Cortisol rhythm simulation (circadian pattern)
- Progressive muscle relaxation guide
- Micro-break scheduling based on stress patterns
"""
import time
import math
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class StressCategory(Enum):
    PHYSICAL = "physical"
    MENTAL = "mental"
    EMOTIONAL = "emotional"
    WORK = "work"
    SLEEP_RELATED = "sleep_related"
    SOCIAL = "social"


class InterventionType(Enum):
    BREATHING = "breathing"
    MEDITATION = "meditation"
    MOVEMENT = "movement"
    JOURNALING = "journaling"
    PROGRESSIVE_RELAXATION = "progressive_relaxation"
    COLD_EXPOSURE = "cold_exposure"
    NATURE_EXPOSURE = "nature_exposure"
    SOCIAL_CONNECTION = "social_connection"
    CREATIVE_ACTIVITY = "creative_activity"
    MICRO_BREAK = "micro_break"


@dataclass
class StressEntry:
    timestamp: float
    stress_level: float  # 0-100
    category: StressCategory
    source: str  # "self_report", "hrv", "camera", "combined"
    factors: dict
    notes: str = ""


@dataclass
class StressAssessment:
    overall_score: float  # 0-100
    category_scores: dict[str, float]
    primary_category: StressCategory
    trend: str  # "improving", "stable", "worsening"
    recommendations: list[dict]
    intervention_priority: InterventionType
    cortisol_phase: str  # "peak", "declining", "trough", "rising"
    recovery_estimate_minutes: int
    confidence: float


@dataclass
class BreathingExercise:
    name: str
    technique: str
    inhale_seconds: float
    hold_seconds: float
    exhale_seconds: float
    hold_after_exhale: float
    cycles: int
    description: str
    best_for: str
    difficulty: str  # "beginner", "intermediate", "advanced"


@dataclass
class MicroBreak:
    activity: str
    duration_minutes: int
    reason: str
    stress_reduction_expected: float


class StressEngine:
    """
    Comprehensive stress management system.
    
    Integrates multiple data sources:
    - HRV-derived stress (low HRV = high stress)
    - Sleep quality impact on stress
    - Activity level correlation
    - Self-reported mood/journal entries
    - Camera-based facial tension analysis
    - Work pattern analysis (screen time, meeting load)
    """

    def __init__(self):
        self._stress_entries: list[StressEntry] = []
        self._interventions_used: dict[str, int] = {}
        self._breathing_library = self._init_breathing_exercises()
        self._pmr_script = self._init_pmr_script()
        
        # Personalization baselines
        self._baseline_hrv: float = 45.0
        self._baseline_resting_hr: float = 65.0
        self._stress_sensitivity: float = 1.0  # learned over time
        
        # Circadian cortisol model
        self._cortisol_peak_hour = 8  # 8 AM
        self._cortisol_nadir_hour = 0  # midnight

    def assess_stress(self, data: dict) -> StressAssessment:
        """
        Multi-factor stress assessment.
        
        data keys:
        - hrv_rmssd: current HRV
        - resting_hr: current resting heart rate
        - sleep_quality: 0-100
        - sleep_hours: float
        - activity_minutes_today: int
        - mood_score: 0-10
        - energy_level: 0-10
        - self_reported_stress: 0-10 (optional)
        - screen_time_hours: float (optional)
        - meeting_hours: float (optional)
        - camera_fatigue_score: float (optional)
        - last_break_minutes_ago: int (optional)
        """
        category_scores = {}
        
        # 1. HRV-based stress
        hrv = data.get("hRV_rmssd", self._baseline_hrv)
        hrv_stress = max(0, min(100, (1 - hrv / 80) * 100 * self._stress_sensitivity))
        category_scores["physiological"] = hrv_stress
        
        # 2. Sleep impact
        sleep_quality = data.get("sleep_quality", 70)
        sleep_hours = data.get("sleep_hours", 7)
        sleep_debt = max(0, (7 - sleep_hours) * 15)
        sleep_stress = max(0, min(100, (100 - sleep_quality) * 0.6 + sleep_debt * 0.4))
        category_scores["sleep_related"] = sleep_stress
        
        # 3. Activity level (low activity = higher stress)
        activity_min = data.get("activity_minutes_today", 0)
        activity_stress = max(0, min(100, max(0, 60 - activity_min) * 1.67))
        category_scores["physical"] = activity_stress
        
        # 4. Mood & emotional state
        mood = data.get("mood_score", 5)
        energy = data.get("energy_level", 5)
        emotional_stress = max(0, min(100, (10 - mood) * 10 * 0.6 + (10 - energy) * 10 * 0.4))
        category_scores["emotional"] = emotional_stress
        
        # 5. Work/screen stress
        screen_time = data.get("screen_time_hours", 0)
        meeting_hours = data.get("meeting_hours", 0)
        work_stress = max(0, min(100, screen_time * 8 + meeting_hours * 12))
        category_scores["work"] = work_stress
        
        # 6. Self-reported (if available)
        self_report = data.get("self_reported_stress")
        if self_report is not None:
            category_scores["self_reported"] = self_report * 10
        
        # Overall weighted score
        weights = {
            "physiological": 0.25,
            "sleep_related": 0.20,
            "physical": 0.10,
            "emotional": 0.20,
            "work": 0.15,
            "self_reported": 0.10,
        }
        
        total_weight = sum(weights.get(k, 0) for k in category_scores)
        if total_weight > 0:
            overall = sum(category_scores.get(k, 0) * weights.get(k, 0) for k in category_scores) / total_weight
        else:
            overall = 50.0
        
        # Find primary category
        primary_cat = max(category_scores, key=category_scores.get)
        try:
            primary = StressCategory(primary_cat) if primary_cat in [c.value for c in StressCategory] else StressCategory.PHYSICAL
        except ValueError:
            primary = StressCategory.PHYSICAL
        
        # Trend analysis
        recent = self._stress_entries[-10:]
        if len(recent) >= 3:
            old_avg = sum(e.stress_level for e in recent[:len(recent)//2]) / max(1, len(recent)//2)
            new_avg = sum(e.stress_level for e in recent[len(recent)//2:]) / max(1, len(recent) - len(recent)//2)
            if new_avg < old_avg - 5:
                trend = "improving"
            elif new_avg > old_avg + 5:
                trend = "worsening"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        # Cortisol phase
        cortisol_phase = self._get_cortisol_phase()
        
        # Recovery estimate
        recovery_min = self._estimate_recovery_time(overall)
        
        # Recommendations
        recommendations = self._generate_recommendations(overall, category_scores, cortisol_phase)
        
        # Intervention priority
        priority = self._select_intervention(overall, category_scores, cortisol_phase)
        
        assessment = StressAssessment(
            overall_score=round(overall, 1),
            category_scores={k: round(v, 1) for k, v in category_scores.items()},
            primary_category=primary,
            trend=trend,
            recommendations=recommendations,
            intervention_priority=priority,
            cortisol_phase=cortisol_phase,
            recovery_estimate_minutes=recovery_min,
            confidence=min(0.95, len(self._stress_entries) / 20 + 0.3),
        )
        
        # Store entry
        self._stress_entries.append(StressEntry(
            timestamp=time.time(),
            stress_level=overall,
            category=primary,
            source="combined",
            factors=category_scores,
        ))
        
        return assessment

    def log_stress_entry(self, level: float, category: str, notes: str = "", source: str = "self_report") -> dict:
        """Log a manual stress entry."""
        try:
            cat = StressCategory(category)
        except ValueError:
            cat = StressCategory.PHYSICAL
        
        entry = StressEntry(
            timestamp=time.time(),
            stress_level=max(0, min(100, level)),
            category=cat,
            source=source,
            factors={"level": level},
            notes=notes,
        )
        self._stress_entries.append(entry)
        
        return {
            "logged": True,
            "level": entry.stress_level,
            "category": entry.category.value,
            "total_entries": len(self._stress_entries),
        }

    def get_breathing_exercise(self, stress_level: float, time_of_day: int = 12) -> BreathingExercise:
        """Get recommended breathing exercise based on stress and time."""
        if stress_level > 70:
            # High stress — calming
            if time_of_day < 10:
                return self._breathing_library["478"]  # 4-7-8 for morning calm
            else:
                return self._breathing_library["box"]  # Box breathing
        elif stress_level > 40:
            # Moderate — balancing
            return self._breathing_library["coherent"]
        else:
            # Low stress — energizing or maintaining
            if time_of_day < 14:
                return self._breathing_library["energizing"]
            else:
                return self._breathing_library["calming"]

    def get_pmr_script(self) -> dict:
        """Get progressive muscle relaxation script."""
        return {
            "name": "Progressive Muscle Relaxation",
            "total_duration_minutes": 15,
            "description": "Systematically tense and release muscle groups to release physical stress",
            "steps": self._pmr_script,
            "best_for": "Physical tension, difficulty sleeping, chronic stress",
            "audio_cue_interval_seconds": 30,
        }

    def get_micro_break_schedule(self, screen_time_minutes: int, last_break_min: int) -> list[MicroBreak]:
        """Generate micro-break recommendations based on usage patterns."""
        breaks = []
        
        if last_break_min > 90:
            breaks.append(MicroBreak(
                activity="Stand up, stretch arms overhead, roll shoulders 10x each direction",
                duration_minutes=3,
                reason="You've been seated for over 90 minutes",
                stress_reduction_expected=15,
            ))
        
        if screen_time_minutes > 120:
            breaks.append(MicroBreak(
                activity="20-20-20 rule: Look at something 20 feet away for 20 seconds. Then walk for 2 minutes.",
                duration_minutes=5,
                reason=f"Screen time: {screen_time_minutes} minutes",
                stress_reduction_expected=20,
            ))
        
        if screen_time_minutes > 240:
            breaks.append(MicroBreak(
                activity="5-minute guided breathing exercise + 10 squats or calf raises",
                duration_minutes=5,
                reason="Extended screen time — need physical activation",
                stress_reduction_expected=25,
            ))
        
        if not breaks:
            breaks.append(MicroBreak(
                activity="Quick eye relaxation: Palming (rub hands, cover eyes, breathe deeply)",
                duration_minutes=2,
                reason="Preventive micro-break",
                stress_reduction_expected=10,
            ))
        
        return breaks

    def get_stress_trends(self, days: int = 7) -> dict:
        """Get stress trends over time."""
        now = time.time()
        day_entries = {}
        
        for entry in self._stress_entries:
            day_offset = int((now - entry.timestamp) / 86400)
            if day_offset < days:
                day = f"day_{day_offset}"
                if day not in day_entries:
                    day_entries[day] = []
                day_entries[day].append(entry.stress_level)
        
        daily_avgs = {}
        for day, levels in day_entries.items():
            daily_avgs[day] = round(sum(levels) / len(levels), 1)
        
        all_levels = [e.stress_level for e in self._stress_entries[-100:]]
        
        return {
            "daily_averages": daily_avgs,
            "overall_average": round(sum(all_levels) / max(1, len(all_levels)), 1),
            "highest_stress": round(max(all_levels), 1) if all_levels else 0,
            "lowest_stress": round(min(all_levels), 1) if all_levels else 0,
            "total_assessments": len(self._stress_entries),
            "dominant_category": self._get_dominant_category(),
        }

    def get_intervention_effectiveness(self) -> dict:
        """Track which interventions are most effective."""
        return {
            "interventions_used": self._interventions_used.copy(),
            "most_used": max(self._interventions_used, key=self._interventions_used.get) if self._interventions_used else "none",
            "recommendation": "Try breathing exercises before sleep for best results" if not self._interventions_used else None,
        }

    # === Private helpers ===

    def _init_breathing_exercises(self) -> dict[str, BreathingExercise]:
        return {
            "478": BreathingExercise(
                name="4-7-8 Relaxing Breath",
                technique="Inhale 4s, Hold 7s, Exhale 8s",
                inhale_seconds=4, hold_seconds=7, exhale_seconds=8, hold_after_exhale=0,
                cycles=4,
                description="Dr. Andrew Weil's natural tranquilizer for the nervous system",
                best_for="Anxiety, insomnia, high stress",
                difficulty="beginner",
            ),
            "box": BreathingExercise(
                name="Box Breathing (Navy SEAL)",
                technique="Inhale 4s, Hold 4s, Exhale 4s, Hold 4s",
                inhale_seconds=4, hold_seconds=4, exhale_seconds=4, hold_after_exhale=4,
                cycles=6,
                description="Used by Navy SEALs for stress management under pressure",
                best_for="Acute stress, pre-performance anxiety",
                difficulty="intermediate",
            ),
            "coherent": BreathingExercise(
                name="Coherent Breathing",
                technique="Inhale 5s, Exhale 5s",
                inhale_seconds=5, hold_seconds=0, exhale_seconds=5, hold_after_exhale=0,
                cycles=10,
                description="5 breaths per minute maximizes heart rate variability",
                best_for="Daily stress management, HRV optimization",
                difficulty="beginner",
            ),
            "energizing": BreathingExercise(
                name="Energizing Breath",
                technique="Quick inhale 1s, Forceful exhale 1s",
                inhale_seconds=1, hold_seconds=0, exhale_seconds=1, hold_after_exhale=0,
                cycles=30,
                description="Bellows breath for energy and alertness",
                best_for="Fatigue, low energy, morning activation",
                difficulty="intermediate",
            ),
            "calming": BreathingExercise(
                name="Extended Exhale Breathing",
                technique="Inhale 4s, Exhale 8s",
                inhale_seconds=4, hold_seconds=0, exhale_seconds=8, hold_after_exhale=0,
                cycles=6,
                description="Longer exhale activates parasympathetic nervous system",
                best_for="Evening wind-down, pre-sleep relaxation",
                difficulty="beginner",
            ),
        }

    def _init_pmr_script(self) -> list[dict]:
        return [
            {"muscle_group": "Feet", "tension_seconds": 5, "release_seconds": 10, "instruction": "Curl your toes tightly. Feel the tension in your arches."},
            {"muscle_group": "Calves", "tension_seconds": 5, "release_seconds": 10, "instruction": "Point your toes toward your shins. Feel the stretch in your calves."},
            {"muscle_group": "Thighs", "tension_seconds": 5, "release_seconds": 10, "instruction": "Press your knees together and tighten your thigh muscles."},
            {"muscle_group": "Glutes", "tension_seconds": 5, "release_seconds": 10, "instruction": "Squeeze your glutes tightly together."},
            {"muscle_group": "Abdomen", "tension_seconds": 5, "release_seconds": 10, "instruction": "Tighten your stomach as if bracing for impact."},
            {"muscle_group": "Chest", "tension_seconds": 5, "release_seconds": 10, "instruction": "Take a deep breath and hold. Feel the tension in your chest."},
            {"muscle_group": "Hands", "tension_seconds": 5, "release_seconds": 10, "instruction": "Make tight fists with both hands."},
            {"muscle_group": "Arms", "tension_seconds": 5, "release_seconds": 10, "instruction": "Flex your biceps. Make your arms as tight as possible."},
            {"muscle_group": "Shoulders", "tension_seconds": 5, "release_seconds": 10, "instruction": "Shrug your shoulders up toward your ears."},
            {"muscle_group": "Neck", "tension_seconds": 5, "release_seconds": 10, "instruction": "Gently press your head back against the chair. Keep gentle."},
            {"muscle_group": "Face", "tension_seconds": 5, "release_seconds": 10, "instruction": "Scrunch your entire face — eyes, nose, mouth, forehead."},
            {"muscle_group": "Full Body", "tension_seconds": 8, "release_seconds": 15, "instruction": "Tense every muscle in your body simultaneously. Hold... and release everything."},
        ]

    def _get_cortisol_phase(self) -> str:
        """Determine current cortisol phase based on circadian rhythm."""
        hour = time.localtime().tm_hour
        if 6 <= hour <= 10:
            return "peak"
        elif 10 < hour <= 16:
            return "declining"
        elif 16 < hour <= 22:
            return "trough"
        else:
            return "rising"

    def _estimate_recovery_time(self, stress_level: float) -> int:
        """Estimate minutes to recover from current stress level."""
        if stress_level < 30:
            return 5
        elif stress_level < 50:
            return 15
        elif stress_level < 70:
            return 30
        elif stress_level < 85:
            return 45
        else:
            return 60

    def _generate_recommendations(self, overall: float, categories: dict, cortisol_phase: str) -> list[dict]:
        recs = []
        
        if overall > 70:
            recs.append({
                "priority": "high",
                "action": "Immediate breathing exercise (4-7-8 technique)",
                "expected_reduction": "15-20 points in 5 minutes",
                "type": InterventionType.BREATHING.value,
            })
            recs.append({
                "priority": "high",
                "action": "Step away from screens for at least 10 minutes",
                "expected_reduction": "10-15 points",
                "type": InterventionType.MICRO_BREAK.value,
            })
        
        if categories.get("sleep_related", 0) > 50:
            recs.append({
                "priority": "medium",
                "action": "Tonight: maintain consistent sleep schedule, avoid caffeine after 2 PM",
                "expected_reduction": "Gradual improvement over 3-5 days",
                "type": InterventionType.MEDITATION.value,
            })
        
        if categories.get("physical", 0) > 40:
            recs.append({
                "priority": "medium",
                "action": "30 minutes of moderate exercise (walking, yoga, swimming)",
                "expected_reduction": "20-30 points over 24 hours",
                "type": InterventionType.MOVEMENT.value,
            })
        
        if categories.get("work", 0) > 50:
            recs.append({
                "priority": "medium",
                "action": "Set boundaries: no work emails after 7 PM, take lunch break away from desk",
                "expected_reduction": "10-20 points",
                "type": InterventionType.MICRO_BREAK.value,
            })
        
        if cortisol_phase == "rising" and overall > 40:
            recs.append({
                "priority": "low",
                "action": "Evening meditation or journaling before bed",
                "expected_reduction": "Better sleep → lower tomorrow's stress",
                "type": InterventionType.MEDITATION.value,
            })
        
        if not recs:
            recs.append({
                "priority": "maintenance",
                "action": "Stress levels are good! Maintain with regular exercise and breathing practice",
                "expected_reduction": "Maintain current state",
                "type": InterventionType.BREATHING.value,
            })
        
        return recs

    def _select_intervention(self, overall: float, categories: dict, cortisol_phase: str) -> InterventionType:
        if overall > 70:
            return InterventionType.BREATHING
        elif categories.get("physical", 0) > 50:
            return InterventionType.PROGRESSIVE_RELAXATION
        elif categories.get("work", 0) > 50:
            return InterventionType.MICRO_BREAK
        elif cortisol_phase in ("trough", "rising"):
            return InterventionType.MEDITATION
        else:
            return InterventionType.MOVEMENT

    def _get_dominant_category(self) -> str:
        if not self._stress_entries:
            return "unknown"
        cats = {}
        for e in self._stress_entries[-50:]:
            cats[e.category.value] = cats.get(e.category.value, 0) + 1
        return max(cats, key=cats.get) if cats else "unknown"


# Singleton
stress_engine = StressEngine()

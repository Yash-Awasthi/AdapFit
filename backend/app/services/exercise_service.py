import json
import os
from typing import List, Optional, Dict, Any
from app.models.schemas import ExerciseItem, PrescribedExercise, ReadinessState, WarmupCooldownItem

class ExerciseService:
    def __init__(self):
        data_path = os.path.join(os.path.dirname(__file__), "..", "data", "exercises.json")
        with open(data_path, "r", encoding="utf-8") as f:
            raw_exercises = json.load(f)
        self.exercises: List[ExerciseItem] = [ExerciseItem(**ex) for ex in raw_exercises]
        self.exercise_map: Dict[str, ExerciseItem] = {ex.id: ex for ex in self.exercises}

    def get_all(self) -> List[ExerciseItem]:
        return self.exercises

    def get_by_id(self, exercise_id: str) -> Optional[ExerciseItem]:
        return self.exercise_map.get(exercise_id)

    def filter_exercises(
        self,
        equipment_list: Optional[List[str]] = None,
        target_muscles: Optional[List[str]] = None,
        exclude_muscles: Optional[List[str]] = None,
        max_axial_load: int = 5,
        category: Optional[str] = None
    ) -> List[ExerciseItem]:
        """
        Filters exercises based on user equipment, focus muscles, sore exclusions, and axial fatigue limit.
        """
        filtered = []
        exclude_set = set(m.lower() for m in (exclude_muscles or []))

        for ex in self.exercises:
            # Equipment check
            if equipment_list and ex.equipment not in equipment_list and "bodyweight" not in ex.equipment:
                continue
            
            # Category check
            if category and ex.category != category:
                continue

            # Axial loading threshold
            if ex.axial_loading_rating > max_axial_load:
                continue

            # Sore muscle exclusion
            primary_lower = [m.lower() for m in ex.primary_muscles]
            if any(m in exclude_set for m in primary_lower):
                continue

            # Target muscle inclusion
            if target_muscles:
                target_lower = [m.lower() for m in target_muscles]
                if not any(m in target_lower for m in primary_lower):
                    continue

            filtered.append(ex)

        return filtered

    def get_fallback_routine(
        self,
        readiness_state: ReadinessState,
        sore_muscles: Optional[List[str]] = None,
        equipment: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generates a 100% deterministic, rule-based workout fallback if LLM is offline.
        """
        eq = equipment or ["bodyweight", "dumbbells"]
        sore = sore_muscles or []

        if readiness_state == ReadinessState.OPTIMAL:
            title = "Adaptive Strength & Hypertrophy (Optimal Readiness)"
            rationale = "High readiness detected (Green). Full volume progressive overload session."
            max_axial = 5
            target_rpe = 8.5
            sets_count = 4
            reps = "8-10"
            rest = 120
            warmup = [
                WarmupCooldownItem(name="World's Greatest Stretch", sets=2, reps="6 per side"),
                WarmupCooldownItem(name="Cat-Cow Dynamic Mobility", duration_sec=60)
            ]
            cooldown = [
                WarmupCooldownItem(name="Foam Rolling SMR (Quads & Glutes)", duration_sec=120)
            ]
            candidates = self.filter_exercises(eq, max_axial_load=max_axial, exclude_muscles=sore, category="strength")
            
        elif readiness_state == ReadinessState.MODERATE:
            title = "Adaptive Maintenance & Hypertrophy"
            rationale = "Moderate readiness (Yellow). Standard training volume with RPE capped at 7.5."
            max_axial = 3
            target_rpe = 7.5
            sets_count = 3
            reps = "10-12"
            rest = 90
            warmup = [
                WarmupCooldownItem(name="Cat-Cow Dynamic Mobility", duration_sec=60)
            ]
            cooldown = [
                WarmupCooldownItem(name="Foam Rolling SMR (Quads & Glutes)", duration_sec=90)
            ]
            candidates = self.filter_exercises(eq, max_axial_load=max_axial, exclude_muscles=sore, category="strength")

        elif readiness_state == ReadinessState.REDUCED:
            title = "Adaptive Scaled-Back & Active Deload"
            rationale = "Low readiness (Orange). Volume reduced by 40%, lower axial load movements."
            max_axial = 2
            target_rpe = 6.0
            sets_count = 2
            reps = "12-15"
            rest = 60
            warmup = [
                WarmupCooldownItem(name="World's Greatest Stretch", duration_sec=90)
            ]
            cooldown = [
                WarmupCooldownItem(name="Foam Rolling SMR (Quads & Glutes)", duration_sec=120)
            ]
            candidates = self.filter_exercises(eq, max_axial_load=max_axial, exclude_muscles=sore)

        else: # DEPLETED (Red)
            title = "Active Recovery & Mobility Restoration"
            rationale = "Depleted state (Red). Complete rest from heavy resistance; prescribed gentle joint mobility and stretching."
            return {
                "title": title,
                "adaptation_rationale": rationale,
                "target_duration_minutes": 25,
                "warmup": [],
                "exercises": [
                    PrescribedExercise(
                        exercise_id="world-greatest-stretch",
                        name="World's Greatest Stretch",
                        target_muscle="Hips & Thoracic Spine",
                        sets=3,
                        target_reps="5 reps per side",
                        target_rpe=2.0,
                        rest_seconds=30,
                        gif_url=self.exercise_map["world-greatest-stretch"].gif_url,
                        notes="Slow continuous breathing through full range of motion."
                    ),
                    PrescribedExercise(
                        exercise_id="cat-cow-stretch",
                        name="Cat-Cow Dynamic Mobility",
                        target_muscle="Spine & Core",
                        sets=3,
                        target_reps="10 reps",
                        target_rpe=2.0,
                        rest_seconds=30,
                        gif_url=self.exercise_map["cat-cow-stretch"].gif_url,
                        notes="Mobilize vertebrae smoothly without forcing."
                    ),
                    PrescribedExercise(
                        exercise_id="foam-rolling-quads-glutes",
                        name="Foam Rolling SMR (Quads & Glutes)",
                        target_muscle="Quads & Glutes",
                        sets=2,
                        target_reps="60s per leg",
                        target_rpe=3.0,
                        rest_seconds=30,
                        gif_url=self.exercise_map["foam-rolling-quads-glutes"].gif_url,
                        notes="Pause on tender points."
                    ),
                    PrescribedExercise(
                        exercise_id="zone1-active-walk",
                        name="Zone 1 Active Recovery Walk",
                        target_muscle="Cardiorespiratory",
                        sets=1,
                        target_reps="15 minutes",
                        target_rpe=3.0,
                        rest_seconds=0,
                        gif_url=self.exercise_map["zone1-active-walk"].gif_url,
                        notes="Casual conversational pace."
                    )
                ],
                "cooldown": []
            }

        # Build exercises from candidates (pick up to 4 diverse exercises)
        selected_exercises: List[PrescribedExercise] = []
        used_muscles = set()

        for cand in candidates:
            prim = cand.primary_muscles[0] if cand.primary_muscles else "chest"
            if prim not in used_muscles or len(selected_exercises) < 3:
                used_muscles.add(prim)
                selected_exercises.append(
                    PrescribedExercise(
                        exercise_id=cand.id,
                        name=cand.name,
                        target_muscle=prim.capitalize(),
                        sets=sets_count,
                        target_reps=reps,
                        target_rpe=target_rpe,
                        rest_seconds=rest,
                        gif_url=cand.gif_url,
                        notes=f"Prescribed for {readiness_state.value} state. Focus on controlled cadence."
                    )
                )
            if len(selected_exercises) >= 4:
                break

        if not selected_exercises:
            # Guaranteed fallback
            pushup = self.exercise_map["pushups"]
            selected_exercises.append(
                PrescribedExercise(
                    exercise_id=pushup.id,
                    name=pushup.name,
                    target_muscle="Chest",
                    sets=sets_count,
                    target_reps=reps,
                    target_rpe=target_rpe,
                    rest_seconds=rest,
                    gif_url=pushup.gif_url,
                    notes="Bodyweight pushup fallback."
                )
            )

        return {
            "title": title,
            "adaptation_rationale": rationale,
            "target_duration_minutes": 45 if readiness_state != ReadinessState.REDUCED else 30,
            "warmup": warmup,
            "exercises": selected_exercises,
            "cooldown": cooldown
        }

exercise_service = ExerciseService()

"""In-workout dynamic fatigue scaling engine.

Detects acute performance drop-offs and dynamically recalibrates
remaining volume, intensity, and exercises.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SetRecord:
    weight: float
    reps: int
    rpe: float
    exercise_id: str = ""
    timestamp: str = ""


@dataclass
class ScalingDecision:
    adjustment_type: str  # weight_reduction, rest_extension, swap_exercise, drop_set
    description: str
    magnitude: Optional[str] = None
    original: Optional[str] = None
    reason: str = ""


@dataclass
class AutoScaleResult:
    should_scale: bool
    confidence: float
    decisions: list[ScalingDecision] = field(default_factory=list)
    fatigue_score: float = 0.0  # 0-100
    summary: str = ""


# Axial loading ratings (1-5) for exercise substitution logic
HIGH_AXIAL_EXERCISES = {
    "barbell-back-squat", "conventional-deadlift", "sumo-deadlift",
    "barbell-back-squat", "overhead-press", "barbell-row",
}

EQUIVALENT_EXERCISES: dict[str, list[str]] = {
    "barbell-back-squat": ["leg-press", "goblet-squat", "bulgarian-split-squat", "hack-squat"],
    "conventional-deadlift": ["romanian-deadlift", "hip-thrust", "cable-pull-through", "leg-curl"],
    "bench-press": ["dumbbell-bench-press", "incline-dumbbell-press", "chest-dip", "push-up"],
    "overhead-press": ["dumbbell-shoulder-press", "lateral-raise", "arnold-press", "machine-press"],
    "barbell-row": ["seated-cable-row", "dumbbell-row", "machine-row", "inverted-row"],
    "pull-up": ["lat-pulldown", "cable-pulldown", "assisted-pull-up"],
    "barbell-curl": ["dumbbell-curl", "hammer-curl", "cable-curl", "preacher-curl"],
    "tricep-dip": ["tricep-pushdown", "overhead-tricep-extension", "skull-crusher"],
}


class AutoScalerEngine:
    """Evaluates intra-set performance and triggers dynamic auto-scale adjustments."""

    def __init__(
        self,
        rpe_threshold: float = 2.0,
        rep_drop_threshold: int = 3,
        weight_reduction_pct: float = 0.10,
        rest_extension_seconds: int = 30,
    ):
        self.rpe_threshold = rpe_threshold
        self.rep_drop_threshold = rep_drop_threshold
        self.weight_reduction_pct = weight_reduction_pct
        self.rest_extension_seconds = rest_extension_seconds

    def evaluate_set(
        self,
        completed_sets: list[SetRecord],
        target_rpe: float,
        target_reps: int,
        rest_seconds: int = 90,
    ) -> AutoScaleResult:
        """Evaluate a just-completed set against targets and return scaling decisions."""
        if not completed_sets:
            return AutoScaleResult(should_scale=False, confidence=0, summary="No sets completed yet.")

        latest = completed_sets[-1]
        decisions: list[ScalingDecision] = []
        fatigue_score = self._compute_fatigue(completed_sets, target_rpe)

        # Check RPE overshoot
        rpe_overshoot = latest.rpe - target_rpe
        if rpe_overshoot >= self.rpe_threshold:
            decisions.append(ScalingDecision(
                adjustment_type="weight_reduction",
                description=f"Reduce weight by {int(self.weight_reduction_pct * 100)}% on next set",
                magnitude=f"{int(self.weight_reduction_pct * 100)}%",
                original=f"{latest.weight}kg",
                reason=f"RPE {latest.rpe:.1f} exceeded target {target_rpe:.1f} by {rpe_overshoot:.1f} points",
            ))
            decisions.append(ScalingDecision(
                adjustment_type="rest_extension",
                description=f"Extend rest by {self.rest_extension_seconds}s",
                magnitude=f"+{self.rest_extension_seconds}s",
                original=f"{rest_seconds}s",
                reason="Elevated fatigue detected",
            ))

        # Check rep shortfall
        if target_reps - latest.reps >= self.rep_drop_threshold:
            decisions.append(ScalingDecision(
                adjustment_type="weight_reduction",
                description=f"Reduce weight by {int(self.weight_reduction_pct * 100)}% — missed {target_reps - latest.reps} reps",
                magnitude=f"{int(self.weight_reduction_pct * 100)}%",
                original=f"{latest.weight}kg at {latest.reps} reps",
                reason=f"Completed {latest.reps} reps, target was {target_reps}",
            ))

        # Check cumulative fatigue across sets
        if len(completed_sets) >= 3:
            avg_rpe = sum(s.rpe for s in completed_sets[-3:]) / 3
            if avg_rpe >= 9.5:
                is_high_axial = latest.exercise_id in HIGH_AXIAL_EXERCISES
                if is_high_axial:
                    decisions.append(ScalingDecision(
                        adjustment_type="swap_exercise",
                        description=f"Swap to a lower-axial-load alternative",
                        original=latest.exercise_id,
                        reason=f"Average RPE {avg_rpe:.1f} on high-axial-load movement — risk of form breakdown",
                    ))
                else:
                    decisions.append(ScalingDecision(
                        adjustment_type="drop_set",
                        description="Drop final set to reduce total volume",
                        reason=f"Average RPE {avg_rpe:.1f} across last 3 sets — excessive fatigue",
                    ))

        should_scale = len(decisions) > 0
        summary = (
            f"{len(decisions)} adjustment(s) recommended. Fatigue: {fatigue_score:.0f}/100."
            if should_scale
            else f"Performance on track. Fatigue: {fatigue_score:.0f}/100."
        )

        return AutoScaleResult(
            should_scale=should_scale,
            confidence=min(0.95, 0.6 + len(completed_sets) * 0.05),
            decisions=decisions,
            fatigue_score=fatigue_score,
            summary=summary,
        )

    def get_substitution_options(self, exercise_id: str, _equipment: list[str] | None = None) -> list[dict]:
        """Return lower-axial-load exercise substitutions for a given exercise."""
        alternatives = EQUIVALENT_EXERCISES.get(exercise_id, [])
        return [
            {"exercise_id": alt, "swap_type": "lower_axial_load", "reason": "Reduce spinal loading while targeting same muscles"}
            for alt in alternatives
        ]

    def _compute_fatigue(self, sets: list[SetRecord], target_rpe: float) -> float:
        """Compute a 0-100 fatigue score from completed sets."""
        if not sets:
            return 0.0
        avg_rpe = sum(s.rpe for s in sets) / len(sets)
        rpe_fatigue = (avg_rpe / 10.0) * 40  # max 40 pts from RPE
        volume_fatigue = min(30, len(sets) * 5)  # up to 30 pts from volume
        drop_fatigue = 0.0
        if len(sets) >= 2:
            rep_drops = [sets[i].reps - sets[i + 1].reps for i in range(len(sets) - 1)]
            avg_drop = sum(rep_drops) / len(rep_drops) if rep_drops else 0
            drop_fatigue = min(30, max(0, avg_drop * 10))  # up to 30 pts from declining reps
        return min(100.0, rpe_fatigue + volume_fatigue + drop_fatigue)


auto_scaler = AutoScalerEngine()

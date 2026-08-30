"""Fitness Assessment Service.

Extracted from fitness-chatbot (inspiration).
Multi-phase fitness assessment: strength, endurance, flexibility,
power, and stabilization with scoring and level classification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FitnessLevel(Enum):
    EXCELLENT = "Excellent"
    VERY_GOOD = "Very Good"
    ABOVE_AVERAGE = "Above Average"
    AVERAGE = "Average"
    BELOW_AVERAGE = "Below Average"
    POOR = "Poor"
    VERY_POOR = "Very Poor"


class AssessmentPhase(Enum):
    STRENGTH = "StrengthAssessment"
    ENDURANCE = "EnduranceAssessment"
    FLEXIBILITY = "FlexibilityAssessment"
    POWER = "PowerAssessment"
    STABILIZATION = "StabilizationAssessment"


LEVEL_THRESHOLDS = [
    (90, FitnessLevel.EXCELLENT),
    (75, FitnessLevel.VERY_GOOD),
    (60, FitnessLevel.ABOVE_AVERAGE),
    (45, FitnessLevel.AVERAGE),
    (30, FitnessLevel.BELOW_AVERAGE),
    (15, FitnessLevel.POOR),
    (0, FitnessLevel.VERY_POOR),
]


@dataclass
class AssessmentResult:
    phase: AssessmentPhase
    score: float
    level: FitnessLevel
    metrics: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class FitnessProfile:
    name: str
    age: int = 30
    weight_kg: float = 70.0
    height_cm: float = 170.0
    gender: str = "unspecified"
    assessments: dict[str, AssessmentResult] = field(default_factory=dict)

    @property
    def bmi(self) -> float:
        return self.weight_kg / (self.height_cm / 100) ** 2 if self.height_cm > 0 else 0

    @property
    def overall_score(self) -> float:
        if not self.assessments:
            return 0
        return sum(a.score for a in self.assessments.values()) / len(self.assessments)

    @property
    def overall_level(self) -> FitnessLevel:
        return classify_level(self.overall_score)


def classify_level(score: float) -> FitnessLevel:
    """Classify fitness level from score."""
    for threshold, level in LEVEL_THRESHOLDS:
        if score >= threshold:
            return level
    return FitnessLevel.VERY_POOR


def assess_strength(pushups: int = 0, situps: int = 0, plank_seconds: float = 0) -> AssessmentResult:
    """Assess upper body and core strength."""
    pushup_score = min(100, pushups * 2)
    situp_score = min(100, situps * 2)
    plank_score = min(100, plank_seconds * 1.5)
    score = (pushup_score + situp_score + plank_score) / 3
    recommendations = []
    if pushups < 10:
        recommendations.append("Add push-up progressions to your routine")
    if plank_seconds < 60:
        recommendations.append("Work on plank holds for core stability")
    return AssessmentResult(
        phase=AssessmentPhase.STRENGTH, score=round(score, 1),
        level=classify_level(score),
        metrics={"pushups": pushups, "situps": situps, "plank_seconds": plank_seconds},
        recommendations=recommendations,
    )


def assess_endurance(run_time_minutes: float = 0, walk_time_minutes: float = 0, rest_heart_rate: int = 70) -> AssessmentResult:
    """Assess cardiovascular endurance."""
    if run_time_minutes > 0:
        if run_time_minutes < 20:
            run_score = 90
        elif run_time_minutes < 30:
            run_score = 75
        elif run_time_minutes < 40:
            run_score = 60
        elif run_time_minutes < 50:
            run_score = 45
        else:
            run_score = 30
    else:
        run_score = 50
    rhr_score = max(0, min(100, 100 - (rest_heart_rate - 40) * 1.5))
    score = (run_score + rhr_score) / 2
    recommendations = []
    if rest_heart_rate > 80:
        recommendations.append("Work on aerobic base building to lower resting heart rate")
    if run_time_minutes > 40:
        recommendations.append("Add interval training to improve running endurance")
    return AssessmentResult(
        phase=AssessmentPhase.ENDURANCE, score=round(score, 1),
        level=classify_level(score),
        metrics={"run_time": run_time_minutes, "rest_hr": rest_heart_rate},
        recommendations=recommendations,
    )


def assess_flexibility(
    sit_reach_cm: float = 0,
    shoulder_reach_cm: float = 0,
    hip_rotation_deg: float = 0,
) -> AssessmentResult:
    """Assess flexibility."""
    sit_score = min(100, max(0, (sit_reach_cm + 10) * 2.5))
    shoulder_score = min(100, max(0, (shoulder_reach_cm + 5) * 3))
    hip_score = min(100, hip_rotation_deg * 1.5)
    score = (sit_score + shoulder_score + hip_score) / 3
    recommendations = []
    if sit_reach_cm < 0:
        recommendations.append("Add hamstring stretching to your daily routine")
    if shoulder_reach_cm < 0:
        recommendations.append("Work on shoulder mobility exercises")
    return AssessmentResult(
        phase=AssessmentPhase.FLEXIBILITY, score=round(score, 1),
        level=classify_level(score),
        metrics={"sit_reach": sit_reach_cm, "shoulder_reach": shoulder_reach_cm, "hip_rotation": hip_rotation_deg},
        recommendations=recommendations,
    )


def assess_power(
    vertical_jump_cm: float = 0,
    broad_jump_cm: float = 0,
    medicine_ball_throw_m: float = 0,
) -> AssessmentResult:
    """Assess explosive power."""
    jump_score = min(100, vertical_jump_cm * 2)
    broad_score = min(100, broad_jump_cm * 0.8)
    mb_score = min(100, medicine_ball_throw_m * 20)
    score = (jump_score + broad_score + mb_score) / 3
    recommendations = []
    if vertical_jump_cm < 30:
        recommendations.append("Add plyometric exercises for explosive power")
    if medicine_ball_throw_m < 3:
        recommendations.append("Work on upper body power with medicine ball drills")
    return AssessmentResult(
        phase=AssessmentPhase.POWER, score=round(score, 1),
        level=classify_level(score),
        metrics={"vertical_jump": vertical_jump_cm, "broad_jump": broad_jump_cm, "mb_throw": medicine_ball_throw_m},
        recommendations=recommendations,
    )


def assess_stabilization(
    single_leg_balance_seconds: float = 0,
    bird_dog_reps: int = 0,
    side_plank_seconds: float = 0,
) -> AssessmentResult:
    """Assess core stabilization and balance."""
    balance_score = min(100, single_leg_balance_seconds * 3.3)
    bird_dog_score = min(100, bird_dog_reps * 5)
    side_plank_score = min(100, side_plank_seconds * 1.5)
    score = (balance_score + bird_dog_score + side_plank_score) / 3
    recommendations = []
    if single_leg_balance_seconds < 10:
        recommendations.append("Practice single-leg balance exercises daily")
    if side_plank_seconds < 30:
        recommendations.append("Build up side plank holds for oblique strength")
    return AssessmentResult(
        phase=AssessmentPhase.STABILIZATION, score=round(score, 1),
        level=classify_level(score),
        metrics={"balance": single_leg_balance_seconds, "bird_dog": bird_dog_reps, "side_plank": side_plank_seconds},
        recommendations=recommendations,
    )


def run_full_assessment(
    pushups: int = 0, situps: int = 0, plank_seconds: float = 0,
    run_time: float = 0, rest_hr: int = 70,
    sit_reach: float = 0, shoulder_reach: float = 0, hip_rotation: float = 0,
    vertical_jump: float = 0, broad_jump: float = 0, mb_throw: float = 0,
    balance: float = 0, bird_dog: int = 0, side_plank: float = 0,
) -> FitnessProfile:
    """Run complete fitness assessment."""
    profile = FitnessProfile(name="User")
    profile.assessments["Strength"] = assess_strength(pushups, situps, plank_seconds)
    profile.assessments["Endurance"] = assess_endurance(run_time, 0, rest_hr)
    profile.assessments["Flexibility"] = assess_flexibility(sit_reach, shoulder_reach, hip_rotation)
    profile.assessments["Power"] = assess_power(vertical_jump, broad_jump, mb_throw)
    profile.assessments["Stabilization"] = assess_stabilization(balance, bird_dog, side_plank)
    return profile


def generate_assessment_report(profile: FitnessProfile) -> dict[str, Any]:
    """Generate comprehensive assessment report."""
    all_recommendations = []
    for assessment in profile.assessments.values():
        all_recommendations.extend(assessment.recommendations)
    return {
        "overall_score": round(profile.overall_score, 1),
        "overall_level": profile.overall_level.value,
        "phases": {
            name: {"score": a.score, "level": a.level.value}
            for name, a in profile.assessments.items()
        },
        "recommendations": all_recommendations,
        "bmi": round(profile.bmi, 1),
    }

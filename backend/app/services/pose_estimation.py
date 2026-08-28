"""Pose Estimation Pipeline — MediaPipe-based landmark extraction and form scoring.

Covers: 33 landmarks, joint angle calculation, rep counting state machine,
form scoring (A-F grade), and exercise classification from keypoints.

References:
- MediaPipe Pose: 33 3D landmarks (x, y, z, visibility)
- GC_Fit pattern: angle-based rep detection
- FormAI: real-time exercise form analysis
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import math


class FormGrade(str, Enum):
    A = "A"  # Perfect form
    B = "B"  # Minor deviation
    C = "C"  # Noticeable issues
    D = "D"  # Significant form breakdown
    F = "F"  # Dangerous / incorrect


@dataclass
class Landmark:
    x: float
    y: float
    z: float
    visibility: float = 0.0


@dataclass
class JointAngle:
    joint: str
    angle_degrees: float
    target_range: tuple[float, float] = (0, 180)
    deviation: float = 0.0


@dataclass
class RepDetection:
    exercise_id: str
    rep_count: int
    current_phase: str  # "eccentric", "concentric", "pause"
    angle: float
    form_grade: FormGrade
    is_valid: bool = True


@dataclass
class FormAssessment:
    exercise_id: str
    overall_grade: FormGrade
    joint_scores: dict[str, float]
    penalties: list[str]
    suggestions: list[str]
    rep_quality_pct: float


# MediaPipe landmark indices
LANDMARKS = {
    "nose": 0, "left_eye_inner": 1, "left_eye": 2, "left_eye_outer": 3,
    "right_eye_inner": 4, "right_eye": 5, "right_eye_outer": 6,
    "left_ear": 7, "right_ear": 8, "mouth_left": 9, "mouth_right": 10,
    "left_shoulder": 11, "right_shoulder": 12,
    "left_elbow": 13, "right_elbow": 14,
    "left_wrist": 15, "right_wrist": 16,
    "left_pinky": 17, "right_pinky": 18,
    "left_index": 19, "right_index": 20,
    "left_thumb": 21, "right_thumb": 22,
    "left_hip": 23, "right_hip": 24,
    "left_knee": 25, "right_knee": 26,
    "left_ankle": 27, "right_ankle": 28,
    "left_heel": 29, "right_heel": 30,
    "left_foot_index": 31, "right_foot_index": 32,
}


def calculate_angle(a: Landmark, b: Landmark, c: Landmark) -> float:
    """Calculate angle at point B formed by A-B-C."""
    ba = (a.x - b.x, a.y - b.y)
    bc = (c.x - b.x, c.y - b.y)
    dot = ba[0] * bc[0] + ba[1] * bc[1]
    mag_ba = math.sqrt(ba[0] ** 2 + ba[1] ** 2)
    mag_bc = math.sqrt(bc[0] ** 2 + bc[1] ** 2)
    if mag_ba == 0 or mag_bc == 0:
        return 0.0
    cos_angle = max(-1.0, min(1.0, dot / (mag_ba * mag_bc)))
    return math.degrees(math.acos(cos_angle))


def calculate_midpoint(a: Landmark, b: Landmark) -> Landmark:
    return Landmark(x=(a.x + b.x) / 2, y=(a.y + b.y) / 2, z=(a.z + b.z) / 2)


# Exercise-specific angle calculators
EXERCISE_ANGLES = {
    "bench-press": lambda lm: calculate_angle(
        lm["right_shoulder"], lm["right_elbow"], lm["right_wrist"]
    ),
    "barbell-back-squat": lambda lm: calculate_angle(
        lm["right_hip"], lm["right_knee"], lm["right_ankle"]
    ),
    "deadlift": lambda lm: calculate_angle(
        lm["right_shoulder"], lm["right_hip"], lm["right_knee"]
    ),
    "barbell-row": lambda lm: calculate_angle(
        lm["right_shoulder"], lm["right_elbow"], lm["right_wrist"]
    ),
    "pull-up": lambda lm: calculate_angle(
        lm["right_shoulder"], lm["right_elbow"], lm["right_wrist"]
    ),
    "overhead-press": lambda lm: calculate_angle(
        lm["right_hip"], lm["right_shoulder"], lm["right_elbow"]
    ),
    "bicep-curl": lambda lm: calculate_angle(
        lm["right_shoulder"], lm["right_elbow"], lm["right_wrist"]
    ),
    "lunge": lambda lm: calculate_angle(
        lm["right_hip"], lm["right_knee"], lm["right_ankle"]
    ),
    "plank": lambda lm: calculate_angle(
        lm["right_shoulder"], lm["right_hip"], lm["right_knee"]
    ),
    "push-up": lambda lm: calculate_angle(
        lm["right_shoulder"], lm["right_elbow"], lm["right_wrist"]
    ),
}


# Rep detection thresholds per exercise
REP_THRESHOLDS = {
    "bench-press": {"concentric_start": 90, "concentric_end": 160, "min_holding_time": 0.3},
    "barbell-back-squat": {"concentric_start": 70, "concentric_end": 165, "min_holding_time": 0.3},
    "deadlift": {"concentric_start": 60, "concentric_end": 170, "min_holding_time": 0.2},
    "pull-up": {"concentric_start": 90, "concentric_end": 160, "min_holding_time": 0.3},
    "barbell-row": {"concentric_start": 80, "concentric_end": 150, "min_holding_time": 0.2},
    "overhead-press": {"concentric_start": 90, "concentric_end": 170, "min_holding_time": 0.3},
    "bicep-curl": {"concentric_start": 50, "concentric_end": 150, "min_holding_time": 0.2},
    "lunge": {"concentric_start": 70, "concentric_end": 170, "min_holding_time": 0.3},
    "push-up": {"concentric_start": 80, "concentric_end": 160, "min_holding_time": 0.3},
}


class PoseRepCounter:
    """State machine for counting reps from continuous landmark stream."""

    def __init__(self, exercise_id: str):
        self.exercise_id = exercise_id
        self.rep_count = 0
        self.in_bottom = False
        self.angle_history: list[float] = []
        self.thresholds = REP_THRESHOLDS.get(exercise_id, {
            "concentric_start": 80, "concentric_end": 160, "min_holding_time": 0.2
        })

    def process_frame(self, angle: float) -> RepDetection:
        self.angle_history.append(angle)

        is_at_bottom = angle <= self.thresholds["concentric_start"]
        is_at_top = angle >= self.thresholds["concentric_end"]

        if is_at_bottom and not self.in_bottom:
            self.in_bottom = True
        elif is_at_top and self.in_bottom:
            self.in_bottom = False
            self.rep_count += 1

        # Determine phase
        if is_at_bottom:
            phase = "eccentric"
        elif is_at_top:
            phase = "pause"
        else:
            phase = "concentric" if not self.in_bottom else "eccentric"

        # Basic form check
        form_grade = self._assess_form(angle)

        return RepDetection(
            exercise_id=self.exercise_id,
            rep_count=self.rep_count,
            current_phase=phase,
            angle=angle,
            form_grade=form_grade,
        )

    def _assess_form(self, angle: float) -> FormGrade:
        if self.angle_history and len(self.angle_history) > 3:
            recent_variance = max(self.angle_history[-5:]) - min(self.angle_history[-5:])
            if recent_variance > 30:
                return FormGrade.C
        if angle < 40:
            return FormGrade.D
        return FormGrade.A

    def get_summary(self) -> dict:
        return {
            "exercise_id": self.exercise_id,
            "total_reps": self.rep_count,
            "angle_readings": len(self.angle_history),
            "min_angle": min(self.angle_history) if self.angle_history else 0,
            "max_angle": max(self.angle_history) if self.angle_history else 0,
        }


def score_form(exercise_id: str, joint_angles: dict[str, float]) -> FormAssessment:
    """Score exercise form based on joint angles."""
    penalties = []
    suggestions = []
    joint_scores = {}

    if exercise_id in ("bench-press", "barbell-row", "push-up"):
        elbow = joint_angles.get("elbow", 90)
        if elbow < 70:
            penalties.append("Elbows flaring too wide")
            suggestions.append("Tuck elbows to ~45 degrees from torso")
            joint_scores["elbow"] = 40
        elif elbow < 85:
            joint_scores["elbow"] = 70
        else:
            joint_scores["elbow"] = 95

    if exercise_id in ("barbell-back-squat", "lunge"):
        knee = joint_angles.get("knee", 90)
        if knee > 170:
            penalties.append("Insufficient depth")
            suggestions.append("Squat until thighs are parallel to floor")
            joint_scores["knee"] = 50
        elif knee < 60:
            penalties.append("Going too deep — risk of knee strain")
            suggestions.append("Stop at parallel, don't bounce")
            joint_scores["knee"] = 60
        else:
            joint_scores["knee"] = 90

    if exercise_id == "deadlift":
        back_angle = joint_angles.get("back", 180)
        if back_angle < 150:
            penalties.append("Rounding of lower back")
            suggestions.append("Maintain neutral spine, brace core")
            joint_scores["back"] = 30
        else:
            joint_scores["back"] = 95

    # Overall grade
    avg_score = sum(joint_scores.values()) / len(joint_scores) if joint_scores else 80
    if avg_score >= 90:
        grade = FormGrade.A
    elif avg_score >= 75:
        grade = FormGrade.B
    elif avg_score >= 55:
        grade = FormGrade.C
    elif avg_score >= 35:
        grade = FormGrade.D
    else:
        grade = FormGrade.F

    return FormAssessment(
        exercise_id=exercise_id,
        overall_grade=grade,
        joint_scores=joint_scores,
        penalties=penalties,
        suggestions=suggestions,
        rep_quality_pct=round(avg_score, 1),
    )


def classify_exercise_from_landmarks(landmarks: dict[str, Landmark]) -> str:
    """Classify which exercise is being performed from landmark positions."""
    # Simplified classifier based on key body positions
    nose = landmarks.get("nose")
    left_shoulder = landmarks.get("left_shoulder")
    right_shoulder = landmarks.get("right_shoulder")
    left_elbow = landmarks.get("left_elbow")
    right_elbow = landmarks.get("right_elbow")
    left_wrist = landmarks.get("left_wrist")
    right_wrist = landmarks.get("right_wrist")
    left_hip = landmarks.get("left_hip")
    right_hip = landmarks.get("right_hip")
    left_knee = landmarks.get("left_knee")
    right_knee = landmarks.get("right_knee")
    left_ankle = landmarks.get("left_ankle")
    right_ankle = landmarks.get("right_ankle")

    if not all([left_shoulder, right_shoulder, left_hip, right_hip]):
        return "unknown"

    shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
    hip_y = (left_hip.y + right_hip.y) / 2
    knee_y = (left_knee.y + right_knee.y) / 2 if left_knee and right_knee else None

    # Check if supine (lying on back) — shoulder and hip at similar Y
    wrist_y = (left_wrist.y + right_wrist.y) / 2 if left_wrist and right_wrist else None

    if wrist_y and abs(shoulder_y - hip_y) < 0.1:
        if wrist_y < shoulder_y:
            return "bench-press"
        return "deadlift"

    if knee_y and hip_y:
        hip_to_knee_angle = calculate_angle(
            Landmark(0, shoulder_y, 0), Landmark(0, hip_y, 0), Landmark(0, knee_y, 0)
        )
        if hip_to_knee_angle < 120:
            return "barbell-back-squat"
        elif hip_to_knee_angle > 170:
            if wrist_y and wrist_y < shoulder_y:
                return "overhead-press"
            return "barbell-row"

    return "unknown"

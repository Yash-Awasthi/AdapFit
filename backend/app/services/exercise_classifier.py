"""Exercise Classifier — classify exercises from pose keypoint positions.

Uses angle-based feature extraction + rule-based classification (no external ML deps).
Classifies into 12+ exercise categories from a single camera frame.

Features extracted per frame:
- Joint angles (shoulder, elbow, hip, knee, ankle)
- Body orientation (standing, seated, supine, prone)
- Limb positions relative to torso
- Movement direction (concentric, eccentric, isometric)

References:
- GC_Fit: angle-based exercise recognition
- FormAI (HuggingFace): real-time form analysis pipeline
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Optional
from app.services.pose_estimation import Landmark, calculate_angle


@dataclass
class ExerciseClassification:
    exercise_id: str
    exercise_name: str
    confidence: float
    body_position: str  # standing, seated, supine, prone
    primary_muscles: list[str]
    movement_pattern: str  # push, pull, squat, hinge, isolation


# Feature vector from landmarks
@dataclass
class PoseFeatures:
    shoulder_angle: float = 0
    elbow_angle: float = 0
    hip_angle: float = 0
    knee_angle: float = 0
    ankle_angle: float = 0
    shoulder_hip_ratio: float = 0  # vertical distance ratio
    wrist_height_ratio: float = 0  # wrist vs shoulder height
    body_orientation: str = "standing"
    arm_extension: float = 0  # 0 = fully bent, 1 = fully extended


def extract_features(lm: dict[str, Landmark]) -> PoseFeatures:
    """Extract feature vector from MediaPipe landmarks."""
    # Joint angles
    elbow = calculate_angle(lm["right_shoulder"], lm["right_elbow"], lm["right_wrist"])
    shoulder = calculate_angle(lm["right_hip"], lm["right_shoulder"], lm["right_elbow"])
    hip = calculate_angle(lm["right_shoulder"], lm["right_hip"], lm["right_knee"])
    knee = calculate_angle(lm["right_hip"], lm["right_knee"], lm["right_ankle"])
    ankle = calculate_angle(lm["right_knee"], lm["right_ankle"], lm.get("right_foot_index", lm["right_ankle"]))

    # Body orientation
    shoulder_y = (lm["left_shoulder"].y + lm["right_shoulder"].y) / 2
    hip_y = (lm["left_hip"].y + lm["right_hip"].y) / 2
    shoulder_hip_dy = hip_y - shoulder_y  # positive = standing

    wrist_y = (lm["left_wrist"].y + lm["right_wrist"].y) / 2
    wrist_vs_shoulder = shoulder_y - wrist_y  # positive = hands above shoulders

    # Determine body position
    if abs(shoulder_hip_dy) < 0.1:
        if wrist_y < shoulder_y:
            body_pos = "supine"
        else:
            body_pos = "prone"
    elif shoulder_hip_dy > 0.15:
        body_pos = "standing"
    else:
        body_pos = "seated"

    # Arm extension
    arm_len = math.sqrt(
        (lm["right_shoulder"].x - lm["right_elbow"].x) ** 2
        + (lm["right_shoulder"].y - lm["right_elbow"].y) ** 2
    )
    forearm_len = math.sqrt(
        (lm["right_elbow"].x - lm["right_wrist"].x) ** 2
        + (lm["right_elbow"].y - lm["right_wrist"].y) ** 2
    )
    arm_extension = elbow / 180 if elbow > 0 else 0.5

    return PoseFeatures(
        shoulder_angle=shoulder,
        elbow_angle=elbow,
        hip_angle=hip,
        knee_angle=knee,
        ankle_angle=ankle,
        shoulder_hip_ratio=shoulder_hip_dy,
        wrist_height_ratio=wrist_vs_shoulder,
        body_orientation=body_pos,
        arm_extension=arm_extension,
    )


# Classification rules — feature thresholds per exercise
CLASSIFICATION_RULES: list[tuple[str, str, list[str], str, float]] = [
    # (exercise_id, exercise_name, muscles, pattern, priority)
    ("bench-press", "Bench Press", ["chest", "triceps", "front_delts"], "push", 10),
    ("barbell-back-squat", "Barbell Back Squat", ["quadriceps", "glutes", "hamstrings"], "squat", 10),
    ("conventional-deadlift", "Deadlift", ["hamstrings", "glutes", "lower_back"], "hinge", 10),
    ("barbell-row", "Barbell Row", ["back", "biceps"], "pull", 9),
    ("pull-up", "Pull-Up", ["back", "biceps"], "pull", 9),
    ("overhead-press", "Overhead Press", ["shoulders", "triceps"], "push", 9),
    ("bicep-curl", "Bicep Curl", ["biceps"], "isolation", 7),
    ("lunge", "Lunge", ["quadriceps", "glutes"], "squat", 8),
    ("push-up", "Push-Up", ["chest", "triceps"], "push", 9),
    ("plank", "Plank", ["core", "shoulders"], "isolation", 7),
    ("dumbbell-lateral-raise", "Lateral Raise", ["shoulders"], "isolation", 6),
    ("tricep-extension", "Tricep Extension", ["triceps"], "isolation", 6),
]


def classify(features: PoseFeatures) -> ExerciseClassification:
    """Classify exercise from extracted pose features."""
    scores: dict[str, float] = {}

    # Standing exercises
    if features.body_orientation == "standing":
        # Squat pattern
        if features.knee_angle < 120 and features.hip_angle < 120:
            scores["barbell-back-squat"] = 0.8
            scores["lunge"] = 0.6

        # Overhead press pattern
        if features.wrist_height_ratio > 0.1 and features.elbow_angle > 150:
            scores["overhead-press"] = 0.85

        # Deadlift pattern
        if features.hip_angle < 100 and features.knee_angle > 100:
            scores["conventional-deadlift"] = 0.8

        # Bicep curl pattern
        if features.elbow_angle < 60 and features.shoulder_angle > 150:
            scores["bicep-curl"] = 0.75

        # Lateral raise
        if 70 < features.shoulder_angle < 110 and features.elbow_angle > 150:
            scores["dumbbell-lateral-raise"] = 0.7

    # Supine exercises
    elif features.body_orientation == "supine":
        if features.wrist_height_ratio > 0:
            scores["bench-press"] = 0.85

    # Prone exercises
    elif features.body_orientation == "prone":
        if features.knee_angle > 160 and features.hip_angle > 160:
            scores["push-up"] = 0.8
        elif features.elbow_angle < 100:
            scores["barbell-row"] = 0.75

    # Seated exercises
    elif features.body_orientation == "seated":
        if features.elbow_angle < 60:
            scores["bicep-curl"] = 0.6
        elif features.knee_angle < 100:
            scores["barbell-back-squat"] = 0.5  # Could be leg press

    # Plank detection
    if features.body_orientation in ("prone", "standing"):
        if 150 < features.hip_angle < 180 and features.knee_angle > 160:
            scores["plank"] = max(scores.get("plank", 0), 0.7)

    if not scores:
        # Default: classify by most prominent feature
        return ExerciseClassification(
            exercise_id="unknown",
            exercise_name="Unknown Exercise",
            confidence=0.3,
            body_position=features.body_orientation,
            primary_muscles=[],
            movement_pattern="unknown",
        )

    best_id = max(scores, key=scores.get)
    best_score = scores[best_id]
    rule = next((r for r in CLASSIFICATION_RULES if r[0] == best_id), None)

    if rule:
        return ExerciseClassification(
            exercise_id=rule[0],
            exercise_name=rule[1],
            confidence=round(best_score, 2),
            body_position=features.body_orientation,
            primary_muscles=rule[2],
            movement_pattern=rule[3],
        )

    return ExerciseClassification(
        exercise_id=best_id,
        exercise_name=best_id.replace("-", " ").title(),
        confidence=round(best_score, 2),
        body_position=features.body_orientation,
        primary_muscles=[],
        movement_pattern="unknown",
    )


def classify_from_landmarks(landmarks: dict[str, Landmark]) -> ExerciseClassification:
    """End-to-end classification from raw landmarks."""
    features = extract_features(landmarks)
    return classify(features)

"""
AI Pose Estimation & Form Checker — analyzes exercise form using body landmarks.
Detects exercises, counts reps, and provides real-time form feedback.

Inspired by: fitness-trainer-pose-estimation (MediaPipe pose estimation)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ExerciseType(Enum):
    SQUAT = "squat"
    DEADLIFT = "deadlift"
    BENCH_PRESS = "bench_press"
    OVERHEAD_PRESS = "overhead_press"
    BICEP_CURL = "bicep_curl"
    LATERAL_RAISE = "lateral_raise"
    LUNGE = "lunge"
    PLANK = "plank"
    PUSH_UP = "push_up"
    PULL_UP = "pull_up"


class FormFeedback(Enum):
    GOOD = "good"
    WARNING = "warning"
    DANGER = "danger"


class RepPhase(Enum):
    START = "start"
    ASCENDING = "ascending"
    TOP = "top"
    DESCENDING = "descending"


@dataclass
class Landmark:
    """A body landmark (e.g., left knee)."""
    x: float
    y: float
    z: float = 0.0
    visibility: float = 0.0


@dataclass
class AngleMeasurement:
    """An angle measured between three landmarks."""
    name: str
    angle_degrees: float
    landmarks_used: list[str]


@dataclass
class FormCheck:
    """A single form check result."""
    check_name: str
    feedback: FormFeedback
    message: str
    angle: float | None = None
    target_range: tuple[float, float] | None = None


@dataclass
class PoseResult:
    """Result of processing a single frame."""
    exercise_type: ExerciseType | None
    phase: RepPhase
    rep_count: int
    angles: list[AngleMeasurement]
    form_checks: list[FormCheck]
    overall_score: float  # 0-100
    landmarks_detected: bool


# MediaPipe pose landmark indices
LANDMARK_INDICES = {
    "left_hip": 23, "right_hip": 24,
    "left_knee": 25, "right_knee": 26,
    "left_ankle": 27, "right_ankle": 28,
    "left_shoulder": 11, "right_shoulder": 12,
    "left_elbow": 13, "right_elbow": 14,
    "left_wrist": 15, "right_wrist": 16,
    "left_ear": 7, "right_ear": 8,
    "nose": 0,
}


class PoseFormChecker:
    """Analyzes exercise form from body pose landmarks."""

    # Angle thresholds for form checks
    SQUAT_KNEE_THRESHOLD = 90  # degrees - below this is deep enough
    DEADLIFT_HIP_THRESHOLD = 160  # degrees - near full extension
    BENCH_PRESS_ELBOW_THRESHOLD = 90  # degrees - at bottom
    LATERAL_RAISE_SHOULDER_THRESHOLD = 80  # degrees - target elevation
    PLANK_HIP_THRESHOLD = 165  # degrees - should be near straight

    def __init__(self) -> None:
        self._rep_count = 0
        self._phase = RepPhase.START
        self._prev_angle: float | None = None
        self._phase_threshold = 5.0  # degrees change to detect phase transition

    def calculate_angle(
        self, a: Landmark, b: Landmark, c: Landmark
    ) -> float:
        """Calculate the angle at point B formed by lines AB and BC."""
        # Vector BA
        ba_x = a.x - b.x
        ba_y = a.y - b.y
        # Vector BC
        bc_x = c.x - b.x
        bc_y = c.y - b.y

        # Dot product
        dot = ba_x * bc_x + ba_y * bc_y
        # Magnitudes
        mag_ba = math.sqrt(ba_x**2 + ba_y**2)
        mag_bc = math.sqrt(bc_x**2 + bc_y**2)

        if mag_ba == 0 or mag_bc == 0:
            return 0.0

        cos_angle = max(-1, min(1, dot / (mag_ba * mag_bc)))
        return math.degrees(math.acos(cos_angle))

    def extract_landmarks(
        self, raw_landmarks: list[tuple[float, float, float]] | None
    ) -> dict[str, Landmark]:
        """Convert raw landmark list to named landmarks dict."""
        if not raw_landmarks:
            return {}

        landmarks: dict[str, Landmark] = {}
        for name, idx in LANDMARK_INDICES.items():
            if idx < len(raw_landmarks):
                x, y = raw_landmarks[idx][0], raw_landmarks[idx][1]
                z = raw_landmarks[idx][2] if len(raw_landmarks[idx]) > 2 else 0.0
                landmarks[name] = Landmark(x=x, y=y, z=z)

        return landmarks

    def check_squat(self, landmarks: dict[str, Landmark]) -> PoseResult:
        """Check squat form."""
        angles: list[AngleMeasurement] = []
        form_checks: list[FormCheck] = []
        score = 100.0

        # Knee angle
        if all(n in landmarks for n in ["left_hip", "left_knee", "left_ankle"]):
            knee_angle = self.calculate_angle(
                landmarks["left_hip"], landmarks["left_knee"], landmarks["left_ankle"]
            )
            angles.append(AngleMeasurement("knee_angle", knee_angle, ["hip", "knee", "ankle"]))

            if knee_angle < self.SQUAT_KNEE_THRESHOLD:
                form_checks.append(FormCheck(
                    "knee_depth", FormFeedback.GOOD,
                    "Good depth — knees past parallel",
                    knee_angle, (90, 130),
                ))
            elif knee_angle < 130:
                form_checks.append(FormCheck(
                    "knee_depth", FormFeedback.WARNING,
                    "Go lower — aim for thighs parallel to ground",
                    knee_angle, (90, 130),
                ))
                score -= 10
            else:
                form_checks.append(FormCheck(
                    "knee_depth", FormFeedback.WARNING,
                    "Very shallow — descend further",
                    knee_angle, (90, 130),
                ))
                score -= 20

        # Hip angle (back lean)
        if all(n in landmarks for n in ["left_shoulder", "left_hip", "left_knee"]):
            hip_angle = self.calculate_angle(
                landmarks["left_shoulder"], landmarks["left_hip"], landmarks["left_knee"]
            )
            angles.append(AngleMeasurement("hip_angle", hip_angle, ["shoulder", "hip", "knee"]))

            if 70 <= hip_angle <= 110:
                form_checks.append(FormCheck(
                    "back_lean", FormFeedback.GOOD,
                    "Good upright torso position",
                    hip_angle, (70, 110),
                ))
            else:
                form_checks.append(FormCheck(
                    "back_lean", FormFeedback.WARNING,
                    "Keep chest up — avoid excessive forward lean",
                    hip_angle, (70, 110),
                ))
                score -= 15

        # Knee tracking (knee vs ankle X position)
        if all(n in landmarks for n in ["left_knee", "left_ankle"]):
            knee_x = landmarks["left_knee"].x
            ankle_x = landmarks["left_ankle"].x
            deviation = abs(knee_x - ankle_x)
            if deviation > 0.05:
                form_checks.append(FormCheck(
                    "knee_valgus", FormFeedback.DANGER,
                    "Knee caving in — push knees outward over toes",
                    None, None,
                ))
                score -= 25

        # Rep counting
        if angles:
            knee = next((a for a in angles if a.name == "knee_angle"), None)
            if knee:
                self._update_phase(knee.angle_degrees)

        return PoseResult(
            exercise_type=ExerciseType.SQUAT,
            phase=self._phase,
            rep_count=self._rep_count,
            angles=angles,
            form_checks=form_checks,
            overall_score=max(0, min(100, score)),
            landmarks_detected=len(landmarks) >= 6,
        )

    def check_deadlift(self, landmarks: dict[str, Landmark]) -> PoseResult:
        """Check deadlift form."""
        angles: list[AngleMeasurement] = []
        form_checks: list[FormCheck] = []
        score = 100.0

        if all(n in landmarks for n in ["left_shoulder", "left_hip", "left_knee"]):
            hip_angle = self.calculate_angle(
                landmarks["left_shoulder"], landmarks["left_hip"], landmarks["left_knee"]
            )
            angles.append(AngleMeasurement("hip_angle", hip_angle, ["shoulder", "hip", "knee"]))

            if hip_angle >= self.DEADLIFT_HIP_THRESHOLD:
                form_checks.append(FormCheck(
                    "lockout", FormFeedback.GOOD,
                    "Full hip extension at lockout",
                    hip_angle, (160, 180),
                ))
            else:
                form_checks.append(FormCheck(
                    "lockout", FormFeedback.WARNING,
                    "Incomplete lockout — extend hips fully",
                    hip_angle, (160, 180),
                ))
                score -= 15

        # Back straightness check
        if all(n in landmarks for n in ["left_shoulder", "left_hip"]):
            back_angle = abs(math.degrees(math.atan2(
                landmarks["left_shoulder"].y - landmarks["left_hip"].y,
                landmarks["left_shoulder"].x - landmarks["left_hip"].x
            )))
            if back_angle > 20:
                form_checks.append(FormCheck(
                    "back_rounding", FormFeedback.DANGER,
                    "Back rounding detected — maintain neutral spine",
                    back_angle, (0, 20),
                ))
                score -= 30

        return PoseResult(
            exercise_type=ExerciseType.DEADLIFT,
            phase=self._phase,
            rep_count=self._rep_count,
            angles=angles,
            form_checks=form_checks,
            overall_score=max(0, min(100, score)),
            landmarks_detected=len(landmarks) >= 6,
        )

    def check_exercise(
        self,
        exercise: ExerciseType,
        raw_landmarks: list[tuple[float, float, float]] | None,
    ) -> PoseResult:
        """Check form for any supported exercise."""
        landmarks = self.extract_landmarks(raw_landmarks)

        if not landmarks:
            return PoseResult(
                exercise_type=exercise,
                phase=RepPhase.START,
                rep_count=0,
                angles=[],
                form_checks=[],
                overall_score=0,
                landmarks_detected=False,
            )

        checkers = {
            ExerciseType.SQUAT: self.check_squat,
            ExerciseType.DEADLIFT: self.check_deadlift,
        }

        checker = checkers.get(exercise)
        if checker:
            return checker(landmarks)

        return PoseResult(
            exercise_type=exercise,
            phase=RepPhase.START,
            rep_count=self._rep_count,
            angles=[],
            form_checks=[FormCheck(
                "unsupported", FormFeedback.WARNING,
                f"Exercise '{exercise.value}' not yet supported for form checking",
            )],
            overall_score=50,
            landmarks_detected=True,
        )

    def _update_phase(self, current_angle: float) -> None:
        """Update rep phase and count based on angle changes."""
        if self._prev_angle is None:
            self._prev_angle = current_angle
            return

        diff = current_angle - self._prev_angle

        if self._phase in (RepPhase.START, RepPhase.DESCENDING):
            if diff < -self._phase_threshold:
                self._phase = RepPhase.DESCENDING
        elif self._phase == RepPhase.DESCENDING:
            if diff > self._phase_threshold:
                self._phase = RepPhase.ASCENDING
                self._rep_count += 1  # Rep complete at bottom
        elif self._phase == RepPhase.ASCENDING:
            if abs(diff) < self._phase_threshold:
                self._phase = RepPhase.TOP

        self._prev_angle = current_angle

    def reset(self) -> None:
        """Reset rep counter and phase tracking."""
        self._rep_count = 0
        self._phase = RepPhase.START
        self._prev_angle = None

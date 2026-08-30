"""
Exercise pose estimation engine with state machine rep counting.

Extracted from fitness-trainer-pose-estimation — state machine exercise tracking.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Tuple
import math


class ExerciseState(Enum):
    IDLE = "idle"
    STARTING = "starting"
    ACTIVE = "active"
    HOLDING = "holding"
    FINISHING = "finishing"


class Grade(Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


@dataclass
class Landmark:
    x: float
    y: float
    z: float = 0.0
    visibility: float = 0.0


@dataclass
class PoseData:
    landmarks: List[Landmark]
    timestamp: float


@dataclass
class ExerciseConfig:
    name: str
    joint_angles: List[Tuple[str, str, str]]  # (joint1, joint2, joint3) for angle calc
    target_reps: int = 10
    min_angle: float = 90.0
    max_angle: float = 170.0
    hold_time: float = 0.0
    rest_time: float = 1.0


@dataclass
class RepResult:
    rep_number: int
    angle_min: float
    angle_max: float
    duration: float
    form_score: float  # 0-100
    feedback: List[str]


@dataclass
class ExerciseSession:
    config: ExerciseConfig
    reps: List[RepResult]
    current_state: ExerciseState
    current_rep: int
    form_score: float
    state_start_time: float


EXERCISE_CONFIGS = {
    "bicep_curl": ExerciseConfig(
        name="Bicep Curl",
        joint_angles=[("shoulder", "elbow", "wrist")],
        target_reps=12,
        min_angle=40,
        max_angle=160,
    ),
    "squat": ExerciseConfig(
        name="Squat",
        joint_angles=[("hip", "knee", "ankle")],
        target_reps=15,
        min_angle=60,
        max_angle=175,
    ),
    "push_up": ExerciseConfig(
        name="Push Up",
        joint_angles=[("shoulder", "elbow", "wrist")],
        target_reps=10,
        min_angle=70,
        max_angle=160,
    ),
    "lunge": ExerciseConfig(
        name="Lunge",
        joint_angles=[("hip", "knee", "ankle")],
        target_reps=10,
        min_angle=70,
        max_angle=170,
    ),
    "plank_hold": ExerciseConfig(
        name="Plank Hold",
        joint_angles=[("shoulder", "hip", "knee")],
        target_reps=1,
        min_angle=160,
        max_angle=180,
        hold_time=30.0,
    ),
    "shoulder_press": ExerciseConfig(
        name="Shoulder Press",
        joint_angles=[("elbow", "shoulder", "hip")],
        target_reps=10,
        min_angle=90,
        max_angle=170,
    ),
    "leg_raise": ExerciseConfig(
        name="Leg Raise",
        joint_angles=[("hip", "knee", "ankle")],
        target_reps=12,
        min_angle=30,
        max_angle=170,
    ),
    "jumping_jack": ExerciseConfig(
        name="Jumping Jack",
        joint_angles=[("hip", "knee", "ankle")],
        target_reps=20,
        min_angle=80,
        max_angle=175,
    ),
    "burpee": ExerciseConfig(
        name="Burpee",
        joint_angles=[("shoulder", "elbow", "wrist")],
        target_reps=8,
        min_angle=70,
        max_angle=175,
    ),
    "mountain_climber": ExerciseConfig(
        name="Mountain Climber",
        joint_angles=[("hip", "knee", "ankle")],
        target_reps=20,
        min_angle=60,
        max_angle=170,
    ),
}


def compute_angle(a: Landmark, b: Landmark, c: Landmark) -> float:
    """Compute angle at point b given three landmarks."""
    ba = (a.x - b.x, a.y - b.y)
    bc = (c.x - b.x, c.y - b.y)
    dot = ba[0] * bc[0] + ba[1] * bc[1]
    mag_ba = math.sqrt(ba[0] ** 2 + ba[1] ** 2)
    mag_bc = math.sqrt(bc[0] ** 2 + bc[1] ** 2)
    if mag_ba == 0 or mag_bc == 0:
        return 0.0
    cos_angle = max(-1, min(1, dot / (mag_ba * mag_bc)))
    return math.degrees(math.acos(cos_angle))


def compute_form_score(angle: float, config: ExerciseConfig) -> float:
    """Compute form score based on angle consistency with target range."""
    mid = (config.min_angle + config.max_angle) / 2
    half_range = (config.max_angle - config.min_angle) / 2
    deviation = abs(angle - mid)
    if deviation <= half_range * 0.5:
        return 100.0
    elif deviation <= half_range:
        return 80.0 - (deviation - half_range * 0.5) / (half_range * 0.5) * 30
    elif deviation <= half_range * 1.5:
        return 50.0 - (deviation - half_range) / (half_range * 0.5) * 20
    else:
        return max(0, 30.0 - (deviation - half_range * 1.5) / half_range * 30)


def get_grade(score: float) -> Grade:
    if score >= 90:
        return Grade.A
    elif score >= 80:
        return Grade.B
    elif score >= 70:
        return Grade.C
    elif score >= 60:
        return Grade.D
    return Grade.F


def create_session(exercise_name: str) -> ExerciseSession:
    config = EXERCISE_CONFIGS.get(exercise_name, EXERCISE_CONFIGS["bicep_curl"])
    return ExerciseSession(
        config=config,
        reps=[],
        current_state=ExerciseState.IDLE,
        current_rep=0,
        form_score=100.0,
        state_start_time=0.0,
    )


def update_state_machine(session: ExerciseSession, angle: float, timestamp: float) -> ExerciseSession:
    """Update exercise state machine based on current angle."""
    config = session.config

    if session.current_state == ExerciseState.IDLE:
        if angle >= config.max_angle * 0.8:
            session.current_state = ExerciseState.STARTING
            session.state_start_time = timestamp

    elif session.current_state == ExerciseState.STARTING:
        if angle <= config.min_angle * 1.2:
            session.current_state = ExerciseState.ACTIVE
            session.current_rep += 1

    elif session.current_state == ExerciseState.ACTIVE:
        if angle >= config.max_angle * 0.8:
            form = compute_form_score(angle, config)
            session.reps.append(RepResult(
                rep_number=session.current_rep,
                angle_min=config.min_angle,
                angle_max=angle,
                duration=timestamp - session.state_start_time,
                form_score=form,
                feedback=[f"Rep {session.current_rep}: form score {form:.0f}"],
            ))
            session.current_state = ExerciseState.HOLDING
            session.state_start_time = timestamp

    elif session.current_state == ExerciseState.HOLDING:
        if timestamp - session.state_start_time >= config.rest_time:
            session.current_state = ExerciseState.STARTING
            session.state_start_time = timestamp

    if session.reps:
        session.form_score = sum(r.form_score for r in session.reps) / len(session.reps)

    return session

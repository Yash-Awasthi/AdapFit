"""
Exercise Form Analyzer
Inspired by Good-GYM's RTMPose-based form analysis

Provides:
- Keypoint angle calculation for form assessment
- Exercise phase detection (up/down)
- Repetition counting
- Form scoring based on angle thresholds
- Custom exercise configuration via JSON-like patterns

Pure functions only — no DB, no async.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import math


# COCO 17-keypoint format
KEYPOINTS = {
    0: "nose", 1: "left_eye", 2: "right_eye",
    3: "left_ear", 4: "right_ear",
    5: "left_shoulder", 6: "right_shoulder",
    7: "left_elbow", 8: "right_elbow",
    9: "left_wrist", 10: "right_wrist",
    11: "left_hip", 12: "right_hip",
    13: "left_knee", 14: "right_knee",
    15: "left_ankle", 16: "right_ankle",
}


@dataclass
class Keypoint:
    """Single keypoint with coordinates and confidence"""
    x: float
    y: float
    confidence: float


@dataclass
class ExerciseConfig:
    """Exercise configuration for form analysis"""
    name: str
    # Keypoint indices for angle calculation
    angle_joints: List[Tuple[int, int, int]]  # (p1, joint, p2)
    # Angle thresholds for phase detection
    down_angle: float  # Angle when in down position
    up_angle: float    # Angle when in up position
    # Tolerance for angle matching
    tolerance: float = 15.0
    # Minimum confidence for keypoints
    min_confidence: float = 0.5


# Pre-configured exercises (from Good-GYM pattern)
EXERCISE_CONFIGS = {
    "squat": ExerciseConfig(
        name="squat",
        angle_joints=[(11, 13, 15), (12, 14, 16)],  # Hip-knee-ankle
        down_angle=90.0,
        up_angle=170.0,
        tolerance=20.0,
    ),
    "push_up": ExerciseConfig(
        name="push_up",
        angle_joints=[(5, 7, 9), (6, 8, 10)],  # Shoulder-elbow-wrist
        down_angle=90.0,
        up_angle=160.0,
        tolerance=15.0,
    ),
    "sit_up": ExerciseConfig(
        name="sit_up",
        angle_joints=[(5, 11, 13), (6, 12, 14)],  # Shoulder-hip-knee
        down_angle=45.0,
        up_angle=120.0,
        tolerance=15.0,
    ),
    "lunge": ExerciseConfig(
        name="lunge",
        angle_joints=[(11, 13, 15), (12, 14, 16)],  # Hip-knee-ankle
        down_angle=90.0,
        up_angle=170.0,
        tolerance=20.0,
    ),
    "bicep_curl": ExerciseConfig(
        name="bicep_curl",
        angle_joints=[(5, 7, 9), (6, 8, 10)],  # Shoulder-elbow-wrist
        down_angle=160.0,
        up_angle=50.0,
        tolerance=15.0,
    ),
    "shoulder_press": ExerciseConfig(
        name="shoulder_press",
        angle_joints=[(5, 7, 9), (6, 8, 10)],  # Shoulder-elbow-wrist
        down_angle=90.0,
        up_angle=170.0,
        tolerance=15.0,
    ),
}


def calculate_angle(p1: Keypoint, joint: Keypoint, p2: Keypoint) -> float:
    """
    Calculate angle at joint formed by p1-joint-p2.
    
    Uses atan2 for robust angle calculation.
    
    Args:
        p1: First point
        joint: Vertex of angle
        p2: Second point
    
    Returns:
        Angle in degrees (0-180)
    """
    v1 = (p1.x - joint.x, p1.y - joint.y)
    v2 = (p2.x - joint.x, p2.y - joint.y)
    
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
    mag2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)
    
    if mag1 == 0 or mag2 == 0:
        return 0.0
    
    cos_angle = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    angle = math.degrees(math.acos(cos_angle))
    
    return angle


def calculate_pose_angles(
    keypoints: Dict[int, Keypoint],
    config: ExerciseConfig
) -> List[float]:
    """
    Calculate angles for all joints in exercise config.
    
    Args:
        keypoints: Dict of keypoint index -> Keypoint
        config: Exercise configuration
    
    Returns:
        List of angles for each joint in config
    """
    angles = []
    
    for p1_idx, joint_idx, p2_idx in config.angle_joints:
        p1 = keypoints.get(p1_idx)
        joint = keypoints.get(joint_idx)
        p2 = keypoints.get(p2_idx)
        
        if all(kp is not None for kp in [p1, joint, p2]):
            if (p1.confidence >= config.min_confidence and
                joint.confidence >= config.min_confidence and
                p2.confidence >= config.min_confidence):
                angle = calculate_angle(p1, joint, p2)
                angles.append(angle)
    
    return angles


def detect_phase(
    angles: List[float],
    config: ExerciseConfig,
    previous_phase: Optional[str] = None
) -> str:
    """
    Detect exercise phase from angles.
    
    Args:
        angles: Current angles
        config: Exercise configuration
        previous_phase: Previous phase for hysteresis
    
    Returns:
        Phase string: "up", "down", or "transition"
    """
    if not angles:
        return "transition"
    
    avg_angle = sum(angles) / len(angles)
    
    # Check if in up position
    if abs(avg_angle - config.up_angle) <= config.tolerance:
        return "up"
    
    # Check if in down position
    if abs(avg_angle - config.down_angle) <= config.tolerance:
        return "down"
    
    # In transition
    return "transition"


def count_repetition(
    phases: List[str],
    phase_sequence: Tuple[str, str] = ("down", "up")
) -> int:
    """
    Count repetitions from phase sequence.
    
    Args:
        phases: List of phases over time
        phase_sequence: Expected sequence for one rep
    
    Returns:
        Number of complete repetitions
    """
    if len(phases) < 2:
        return 0
    
    count = 0
    expected_idx = 0
    
    for phase in phases:
        if phase == phase_sequence[expected_idx]:
            expected_idx += 1
            if expected_idx >= len(phase_sequence):
                count += 1
                expected_idx = 0
    
    return count


def score_form(
    angles: List[float],
    config: ExerciseConfig,
    target_angle: Optional[float] = None
) -> Dict[str, any]:
    """
    Score exercise form based on angle accuracy.
    
    Args:
        angles: Current angles
        config: Exercise configuration
        target_angle: Optional target angle (uses config.down_angle if None)
    
    Returns:
        Form score and feedback
    """
    if not angles:
        return {
            "score": 0,
            "feedback": "No pose detected",
            "angle_deviation": 0,
        }
    
    avg_angle = sum(angles) / len(angles)
    target = target_angle if target_angle is not None else config.down_angle
    
    deviation = abs(avg_angle - target)
    
    # Score: 100 at target, decreasing with deviation
    if deviation <= config.tolerance * 0.5:
        score = 100
        feedback = "Excellent form"
    elif deviation <= config.tolerance:
        score = 80
        feedback = "Good form"
    elif deviation <= config.tolerance * 1.5:
        score = 60
        feedback = "Fair form — adjust angle"
    elif deviation <= config.tolerance * 2:
        score = 40
        feedback = "Poor form — significant deviation"
    else:
        score = 20
        feedback = "Form needs major correction"
    
    return {
        "score": score,
        "feedback": feedback,
        "angle_deviation": round(deviation, 1),
        "current_angle": round(avg_angle, 1),
        "target_angle": target,
    }


def analyze_exercise_frame(
    keypoints: Dict[int, Keypoint],
    exercise_name: str,
    previous_phase: Optional[str] = None
) -> Dict[str, any]:
    """
    Analyze a single frame of exercise.
    
    Args:
        keypoints: Detected keypoints
        exercise_name: Name of exercise
        previous_phase: Previous phase for hysteresis
    
    Returns:
        Analysis results with phase, angles, form score
    """
    config = EXERCISE_CONFIGS.get(exercise_name)
    if not config:
        return {"error": f"Unknown exercise: {exercise_name}"}
    
    # Calculate angles
    angles = calculate_pose_angles(keypoints, config)
    
    # Detect phase
    phase = detect_phase(angles, config, previous_phase)
    
    # Score form
    form_score = score_form(angles, config)
    
    return {
        "exercise": exercise_name,
        "phase": phase,
        "angles": [round(a, 1) for a in angles],
        "form_score": form_score,
        "keypoints_detected": len([k for k in keypoints.values() if k.confidence >= config.min_confidence]),
    }


def get_exercise_configs() -> Dict[str, Dict]:
    """Get all available exercise configurations"""
    return {
        name: {
            "name": config.name,
            "down_angle": config.down_angle,
            "up_angle": config.up_angle,
            "tolerance": config.tolerance,
        }
        for name, config in EXERCISE_CONFIGS.items()
    }


def create_custom_exercise(
    name: str,
    angle_joints: List[Tuple[int, int, int]],
    down_angle: float,
    up_angle: float,
    tolerance: float = 15.0,
    min_confidence: float = 0.5
) -> ExerciseConfig:
    """Create a custom exercise configuration"""
    return ExerciseConfig(
        name=name,
        angle_joints=angle_joints,
        down_angle=down_angle,
        up_angle=up_angle,
        tolerance=tolerance,
        min_confidence=min_confidence,
    )

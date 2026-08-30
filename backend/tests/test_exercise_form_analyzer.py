"""Tests for exercise form analyzer"""
import pytest
from app.services.exercise_form_analyzer import (
    Keypoint, ExerciseConfig, calculate_angle, calculate_pose_angles,
    detect_phase, count_repetition, score_form, analyze_exercise_frame,
    EXERCISE_CONFIGS, create_custom_exercise,
)


class TestCalculateAngle:
    def test_right_angle(self):
        p1 = Keypoint(0, 1, 0.9)
        joint = Keypoint(0, 0, 0.9)
        p2 = Keypoint(1, 0, 0.9)
        angle = calculate_angle(p1, joint, p2)
        assert 85 <= angle <= 95

    def test_straight_line(self):
        p1 = Keypoint(0, 0, 0.9)
        joint = Keypoint(1, 0, 0.9)
        p2 = Keypoint(2, 0, 0.9)
        angle = calculate_angle(p1, joint, p2)
        assert 170 <= angle <= 180

    def test_zero_length_vector(self):
        p1 = Keypoint(0, 0, 0.9)
        joint = Keypoint(0, 0, 0.9)
        p2 = Keypoint(1, 0, 0.9)
        angle = calculate_angle(p1, joint, p2)
        assert angle == 0.0


class TestDetectPhase:
    def test_up_phase(self):
        config = EXERCISE_CONFIGS["squat"]
        angles = [170.0]
        phase = detect_phase(angles, config)
        assert phase == "up"

    def test_down_phase(self):
        config = EXERCISE_CONFIGS["squat"]
        angles = [90.0]
        phase = detect_phase(angles, config)
        assert phase == "down"

    def test_transition(self):
        config = EXERCISE_CONFIGS["squat"]
        angles = [130.0]
        phase = detect_phase(angles, config)
        assert phase == "transition"

    def test_empty_angles(self):
        config = EXERCISE_CONFIGS["squat"]
        phase = detect_phase([], config)
        assert phase == "transition"


class TestCountRepetition:
    def test_single_rep(self):
        phases = ["down", "up"]
        count = count_repetition(phases)
        assert count == 1

    def test_multiple_reps(self):
        phases = ["down", "up", "down", "up", "down", "up"]
        count = count_repetition(phases)
        assert count == 3

    def test_incomplete_rep(self):
        phases = ["down", "up", "down"]
        count = count_repetition(phases)
        assert count == 1

    def test_no_reps(self):
        phases = ["up", "up"]
        count = count_repetition(phases)
        assert count == 0


class TestScoreForm:
    def test_excellent_form(self):
        config = EXERCISE_CONFIGS["squat"]
        angles = [90.0]
        result = score_form(angles, config)
        assert result["score"] == 100
        assert result["feedback"] == "Excellent form"

    def test_good_form(self):
        config = EXERCISE_CONFIGS["squat"]
        angles = [105.0]
        result = score_form(angles, config)
        assert result["score"] == 80
        assert result["feedback"] == "Good form"

    def test_poor_form(self):
        config = EXERCISE_CONFIGS["squat"]
        angles = [140.0]
        result = score_form(angles, config)
        assert result["score"] <= 40

    def test_empty_angles(self):
        config = EXERCISE_CONFIGS["squat"]
        result = score_form([], config)
        assert result["score"] == 0


class TestAnalyzeExerciseFrame:
    def test_squat_analysis(self):
        keypoints = {
            11: Keypoint(0.3, 0.5, 0.9),  # left_hip
            13: Keypoint(0.3, 0.7, 0.9),  # left_knee
            15: Keypoint(0.3, 0.9, 0.9),  # left_ankle
            12: Keypoint(0.5, 0.5, 0.9),  # right_hip
            14: Keypoint(0.5, 0.7, 0.9),  # right_knee
            16: Keypoint(0.5, 0.9, 0.9),  # right_ankle
        }
        result = analyze_exercise_frame(keypoints, "squat")
        assert result["exercise"] == "squat"
        assert result["phase"] in ["up", "down", "transition"]
        assert "angles" in result
        assert "form_score" in result

    def test_unknown_exercise(self):
        result = analyze_exercise_frame({}, "unknown")
        assert "error" in result


class TestCustomExercise:
    def test_create_custom(self):
        config = create_custom_exercise(
            name="custom",
            angle_joints=[(5, 7, 9)],
            down_angle=90.0,
            up_angle=170.0,
        )
        assert config.name == "custom"
        assert config.down_angle == 90.0

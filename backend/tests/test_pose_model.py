"""The MediaPipe pose model finds a person in a saved frame (needs the model file the Dockerfile downloads)."""
from pathlib import Path

import pytest

from app.api.v1.endpoints import form_check

pytestmark = pytest.mark.skipif(form_check._pose_model is None, reason="pose model or its EGL libraries not installed")


def test_pose_model_finds_every_landmark_in_a_saved_frame():
    landmarks = form_check._decode_landmarks((Path(__file__).parent / "fixtures" / "pose.jpg").read_bytes())
    assert landmarks is not None and set(landmarks) == set(form_check.LANDMARKS)
    assert landmarks["nose"].visibility > 0.9
    assert landmarks["nose"].y < landmarks["left_hip"].y

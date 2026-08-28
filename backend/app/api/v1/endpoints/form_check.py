"""Form Check — pose estimation from a single camera frame.

Accepts a base64 JPEG, runs MediaPipe Pose to extract landmarks, computes the
exercise-relevant joint angle, and scores form using the existing rule-based
scorer in app.services.pose_estimation.
"""
from __future__ import annotations
import base64
import io
from typing import Optional

import numpy as np
from PIL import Image
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.pose_estimation import (
    Landmark, LANDMARKS, EXERCISE_ANGLES, score_form,
)

router = APIRouter()

try:
    import mediapipe as mp
    _pose_model = mp.solutions.pose.Pose(static_image_mode=True, model_complexity=1)
except Exception:
    _pose_model = None


class FormCheckRequest(BaseModel):
    exercise_id: str
    image_base64: str = Field(..., description="JPEG/PNG frame, base64-encoded, no data: prefix")


class FormCheckResponse(BaseModel):
    detected: bool
    exercise_id: str
    angle: Optional[float] = None
    grade: Optional[str] = None
    penalties: list[str] = []
    suggestions: list[str] = []
    rep_quality_pct: Optional[float] = None
    message: Optional[str] = None


class RepStateMachine:
    """Hysteresis-based rep counter driven by joint angle (degrees).

    Squat-style exercises: angle drops toward 90° at the bottom.
    Push/curl-style: angle opens toward 160°+ at the top.
    Tracks per-rep quality from the grade of the bottom/top frame.
    """

    def __init__(self, min_angle: float = 90.0, max_angle: float = 160.0, hysteresis: float = 10.0):
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.hysteresis = hysteresis
        self.state = "START"  # START -> DESCENDING -> BOTTOM -> ASCENDING -> TOP
        self.rep_count = 0
        self.last_grade: Optional[str] = None
        self.bottom_grade: Optional[str] = None
        self.grades: list[str] = []

    def process(self, angle: float, grade: Optional[str] = None) -> dict:
        rep_completed = False
        if grade:
            self.last_grade = grade
        if self.state == "START":
            if angle > self.max_angle - self.hysteresis:
                self.state = "DESCENDING"
        elif self.state == "DESCENDING":
            if angle < self.min_angle:
                self.state = "BOTTOM"
                self.bottom_grade = self.last_grade  # grade at the deepest point
        elif self.state == "BOTTOM":
            if angle > self.min_angle + self.hysteresis:
                self.state = "ASCENDING"
        elif self.state == "ASCENDING":
            if angle > self.max_angle - self.hysteresis:
                self.state = "TOP"
                self.rep_count += 1
                rep_completed = True
                if self.bottom_grade:
                    self.grades.append(self.bottom_grade)
        elif self.state == "TOP":
            self.state = "DESCENDING"
        return {"count": self.rep_count, "state": self.state, "rep_completed": rep_completed}

    def reset(self):
        self.state = "START"
        self.rep_count = 0
        self.grades = []
        self.last_grade = None


class BatchFormCheckRequest(BaseModel):
    exercise_id: str
    frames: list[str] = Field(..., description="Up to 12 base64 JPEG frames, in capture order")
    reset_counter: bool = True


class BatchFrameResult(BaseModel):
    frame_index: int
    detected: bool
    angle: Optional[float] = None
    grade: Optional[str] = None
    rep_count: int = 0
    rep_completed: bool = False
    rep_state: str = "START"
    message: Optional[str] = None


class BatchFormCheckResponse(BaseModel):
    exercise_id: str
    total_reps: int
    frames: list[BatchFrameResult]
    average_grade: Optional[str] = None
    grade_distribution: dict[str, int] = {}
    suggestions: list[str] = []


def _decode_landmarks(image_bytes: bytes) -> Optional[dict[str, Landmark]]:
    if _pose_model is None:
        return None
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    frame = np.array(img)
    result = _pose_model.process(frame)
    if not result.pose_landmarks:
        return None
    out = {}
    for name, idx in LANDMARKS.items():
        lm = result.pose_landmarks.landmark[idx]
        out[name] = Landmark(x=lm.x, y=lm.y, z=lm.z, visibility=lm.visibility)
    return out


@router.post("/analyze", response_model=FormCheckResponse)
async def analyze_form(req: FormCheckRequest):
    """Score a single captured frame for the given exercise."""
    if _pose_model is None:
        raise HTTPException(status_code=503, detail="Pose estimation model is not available on this server")

    if not req.image_base64 or len(req.image_base64) < 100:
        return FormCheckResponse(
            detected=False, exercise_id=req.exercise_id,
            message="No image received — capture a full-body frame first.",
        )

    try:
        image_bytes = base64.b64decode(req.image_base64, validate=False)
    except Exception:
        raise HTTPException(status_code=400, detail="image_base64 is not valid base64")

    try:
        landmarks = _decode_landmarks(image_bytes)
    except Exception:
        return FormCheckResponse(
            detected=False, exercise_id=req.exercise_id,
            message="Couldn't read that image — try a clearer, well-lit frame.",
        )
    if landmarks is None:
        return FormCheckResponse(
            detected=False, exercise_id=req.exercise_id,
            message="No person detected in frame — step back so your full body is visible.",
        )

    angle_fn = EXERCISE_ANGLES.get(req.exercise_id)
    if angle_fn is None:
        return FormCheckResponse(
            detected=True, exercise_id=req.exercise_id,
            message=f"Form scoring isn't tuned for '{req.exercise_id}' yet.",
        )

    angle = angle_fn(landmarks)

    joint_key = "elbow" if req.exercise_id in ("bench-press", "barbell-row", "push-up", "pull-up", "overhead-press", "bicep-curl") else (
        "knee" if req.exercise_id in ("barbell-back-squat", "lunge") else (
        "back" if req.exercise_id == "deadlift" else "elbow"
    ))
    assessment = score_form(req.exercise_id, {joint_key: angle})

    return FormCheckResponse(
        detected=True,
        exercise_id=req.exercise_id,
        angle=round(angle, 1),
        grade=assessment.overall_grade.value,
        penalties=assessment.penalties,
        suggestions=assessment.suggestions,
        rep_quality_pct=assessment.rep_quality_pct,
    )


@router.post("/analyze-batch", response_model=BatchFormCheckResponse)
async def analyze_form_batch(req: BatchFormCheckRequest):
    """Analyze a burst of frames and count reps with a hysteresis state machine.

    The mobile app captures frames every ~1-1.5s during a set and sends them in
    one call; the server returns per-frame angles, grades, and a running rep
    count so the client can show live feedback without streaming.
    """
    if _pose_model is None:
        raise HTTPException(status_code=503, detail="Pose estimation model is not available on this server")
    if not req.frames or len(req.frames) > 12:
        raise HTTPException(status_code=400, detail="Send between 1 and 12 frames")

    angle_fn = EXERCISE_ANGLES.get(req.exercise_id)
    if angle_fn is None:
        raise HTTPException(status_code=400, detail=f"Form scoring isn't tuned for '{req.exercise_id}'")

    joint_key = "elbow" if req.exercise_id in ("bench-press", "barbell-row", "push-up", "pull-up", "overhead-press", "bicep-curl") else (
        "knee" if req.exercise_id in ("barbell-back-squat", "lunge") else (
        "back" if req.exercise_id == "deadlift" else "elbow"
    ))

    # Squat/lunge count on knee flexion (bottom = ~90°); push/curl count on elbow extension
    machine = RepStateMachine(
        min_angle=90.0 if joint_key == "knee" else 100.0,
        max_angle=160.0,
        hysteresis=12.0,
    )
    if not req.reset_counter:
        pass  # client owns persistence; server counts within this batch

    results: list[BatchFrameResult] = []
    all_grades: list[str] = []
    suggestions: list[str] = []

    for i, frame_b64 in enumerate(req.frames):
        if not frame_b64 or len(frame_b64) < 100:
            results.append(BatchFrameResult(frame_index=i, detected=False, message="Empty frame skipped"))
            continue
        try:
            image_bytes = base64.b64decode(frame_b64, validate=False)
            landmarks = _decode_landmarks(image_bytes)
        except Exception:
            results.append(BatchFrameResult(frame_index=i, detected=False, message="Unreadable frame skipped"))
            continue
        if landmarks is None:
            results.append(BatchFrameResult(frame_index=i, detected=False, message="No person detected in frame"))
            continue

        angle = angle_fn(landmarks)
        assessment = score_form(req.exercise_id, {joint_key: angle})
        grade = assessment.overall_grade.value
        all_grades.append(grade)
        if assessment.suggestions:
            suggestions.extend(assessment.suggestions)

        step = machine.process(angle, grade)
        results.append(BatchFrameResult(
            frame_index=i,
            detected=True,
            angle=round(angle, 1),
            grade=grade,
            rep_count=step["count"],
            rep_completed=step["rep_completed"],
            rep_state=step["state"],
        ))

    grade_dist: dict[str, int] = {}
    for g in all_grades:
        grade_dist[g] = grade_dist.get(g, 0) + 1

    avg_grade = None
    if all_grades:
        order = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1}
        avg = sum(order.get(g, 0) for g in all_grades) / len(all_grades)
        avg_grade = min((g for g, v in order.items() if v <= round(avg)), key=lambda g: order[g]) if all_grades else None

    return BatchFormCheckResponse(
        exercise_id=req.exercise_id,
        total_reps=machine.rep_count,
        frames=results,
        average_grade=avg_grade,
        grade_distribution=grade_dist,
        suggestions=list(dict.fromkeys(suggestions))[:6],
    )


@router.get("/exercises")
async def supported_exercises():
    """List exercise IDs the form checker currently supports."""
    return {"exercise_ids": list(EXERCISE_ANGLES.keys()), "model_available": _pose_model is not None}

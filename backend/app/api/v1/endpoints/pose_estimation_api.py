"""
Pose Estimation & Form Checking API — real-time exercise form analysis.
"""
from __future__ import annotations

from enum import Enum
from functools import lru_cache

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()


# --- Response Models (fastapi-python: declare return type annotations) ---

class FormFeedback(str, Enum):
    GOOD = "good"
    WARNING = "warning"
    DANGER = "danger"


class AngleInfo(BaseModel):
    name: str
    degrees: float = Field(ge=0, le=360)


class FormCheckItem(BaseModel):
    check: str
    feedback: FormFeedback
    message: str


class FormCheckResponse(BaseModel):
    exercise: str | None
    phase: str
    rep_count: int
    overall_score: float = Field(ge=0, le=100)
    form_checks: list[FormCheckItem]
    angles: list[AngleInfo]


class ExerciseListResponse(BaseModel):
    exercises: list[str]
    count: int


# --- Input Validation (security-review: validate user input) ---

VALID_EXERCISES = frozenset({
    "squat", "deadlift", "bench_press", "overhead_press",
    "bicep_curl", "lateral_raise", "lunge", "plank", "push_up", "pull_up",
})


class FormCheckRequest(BaseModel):
    exercise_type: str = Field(
        default="squat",
        description="Exercise type to check form for",
        pattern=r"^[a-z_]+$",
    )
    landmarks: list[list[float]] = Field(
        min_length=1,
        max_length=500,
        description="Body landmark coordinates from pose estimator",
    )

    def model_post_init(self, __context: object) -> None:
        if self.exercise_type not in VALID_EXERCISES:
            raise ValueError(
                f"Invalid exercise_type '{self.exercise_type}'. "
                f"Valid: {sorted(VALID_EXERCISES)}"
            )


# --- Cached singleton (performance-optimization: avoid repeated instantiation) ---

@lru_cache(maxsize=1)
def _get_checker():
    from src.pose.form_checker import PoseFormChecker
    return PoseFormChecker()


# --- Routes ---

@router.post(
    "/form-check",
    response_model=FormCheckResponse,
    summary="Check exercise form from pose landmarks",
)
async def check_form(req: FormCheckRequest) -> FormCheckResponse:
    """Analyze body landmarks and return form feedback with angles and rep count."""
    from src.pose.form_checker import ExerciseType

    exercise_map = {
        "squat": ExerciseType.SQUAT,
        "deadlift": ExerciseType.DEADLIFT,
        "bench_press": ExerciseType.BENCH_PRESS,
        "overhead_press": ExerciseType.OVERHEAD_PRESS,
    }
    exercise = exercise_map.get(req.exercise_type, ExerciseType.SQUAT)
    checker = _get_checker()

    try:
        result = checker.check_exercise(exercise, [tuple(lm) for lm in req.landmarks])
    except (ValueError, IndexError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return FormCheckResponse(
        exercise=result.exercise_type.value if result.exercise_type else None,
        phase=result.phase.value,
        rep_count=result.rep_count,
        overall_score=result.overall_score,
        form_checks=[
            FormCheckItem(
                check=fc.check_name,
                feedback=FormFeedback(fc.feedback.value),
                message=fc.message,
            )
            for fc in result.form_checks
        ],
        angles=[
            AngleInfo(name=a.name, degrees=a.angle_degrees)
            for a in result.angles
        ],
    )


@router.get(
    "/exercises",
    response_model=ExerciseListResponse,
    summary="List supported exercises",
)
async def list_exercises() -> ExerciseListResponse:
    return ExerciseListResponse(
        exercises=sorted(VALID_EXERCISES),
        count=len(VALID_EXERCISES),
    )

"""Workout templates: save, load, reuse custom workout routines."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter()


class TemplateExercise(BaseModel):
    exercise_id: str
    name: str
    target_muscle: str
    sets: int = Field(ge=1, le=20, default=3)
    target_reps: str = Field(default="8-12")
    target_rpe: float = Field(ge=1, le=10, default=7)
    rest_seconds: int = Field(ge=0, le=600, default=90)
    notes: Optional[str] = None


class WorkoutTemplateCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100, examples=["Push Day A"])
    description: str = Field(max_length=500, default="")
    category: str = Field(default="custom", examples=["push", "pull", "legs", "upper", "lower", "full_body", "custom"])
    exercises: List[TemplateExercise] = Field(min_length=1)
    target_duration_minutes: int = Field(ge=10, le=180, default=45)
    difficulty: str = Field(default="intermediate", examples=["beginner", "intermediate", "advanced"])
    tags: List[str] = Field(default_factory=list)


class WorkoutTemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    exercises: List[TemplateExercise]
    target_duration_minutes: int
    difficulty: str
    tags: List[str]
    created_by: str = "system"
    created_at: str = "2026-01-01T00:00:00Z"
    use_count: int = 0
    is_builtin: bool = False


class TemplateUseRequest(BaseModel):
    template_id: str


# In-memory storage
templates: dict = {}  # user_id -> list of templates
use_counts: dict[str, int] = {}  # template_id -> count


# --- Built-in templates ---
BUILTIN_TEMPLATES = [
    WorkoutTemplateResponse(
        id="builtin_push", name="Push Day", description="Chest, shoulders, triceps",
        category="push", exercises=[
            TemplateExercise(exercise_id="bench_press", name="Barbell Bench Press", target_muscle="chest", sets=4, target_reps="6-8", target_rpe=8, rest_seconds=120),
            TemplateExercise(exercise_id="ohp", name="Overhead Press", target_muscle="shoulders", sets=3, target_reps="8-10", target_rpe=7, rest_seconds=90),
            TemplateExercise(exercise_id="incline_db", name="Incline Dumbbell Press", target_muscle="chest", sets=3, target_reps="10-12", target_rpe=7, rest_seconds=90),
            TemplateExercise(exercise_id="lateral_raise", name="Lateral Raise", target_muscle="shoulders", sets=3, target_reps="12-15", target_rpe=6, rest_seconds=60),
            TemplateExercise(exercise_id="tricep_pushdown", name="Tricep Pushdown", target_muscle="triceps", sets=3, target_reps="10-12", target_rpe=7, rest_seconds=60),
        ],
        target_duration_minutes=50, difficulty="intermediate", tags=["push", "upper"], is_builtin=True,
    ),
    WorkoutTemplateResponse(
        id="builtin_pull", name="Pull Day", description="Back, biceps, rear delts",
        category="pull", exercises=[
            TemplateExercise(exercise_id="deadlift", name="Barbell Deadlift", target_muscle="back", sets=3, target_reps="5-6", target_rpe=9, rest_seconds=150),
            TemplateExercise(exercise_id="barbell_row", name="Barbell Row", target_muscle="back", sets=4, target_reps="8-10", target_rpe=8, rest_seconds=90),
            TemplateExercise(exercise_id="lat_pulldown", name="Lat Pulldown", target_muscle="back", sets=3, target_reps="10-12", target_rpe=7, rest_seconds=90),
            TemplateExercise(exercise_id="face_pull", name="Face Pull", target_muscle="shoulders", sets=3, target_reps="12-15", target_rpe=6, rest_seconds=60),
            TemplateExercise(exercise_id="barbell_curl", name="Barbell Curl", target_muscle="biceps", sets=3, target_reps="10-12", target_rpe=7, rest_seconds=60),
        ],
        target_duration_minutes=55, difficulty="intermediate", tags=["pull", "upper"], is_builtin=True,
    ),
    WorkoutTemplateResponse(
        id="builtin_legs", name="Leg Day", description="Quads, hamstrings, glutes, calves",
        category="legs", exercises=[
            TemplateExercise(exercise_id="squat", name="Barbell Back Squat", target_muscle="quadriceps", sets=4, target_reps="6-8", target_rpe=8, rest_seconds=150),
            TemplateExercise(exercise_id="romanian_deadlift", name="Romanian Deadlift", target_muscle="hamstrings", sets=3, target_reps="8-10", target_rpe=7, rest_seconds=120),
            TemplateExercise(exercise_id="leg_press", name="Leg Press", target_muscle="quadriceps", sets=3, target_reps="10-12", target_rpe=7, rest_seconds=90),
            TemplateExercise(exercise_id="leg_curl", name="Leg Curl", target_muscle="hamstrings", sets=3, target_reps="12-15", target_rpe=6, rest_seconds=60),
            TemplateExercise(exercise_id="calf_raise", name="Calf Raise", target_muscle="calves", sets=4, target_reps="15-20", target_rpe=6, rest_seconds=45),
        ],
        target_duration_minutes=55, difficulty="intermediate", tags=["legs", "lower"], is_builtin=True,
    ),
    WorkoutTemplateResponse(
        id="builtin_upper", name="Upper Body", description="Full upper body session",
        category="upper", exercises=[
            TemplateExercise(exercise_id="bench_press", name="Bench Press", target_muscle="chest", sets=3, target_reps="8-10", target_rpe=7, rest_seconds=90),
            TemplateExercise(exercise_id="barbell_row", name="Barbell Row", target_muscle="back", sets=3, target_reps="8-10", target_rpe=7, rest_seconds=90),
            TemplateExercise(exercise_id="ohp", name="Overhead Press", target_muscle="shoulders", sets=3, target_reps="10-12", target_rpe=7, rest_seconds=90),
            TemplateExercise(exercise_id="lat_pulldown", name="Lat Pulldown", target_muscle="back", sets=3, target_reps="10-12", target_rpe=7, rest_seconds=60),
            TemplateExercise(exercise_id="tricep_dips", name="Tricep Dips", target_muscle="triceps", sets=3, target_reps="10-12", target_rpe=7, rest_seconds=60),
            TemplateExercise(exercise_id="barbell_curl", name="Barbell Curl", target_muscle="biceps", sets=3, target_reps="10-12", target_rpe=7, rest_seconds=60),
        ],
        target_duration_minutes=60, difficulty="intermediate", tags=["upper", "full"], is_builtin=True,
    ),
]


@router.get("", response_model=List[WorkoutTemplateResponse])
async def list_templates(
    user_id: str = Query("default"),
    category: Optional[str] = Query(None),
    include_builtin: bool = Query(True),
):
    """List available workout templates."""
    user_templates = templates.get(user_id, [])
    result = list(user_templates)

    if include_builtin:
        builtin = BUILTIN_TEMPLATES
        if category:
            builtin = [t for t in builtin if t.category == category]
        result = builtin + result
    elif category:
        result = [t for t in result if t.category == category]

    return result


@router.get("/categories")
async def list_categories():
    """List available template categories."""
    return {
        "categories": [
            {"id": "push", "name": "Push", "description": "Chest, shoulders, triceps"},
            {"id": "pull", "name": "Pull", "description": "Back, biceps, rear delts"},
            {"id": "legs", "name": "Legs", "description": "Quads, hamstrings, glutes"},
            {"id": "upper", "name": "Upper Body", "description": "Full upper body"},
            {"id": "lower", "name": "Lower Body", "description": "Full lower body"},
            {"id": "full_body", "name": "Full Body", "description": "Complete workout"},
            {"id": "custom", "name": "Custom", "description": "User-created templates"},
        ]
    }


@router.get("/{template_id}", response_model=WorkoutTemplateResponse)
async def get_template(template_id: str, user_id: str = Query("default")):
    """Get a specific template."""
    # Check builtins first
    for t in BUILTIN_TEMPLATES:
        if t.id == template_id:
            return t

    # Check user templates
    for t in templates.get(user_id, []):
        if t.id == template_id:
            return t

    raise HTTPException(status_code=404, detail="Template not found")


@router.post("", response_model=WorkoutTemplateResponse, status_code=201)
async def create_template(request: WorkoutTemplateCreate, user_id: str = Query("default")):
    """Create a custom workout template."""
    tid = str(uuid.uuid4())[:8]
    template = WorkoutTemplateResponse(
        id=tid,
        name=request.name,
        description=request.description,
        category=request.category,
        exercises=request.exercises,
        target_duration_minutes=request.target_duration_minutes,
        difficulty=request.difficulty,
        tags=request.tags,
        created_by=user_id,
        created_at=datetime.now(timezone.utc).isoformat(),
        use_count=0,
    )
    templates.setdefault(user_id, []).append(template)
    return template


@router.put("/{template_id}", response_model=WorkoutTemplateResponse)
async def update_template(
    template_id: str, request: WorkoutTemplateCreate, user_id: str = Query("default"),
):
    """Update a custom template."""
    for t in templates.get(user_id, []):
        if t.id == template_id:
            t.name = request.name
            t.description = request.description
            t.category = request.category
            t.exercises = request.exercises
            t.target_duration_minutes = request.target_duration_minutes
            t.difficulty = request.difficulty
            t.tags = request.tags
            return t

    raise HTTPException(status_code=404, detail="Template not found or is builtin")


@router.delete("/{template_id}")
async def delete_template(template_id: str, user_id: str = Query("default")):
    """Delete a custom template."""
    user_templates = templates.get(user_id, [])
    for i, t in enumerate(user_templates):
        if t.id == template_id:
            user_templates.pop(i)
            return {"deleted": True}

    raise HTTPException(status_code=404, detail="Template not found or is builtin")


@router.post("/{template_id}/use")
async def use_template(template_id: str, user_id: str = Query("default")):
    """Mark a template as used (increments use count)."""
    # Find template
    for t in BUILTIN_TEMPLATES:
        if t.id == template_id:
            use_counts[template_id] = use_counts.get(template_id, 0) + 1
            return {"message": f"Template '{t.name}' marked as used", "use_count": use_counts[template_id]}

    for t in templates.get(user_id, []):
        if t.id == template_id:
            t.use_count += 1
            return {"message": f"Template '{t.name}' marked as used", "use_count": t.use_count}

    raise HTTPException(status_code=404, detail="Template not found")


@router.post("/from-workout/{workout_id}")
async def create_from_workout(workout_id: str, name: str = Query(...), user_id: str = Query("default")):
    """Create a template from an existing completed workout."""
    try:
        from app.api.v1.endpoints.workouts import workout_history
        workouts = workout_history.get(user_id, [])
    except (ImportError, AttributeError):
        workouts = []

    workout = next((w for w in workouts if w.get("workout_id") == workout_id), None)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    exercises = []
    for ex in workout.get("exercises", []):
        exercises.append(TemplateExercise(
            exercise_id=ex.get("exercise_id", ""),
            name=ex.get("name", ""),
            target_muscle=ex.get("target_muscle", ""),
            sets=ex.get("sets", 3),
            target_reps=ex.get("target_reps", "8-12"),
            target_rpe=ex.get("target_rpe", 7),
            rest_seconds=ex.get("rest_seconds", 90),
        ))

    if not exercises:
        raise HTTPException(status_code=400, detail="Workout has no exercises")

    tid = str(uuid.uuid4())[:8]
    template = WorkoutTemplateResponse(
        id=tid, name=name,
        description=f"Created from workout on {workout.get('target_date', 'unknown')}",
        category="custom", exercises=exercises,
        target_duration_minutes=workout.get("target_duration_minutes", 45),
        difficulty="intermediate", tags=["from_workout"],
        created_by=user_id, created_at=datetime.now(timezone.utc).isoformat(),
    )
    templates.setdefault(user_id, []).append(template)
    return template

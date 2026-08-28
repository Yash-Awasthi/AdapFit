"""Warmup/cooldown routine generator: dynamic stretching based on target muscles."""
from fastapi import APIRouter, Query, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional


def _muscles_from_request(request: Request) -> list[str]:
    """Read muscle list from either `target_muscles` (mobile app) or `muscles` (legacy)."""
    raw = request.query_params.get("target_muscles") or request.query_params.get("muscles")
    if not raw:
        raise HTTPException(status_code=400, detail="Provide target_muscles (comma-separated)")
    return [m.strip() for m in raw.split(",") if m.strip()]

router = APIRouter()


class StretchExercise(BaseModel):
    name: str
    duration_seconds: int
    muscle_group: str
    type: str  # "dynamic", "static", "foam_roll", "activation"
    instructions: str
    sets: int = 1
    rest_seconds: int = 0


class WarmupCooldownRoutine(BaseModel):
    name: str
    routine_type: str  # "warmup", "cooldown"
    target_muscles: List[str]
    total_duration_seconds: int
    exercises: List[StretchExercise]
    phase: str  # "general", "specific", "activation"
    notes: str


# --- Stretch database ---
WARMUP_STRETCHES = {
    "chest": [
        {"name": "Arm Circles", "dur": 30, "type": "dynamic", "instructions": "Extend arms to sides, make small circles gradually increasing size.", "muscle_group": "chest"},
        {"name": "Chest Opener", "dur": 20, "type": "dynamic", "instructions": "Clasp hands behind back, lift arms and squeeze shoulder blades.", "muscle_group": "chest"},
    ],
    "back": [
        {"name": "Cat-Cow", "dur": 30, "type": "dynamic", "instructions": "On all fours, alternate arching and rounding your back.", "muscle_group": "back"},
        {"name": "Thoracic Rotations", "dur": 30, "type": "dynamic", "instructions": "Side-lying, rotate top arm open keeping hips stacked.", "muscle_group": "back"},
    ],
    "shoulders": [
        {"name": "Shoulder Pass-Throughs", "dur": 30, "type": "dynamic", "instructions": "Hold band/bar wide, pass over head and behind back.", "muscle_group": "shoulders"},
        {"name": "Wall Slides", "dur": 30, "type": "dynamic", "instructions": "Stand against wall, slide arms up and down keeping contact.", "muscle_group": "shoulders"},
    ],
    "biceps": [
        {"name": "Arm Cross-Body Stretch", "dur": 20, "type": "dynamic", "instructions": "Pull arm across chest, alternate sides.", "muscle_group": "biceps"},
    ],
    "triceps": [
        {"name": "Overhead Tricep Stretch", "dur": 20, "type": "dynamic", "instructions": "Reach hand down back, gently push elbow with other hand.", "muscle_group": "triceps"},
    ],
    "quadriceps": [
        {"name": "Walking Lunges", "dur": 40, "type": "dynamic", "instructions": "Step forward into lunge, alternate legs. 10 per side.", "muscle_group": "quadriceps"},
        {"name": "Leg Swings", "dur": 30, "type": "dynamic", "instructions": "Hold support, swing leg forward and back. 15 per side.", "muscle_group": "quadriceps"},
    ],
    "hamstrings": [
        {"name": "Frankenstein Kicks", "dur": 30, "type": "dynamic", "instructions": "Walk forward kicking leg up to opposite hand. 10 per side.", "muscle_group": "hamstrings"},
        {"name": "Inchworms", "dur": 30, "type": "dynamic", "instructions": "Hinge at hips, walk hands to plank, walk back. 5 reps.", "muscle_group": "hamstrings"},
    ],
    "glutes": [
        {"name": "Glute Bridges", "dur": 30, "type": "activation", "instructions": "Lie on back, drive hips up squeezing glutes. 15 reps.", "muscle_group": "glutes"},
        {"name": "Fire Hydrants", "dur": 30, "type": "dynamic", "instructions": "On all fours, lift knee out to side. 12 per side.", "muscle_group": "glutes"},
    ],
    "calves": [
        {"name": "Calf Raises", "dur": 30, "type": "dynamic", "instructions": "Rise onto toes, lower slowly. 20 reps.", "muscle_group": "calves"},
    ],
    "core": [
        {"name": "Dead Bugs", "dur": 30, "type": "activation", "instructions": "Lie on back, extend opposite arm and leg. 10 per side.", "muscle_group": "core"},
        {"name": "Bird Dogs", "dur": 30, "type": "activation", "instructions": "On all fours, extend opposite arm and leg. 10 per side.", "muscle_group": "core"},
    ],
    "hip_flexors": [
        {"name": "Kneeling Hip Flexor Stretch", "dur": 30, "type": "dynamic", "instructions": "Half-kneeling, push hips forward gently. 15 per side.", "muscle_group": "hip_flexors"},
    ],
}

COOLDOWN_STRETCHES = {
    "chest": [
        {"name": "Doorway Chest Stretch", "dur": 30, "type": "static", "instructions": "Place forearms on door frame, lean forward. Hold.", "muscle_group": "chest"},
    ],
    "back": [
        {"name": "Child's Pose", "dur": 45, "type": "static", "instructions": "Kneel, sit back on heels, reach arms forward. Hold.", "muscle_group": "back"},
        {"name": "Seated Spinal Twist", "dur": 30, "type": "static", "instructions": "Sit cross-legged, twist torso to each side. Hold 15s.", "muscle_group": "back"},
    ],
    "shoulders": [
        {"name": "Cross-Body Shoulder Stretch", "dur": 30, "type": "static", "instructions": "Pull arm across chest, hold 15s per side.", "muscle_group": "shoulders"},
    ],
    "biceps": [
        {"name": "Wall Bicep Stretch", "dur": 30, "type": "static", "instructions": "Place palm on wall behind you, turn away. 15s per side.", "muscle_group": "biceps"},
    ],
    "triceps": [
        {"name": "Overhead Tricep Stretch", "dur": 30, "type": "static", "instructions": "Reach hand down back, hold elbow. 15s per side.", "muscle_group": "triceps"},
    ],
    "quadriceps": [
        {"name": "Standing Quad Stretch", "dur": 30, "type": "static", "instructions": "Pull foot to glute, hold 15s per side.", "muscle_group": "quadriceps"},
    ],
    "hamstrings": [
        {"name": "Standing Hamstring Stretch", "dur": 30, "type": "static", "instructions": "Place heel on low surface, hinge forward. 15s per side.", "muscle_group": "hamstrings"},
        {"name": "Pigeon Pose", "dur": 45, "type": "static", "instructions": "One leg bent under, other extended back. Hold.", "muscle_group": "hamstrings"},
    ],
    "glutes": [
        {"name": "Figure-4 Stretch", "dur": 30, "type": "static", "instructions": "Lie on back, cross ankle over knee, pull toward chest. 15s per side.", "muscle_group": "glutes"},
    ],
    "calves": [
        {"name": "Wall Calf Stretch", "dur": 30, "type": "static", "instructions": "Hands on wall, step back with one leg, press heel down. 15s per side.", "muscle_group": "calves"},
    ],
    "core": [
        {"name": "Cobra Stretch", "dur": 30, "type": "static", "instructions": "Lie face down, press up lifting chest. Hold.", "muscle_group": "core"},
    ],
    "hip_flexors": [
        {"name": "Half-Kneeling Hip Flexor", "dur": 30, "type": "static", "instructions": "Half-kneeling, push hips forward gently. 15s per side.", "muscle_group": "hip_flexors"},
    ],
}

# General warmup (always included)
GENERAL_WARMUP = [
    {"name": "Jumping Jacks", "dur": 30, "type": "dynamic", "instructions": "Full range of motion, moderate pace.", "muscle_group": "full_body"},
    {"name": "High Knees", "dur": 30, "type": "dynamic", "instructions": "Drive knees up to hip height, pump arms.", "muscle_group": "full_body"},
    {"name": "Butt Kicks", "dur": 20, "type": "dynamic", "instructions": "Kick heels to glutes while jogging in place.", "muscle_group": "full_body"},
]


def generate_warmup(target_muscles: List[str], duration_minutes: int = 10) -> WarmupCooldownRoutine:
    """Generate a dynamic warmup routine based on target muscles."""
    exercises = []

    # Add general warmup first
    for g in GENERAL_WARMUP:
        exercises.append(StretchExercise(
            name=g["name"], duration_seconds=g["dur"], muscle_group="full_body",
            type=g["type"], instructions=g["instructions"],
        ))

    # Add muscle-specific dynamic stretches
    seen_muscles = set()
    for muscle in target_muscles:
        muscle_lower = muscle.lower().replace(" ", "_")
        if muscle_lower in WARMUP_STRETCHES and muscle_lower not in seen_muscles:
            seen_muscles.add(muscle_lower)
            for s in WARMUP_STRETCHES[muscle_lower][:2]:  # Max 2 per muscle
                exercises.append(StretchExercise(
                    name=s["name"], duration_seconds=s["dur"],
                    muscle_group=s["muscle_group"], type=s["type"],
                    instructions=s["instructions"],
                ))

    total = sum(e.duration_seconds for e in exercises)

    return WarmupCooldownRoutine(
        name=f"Dynamic Warmup ({', '.join(target_muscles[:3])})",
        routine_type="warmup",
        target_muscles=target_muscles,
        total_duration_seconds=total,
        exercises=exercises,
        phase="specific",
        notes="Complete all exercises in order. Focus on range of motion, not speed.",
    )


def generate_cooldown(target_muscles: List[str], duration_minutes: int = 8) -> WarmupCooldownRoutine:
    """Generate a static cooldown routine based on target muscles."""
    exercises = []

    for muscle in target_muscles:
        muscle_lower = muscle.lower().replace(" ", "_")
        if muscle_lower in COOLDOWN_STRETCHES:
            for s in COOLDOWN_STRETCHES[muscle_lower][:2]:  # Max 2 per muscle
                exercises.append(StretchExercise(
                    name=s["name"], duration_seconds=s["dur"],
                    muscle_group=s["muscle_group"], type=s["type"],
                    instructions=s["instructions"],
                ))

    if not exercises:
        # Fallback full-body cooldown
        exercises = [
            StretchExercise(name="Standing Forward Fold", duration_seconds=30, muscle_group="hamstrings", type="static", instructions="Hinge at hips, let head hang. Hold."),
            StretchExercise(name="Child's Pose", duration_seconds=45, muscle_group="back", type="static", instructions="Kneel, sit back on heels, reach forward. Hold."),
            StretchExercise(name="Cobra Stretch", duration_seconds=30, muscle_group="core", type="static", instructions="Lie face down, press up lifting chest. Hold."),
        ]

    total = sum(e.duration_seconds for e in exercises)

    return WarmupCooldownRoutine(
        name=f"Cool-Down ({', '.join(target_muscles[:3])})",
        routine_type="cooldown",
        target_muscles=target_muscles,
        total_duration_seconds=total,
        exercises=exercises,
        phase="general",
        notes="Hold each stretch 15-30 seconds. Breathe deeply. Don't bounce.",
    )


@router.get("/warmup", response_model=WarmupCooldownRoutine)
async def get_warmup(request: Request, duration: int = Query(10, ge=5, le=30)):
    """Generate a dynamic warmup for target muscles."""
    return generate_warmup(_muscles_from_request(request), duration)


@router.get("/cooldown", response_model=WarmupCooldownRoutine)
async def get_cooldown(request: Request, duration: int = Query(8, ge=5, le=20)):
    """Generate a static cooldown for target muscles."""
    return generate_cooldown(_muscles_from_request(request), duration)


@router.get("/full", response_model=dict)
async def get_full_routine(request: Request):
    """Generate both warmup and cooldown routines."""
    muscle_list = _muscles_from_request(request)
    warmup = generate_warmup(muscle_list)
    cooldown = generate_cooldown(muscle_list)
    return {
        "warmup": warmup.model_dump(),
        "cooldown": cooldown.model_dump(),
        "total_duration_seconds": warmup.total_duration_seconds + cooldown.total_duration_seconds,
    }


@router.get("/muscles")
async def available_muscles():
    """List available muscle groups for routine generation."""
    return {
        "muscles": [
            {"id": m, "name": m.replace("_", " ").title()}
            for m in WARMUP_STRETCHES.keys()
        ]
    }

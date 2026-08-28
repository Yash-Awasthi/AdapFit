"""Exercise Library Browser — advanced search with muscle, equipment, difficulty filters."""

from __future__ import annotations
from fastapi import APIRouter, Query
from typing import Optional
from app.services.exercise_service import exercise_service

router = APIRouter()

MUSCLE_GROUPS = [
    "chest", "back", "shoulders", "biceps", "triceps",
    "quadriceps", "hamstrings", "glutes", "calves", "core",
    "forearms", "full_body",
]

EQUIPMENT = [
    "barbell", "dumbbells", "cable", "machine", "bodyweight",
    "kettlebell", "bands", "ez-bar", "smith_machine",
]

DIFFICULTY_LEVELS = ["beginner", "intermediate", "advanced"]

MOVEMENT_PATTERNS = ["push", "pull", "squat", "hinge", "carry", "rotation", "isolation"]


@router.get("")
async def search_exercises(
    q: Optional[str] = Query(None, description="Search query"),
    muscle: Optional[str] = Query(None, description="Filter by muscle group"),
    equipment: Optional[str] = Query(None, description="Filter by equipment"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    pattern: Optional[str] = Query(None, description="Filter by movement pattern"),
    category: Optional[str] = Query(None, description="Filter by category (strength/stretching/cardio)"),
    axial_max: Optional[int] = Query(None, ge=1, le=5, description="Max axial load rating"),
    sort: str = Query("name", pattern="^(name|difficulty|axial|muscle)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Search and filter the exercise library."""
    all_exercises = exercise_service.get_all()

    # Convert to dicts
    exercises = []
    for ex in all_exercises:
        ex_dict = {
            "id": ex.id,
            "name": ex.name,
            "category": ex.category,
            "primary_muscles": ex.primary_muscles,
            "secondary_muscles": getattr(ex, "secondary_muscles", []),
            "equipment": ex.equipment,
            "mechanics": getattr(ex, "mechanics", "compound"),
            "axial_loading_rating": ex.axial_loading_rating,
            "gif_url": getattr(ex, "gif_url", None),
            "instructions": getattr(ex, "instructions", []),
        }
        exercises.append(ex_dict)

    # Apply filters
    if q:
        query = q.lower()
        exercises = [
            e for e in exercises
            if query in e["name"].lower()
            or query in " ".join(e["primary_muscles"]).lower()
            or query in e.get("equipment", "").lower()
        ]

    if muscle:
        exercises = [e for e in exercises if muscle in e["primary_muscles"]]

    if equipment:
        exercises = [e for e in exercises if equipment.lower() in (e.get("equipment") or "").lower()]

    if difficulty:
        # Map difficulty to axial load ranges
        diff_ranges = {"beginner": (1, 2), "intermediate": (3, 3), "advanced": (4, 5)}
        low, high = diff_ranges.get(difficulty, (1, 5))
        exercises = [e for e in exercises if low <= e["axial_loading_rating"] <= high]

    if pattern:
        exercises = [e for e in exercises if pattern == e.get("mechanics", "")]

    if category:
        exercises = [e for e in exercises if category == e["category"]]

    if axial_max is not None:
        exercises = [e for e in exercises if e["axial_loading_rating"] <= axial_max]

    # Sort
    if sort == "difficulty":
        exercises.sort(key=lambda e: e["axial_loading_rating"])
    elif sort == "axial":
        exercises.sort(key=lambda e: e["axial_loading_rating"], reverse=True)
    elif sort == "muscle":
        exercises.sort(key=lambda e: e["primary_muscles"][0] if e["primary_muscles"] else "")
    else:
        exercises.sort(key=lambda e: e["name"])

    total = len(exercises)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "items": exercises[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "filters_applied": {
            "q": q, "muscle": muscle, "equipment": equipment,
            "difficulty": difficulty, "pattern": pattern,
            "category": category, "axial_max": axial_max,
        },
    }


@router.get("/filters")
async def get_available_filters():
    """Get all available filter options with counts."""
    all_exercises = exercise_service.get_all()

    muscle_counts: dict[str, int] = {}
    equipment_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    difficulty_counts = {"beginner": 0, "intermediate": 0, "advanced": 0}

    for ex in all_exercises:
        for m in ex.primary_muscles:
            muscle_counts[m] = muscle_counts.get(m, 0) + 1
        equip = getattr(ex, "equipment", "unknown")
        equipment_counts[equip] = equipment_counts.get(equip, 0) + 1
        cat = ex.category
        category_counts[cat] = category_counts.get(cat, 0) + 1

        axial = ex.axial_loading_rating
        if axial <= 2:
            difficulty_counts["beginner"] += 1
        elif axial <= 3:
            difficulty_counts["intermediate"] += 1
        else:
            difficulty_counts["advanced"] += 1

    return {
        "muscle_groups": [{"name": m, "count": c} for m, c in sorted(muscle_counts.items(), key=lambda x: x[1], reverse=True)],
        "equipment": [{"name": e, "count": c} for e, c in sorted(equipment_counts.items(), key=lambda x: x[1], reverse=True)],
        "categories": [{"name": c, "count": n} for c, n in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)],
        "difficulty": difficulty_counts,
        "total_exercises": len(all_exercises),
    }


@router.get("/by-muscle/{muscle}")
async def get_exercises_by_muscle(muscle: str, limit: int = Query(20, ge=1, le=50)):
    """Get exercises targeting a specific muscle group."""
    all_exercises = exercise_service.get_all()
    matching = [
        {
            "id": ex.id, "name": ex.name, "equipment": getattr(ex, "equipment", ""),
            "axial_loading_rating": ex.axial_loading_rating,
            "gif_url": getattr(ex, "gif_url", None),
        }
        for ex in all_exercises
        if muscle in ex.primary_muscles
    ]
    return {"muscle": muscle, "exercises": matching[:limit], "total": len(matching)}


@router.get("/{exercise_id}/detail")
async def get_exercise_detail(exercise_id: str):
    """Get full exercise details including GIF, instructions, and substitutions."""
    all_exercises = exercise_service.get_all()
    ex = next((e for e in all_exercises if e.id == exercise_id), None)
    if not ex:
        return {"error": "Exercise not found"}

    # Get substitutions
    from app.services.exercise_substitution import get_substitutions
    subs = get_substitutions(exercise_id)

    return {
        "id": ex.id,
        "name": ex.name,
        "category": ex.category,
        "primary_muscles": ex.primary_muscles,
        "secondary_muscles": getattr(ex, "secondary_muscles", []),
        "equipment": getattr(ex, "equipment", ""),
        "mechanics": getattr(ex, "mechanics", "compound"),
        "axial_loading_rating": ex.axial_loading_rating,
        "gif_url": getattr(ex, "gif_url", None),
        "instructions": getattr(ex, "instructions", []),
        "substitutions": subs[:3],
    }

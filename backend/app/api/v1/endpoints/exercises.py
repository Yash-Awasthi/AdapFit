from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from app.models.schemas import ExerciseItem, SemanticSearchRequest, ExerciseSubstitutionRequest
from app.services.exercise_service import exercise_service
from app.services.vector_store import vector_store
from app.core.cache import api_response_cache as cache

router = APIRouter()

@router.get("")
async def list_exercises(
    category: Optional[str] = Query(None, description="strength, stretching, cardio"),
    equipment: Optional[str] = Query(None, description="barbell, dumbbells, bodyweight, cables"),
    muscle: Optional[str] = Query(None, description="chest, back, quads, hamstrings, shoulders, core"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List exercises with optional filters. Paginated."""
    eq_list = [equipment] if equipment else None
    muscles = [muscle] if muscle else None
    # Check cache for filter+page combo
    cache_key = f"/exercises:{category}:{equipment}:{muscle}:{page}:{page_size}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    all_exercises = exercise_service.filter_exercises(
        equipment_list=eq_list,
        target_muscles=muscles,
        category=category
    )
    total = len(all_exercises)
    start = (page - 1) * page_size
    items = all_exercises[start:start + page_size]
    result = {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }
    cache.set(cache_key, result, ttl=120)  # Cache for 2 min
    return result

@router.get("/{exercise_id}", response_model=ExerciseItem)
async def get_exercise(exercise_id: str):
    ex = exercise_service.get_by_id(exercise_id)
    if not ex:
        raise HTTPException(status_code=404, detail=f"Exercise {exercise_id} not found")
    return ex

@router.post("/search")
async def search_exercises(req: SemanticSearchRequest):
    """Semantic search for exercises using vector similarity."""
    results = vector_store.semantic_search(
        query=req.query,
        top_k=req.top_k,
        filter_equipment=req.filter_equipment,
        filter_muscles=req.filter_muscles,
        exclude_muscles=req.exclude_muscles,
    )
    return {"query": req.query, "items": results, "count": len(results)}

@router.post("/{exercise_id}/alternatives")
async def find_alternatives(exercise_id: str, req: ExerciseSubstitutionRequest):
    """Find semantically similar exercise alternatives."""
    alternatives = vector_store.find_alternatives(
        exercise_id=exercise_id,
        top_k=req.top_k,
        exclude_muscles=req.exclude_muscles,
    )
    return {"exercise_id": exercise_id, "items": alternatives, "count": len(alternatives)}

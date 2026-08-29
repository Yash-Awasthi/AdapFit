"""
AdapFit Vector Store
Semantic exercise search backed by pgvector when DATABASE_URL is configured.
Falls back to an in-process cosine scan (degraded mode) otherwise.
"""
import asyncio
import math
import threading
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.db import get_pool

# Lazy-loaded ML dependency — imported only when first needed, not at boot.
_EMBED_MODEL = None
_HAS_EMBEDDINGS = None  # None = not checked yet
_DIMENSION = 384  # all-MiniLM-L6-v2 dimension

_PG_SEARCH_SQL = """
    SELECT id, name, category, primary_muscles, secondary_muscles, equipment,
           mechanics, axial_loading_rating, gif_url, instructions,
           1 - (embedding <=> $1) AS similarity_score
    FROM exercises
    WHERE embedding IS NOT NULL
      AND ($2::text[] IS NULL OR equipment = ANY($2) OR equipment ILIKE '%bodyweight%')
      AND ($3::text[] IS NULL OR primary_muscles && $3::text[])
      AND ($4::text[] IS NULL OR NOT (primary_muscles && $4::text[]))
    ORDER BY embedding <=> $1
    LIMIT $5
"""

# ponytail: asyncpg pools are bound to the loop that created them. All pgvector
# calls run on this one dedicated background loop so the pool stays usable
# across sync calls; a future caller of get_pool() on the main loop would need
# to route through this same bridge instead.
_bg_loop: Optional[asyncio.AbstractEventLoop] = None
_bg_lock = threading.Lock()


def _get_background_loop() -> asyncio.AbstractEventLoop:
    global _bg_loop
    if _bg_loop is None:
        with _bg_lock:
            if _bg_loop is None:
                loop = asyncio.new_event_loop()
                threading.Thread(target=loop.run_forever, daemon=True).start()
                _bg_loop = loop
    return _bg_loop


def _run_sync(coro):
    return asyncio.run_coroutine_threadsafe(coro, _get_background_loop()).result()


def _ensure_sentence_transformers():
    """Lazily load sentence-transformers model on first use."""
    global _EMBED_MODEL, _HAS_EMBEDDINGS
    if _HAS_EMBEDDINGS is not None:
        return
    try:
        from sentence_transformers import SentenceTransformer
        _EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        _HAS_EMBEDDINGS = True
    except Exception:
        _EMBED_MODEL = None
        _HAS_EMBEDDINGS = False


def exercise_text(ex: Dict[str, Any]) -> str:
    """Text representation of an exercise used to build its embedding."""
    return f"{ex.get('name', '')} {' '.join(ex.get('primary_muscles', []))} {ex.get('equipment', '')} {ex.get('mechanic', '')} {ex.get('category', '')}"


def embed(text: str) -> List[float]:
    """Real sentence-transformers embedding. Raises if the model is not installed —
    callers writing to pgvector need real vectors, not the degraded hash fallback."""
    _ensure_sentence_transformers()
    if not (_HAS_EMBEDDINGS and _EMBED_MODEL is not None):
        raise RuntimeError("sentence-transformers is not available; install it to compute exercise embeddings")
    return _EMBED_MODEL.encode(text).tolist()


def _simple_embedding(text: str) -> List[float]:
    """Hash-based fallback embedding when sentence-transformers is unavailable."""
    import hashlib
    h = hashlib.sha512(text.lower().encode()).digest()
    vec = [(h[i] / 255.0) * 2 - 1 for i in range(min(len(h), _DIMENSION))]
    while len(vec) < _DIMENSION:
        vec.append(0.0)
    return vec[:_DIMENSION]


def _embed_query(text: str) -> List[float]:
    _ensure_sentence_transformers()
    if _HAS_EMBEDDINGS and _EMBED_MODEL is not None:
        return _EMBED_MODEL.encode(text).tolist()
    return _simple_embedding(text)


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _row_to_exercise(row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "category": row["category"],
        "primary_muscles": list(row["primary_muscles"] or []),
        "secondary_muscles": list(row["secondary_muscles"] or []),
        "equipment": row["equipment"],
        "mechanic": row["mechanics"],
        "axial_loading_rating": row["axial_loading_rating"],
        "gif_url": row["gif_url"],
        "instructions": list(row["instructions"] or []),
        "similarity_score": round(float(row["similarity_score"]), 3),
    }


def _apply_filters(ex: Dict[str, Any], filter_equipment, filter_muscles, exclude_muscles) -> bool:
    """True if ex survives the equipment/muscle filters (used by the degraded scan)."""
    if filter_equipment and ex.get("equipment", "") not in filter_equipment:
        if "bodyweight" not in ex.get("equipment", ""):
            return False
    muscles = [m.lower() for m in ex.get("primary_muscles", [])]
    if filter_muscles and not any(m.lower() in muscles for m in filter_muscles):
        return False
    if exclude_muscles and any(m.lower() in muscles for m in exclude_muscles):
        return False
    return True


class VectorStore:
    """pgvector-backed exercise search, with an in-process cosine scan as degraded fallback."""

    def __init__(self):
        self.exercises: List[dict] = []
        self._degraded_embeddings_cache: Optional[List[List[float]]] = None
        self._initialized = False

    def initialize(self, exercises: List[dict]):
        """Register the exercise catalog for search. Embeddings are not computed here —
        they come from backend/scripts/embed_exercises.py (pgvector path) or are computed
        lazily, once, on first degraded-mode search."""
        self.exercises = exercises
        self._degraded_embeddings_cache = None
        self._initialized = True

    async def _pg_search(self, query_emb, top_k, filter_equipment, filter_muscles, exclude_muscles) -> Optional[List[Dict[str, Any]]]:
        pool = await get_pool()
        if pool is None:
            return None
        eq = list(filter_equipment) if filter_equipment else None
        inc = [m.lower() for m in filter_muscles] if filter_muscles else None
        exc = [m.lower() for m in exclude_muscles] if exclude_muscles else None
        async with pool.acquire() as conn:
            rows = await conn.fetch(_PG_SEARCH_SQL, query_emb, eq, inc, exc, top_k)
        return [_row_to_exercise(r) for r in rows]

    def _degraded_embeddings(self) -> List[List[float]]:
        if self._degraded_embeddings_cache is None:
            self._degraded_embeddings_cache = [_embed_query(exercise_text(ex)) for ex in self.exercises]
        return self._degraded_embeddings_cache

    def _degraded_search(self, query_emb, top_k, filter_equipment, filter_muscles, exclude_muscles) -> List[Dict[str, Any]]:
        scored = []
        for ex, emb in zip(self.exercises, self._degraded_embeddings()):
            if not _apply_filters(ex, filter_equipment, filter_muscles, exclude_muscles):
                continue
            score = _cosine_similarity(query_emb, emb)
            scored.append({**ex, "similarity_score": round(score, 3)})
        scored.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored[:top_k]

    def semantic_search(self, query: str, top_k: int = 5, filter_equipment: Optional[List[str]] = None, filter_muscles: Optional[List[str]] = None, exclude_muscles: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Semantic similarity search for exercises."""
        if not self._initialized or not self.exercises:
            return []

        query_emb = _embed_query(query)

        if settings.DATABASE_URL:
            try:
                results = _run_sync(self._pg_search(query_emb, top_k, filter_equipment, filter_muscles, exclude_muscles))
                if results is not None:
                    return results
            except Exception:
                pass  # DB unreachable or not yet seeded — fall through to the degraded scan

        return self._degraded_search(query_emb, top_k, filter_equipment, filter_muscles, exclude_muscles)

    def find_alternatives(self, exercise_id: str, top_k: int = 3, exclude_muscles: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Find semantically similar exercises as alternatives."""
        target = next((ex for ex in self.exercises if ex.get("id") == exercise_id), None)
        if not target:
            return []

        query_text = exercise_text(target)
        results = self.semantic_search(query_text, top_k=top_k + 1, exclude_muscles=exclude_muscles)
        return [r for r in results if r.get("id") != exercise_id][:top_k]

    def get_status(self) -> Dict[str, Any]:
        if _HAS_EMBEDDINGS is None:
            embedding_source = "unchecked"
        elif _HAS_EMBEDDINGS:
            embedding_source = "sentence-transformers"
        else:
            embedding_source = "hash_fallback"

        pgvector_configured = bool(settings.DATABASE_URL)
        return {
            "initialized": self._initialized,
            "indexed_exercises": len(self.exercises),
            "search_backend": "pgvector" if pgvector_configured else "degraded_linear_scan",
            "embedding_source": embedding_source,
            "degraded": (not pgvector_configured) or embedding_source == "hash_fallback",
        }


vector_store = VectorStore()

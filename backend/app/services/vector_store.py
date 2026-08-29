"""
AdapFit Vector Store
Qdrant-powered semantic exercise search with sentence-transformers embeddings.
Falls back to cosine similarity on raw vectors when Qdrant is unavailable.
"""
import math
import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

# Lazy-loaded ML dependencies — imported only when first needed
_EMBED_MODEL = None
_HAS_EMBEDDINGS = None  # None = not checked yet
_QDRANT_CLIENT = None
_HAS_QDRANT = None
_QDRANT_IMPORTED = False
_DIMENSION = 384  # all-MiniLM-L6-v2 dimension


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


def _ensure_qdrant():
    """Lazily initialize Qdrant client on first use."""
    global _QDRANT_CLIENT, _HAS_QDRANT, _QDRANT_IMPORTED
    if _QDRANT_IMPORTED:
        return
    _QDRANT_IMPORTED = True
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue
        _QDRANT_CLIENT = QdrantClient(":memory:")
        _HAS_QDRANT = True
    except Exception:
        _QDRANT_CLIENT = None
        _HAS_QDRANT = False


def _get_qdrant_models():
    """Import qdrant models on demand."""
    from qdrant_client.models import VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue
    return VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue


def _simple_embedding(text: str) -> List[float]:
    """Hash-based fallback embedding when sentence-transformers unavailable."""
    import hashlib
    h = hashlib.sha512(text.lower().encode()).digest()
    vec = []
    for i in range(0, min(len(h), DIMENSION)):
        vec.append((h[i] / 255.0) * 2 - 1)
    while len(vec) < DIMENSION:
        vec.append(0.0)
    return vec[:DIMENSION]


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class VectorStore:
    """Hybrid vector store: Qdrant (if available) + in-memory fallback."""
    
    COLLECTION_NAME = "exercises"
    
    def __init__(self):
        self.exercises: List[dict] = []
        self.embeddings: List[List[float]] = []
        self._initialized = False
    
    def initialize(self, exercises: List[dict]):
        """Index all exercises with embeddings."""
        _ensure_sentence_transformers()
        _ensure_qdrant()
        self.exercises = exercises
        
        for ex in exercises:
            # Build text representation for embedding
            text = f"{ex.get('name', '')} {' '.join(ex.get('primary_muscles', []))} {ex.get('equipment', '')} {ex.get('mechanic', '')} {ex.get('category', '')}"
            if _HAS_EMBEDDINGS and _EMBED_MODEL is not None:
                emb = _EMBED_MODEL.encode(text).tolist()
            else:
                emb = _simple_embedding(text)
            self.embeddings.append(emb)
        
        # Try to create Qdrant collection
        if _HAS_QDRANT and _QDRANT_CLIENT is not None:
            try:
                VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue = _get_qdrant_models()
                collections = [c.name for c in _QDRANT_CLIENT.get_collections().collections]
                if self.COLLECTION_NAME not in collections:
                    _QDRANT_CLIENT.create_collection(
                        collection_name=self.COLLECTION_NAME,
                        vectors_config=VectorParams(size=_DIMENSION, distance=Distance.COSINE),
                    )
                
                points = []
                for i, (ex, emb) in enumerate(zip(exercises, self.embeddings)):
                    payload = {k: v for k, v in ex.items() if k != "embedding"}
                    points.append(PointStruct(id=i, vector=emb, payload=payload))
                
                _QDRANT_CLIENT.upsert(collection_name=self.COLLECTION_NAME, points=points)
            except Exception:
                pass
        
        self._initialized = True
    
    def semantic_search(self, query: str, top_k: int = 5, filter_equipment: Optional[List[str]] = None, filter_muscles: Optional[List[str]] = None, exclude_muscles: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Semantic similarity search for exercises."""
        if not self._initialized or not self.exercises:
            return []
        
        _ensure_sentence_transformers()
        _ensure_qdrant()

        if _HAS_EMBEDDINGS and _EMBED_MODEL is not None:
            query_emb = _EMBED_MODEL.encode(query).tolist()
        else:
            query_emb = _simple_embedding(query)
        
        # Try Qdrant first
        if _HAS_QDRANT and _QDRANT_CLIENT is not None:
            try:
                Filter, FieldCondition, MatchValue = _get_qdrant_models()[3:6]
                must_conditions = []
                if filter_equipment:
                    must_conditions.append(FieldCondition(key="equipment", match=MatchValue(value=filter_equipment[0])))
                
                search_filter = Filter(must=must_conditions) if must_conditions else None
                
                results = _QDRANT_CLIENT.search(
                    collection_name=self.COLLECTION_NAME,
                    query_vector=query_emb,
                    limit=top_k,
                    query_filter=search_filter,
                )
                
                scored = []
                for r in results:
                    ex = r.payload
                    ex["similarity_score"] = round(r.score, 3)
                    if filter_muscles:
                        muscles = [m.lower() for m in ex.get("primary_muscles", [])]
                        if not any(m.lower() in muscles for m in filter_muscles):
                            continue
                    if exclude_muscles:
                        muscles = [m.lower() for m in ex.get("primary_muscles", [])]
                        if any(m.lower() in muscles for m in exclude_muscles):
                            continue
                    scored.append(ex)
                return scored[:top_k]
            except Exception:
                pass
        
        # In-memory fallback
        scored = []
        for i, (ex, emb) in enumerate(zip(self.exercises, self.embeddings)):
            score = _cosine_similarity(query_emb, emb)
            
            # Apply filters
            if filter_equipment and ex.get("equipment", "") not in filter_equipment:
                if "bodyweight" not in ex.get("equipment", ""):
                    continue
            if filter_muscles:
                muscles = [m.lower() for m in ex.get("primary_muscles", [])]
                if not any(m.lower() in muscles for m in filter_muscles):
                    continue
            if exclude_muscles:
                muscles = [m.lower() for m in ex.get("primary_muscles", [])]
                if any(m.lower() in muscles for m in exclude_muscles):
                    continue
            
            scored.append({**ex, "similarity_score": round(score, 3)})
        
        scored.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored[:top_k]
    
    def find_alternatives(self, exercise_id: str, top_k: int = 3, exclude_muscles: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Find semantically similar exercises as alternatives."""
        target = None
        target_emb = None
        for i, ex in enumerate(self.exercises):
            if ex.get("id") == exercise_id:
                target = ex
                target_emb = self.embeddings[i]
                break
        
        if not target or not target_emb:
            return []
        
        query_text = f"{target.get('name', '')} {' '.join(target.get('primary_muscles', []))} {target.get('equipment', '')}"
        return self.semantic_search(query_text, top_k=top_k + 1, exclude_muscles=exclude_muscles)[1:]  # skip self
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "qdrant_available": _HAS_QDRANT,
            "embeddings_available": _HAS_EMBEDDINGS,
            "indexed_exercises": len(self.exercises),
            "initialized": self._initialized,
        }


vector_store = VectorStore()

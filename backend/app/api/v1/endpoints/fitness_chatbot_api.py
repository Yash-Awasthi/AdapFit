"""
Fitness RAG Chatbot API — AI-powered fitness guidance with knowledge retrieval.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()


# --- Response Models ---

class ChatResponse(BaseModel):
    answer: str
    intent: str
    confidence: str
    sources: list[str]
    suggestions: list[str]
    disclaimers: list[str]


class IntentInfo(BaseModel):
    intent: str
    description: str


class KnowledgeStatsResponse(BaseModel):
    total_chunks: int
    categories: list[str]
    total_tags: int


# --- Input Validation (security-review: length limits, sanitization) ---

class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000, description="Fitness question to ask")
    user_id: str = Field(default="", max_length=128)


class KnowledgeAddRequest(BaseModel):
    content: str = Field(min_length=1, max_length=10000)
    source: str = Field(min_length=1, max_length=256)
    category: str = Field(min_length=1, max_length=64, pattern=r"^[a-z_]+$")
    tags: list[str] = Field(default_factory=list, max_length=20)


# --- Cached singletons (performance-optimization) ---

@lru_cache(maxsize=1)
def _get_bot():
    from src.chat.fitness_rag import FitnessRAGChatbot
    return FitnessRAGChatbot()


@lru_cache(maxsize=1)
def _get_kb():
    from src.chat.fitness_rag import FitnessKnowledgeBase
    return FitnessKnowledgeBase()


# --- Routes ---

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask a fitness question and get AI-powered guidance",
)
async def chat(req: ChatRequest) -> ChatResponse:
    """Process a fitness query through RAG and return personalized guidance."""
    bot = _get_bot()

    try:
        response = bot.chat(req.query)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {exc}",
        ) from exc

    return ChatResponse(
        answer=response.answer,
        intent=response.intent.value,
        confidence=response.confidence.value,
        sources=response.sources,
        suggestions=response.suggestions,
        disclaimers=response.disclaimers,
    )


@router.get(
    "/intents",
    response_model=list[IntentInfo],
    summary="List supported query intents",
)
async def list_intents() -> list[IntentInfo]:
    return [
        IntentInfo(intent="workout", description="Exercise, training, lifting, workout routines"),
        IntentInfo(intent="nutrition", description="Diet, food, protein, calories, meal planning"),
        IntentInfo(intent="recovery", description="Sleep, rest, HRV, stretching, deload"),
        IntentInfo(intent="injury", description="Pain, injury prevention, rehab, medical concerns"),
        IntentInfo(intent="programming", description="Training programs, splits, periodization"),
    ]


@router.get(
    "/knowledge/stats",
    response_model=KnowledgeStatsResponse,
    summary="Get knowledge base statistics",
)
async def knowledge_stats() -> KnowledgeStatsResponse:
    kb = _get_kb()
    categories = sorted({c.category for c in kb._chunks.values()})
    tags = sorted({t for c in kb._chunks.values() for t in c.tags})
    return KnowledgeStatsResponse(
        total_chunks=len(kb._chunks),
        categories=categories,
        total_tags=len(tags),
    )

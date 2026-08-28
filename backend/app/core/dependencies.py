"""Dependency injection layer following FastAPI best practices.

Provides clean, testable access to services and storage.
"""

from __future__ import annotations
from typing import AsyncGenerator
from fastapi import Depends, HTTPException
from app.core.storage import storage
from app.services.recovery_engine import RecoveryEngine
from app.services.ml_engine import ml_engine
from app.services.nlp_pipeline import nlp_pipeline
from app.services.intent_classifier import intent_classifier
from app.services.rag_knowledge import rag_retriever
from app.services.auto_scaler import auto_scaler


async def get_storage():
    """Dependency: provide the storage engine."""
    return storage


async def get_recovery_engine() -> RecoveryEngine:
    """Dependency: provide the recovery engine."""
    return RecoveryEngine()


async def get_ml_engine():
    """Dependency: provide the ML engine."""
    return ml_engine


async def get_nlp_pipeline():
    """Dependency: provide the NLP pipeline."""
    return nlp_pipeline


async def get_intent_classifier():
    """Dependency: provide the intent classifier."""
    return intent_classifier


async def get_rag_retriever():
    """Dependency: provide the RAG knowledge retriever."""
    return rag_retriever


async def get_auto_scaler():
    """Dependency: provide the auto-scaler engine."""
    return auto_scaler


async def require_user(user_id: str) -> str:
    """Dependency: validate user_id exists, raise 404 if not."""
    user = await storage.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return user_id


async def get_user_with_recovery(user_id: str) -> dict:
    """Dependency: fetch user and their latest recovery data together."""
    user = await storage.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    recovery_logs = await storage.get_recovery_logs(user_id, 1)
    latest_recovery = recovery_logs[-1] if recovery_logs else {}

    return {
        "user": user,
        "recovery": latest_recovery,
        "user_id": user_id,
    }

"""QR code sharing endpoints — generate share codes and decode imports."""

from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.services.qr_generator import generate_share_code, decode_share_code, generate_quick_share_text

router = APIRouter()


class ShareRequest(BaseModel):
    workout_data: dict
    user_id: str = "default"


class DecodeRequest(BaseModel):
    share_code: str


@router.post("/generate")
async def generate_qr_share(req: ShareRequest):
    """Generate a QR-scannable share code for a workout."""
    return generate_share_code(req.workout_data, req.user_id)


@router.post("/decode")
async def decode_qr_share(req: DecodeRequest):
    """Decode a QR share code into importable workout data."""
    result = decode_share_code(req.share_code)
    if not result:
        raise HTTPException(status_code=400, detail="Invalid or corrupted share code")
    return {
        "workout": result,
        "importable": True,
    }


@router.post("/share-text")
async def generate_share_text(req: ShareRequest):
    """Generate human-readable share text for messaging apps."""
    return {
        "text": generate_quick_share_text(req.workout_data),
    }

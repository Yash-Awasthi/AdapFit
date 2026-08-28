"""API key management endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.core.auth import api_key_manager

router = APIRouter()


class CreateKeyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    tier: str = Field(default="free", pattern="^(free|pro|enterprise)$")
    rate_limit: int = Field(default=100, ge=10, le=10000)


class CreateKeyResponse(BaseModel):
    api_key: str
    name: str
    tier: str
    rate_limit: int
    warning: str = "Store this key securely. It cannot be retrieved later."


@router.post("/keys", response_model=CreateKeyResponse)
async def create_api_key(req: CreateKeyRequest):
    """Create a new API key."""
    rate_limits = {"free": 100, "pro": 1000, "enterprise": 10000}
    raw_key = api_key_manager.create_key(
        name=req.name,
        tier=req.tier,
        rate_limit=req.rate_limit or rate_limits.get(req.tier, 100),
    )
    return CreateKeyResponse(
        api_key=raw_key,
        name=req.name,
        tier=req.tier,
        rate_limit=req.rate_limit,
    )


@router.get("/keys")
async def list_api_keys():
    """List all API keys (without exposing raw keys)."""
    return {"keys": api_key_manager.list_keys()}


@router.get("/keys/info")
async def get_key_info(api_key: str):
    """Get info about a specific API key."""
    info = api_key_manager.get_key_info(api_key)
    if not info:
        raise HTTPException(status_code=404, detail="Key not found")
    return info


@router.delete("/keys/{api_key}")
async def revoke_api_key(api_key: str):
    """Revoke an API key."""
    if api_key_manager.revoke_key(api_key):
        return {"revoked": True}
    raise HTTPException(status_code=404, detail="Key not found")

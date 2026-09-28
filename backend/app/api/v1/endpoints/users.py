import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from app.models.schemas import UserProfileCreate, UserProfileResponse, UserProfileUpdate
from app.core.dependencies import require_user
from app.core.storage import storage
from app.services import personal_baseline

router = APIRouter()

@router.post("", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_user(profile: UserProfileCreate, account: dict = Depends(require_user)):
    """Create or complete the signed-in account's profile. The id is always the account's own."""
    user_data = profile.model_dump()
    user_data["email"] = account.get("email") or user_data["email"]
    existing = await storage.get_user(account["id"])
    if existing:
        return UserProfileResponse(**await storage.update_user(account["id"], user_data))
    user_data["id"] = account["id"]

    user = await storage.create_user(user_data)

    # Population defaults until the user has logged enough to have their own.
    await storage.set_baseline(user["id"], dict(personal_baseline.DEFAULTS))

    await storage.get_agent_memory(user["id"])

    return UserProfileResponse(**user)

@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user(user_id: str):
    user = await storage.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return UserProfileResponse(**user)

@router.patch("/{user_id}", response_model=UserProfileResponse)
async def update_user(user_id: str, updates: UserProfileUpdate):
    user = await storage.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    update_data = updates.model_dump(exclude_unset=True)
    if not update_data:
        return UserProfileResponse(**user)
    user = await storage.update_user(user_id, update_data)
    return UserProfileResponse(**user)

class BaselineUpdate(BaseModel):
    """
    The parts of a baseline the user sets rather than the app measures.

    The measured ones — HRV mean and deviation, resting heart rate — come from
    their own readings and are recalibrated, not typed in.
    """
    sleep_target_hours: Optional[float] = Field(None, ge=4, le=12)
    chronic_load_28d: Optional[float] = Field(None, ge=0, le=5000)


@router.post("/{user_id}/baselines")
async def set_baselines(user_id: str, update: BaselineUpdate):
    """Set the preference parts of a baseline, leaving the measured ones alone."""
    changes = update.model_dump(exclude_none=True)
    if not changes:
        raise HTTPException(status_code=400, detail="No baseline values supplied")
    current = await storage.get_baseline(user_id) or dict(personal_baseline.DEFAULTS)
    merged = {**{k: v for k, v in current.items() if k in personal_baseline.DEFAULTS}, **changes}
    await storage.set_baseline(user_id, merged)
    return {"user_id": user_id, "baselines": merged}


@router.get("/{user_id}/baselines")
async def get_baselines(user_id: str):
    baseline = await storage.get_baseline(user_id)
    if not baseline:
        raise HTTPException(status_code=404, detail=f"Baselines for user {user_id} not found")
    return baseline

@router.post("/{user_id}/baselines/recalibrate")
async def recalibrate_baselines(user_id: str):
    """Recalibrate baselines from recent recovery data."""
    baseline = await personal_baseline.refresh(user_id)
    return {"user_id": user_id, "baselines": baseline, "method": "rolling_28d"}

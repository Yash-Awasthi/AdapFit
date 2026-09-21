import uuid
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import UserProfileCreate, UserProfileResponse, UserProfileUpdate
from app.core.storage import storage
from app.services import personal_baseline

router = APIRouter()

@router.post("", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_user(profile: UserProfileCreate):
    """Create a new user profile with default baselines."""
    user_data = profile.model_dump()
    user_data["id"] = str(uuid.uuid4())

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

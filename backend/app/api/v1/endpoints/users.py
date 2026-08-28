import uuid
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import UserProfileCreate, UserProfileResponse, UserProfileUpdate
from app.core.storage import storage
from app.services.spark_processor import spark_analytics

router = APIRouter()

@router.post("", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_user(profile: UserProfileCreate):
    """Create a new user profile with default baselines."""
    user_data = profile.model_dump()
    user_data["id"] = str(uuid.uuid4())

    user = await storage.create_user(user_data)

    await storage.set_baseline(user["id"], {
        "hrv_mean_rmssd": 50.0,
        "hrv_std_rmssd": 10.0,
        "rhr_baseline": 65.0,
        "sleep_target_hours": 8.0,
        "chronic_load_28d": 500.0,
    })

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
    recovery_logs = await storage.get_recovery_logs(user_id, 28)
    new_baselines = spark_analytics.compute_rolling_baselines(recovery_logs)
    await storage.set_baseline(user_id, new_baselines)
    return {"user_id": user_id, "baselines": new_baselines, "method": "rolling_28d"}

"""
Biometric Data Unlock & Health Data Sharing API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/data-sharing", tags=["Health Data Sharing"])


class CreateShareRequest(BaseModel):
    user_id: str
    recipient_name: str
    share_type: str
    custom_duration_days: Optional[int] = None
    custom_data_scope: Optional[str] = None
    pin_code: Optional[str] = None


class LogAccessRequest(BaseModel):
    user_id: str
    share_id: str
    accessed_by: str


@router.post("/share")
async def create_share(req: CreateShareRequest):
    from app.services.biometric_unlock import biometric_unlock
    return biometric_unlock.create_share(req.user_id, req.recipient_name, req.share_type, req.custom_duration_days, req.custom_data_scope, req.pin_code)


@router.post("/revoke/{user_id}/{share_id}")
async def revoke_share(user_id: str, share_id: str):
    from app.services.biometric_unlock import biometric_unlock
    return biometric_unlock.revoke_share(user_id, share_id)


@router.get("/active/{user_id}")
async def get_active_shares(user_id: str):
    from app.services.biometric_unlock import biometric_unlock
    return biometric_unlock.get_active_shares(user_id)


@router.post("/access/log")
async def log_access(req: LogAccessRequest):
    from app.services.biometric_unlock import biometric_unlock
    return biometric_unlock.log_access(req.user_id, req.share_id, req.accessed_by)


@router.get("/analytics/{user_id}")
async def get_analytics(user_id: str):
    from app.services.biometric_unlock import biometric_unlock
    return biometric_unlock.get_share_analytics(user_id)


@router.get("/share-types")
async def get_share_types():
    from app.services.biometric_unlock import biometric_unlock
    return biometric_unlock.SHARE_TYPES


@router.get("/data-scopes")
async def get_data_scopes():
    from app.services.biometric_unlock import biometric_unlock
    return biometric_unlock.DATA_SCOPES

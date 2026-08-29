"""
End-to-End Encryption API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter(prefix="/encryption", tags=["E2E Encryption"])


class GenerateMasterKeyRequest(BaseModel):
    key_name: str


class DeriveUserKeyRequest(BaseModel):
    user_id: str
    password: str
    salt: Optional[str] = None


class EncryptDataRequest(BaseModel):
    user_id: str
    data: dict
    key_id: str


class DecryptDataRequest(BaseModel):
    user_id: str
    encrypted_id: str
    key_id: str


class SecureShareRequest(BaseModel):
    user_id: str
    encrypted_id: str
    recipient_id: str
    expiry_hours: int = 24


class RevokeShareRequest(BaseModel):
    share_id: str
    user_id: str


@router.post("/master-key/generate")
async def generate_master_key(req: GenerateMasterKeyRequest):
    from app.core.encryption import e2e_encryption
    return e2e_encryption.generate_master_key(req.key_name)


@router.post("/user-key/derive")
async def derive_user_key(req: DeriveUserKeyRequest):
    from app.core.encryption import e2e_encryption
    return e2e_encryption.derive_user_key(req.user_id, req.password, req.salt)


@router.post("/encrypt")
async def encrypt_data(req: EncryptDataRequest):
    from app.core.encryption import e2e_encryption
    return e2e_encryption.encrypt_data(req.user_id, req.data, req.key_id)


@router.post("/decrypt")
async def decrypt_data(req: DecryptDataRequest):
    from app.core.encryption import e2e_encryption
    return e2e_encryption.decrypt_data(req.user_id, req.encrypted_id, req.key_id)


@router.post("/share")
async def create_secure_share(req: SecureShareRequest):
    from app.core.encryption import e2e_encryption
    return e2e_encryption.create_secure_share(req.user_id, req.encrypted_id, req.recipient_id, req.expiry_hours)


@router.post("/share/revoke")
async def revoke_share(req: RevokeShareRequest):
    from app.core.encryption import e2e_encryption
    return e2e_encryption.revoke_share(req.share_id, req.user_id)


@router.post("/key/{key_id}/rotate")
async def rotate_key(key_id: str):
    from app.core.encryption import e2e_encryption
    return e2e_encryption.rotate_key(key_id)


@router.get("/audit/{user_id}")
async def get_audit_trail(user_id: str, limit: int = 100):
    from app.core.encryption import e2e_encryption
    return e2e_encryption.get_audit_trail(user_id, limit)


@router.get("/compliance")
async def get_compliance_status():
    from app.core.encryption import e2e_encryption
    return e2e_encryption.get_compliance_status()


@router.get("/algorithms")
async def get_algorithms():
    from app.core.encryption import e2e_encryption
    return e2e_encryption.ENCRYPTION_ALGORITHMS

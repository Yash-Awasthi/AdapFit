"""
Encrypted vault and key management.

Users keep records here, optionally under a passphrase the server never stores,
and can share one with another account for a limited time and number of reads.
Admins generate keys for the at-rest keyring and re-encrypt stored data after a rotation.
"""
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.core import audit, crypto, durable, encryption
from app.core.dependencies import require_admin, require_user
from app.services import health_data_security as controls

router = APIRouter(prefix="/encryption", tags=["Encryption"])


class EncryptDataRequest(BaseModel):
    data: dict
    label: str = Field("", max_length=120)
    passphrase: Optional[str] = Field(None, max_length=256)


class DecryptDataRequest(BaseModel):
    encrypted_id: str
    passphrase: Optional[str] = Field(None, max_length=256)
    share_id: Optional[str] = None


class SecureShareRequest(BaseModel):
    encrypted_id: str
    recipient_id: str
    expiry_hours: int = Field(24, ge=1, le=encryption.MAX_SHARE_HOURS)
    max_accesses: int = Field(10, ge=1, le=100)


class RevokeShareRequest(BaseModel):
    share_id: str


@router.post("/encrypt")
async def encrypt_data(req: EncryptDataRequest, user: dict = Depends(require_user)):
    try:
        return encryption.encrypt(user["id"], req.data, req.label, req.passphrase)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/decrypt")
async def decrypt_data(req: DecryptDataRequest, request: Request, user: dict = Depends(require_user)):
    try:
        result = encryption.decrypt(user["id"], req.encrypted_id, req.passphrase, req.share_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Record not found")
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    if result["via_share"]:
        await audit.record("vault_share_read", user_id=result["owner_id"], actor_id=user["id"],
                           ip=request.client.host if request.client else "", share_id=result["via_share"])
    return result


@router.get("/records")
async def list_records(user: dict = Depends(require_user)):
    return {"records": encryption.list_records(user["id"])}


@router.delete("/records/{record_id}")
async def delete_record(record_id: str, user: dict = Depends(require_user)):
    if not encryption.delete(user["id"], record_id):
        raise HTTPException(status_code=404, detail="Record not found")
    return {"deleted": True}


@router.post("/share")
async def create_secure_share(req: SecureShareRequest, user: dict = Depends(require_user)):
    from app.core.auth import user_manager

    if await user_manager.get_user(req.recipient_id) is None:
        raise HTTPException(status_code=404, detail="Recipient not found")
    try:
        result = encryption.share(user["id"], req.encrypted_id, req.recipient_id, req.expiry_hours, req.max_accesses)
    except LookupError:
        raise HTTPException(status_code=404, detail="Record not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    await audit.record("vault_shared", user_id=user["id"], recipient_id=req.recipient_id, share_id=result["id"])
    return result


@router.post("/share/revoke")
async def revoke_share(req: RevokeShareRequest, user: dict = Depends(require_user)):
    if not encryption.revoke_share(user["id"], req.share_id):
        raise HTTPException(status_code=404, detail="Share not found")
    await audit.record("vault_share_revoked", user_id=user["id"], share_id=req.share_id)
    return {"status": "revoked", "share_id": req.share_id}


@router.get("/shares")
async def list_shares(user: dict = Depends(require_user)):
    return encryption.shares_for(user["id"])


@router.post("/master-key/generate")
async def generate_master_key(admin: dict = Depends(require_admin)):
    """A fresh at-rest key to put first in DATA_ENCRYPTION_KEYS. It is shown once and not stored here."""
    key_id = f"k{int(time.time())}"
    await audit.record("encryption_key_generated", actor_id=admin["id"], key_id=key_id)
    return {"key": f"{key_id}:{crypto.new_key()}", "active_key_id": crypto.active_key_id(),
            "next_steps": "Prepend to DATA_ENCRYPTION_KEYS, restart, call POST /encryption/key/rotate, "
                          "then remove the old key."}


@router.post("/key/rotate")
async def rotate_key(admin: dict = Depends(require_admin)):
    """Re-encrypt every stored row that is not under the active key."""
    await durable.flush()
    rewritten = await durable.reseal_all()
    await audit.record("encryption_key_rotated", actor_id=admin["id"], active_key_id=crypto.active_key_id(),
                       rows=rewritten)
    return {"active_key_id": crypto.active_key_id(), "rows_reencrypted": rewritten}


@router.get("/audit/{user_id}")
async def get_audit_trail(user_id: str, limit: int = 100, user: dict = Depends(require_user)):
    return {"entries": await audit.entries(user["id"], limit)}


@router.get("/compliance")
async def get_compliance_status():
    return {"controls": controls.control_status(), "active_key_id": crypto.active_key_id(),
            "note": "Self-check of technical controls, not a certification."}


@router.get("/algorithms")
async def get_algorithms():
    return encryption.ALGORITHMS

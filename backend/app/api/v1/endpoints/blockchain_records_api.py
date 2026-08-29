"""Blockchain Health Records API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List
from app.services.blockchain_records import blockchain_records_service

router = APIRouter(prefix="/health-records", tags=["Blockchain Health Records"])

class RecordRequest(BaseModel):
    user_id: str
    record_data: Dict[str, Any]

class AccessRequest(BaseModel):
    user_id: str
    grantee: str
    record_types: List[str]
    expiry_hours: int = 24

@router.post("/add")
async def add_record(req: RecordRequest):
    result = blockchain_records_service.add_record(req.user_id, req.record_data)
    return {"success": True, "data": result}

@router.get("/verify/{user_id}")
async def verify_chain(user_id: str):
    result = blockchain_records_service.verify_chain(user_id)
    return {"success": True, "data": result}

@router.get("/history/{user_id}")
async def get_history(user_id: str, record_type: str = "", limit: int = 50):
    result = blockchain_records_service.get_record_history(user_id, record_type, limit)
    return {"success": True, "data": result}

@router.post("/grant-access")
async def grant_access(req: AccessRequest):
    result = blockchain_records_service.grant_access(req.user_id, req.grantee, req.record_types, req.expiry_hours)
    return {"success": True, "data": result}

@router.post("/revoke-access")
async def revoke_access(user_id: str, grantee: str):
    result = blockchain_records_service.revoke_access(user_id, grantee)
    return {"success": True, "data": result}

@router.get("/audit/{user_id}")
async def get_audit_log(user_id: str):
    result = blockchain_records_service.get_audit_log(user_id)
    return {"success": True, "data": result}

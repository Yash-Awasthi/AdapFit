"""
Health Data Security API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/security", tags=["Health Data Security"])


class AuditEventRequest(BaseModel):
    user_id: str
    action: str
    resource: str
    details: str = ""
    ip_address: str = ""


class DataAccessRequest(BaseModel):
    user_id: str
    accessor: str
    data_type: str
    purpose: str


@router.post("/audit/log")
async def log_audit_event(req: AuditEventRequest):
    from app.services.health_data_security import health_security
    return health_security.log_audit_event(req.user_id, req.action, req.resource, req.details, req.ip_address)


@router.post("/access/log")
async def log_data_access(req: DataAccessRequest):
    from app.services.health_data_security import health_security
    return health_security.log_data_access(req.user_id, req.accessor, req.data_type, req.purpose)


@router.get("/compliance/{standard}")
async def check_compliance(standard: str):
    from app.services.health_data_security import health_security
    return health_security.check_compliance(standard)


@router.get("/audit/{user_id}")
async def get_audit_logs(user_id: str, limit: int = 100):
    from app.services.health_data_security import health_security
    return health_security.get_audit_logs(user_id, limit)


@router.get("/access-summary/{user_id}")
async def get_access_summary(user_id: str):
    from app.services.health_data_security import health_security
    return health_security.get_data_access_summary(user_id)


@router.get("/standards")
async def get_compliance_standards():
    from app.services.health_data_security import health_security
    return health_security.COMPLIANCE_STANDARDS


@router.get("/encryption-methods")
async def get_encryption_methods():
    from app.services.health_data_security import health_security
    return health_security.ENCRYPTION_METHODS

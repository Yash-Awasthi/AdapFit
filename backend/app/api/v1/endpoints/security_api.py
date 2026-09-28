"""
Health data security: the caller's own security log, who has accessed their data, and a
self-check of the deployment's technical controls.
"""
from collections import Counter

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core import audit
from app.core.dependencies import require_user
from app.services import health_data_security as controls

router = APIRouter(prefix="/security", tags=["Health Data Security"])


class AuditEventRequest(BaseModel):
    action: str = Field(max_length=60)
    resource: str = Field(max_length=120)
    details: str = Field("", max_length=500)


class DataAccessRequest(BaseModel):
    accessor: str = Field(max_length=120)
    data_type: str = Field(max_length=60)
    purpose: str = Field(max_length=200)


@router.post("/audit/log")
async def log_audit_event(req: AuditEventRequest, user: dict = Depends(require_user)):
    """An event the app reports about the caller's own account; stored as client-reported."""
    await audit.record("client_event", user_id=user["id"], action=req.action, resource=req.resource,
                       details=req.details)
    return {"recorded": True}


@router.post("/access/log")
async def log_data_access(req: DataAccessRequest, user: dict = Depends(require_user)):
    """The caller notes that they showed or sent their data to someone (a doctor, a family member)."""
    await audit.record("data_disclosed", user_id=user["id"], accessor=req.accessor, data_type=req.data_type,
                       purpose=req.purpose)
    return {"recorded": True}


@router.get("/compliance/{standard}")
async def check_compliance(standard: str):
    return controls.check_compliance(standard)


@router.get("/audit/{user_id}")
async def get_audit_logs(user_id: str, limit: int = 100, user: dict = Depends(require_user)):
    return {"entries": await audit.entries(user["id"], limit)}


@router.get("/access-summary/{user_id}")
async def get_access_summary(user_id: str, user: dict = Depends(require_user)):
    """Who other than the caller touched their account, and what the caller disclosed and to whom."""
    entries = await audit.entries(user["id"], 1000)
    others = Counter(e["actor_id"] for e in entries if e["actor_id"] and e["actor_id"] != user["id"])
    disclosed = Counter(e["details"].get("accessor", "") for e in entries if e["event"] == "data_disclosed")
    return {"accessed_by_others": dict(others.most_common(10)), "disclosed_to": dict(disclosed.most_common(10)),
            "total_events": len(entries)}


@router.get("/standards")
async def get_compliance_standards():
    return {k: {"name": v["name"], "controls": v["controls"]} for k, v in controls.STANDARDS.items()}


@router.get("/encryption-methods")
async def get_encryption_methods():
    from app.core.encryption import ALGORITHMS
    return ALGORITHMS

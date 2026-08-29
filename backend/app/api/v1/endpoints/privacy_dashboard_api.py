"""
Privacy Dashboard API — Central view of all data sharing status.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.core.dependencies import require_user
from app.services.family_network import family_network_service

router = APIRouter()


class RevokeAccessRequest(BaseModel):
    entity_type: str
    entity_id: str
    data_types: Optional[list[str]] = None


@router.get("/overview")
async def get_privacy_overview(user: dict = Depends(require_user)):
    connections = family_network_service.get_connections(user["id"])
    shared_with = []
    for conn in connections:
        shared = [k for k, v in conn.get("i_share", {}).items() if v]
        shared_with.append({
            "user_id": conn["other_user_id"],
            "relationship": conn["relationship"],
            "data_shared": shared,
            "status": conn["status"],
            "connected_since": conn["connected_since"],
        })
    return {
        "user_id": user["id"],
        "total_connections": len(connections),
        "sharing_data_count": sum(1 for c in shared_with if c["data_shared"]),
        "shared_with": shared_with,
    }


@router.get("/access-history")
async def get_access_history(user: dict = Depends(require_user), limit: int = 50):
    return {"history": family_network_service.get_audit_history(user["id"], limit)}


@router.post("/revoke")
async def revoke_access(request: RevokeAccessRequest, user: dict = Depends(require_user)):
    if request.entity_type != "person":
        return {"error": f"Revocation for {request.entity_type} not implemented"}
    connections = family_network_service.get_connections(user["id"])
    for conn in connections:
        if conn["other_user_id"] == request.entity_id:
            if request.data_types:
                for dt in request.data_types:
                    family_network_service.revoke_permissions(conn["connection_id"], user["id"], dt)
                return {"revoked": True, "data_types": request.data_types}
            return family_network_service.revoke_connection(conn["connection_id"], user["id"])
    return {"error": "Connection not found"}


@router.get("/data-categories")
async def get_data_categories():
    return {"categories": [
        {"id": "activity", "name": "Activity", "sensitivity": "low"},
        {"id": "vitals", "name": "Vital Signs", "sensitivity": "high"},
        {"id": "sleep", "name": "Sleep", "sensitivity": "medium"},
        {"id": "nutrition", "name": "Nutrition", "sensitivity": "low"},
        {"id": "mental_health", "name": "Mental Health", "sensitivity": "high"},
        {"id": "medications", "name": "Medications", "sensitivity": "high"},
        {"id": "location", "name": "Location", "sensitivity": "high"},
        {"id": "medical", "name": "Medical Info", "sensitivity": "critical"},
    ]}


@router.get("/export")
async def get_export_options(user: dict = Depends(require_user)):
    return {
        "formats": ["json", "csv", "fhir"],
        "data_included": ["Activity", "Sleep", "Heart rate", "Workouts", "Nutrition", "Medications"],
    }

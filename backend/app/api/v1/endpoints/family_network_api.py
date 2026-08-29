"""
Family Health Network API — Private Family Connections with Granular Permissions

Invite → Accept → Set Permissions → Share selectively → Audit everything
All data is private by default. No auto-exposure.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
from app.services.family_network import family_network_service
from app.core.dependencies import require_user

router = APIRouter()


class InviteRequest(BaseModel):
    invitee_id: str = Field(min_length=1)
    relationship: str = Field(default="custom", description="parent, child, spouse, sibling, caregiver, dependent, custom")
    message: str = Field(default="", max_length=500)


class AcceptInviteRequest(BaseModel):
    invite_id: str
    token: str = ""


class SetPermissionsRequest(BaseModel):
    connection_id: str
    permissions: dict = Field(description="Permission flags: view_activity, view_workouts, view_sleep, etc.")


class RevokePermissionRequest(BaseModel):
    connection_id: str
    data_type: str


class CheckPermissionRequest(BaseModel):
    connection_id: str
    permission: str = Field(description="Permission to check, e.g. view_vitals, view_sleep")


@router.post("/invite")
async def send_invite(request: InviteRequest, user: dict = Depends(require_user)):
    """Send a family connection invite."""
    return family_network_service.send_invite(
        user["id"], request.invitee_id, request.relationship, request.message
    )


@router.post("/invite/accept")
async def accept_invite(request: AcceptInviteRequest, user: dict = Depends(require_user)):
    """Accept a family connection invite."""
    return family_network_service.accept_invite(request.invite_id, user["id"], request.token)


@router.post("/invite/decline")
async def decline_invite(invite_id: str, user: dict = Depends(require_user)):
    """Decline a family connection invite."""
    return family_network_service.decline_invite(invite_id, user["id"])


@router.get("/invites")
async def get_invites(user: dict = Depends(require_user)):
    """Get pending invites for this user."""
    return {"invites": family_network_service.get_pending_invites(user["id"])}


@router.get("/connections")
async def get_connections(user: dict = Depends(require_user)):
    """Get all family connections with current permissions."""
    return {"connections": family_network_service.get_connections(user["id"])}


@router.post("/permissions")
async def set_permissions(request: SetPermissionsRequest, user: dict = Depends(require_user)):
    """
    Set sharing permissions for a connection.
    
    Permissions control what data YOU share with the connected person.
    All permissions default to False (no sharing).
    """
    return family_network_service.set_permissions(
        request.connection_id, user["id"], request.permissions
    )


@router.get("/permissions/{connection_id}")
async def get_permissions(connection_id: str, user: dict = Depends(require_user)):
    """Get current sharing permissions for a connection."""
    return family_network_service.get_permissions(connection_id, user["id"])


@router.post("/permissions/revoke")
async def revoke_permission(request: RevokePermissionRequest, user: dict = Depends(require_user)):
    """Revoke sharing of a specific data type."""
    return family_network_service.revoke_permissions(
        request.connection_id, user["id"], request.data_type
    )


@router.post("/permissions/check")
async def check_permission(request: CheckPermissionRequest, user: dict = Depends(require_user)):
    """
    Check if the authenticated user has permission to view a specific data type
    through a family connection. Use this BEFORE returning health data.
    """
    return family_network_service.check_permission(
        request.connection_id, user["id"], request.permission
    )


@router.post("/connection/pause")
async def pause_connection(connection_id: str, user: dict = Depends(require_user)):
    """Pause a connection — temporarily stops all data sharing."""
    return family_network_service.pause_connection(connection_id, user["id"])


@router.post("/connection/resume")
async def resume_connection(connection_id: str, user: dict = Depends(require_user)):
    """Resume a paused connection."""
    return family_network_service.resume_connection(connection_id, user["id"])


@router.post("/connection/revoke")
async def revoke_connection(connection_id: str, user: dict = Depends(require_user)):
    """Permanently revoke a connection. Cannot be undone."""
    return family_network_service.revoke_connection(connection_id, user["id"])


@router.get("/audit")
async def get_audit_history(user: dict = Depends(require_user), limit: int = 50):
    """Get audit history of all sharing actions."""
    return {"audit": family_network_service.get_audit_history(user["id"], limit)}

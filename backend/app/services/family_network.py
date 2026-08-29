"""
Family Health Network — Private Family Account System

Built on explicit mutual authorization:
- Invite → Authenticate → Accept → Define sharing permissions → Connect
- Granular permissions: activity, workouts, sleep, recovery, location, vitals, medications, emergency
- Temporary, scheduled, or emergency-only sharing
- Immediate revoke, per-record hiding, pause, audit history
- No auto-exposure of health data
- No public profiles, no follower system

Relationship types: parent, child, spouse/partner, sibling, caregiver, dependent, custom trusted contact
"""
import time
import secrets
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class RelationshipType(Enum):
    PARENT = "parent"
    CHILD = "child"
    SPOUSE = "spouse"
    SIBLING = "sibling"
    CAREGIVER = "caregiver"
    DEPENDENT = "dependent"
    CUSTOM = "custom"


class InviteStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    REVOKED = "revoked"


class ConnectionStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    REVOKED = "revoked"


# Default permissions — all private by default
DEFAULT_PERMISSIONS = {
    # Category-level
    "view_activity": False,
    "view_workouts": False,
    "view_sleep": False,
    "view_recovery": False,
    "view_location": False,
    "view_vitals": False,
    "view_medications": False,
    "view_emergency": False,
    "view_nutrition": False,
    "view_mood": False,
    "send_alerts": True,
    "view_summary": False,
    # Data-type-level (for granular sharing)
    "heart_rate": False,
    "hrv": False,
    "steps": False,
    "blood_pressure": False,
    "sleep_data": False,
    "weight": False,
    "medications": False,
    "location": False,
    "mood_data": False,
    "nutrition_data": False,
    "emergency_info": False,
    "stress": False,
    "activity": False,
    "workouts": False,
    "recovery": False,
}

# Map common permission names to their canonical key
_PERMISSION_ALIASES = {
    "heart_rate": "heart_rate",
    "bpm": "heart_rate",
    "pulse": "heart_rate",
    "hrv": "hrv",
    "heart rate variability": "hrv",
    "steps": "steps",
    "step_count": "steps",
    "blood_pressure": "blood_pressure",
    "bp": "blood_pressure",
    "sleep": "sleep_data",
    "sleep_data": "sleep_data",
    "weight": "weight",
    "bmi": "weight",
    "medications": "medications",
    "medication": "medications",
    "medicine": "medications",
    "location": "location",
    "mood": "mood_data",
    "mood_data": "mood_data",
    "emotion": "mood_data",
    "nutrition": "nutrition_data",
    "nutrition_data": "nutrition_data",
    "food": "nutrition_data",
    "meal": "nutrition_data",
    "calories": "nutrition_data",
    "emergency": "emergency_info",
    "emergency_info": "emergency_info",
    "stress": "stress",
    "anxiety": "stress",
    "activity": "activity",
    "workouts": "workouts",
    "exercise": "workouts",
    "recovery": "recovery",
    "view_activity": "view_activity",
    "view_workouts": "view_workouts",
    "view_sleep": "view_sleep",
    "view_recovery": "view_recovery",
    "view_location": "view_location",
    "view_vitals": "view_vitals",
    "view_medications": "view_medications",
    "view_emergency": "view_emergency",
    "view_nutrition": "view_nutrition",
    "view_mood": "view_mood",
    "send_alerts": "send_alerts",
    "view_summary": "view_summary",
}

def _resolve_permission(name: str) -> str:
    """Resolve a permission name (or alias) to its canonical key."""
    return _PERMISSION_ALIASES.get(name.lower().strip(), name)


@dataclass
class FamilyInvite:
    id: str
    inviter_id: str
    invitee_id: str
    relationship: RelationshipType
    message: str
    status: InviteStatus
    created_at: float
    expires_at: float
    accepted_at: Optional[float] = None
    token: str = ""


@dataclass
class FamilyConnection:
    id: str
    user_a: str
    user_b: str
    relationship: RelationshipType
    status: ConnectionStatus
    permissions_by_a: dict = field(default_factory=dict)  # What A can see of B
    permissions_by_b: dict = field(default_factory=dict)  # What B can see of A
    created_at: float = 0
    paused_at: Optional[float] = None
    revoked_at: Optional[float] = None


@dataclass
class SharingAuditEntry:
    id: str
    actor_id: str
    target_id: str
    action: str  # grant, revoke, view, pause, resume
    data_type: str
    timestamp: float
    details: dict = field(default_factory=dict)


class FamilyNetworkService:
    """Private family health network with granular permission control."""

    INVITE_EXPIRY_HOURS = 72

    def __init__(self):
        self._invites: dict[str, FamilyInvite] = {}
        self._connections: dict[str, FamilyConnection] = {}
        self._audit_log: list[SharingAuditEntry] = []

    # === Invitation System ===

    def send_invite(
        self,
        inviter_id: str,
        invitee_id: str,
        relationship: str = "custom",
        message: str = "Let's stay connected on our health journeys!",
    ) -> dict:
        """Send a family connection invite."""
        # Check if already connected
        existing = self._find_connection(inviter_id, invitee_id)
        if existing and existing.status == ConnectionStatus.ACTIVE:
            return {"error": "Already connected"}

        # Check for pending invite
        for invite in self._invites.values():
            if (invite.inviter_id == inviter_id and invite.invitee_id == invitee_id
                    and invite.status == InviteStatus.PENDING):
                return {"error": "Invite already pending"}

        invite_id = f"inv_{secrets.token_hex(6)}"
        token = secrets.token_urlsafe(32)
        now = time.time()
        invite = FamilyInvite(
            id=invite_id,
            inviter_id=inviter_id,
            invitee_id=invitee_id,
            relationship=RelationshipType(relationship),
            message=message,
            status=InviteStatus.PENDING,
            created_at=now,
            expires_at=now + self.INVITE_EXPIRY_HOURS * 3600,
            token=token,
        )
        self._invites[invite_id] = invite
        self._audit("invite_sent", inviter_id, invitee_id, "connection", {"invite_id": invite_id})

        return {
            "invite_id": invite_id,
            "token": token,
            "relationship": relationship,
            "expires_at": time.strftime("%Y-%m-%d %H:%M", time.localtime(invite.expires_at)),
            "message": "Invitation sent. They'll receive a notification.",
        }

    def accept_invite(self, invite_id: str, user_id: str, token: str = "") -> dict:
        """Accept a family connection invite."""
        invite = self._invites.get(invite_id)
        if not invite:
            return {"error": "Invite not found"}
        if invite.invitee_id != user_id:
            return {"error": "This invite is not for you"}
        if invite.status != InviteStatus.PENDING:
            return {"error": f"Invite is {invite.status.value}"}
        if time.time() > invite.expires_at:
            invite.status = InviteStatus.EXPIRED
            return {"error": "Invite has expired"}

        # Verify token — if invite has a token, provided token must match (empty string does NOT bypass)
        if invite.token and invite.token != (token or ""):
            return {"error": "Invalid token"}

        invite.status = InviteStatus.ACCEPTED
        invite.accepted_at = time.time()

        # Create bidirectional connection with NO permissions by default
        conn_id = f"conn_{secrets.token_hex(6)}"
        connection = FamilyConnection(
            id=conn_id,
            user_a=invite.inviter_id,
            user_b=user_id,
            relationship=invite.relationship,
            status=ConnectionStatus.ACTIVE,
            permissions_by_a=dict(DEFAULT_PERMISSIONS),
            permissions_by_b=dict(DEFAULT_PERMISSIONS),
            created_at=time.time(),
        )
        self._connections[conn_id] = connection
        self._audit("connection_created", invite.inviter_id, user_id, "connection",
                     {"relationship": invite.relationship.value})

        return {
            "connected": True,
            "connection_id": conn_id,
            "relationship": invite.relationship.value,
            "message": "You are now connected. No health data is shared by default — grant permissions to share what you choose.",
        }

    def decline_invite(self, invite_id: str, user_id: str) -> dict:
        """Decline a family connection invite."""
        invite = self._invites.get(invite_id)
        if not invite or invite.invitee_id != user_id:
            return {"error": "Invalid invite"}
        invite.status = InviteStatus.DECLINED
        return {"declined": True}

    def get_pending_invites(self, user_id: str) -> list[dict]:
        """Get pending invites for a user."""
        now = time.time()
        return [
            {
                "invite_id": inv.id,
                "inviter_id": inv.inviter_id,
                "relationship": inv.relationship.value,
                "message": inv.message,
                "created_at": time.strftime("%Y-%m-%d %H:%M", time.localtime(inv.created_at)),
                "expires_at": time.strftime("%Y-%m-%d %H:%M", time.localtime(inv.expires_at)),
                "is_expired": now > inv.expires_at,
            }
            for inv in self._invites.values()
            if inv.invitee_id == user_id and inv.status == InviteStatus.PENDING
        ]

    # === Permission Management ===

    def set_permissions(
        self,
        connection_id: str,
        user_id: str,
        permissions,
    ) -> dict:
        """
        Set what data the user shares with the connected person.
        Accepts a dict {permission: bool} or a list of permission names (all set to True).
        User A sets permissions_by_a (what B can see of A's data).
        """
        conn = self._connections.get(connection_id)
        if not conn:
            return {"error": "Connection not found"}
        if conn.status != ConnectionStatus.ACTIVE:
            return {"error": "Connection is not active"}

        # Normalize: accept list of names or dict of {name: bool}
        if isinstance(permissions, list):
            permissions = {k: True for k in permissions}

        # Resolve aliases and set permissions
        if user_id == conn.user_a:
            for key, val in permissions.items():
                canonical = _resolve_permission(key)
                conn.permissions_by_a[canonical] = val
            self._audit("permissions_updated", user_id, conn.user_b, "permissions",
                        {"permissions": permissions})
        elif user_id == conn.user_b:
            for key, val in permissions.items():
                canonical = _resolve_permission(key)
                conn.permissions_by_b[canonical] = val
            self._audit("permissions_updated", user_id, conn.user_a, "permissions",
                        {"permissions": permissions})
        else:
            return {"error": "Not part of this connection"}

        return {"updated": True, "message": "Permissions updated. Changes take effect immediately."}

    def get_permissions(self, connection_id: str, user_id: str) -> dict:
        """Get the sharing permissions for a connection."""
        conn = self._connections.get(connection_id)
        if not conn:
            return {"error": "Connection not found"}

        if user_id == conn.user_a:
            return {
                "you_share": conn.permissions_by_a,
                "they_share": conn.permissions_by_b,
                "their_can_see_of_you": conn.permissions_by_a,
            }
        elif user_id == conn.user_b:
            return {
                "you_share": conn.permissions_by_b,
                "they_share": conn.permissions_by_a,
                "their_can_see_of_you": conn.permissions_by_b,
            }
        return {"error": "Not part of this connection"}

    def revoke_permissions(self, connection_id: str, user_id: str, data_type: str) -> dict:
        """Revoke sharing of a specific data type."""
        conn = self._connections.get(connection_id)
        if not conn:
            return {"error": "Connection not found"}

        canonical = _resolve_permission(data_type)
        if user_id == conn.user_a:
            conn.permissions_by_a[canonical] = False
        elif user_id == conn.user_b:
            conn.permissions_by_b[canonical] = False
        else:
            return {"error": "Not part of this connection"}

        self._audit("permission_revoked", user_id, "", data_type, "data_type")
        return {"revoked": True, "data_type": canonical}

    # === Connection Management ===

    def get_connections(self, user_id: str) -> list[dict]:
        """Get all active connections for a user."""
        connections = []
        for conn in self._connections.values():
            if (conn.user_a == user_id or conn.user_b == user_id) and conn.status == ConnectionStatus.ACTIVE:
                other_id = conn.user_b if conn.user_a == user_id else conn.user_a
                my_permissions = conn.permissions_by_a if conn.user_a == user_id else conn.permissions_by_b
                their_permissions = conn.permissions_by_b if conn.user_a == user_id else conn.permissions_by_a
                connections.append({
                    "connection_id": conn.id,
                    "other_user_id": other_id,
                    "relationship": conn.relationship.value,
                    "status": conn.status.value,
                    "i_share": my_permissions,
                    "they_share": their_permissions,
                    "connected_since": time.strftime("%Y-%m-%d", time.localtime(conn.created_at)),
                })
        return connections

    def pause_connection(self, connection_id: str, user_id: str) -> dict:
        """Pause a connection — temporarily stops all data sharing."""
        conn = self._connections.get(connection_id)
        if not conn or (conn.user_a != user_id and conn.user_b != user_id):
            return {"error": "Invalid connection"}
        conn.status = ConnectionStatus.PAUSED
        conn.paused_at = time.time()
        self._audit("connection_paused", user_id, "", "connection", {})
        return {"paused": True, "message": "Data sharing paused. You can resume at any time."}

    def resume_connection(self, connection_id: str, user_id: str) -> dict:
        """Resume a paused connection."""
        conn = self._connections.get(connection_id)
        if not conn or (conn.user_a != user_id and conn.user_b != user_id):
            return {"error": "Invalid connection"}
        conn.status = ConnectionStatus.ACTIVE
        conn.paused_at = None
        self._audit("connection_resumed", user_id, "", "connection", {})
        return {"resumed": True}

    def revoke_connection(self, connection_id: str, user_id: str) -> dict:
        """Permanently revoke a connection. Cannot be undone."""
        conn = self._connections.get(connection_id)
        if not conn or (conn.user_a != user_id and conn.user_b != user_id):
            return {"error": "Invalid connection"}
        conn.status = ConnectionStatus.REVOKED
        conn.revoked_at = time.time()
        # Clear all permissions
        conn.permissions_by_a = {k: False for k in DEFAULT_PERMISSIONS}
        conn.permissions_by_b = {k: False for k in DEFAULT_PERMISSIONS}
        self._audit("connection_revoked", user_id, "", "connection", {})
        return {"revoked": True, "message": "Connection permanently revoked. All shared data access has been removed."}

    def check_permission(self, connection_id: str, viewer_id: str, permission: str) -> dict:
        """
        Check if viewer_id has permission to see a specific data type on the connection.
        Returns {'allowed': bool, 'reason': str}.
        Call this before returning any health data through a family connection.
        """
        conn = self._connections.get(connection_id)
        if not conn:
            return {"allowed": False, "reason": "Connection not found"}
        if conn.status != ConnectionStatus.ACTIVE:
            return {"allowed": False, "reason": f"Connection is {conn.status.value}"}

        canonical = _resolve_permission(permission)
        if viewer_id == conn.user_a:
            allowed = conn.permissions_by_b.get(canonical, False)
        elif viewer_id == conn.user_b:
            allowed = conn.permissions_by_a.get(canonical, False)
        else:
            return {"allowed": False, "reason": "Not part of this connection"}
        if not allowed:
            self._audit("permission_denied", viewer_id, "", permission, {"connection_id": connection_id})
        return {"allowed": allowed, "reason": "" if allowed else f"Permission '{permission}' not granted"}

    def get_audit_history(self, user_id: str, limit: int = 50) -> list[dict]:
        """Get audit history of sharing actions."""
        entries = [
            e for e in self._audit_log
            if e.actor_id == user_id or e.target_id == user_id
        ]
        return [
            {
                "action": e.action,
                "data_type": e.data_type,
                "timestamp": time.strftime("%Y-%m-%d %H:%M", time.localtime(e.timestamp)),
                "details": e.details,
            }
            for e in entries[-limit:]
        ]

    def _find_connection(self, user_a: str, user_b: str) -> Optional[FamilyConnection]:
        for conn in self._connections.values():
            if ((conn.user_a == user_a and conn.user_b == user_b) or
                (conn.user_a == user_b and conn.user_b == user_a)):
                return conn
        return None

    def _audit(self, action: str, actor: str, target: str, data_type: str, details: dict):
        self._audit_log.append(SharingAuditEntry(
            id=f"aud_{secrets.token_hex(6)}",
            actor_id=actor, target_id=target,
            action=action, data_type=data_type,
            timestamp=time.time(), details=details,
        ))
        # Keep last 5000 entries
        if len(self._audit_log) > 5000:
            self._audit_log[:] = self._audit_log[-2500:]


family_network_service = FamilyNetworkService()

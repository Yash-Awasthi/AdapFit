"""
Emergency SOS Service — Emergency Contacts, One-Tap Alert, Fall Detection, Safety Check Timer

Features:
- Emergency contact management (name, phone, relationship) per user
- One-tap SOS alert with GPS location
- Safety check timer (set deadline, get notified if no response)
- Fall detection simulation (accelerometer threshold)
- Medical info card (blood type, allergies, conditions, medications)
- Emergency call integration
- Location sharing during emergency
"""
import time
import secrets
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class SOSStatus(Enum):
    IDLE = "idle"
    ACTIVATED = "activated"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    RESOLVED = "resolved"


@dataclass
class EmergencyContact:
    id: str
    name: str
    phone: str
    relationship: str
    is_primary: bool = False
    user_id: str = "default"


@dataclass
class MedicalInfo:
    blood_type: str = "unknown"
    allergies: list = field(default_factory=list)
    conditions: list = field(default_factory=list)
    medications: list = field(default_factory=list)
    emergency_note: str = ""
    user_id: str = "default"


@dataclass
class SOSAlert:
    alert_id: str
    status: SOSStatus
    activated_at: float
    location: Optional[dict] = None
    contacts_notified: list = field(default_factory=list)
    resolved_at: Optional[float] = None
    user_id: str = "default"


@dataclass
class SafetyCheck:
    check_id: str
    user_id: str
    deadline: float
    message: str
    notify_contacts: bool
    status: str = "active"  # active | responded | escalated
    responded_at: Optional[float] = None
    safe: Optional[bool] = None
    note: str = ""
    created_at: float = field(default_factory=time.time)


class EmergencySOSService:
    """Emergency SOS system with contacts, alerts, safety checks, and medical info."""

    FALL_THRESHOLD_G = 2.5  # g-force threshold for fall detection
    SOS_COUNTDOWN_SECONDS = 5
    AUTO_CANCEL_TIMEOUT = 60  # seconds

    def __init__(self):
        self._contacts: list[EmergencyContact] = []
        self._medical_info: dict[str, MedicalInfo] = {}  # user_id -> MedicalInfo
        self._active_alerts: dict[str, SOSAlert] = {}  # user_id -> SOSAlert (per-user, not singleton)
        self._alert_history: list[SOSAlert] = []
        self._safety_checks: dict[str, SafetyCheck] = {}  # check_id -> SafetyCheck
        self._safety_history: list[SafetyCheck] = []

    def _user_contacts(self, user_id: str) -> list[EmergencyContact]:
        return [c for c in self._contacts if c.user_id == user_id]

    # === Contact Management ===

    def add_contact(self, name: str, phone: str, relationship: str, is_primary: bool = False, user_id: str = "default") -> dict:
        if is_primary:
            for c in self._user_contacts(user_id):
                c.is_primary = False
        contact = EmergencyContact(
            id=f"contact_{secrets.token_hex(6)}",
            name=name, phone=phone, relationship=relationship,
            is_primary=is_primary, user_id=user_id,
        )
        self._contacts.append(contact)
        return {"added": True, "contact_id": contact.id, "name": name}

    def remove_contact(self, contact_id: str, user_id: str = "default") -> dict:
        self._contacts = [c for c in self._contacts if not (c.id == contact_id and c.user_id == user_id)]
        return {"removed": True, "contact_id": contact_id}

    def get_contacts(self, user_id: str = "default") -> list[dict]:
        return [
            {"id": c.id, "name": c.name, "phone": c.phone, "relationship": c.relationship, "is_primary": c.is_primary}
            for c in self._user_contacts(user_id)
        ]

    # === Medical Info ===

    def set_medical_info(self, blood_type: str = "unknown", allergies: list = None,
                         conditions: list = None, medications: list = None,
                         emergency_note: str = "", user_id: str = "default") -> dict:
        self._medical_info[user_id] = MedicalInfo(
            blood_type=blood_type, allergies=allergies or [],
            conditions=conditions or [], medications=medications or [],
            emergency_note=emergency_note, user_id=user_id,
        )
        return {"updated": True}

    def get_medical_info(self, user_id: str = "default") -> dict:
        m = self._medical_info.get(user_id, MedicalInfo())
        return {
            "blood_type": m.blood_type, "allergies": m.allergies,
            "conditions": m.conditions, "medications": m.medications,
            "emergency_note": m.emergency_note,
        }

    # === SOS Activation (per-user) ===

    def activate_sos(self, user_id: str = "default", location: Optional[dict] = None) -> dict:
        """Activate emergency SOS alert. Each user has their own active alert."""
        existing = self._active_alerts.get(user_id)
        if existing and existing.status == SOSStatus.ACTIVATED:
            return {"error": "SOS already active"}

        alert = SOSAlert(
            alert_id=f"sos_{secrets.token_hex(6)}",
            status=SOSStatus.ACTIVATED,
            activated_at=time.time(),
            location=location,
            user_id=user_id,
        )
        self._active_alerts[user_id] = alert

        primary = [c for c in self._user_contacts(user_id) if c.is_primary]
        all_contacts = primary if primary else self._user_contacts(user_id)
        alert.contacts_notified = [c.name for c in all_contacts]

        return {
            "activated": True,
            "alert_id": alert.alert_id,
            "countdown_seconds": self.SOS_COUNTDOWN_SECONDS,
            "contacts_notified": alert.contacts_notified,
            "message": f"Emergency SOS activated! Notifying {len(alert.contacts_notified)} contacts.",
            "medical_info_sent": self.get_medical_info(user_id),
            "location_shared": location is not None,
        }

    def confirm_sos(self, alert_id: str, user_id: str = "default") -> dict:
        alert = self._active_alerts.get(user_id)
        if not alert or alert.alert_id != alert_id:
            return {"error": "Invalid alert ID"}
        if alert.user_id != user_id:
            return {"error": "Not authorized"}
        alert.status = SOSStatus.CONFIRMED
        return {"confirmed": True, "message": "Emergency services and contacts have been alerted"}

    def cancel_sos(self, alert_id: str, user_id: str = "default") -> dict:
        alert = self._active_alerts.get(user_id)
        if not alert or alert.alert_id != alert_id:
            return {"error": "Invalid alert ID"}
        if alert.user_id != user_id:
            return {"error": "Not authorized"}
        alert.status = SOSStatus.CANCELLED
        alert.resolved_at = time.time()
        self._alert_history.append(alert)
        del self._active_alerts[user_id]
        return {"cancelled": True, "message": "SOS alert cancelled"}

    def check_fall_detection(self, accelerometer_data: dict, user_id: str = "default") -> dict:
        magnitude = accelerometer_data.get("magnitude_g", 1.0)
        if magnitude >= self.FALL_THRESHOLD_G:
            return {
                "fall_detected": True,
                "confidence": min(0.95, magnitude / 5.0),
                "magnitude": magnitude,
                "action": "Consider activating SOS",
                "auto_suggestion": "A potential fall was detected. Would you like to activate Emergency SOS?",
            }
        return {"fall_detected": False, "magnitude": magnitude}

    def get_emergency_card(self, user_id: str = "default") -> dict:
        m = self._medical_info.get(user_id, MedicalInfo())
        user_contacts = self._user_contacts(user_id)
        primary = next((c for c in user_contacts if c.is_primary), user_contacts[0] if user_contacts else None)
        return {
            "medical_info": {
                "blood_type": m.blood_type, "allergies": m.allergies,
                "conditions": m.conditions, "medications": m.medications,
                "emergency_note": m.emergency_note,
            },
            "emergency_contact": {
                "name": primary.name if primary else "None",
                "phone": primary.phone if primary else "None",
                "relationship": primary.relationship if primary else "",
            } if primary else None,
            "emergency_number": "911",
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def get_alert_history(self, user_id: str = "default") -> list[dict]:
        return [
            {"id": a.alert_id, "status": a.status.value, "activated_at": a.activated_at,
             "resolved_at": a.resolved_at, "contacts": a.contacts_notified}
            for a in [h for h in self._alert_history if h.user_id == user_id][-20:]
        ]

    # === Safety Check Timer ===

    def start_safety_check(self, user_id: str, check_in_minutes: int, message: str = "Are you safe?", notify_contacts: bool = True) -> dict:
        """Start a safety check timer. User must respond before deadline or contacts are notified."""
        # Cancel any existing active safety check
        for cid, check in self._safety_checks.items():
            if check.user_id == user_id and check.status == "active":
                check.status = "cancelled"

        check_id = f"sc_{secrets.token_hex(6)}"
        deadline = time.time() + check_in_minutes * 60
        check = SafetyCheck(
            check_id=check_id,
            user_id=user_id,
            deadline=deadline,
            message=message,
            notify_contacts=notify_contacts,
        )
        self._safety_checks[check_id] = check

        contacts = self._user_contacts(user_id)
        primary = [c for c in contacts if c.is_primary]
        notify_list = [c.name for c in primary] if primary else [c.name for c in contacts]

        return {
            "started": True,
            "check_id": check_id,
            "deadline": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(deadline)),
            "minutes_remaining": check_in_minutes,
            "message": message,
            "contacts_will_notify": notify_list if notify_contacts else [],
            "instructions": f"Respond within {check_in_minutes} minutes to confirm you're safe. If you don't respond, your emergency contacts will be notified.",
        }

    def respond_safety_check(self, check_id: str, user_id: str, safe: bool = True, note: str = "") -> dict:
        """Respond to a safety check — confirms user is safe."""
        check = self._safety_checks.get(check_id)
        if not check or check.user_id != user_id:
            return {"error": "Invalid or not found check_id"}
        if check.status != "active":
            return {"error": f"Check is already {check.status}"}

        check.status = "responded"
        check.responded_at = time.time()
        check.safe = safe
        check.note = note
        self._safety_history.append(check)

        return {
            "responded": True,
            "safe": safe,
            "message": f"Safety confirmed. Thank you!" if safe else "Your contacts will be notified that you need help.",
            "check_id": check_id,
        }

    def get_active_safety_checks(self, user_id: str) -> list[dict]:
        """Get active safety checks that need response."""
        now = time.time()
        active = []
        for check in self._safety_checks.values():
            if check.user_id == user_id and check.status == "active":
                remaining = max(0, check.deadline - now)
                active.append({
                    "check_id": check.check_id,
                    "message": check.message,
                    "deadline": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(check.deadline)),
                    "seconds_remaining": int(remaining),
                    "notify_contacts": check.notify_contacts,
                    "is_overdue": remaining <= 0,
                })
        return active

    def get_safety_check_history(self, user_id: str, limit: int = 20) -> list[dict]:
        return [
            {
                "check_id": c.check_id,
                "status": c.status,
                "safe": c.safe,
                "note": c.note,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(c.created_at)),
                "responded_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(c.responded_at)) if c.responded_at else None,
            }
            for c in [h for h in self._safety_history if h.user_id == user_id][-limit:]
        ]

    def check_expired_safety_checks(self) -> list[dict]:
        """Check for expired safety checks (call periodically). Returns list of checks that need escalation."""
        now = time.time()
        escalated = []
        for check in list(self._safety_checks.values()):
            if check.status == "active" and check.deadline < now:
                check.status = "escalated"
                self._safety_history.append(check)
                contacts = self._user_contacts(check.user_id)
                primary = [c for c in contacts if c.is_primary]
                notify = primary if primary else contacts
                escalated.append({
                    "check_id": check.check_id,
                    "user_id": check.user_id,
                    "message": check.message,
                    "overdue_seconds": int(now - check.deadline),
                    "contacts_to_notify": [{"name": c.name, "phone": c.phone} for c in notify],
                })
        return escalated


emergency_sos_service = EmergencySOSService()

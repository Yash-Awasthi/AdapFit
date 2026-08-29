"""
Family & Caregiver Mode — Monitor family members' health

Features:
- Family group creation and management
- Health data sharing with permission levels
- Elderly parent monitoring (medication adherence, vitals)
- Child health tracking
- Emergency alerts for family members
- Caregiver dashboard
"""
import time
import secrets
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class FamilyMember:
    user_id: str
    name: str
    relationship: str  # parent, child, spouse, sibling, other
    age: int
    avatar_url: str = ""
    is_caregiver: bool = False
    permissions: dict = field(default_factory=lambda: {"view_vitals": True, "view_medications": True, "view_location": False, "send_alerts": True})
    added_at: float = field(default_factory=time.time)


class FamilyModeService:
    """Family health monitoring and caregiving features."""

    def __init__(self):
        self._groups: dict[str, list[FamilyMember]] = {}
        self._alerts: list[dict] = []
        self._shared_data: dict[str, dict] = {}

    def create_group(self, owner_id: str, group_name: str = "My Family") -> dict:
        group_id = f"family_{secrets.token_hex(6)}"
        self._groups[group_id] = [FamilyMember(user_id=owner_id, name="You", relationship="self", age=30, is_caregiver=True)]
        return {"group_id": group_id, "group_name": group_name, "members": 1}

    def add_member(self, group_id: str, name: str, relationship: str, age: int, user_id: str = "") -> dict:
        group = self._groups.get(group_id)
        if not group:
            return {"error": "Group not found"}
        member_id = user_id or f"member_{secrets.token_hex(6)}"
        member = FamilyMember(user_id=member_id, name=name, relationship=relationship, age=age)
        group.append(member)
        return {"added": True, "member": {"id": member_id, "name": name, "relationship": relationship}}

    def get_members(self, group_id: str) -> list[dict]:
        group = self._groups.get(group_id, [])
        return [{"user_id": m.user_id, "name": m.name, "relationship": m.relationship, "age": m.age, "is_caregiver": m.is_caregiver, "permissions": m.permissions} for m in group]

    def update_permissions(self, group_id: str, member_id: str, permissions: dict) -> dict:
        group = self._groups.get(group_id, [])
        for m in group:
            if m.user_id == member_id:
                m.permissions.update(permissions)
                return {"updated": True}
        return {"error": "Member not found"}

    def send_family_alert(self, group_id: str, from_member: str, alert_type: str, message: str) -> dict:
        alert = {
            "id": f"alert_{secrets.token_hex(6)}", "group_id": group_id,
            "from": from_member, "type": alert_type, "message": message,
            "timestamp": time.time(), "read": False,
        }
        self._alerts.append(alert)
        return {"sent": True, "alert_id": alert["id"]}

    def get_alerts(self, group_id: str, unread_only: bool = False) -> list[dict]:
        alerts = [a for a in self._alerts if a["group_id"] == group_id]
        if unread_only:
            alerts = [a for a in alerts if not a["read"]]
        return alerts

    def share_health_data(self, group_id: str, member_id: str, data_type: str, data: dict) -> dict:
        key = f"{group_id}:{member_id}:{data_type}"
        self._shared_data[key] = {"data": data, "shared_at": time.time()}
        return {"shared": True, "data_type": data_type}

    def get_shared_data(self, group_id: str, member_id: str, data_type: str) -> Optional[dict]:
        key = f"{group_id}:{member_id}:{data_type}"
        return self._shared_data.get(key)

    def get_caregiver_dashboard(self, group_id: str) -> dict:
        members = self.get_members(group_id)
        alerts = self.get_alerts(group_id, unread_only=True)
        return {
            "total_members": len(members),
            "caregivers": sum(1 for m in members if m.get("is_caregiver")),
            "dependents": sum(1 for m in members if not m.get("is_caregiver")),
            "unread_alerts": len(alerts),
            "recent_alerts": alerts[:5],
            "members": members,
        }

    def get_elderly_monitoring(self, group_id: str, member_id: str) -> dict:
        return {
            "member_id": member_id,
            "medication_adherence": 92,
            "last_vitals_check": time.strftime("%Y-%m-%d %H:%M"),
            "activity_level": "moderate",
            "sleep_quality": 7,
            "mood_trend": "stable",
            "fall_risk": "low",
            "alerts": ["Medication due in 2 hours", "Blood pressure check recommended"],
        }

    def get_child_health(self, group_id: str, member_id: str) -> dict:
        return {
            "member_id": member_id,
            "growth_percentile": 75,
            "vaccinations_up_to_date": True,
            "activity_minutes_today": 45,
            "screen_time_today": 120,
            "sleep_hours_last_night": 9.5,
            "nutrition_score": 82,
            "milestones": ["Walking at 12 months", "First words at 18 months"],
        }


family_mode_service = FamilyModeService()

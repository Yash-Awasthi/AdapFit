"""
Biometric Health Data Unlock & Sharing
Secure sharing of health data with providers, family, and researchers.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
import hashlib


class BiometricDataUnlock:
    SHARE_TYPES = {
        "provider": {"name": "Healthcare Provider", "duration_days": 90, "data_scope": "full"},
        "family": {"name": "Family Member", "duration_days": 30, "data_scope": "summary"},
        "researcher": {"name": "Research Study", "duration_days": 365, "data_scope": "anonymized"},
        "insurance": {"name": "Insurance Company", "duration_days": 180, "data_scope": "summary"},
        "emergency": {"name": "Emergency Access", "duration_days": 1, "data_scope": "critical"},
        "fitness_app": {"name": "Fitness App", "duration_days": 365, "data_scope": "activity"},
    }

    DATA_SCOPES = {
        "critical": ["vitals", "allergies", "medications", "emergency_contacts", "medical_conditions"],
        "summary": ["vitals", "medications", "conditions", "allergies", "recent_activity"],
        "full": ["vitals", "medications", "conditions", "allergies", "lab_results", "imaging", "notes", "activity", "sleep", "nutrition"],
        "anonymized": ["aggregated_metrics", "trends", "outcomes"],
        "activity": ["steps", "workouts", "heart_rate", "sleep"],
    }

    def __init__(self):
        self.shares: Dict[str, List[dict]] = {}
        self.access_logs: Dict[str, List[dict]] = {}
        self.revoked: Dict[str, List[str]] = {}

    def create_share(self, user_id: str, recipient_name: str, share_type: str, custom_duration_days: Optional[int] = None, custom_data_scope: Optional[str] = None, pin_code: Optional[str] = None) -> dict:
        share_config = self.SHARE_TYPES.get(share_type, {})
        duration = custom_duration_days or share_config.get("duration_days", 30)
        data_scope = custom_data_scope or share_config.get("data_scope", "summary")
        share_id = str(uuid.uuid4())[:8]
        access_token = hashlib.sha256(f"{user_id}_{share_id}_{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        share = {
            "share_id": share_id,
            "user_id": user_id,
            "recipient_name": recipient_name,
            "share_type": share_type,
            "share_type_name": share_config.get("name", share_type),
            "data_scope": data_scope,
            "data_fields": self.DATA_SCOPES.get(data_scope, []),
            "access_token": access_token,
            "pin_required": pin_code is not None,
            "expires_at": (datetime.now() + timedelta(days=duration)).isoformat(),
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "access_count": 0,
        }
        self.shares.setdefault(user_id, []).append(share)
        return share

    def revoke_share(self, user_id: str, share_id: str) -> dict:
        for share in self.shares.get(user_id, []):
            if share["share_id"] == share_id:
                share["is_active"] = False
                share["revoked_at"] = datetime.now().isoformat()
                self.revoked.setdefault(user_id, []).append(share_id)
                return {"share_id": share_id, "status": "revoked"}
        return {"error": "Share not found"}

    def get_active_shares(self, user_id: str) -> List[dict]:
        now = datetime.now()
        return [s for s in self.shares.get(user_id, []) if s["is_active"] and datetime.fromisoformat(s["expires_at"]) > now]

    def log_access(self, user_id: str, share_id: str, accessed_by: str) -> dict:
        entry = {"share_id": share_id, "accessed_by": accessed_by, "timestamp": datetime.now().isoformat()}
        self.access_logs.setdefault(user_id, []).append(entry)
        for share in self.shares.get(user_id, []):
            if share["share_id"] == share_id:
                share["access_count"] += 1
        return entry

    def get_share_analytics(self, user_id: str) -> dict:
        shares = self.shares.get(user_id, [])
        return {"total_shares": len(shares), "active_shares": len(self.get_active_shares(user_id)), "total_accesses": sum(s["access_count"] for s in shares), "by_type": {t: sum(1 for s in shares if s["share_type"] == t) for t in set(s["share_type"] for s in shares) if shares}}


biometric_unlock = BiometricDataUnlock()

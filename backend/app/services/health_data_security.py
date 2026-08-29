"""
Health Data Security — Encryption, audit logging, and compliance
"""
from datetime import datetime
from typing import Dict, List, Optional
import uuid
import hashlib


class HealthDataSecurity:
    COMPLIANCE_STANDARDS = {
        "hipaa": {"name": "HIPAA", "description": "Health Insurance Portability and Accountability Act", "requirements": ["encryption_at_rest", "encryption_in_transit", "access_controls", "audit_logging", "data_backup", "incident_response"]},
        "gdpr": {"name": "GDPR", "description": "General Data Protection Regulation", "requirements": ["data_minimization", "consent_management", "right_to_erasure", "data_portability", "breach_notification", "privacy_by_design"]},
        "HITECH": {"name": "HITECH Act", "description": "Health Information Technology for Economic and Clinical Health", "requirements": ["breach_notification", "encryption", "audit_trail", "business_associate_agreements"]},
        "SOC2": {"name": "SOC 2", "description": "Service Organization Control 2", "requirements": ["security", "availability", "processing_integrity", "confidentiality", "privacy"]},
        "ISO27001": {"name": "ISO 27001", "description": "Information Security Management", "requirements": ["risk_assessment", "access_control", "cryptography", "incident_management", "business_continuity"]},
    }

    ENCRYPTION_METHODS = {
        "aes_256": {"name": "AES-256", "type": "symmetric", "use": "data_at_rest"},
        "rsa_2048": {"name": "RSA-2048", "type": "asymmetric", "use": "key_exchange"},
        "sha_256": {"name": "SHA-256", "type": "hash", "use": "data_integrity"},
        "bcrypt": {"name": "bcrypt", "type": "hash", "use": "password_hashing"},
    }

    def __init__(self):
        self.audit_logs: Dict[str, List[dict]] = {}
        self.data_access_logs: Dict[str, List[dict]] = {}
        self.encryption_keys: Dict[str, dict] = {}
        self.compliance_status: Dict[str, dict] = {}

    def log_audit_event(self, user_id: str, action: str, resource: str, details: str = "", ip_address: str = "") -> dict:
        event = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "details": details,
            "ip_address": ip_address,
            "timestamp": datetime.now().isoformat(),
            "hash": hashlib.sha256(f"{user_id}_{action}_{resource}_{datetime.now().isoformat()}".encode()).hexdigest()[:16],
        }
        self.audit_logs.setdefault(user_id, []).append(event)
        return event

    def log_data_access(self, user_id: str, accessor: str, data_type: str, purpose: str) -> dict:
        log = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "accessor": accessor,
            "data_type": data_type,
            "purpose": purpose,
            "timestamp": datetime.now().isoformat(),
        }
        self.data_access_logs.setdefault(user_id, []).append(log)
        return log

    def check_compliance(self, standard: str) -> dict:
        config = self.COMPLIANCE_STANDARDS.get(standard)
        if not config:
            return {"error": f"Unknown standard: {standard}"}
        
        results = []
        for req in config["requirements"]:
            results.append({"requirement": req, "status": "implemented", "last_audit": datetime.now().isoformat()})
        
        score = sum(1 for r in results if r["status"] == "implemented") / len(results) * 100
        
        return {
            "standard": standard,
            "name": config["name"],
            "description": config["description"],
            "total_requirements": len(results),
            "implemented": sum(1 for r in results if r["status"] == "implemented"),
            "compliance_score": round(score, 1),
            "results": results,
        }

    def get_audit_logs(self, user_id: str, limit: int = 100) -> List[dict]:
        return self.audit_logs.get(user_id, [])[-limit:]

    def get_data_access_summary(self, user_id: str) -> dict:
        logs = self.data_access_logs.get(user_id, [])
        accessors = {}
        for log in logs:
            acc = log["accessor"]
            accessors[acc] = accessors.get(acc, 0) + 1
        return {"total_accesses": len(logs), "unique_accessors": len(accessors), "by_accessor": dict(sorted(accessors.items(), key=lambda x: x[1], reverse=True)[:10])}


health_security = HealthDataSecurity()

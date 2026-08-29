"""Medical ID & Emergency Health Information Service.

Based on 2025 medical ID research:
- QR code medical ID generation
- Emergency contact management
- Medical information wallet card
- Allergy and medication display
- Health data sharing with providers
- ICE (In Case of Emergency) profile
"""

import time
import json
import hashlib
from typing import Dict, List, Optional, Any


class MedicalIDService:
    """Emergency medical ID and health information management."""

    def __init__(self):
        self.profiles: Dict[str, Dict] = {}

    def create_medical_id(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive medical ID."""
        profile = {
            "user_id": user_id,
            "full_name": data.get("full_name", "Unknown"),
            "date_of_birth": data.get("dob"),
            "blood_type": data.get("blood_type", "unknown"),
            "height": data.get("height"),
            "weight": data.get("weight"),
            "allergies": data.get("allergies", []),
            "medications": data.get("medications", []),
            "medical_conditions": data.get("conditions", []),
            "surgical_history": data.get("surgeries", []),
            "implants": data.get("implants", []),
            "emergency_contacts": data.get("emergency_contacts", []),
            "primary_physician": data.get("physician"),
            "insurance": data.get("insurance"),
            "organ_donor": data.get("organ_donor", False),
            "dnr_order": data.get("dnr", False),
            "special_needs": data.get("special_needs", ""),
            "notes": data.get("notes", ""),
            "last_updated": time.time(),
            "qr_code_hash": None,
        }

        # Generate QR code hash
        qr_data = {
            "name": profile["full_name"],
            "blood_type": profile["blood_type"],
            "allergies": profile["allergies"],
            "medications": profile["medications"],
            "conditions": profile["medical_conditions"],
            "contacts": profile["emergency_contacts"],
        }
        profile["qr_code_hash"] = hashlib.sha256(json.dumps(qr_data, sort_keys=True).encode()).hexdigest()[:16]
        profile["qr_code_data"] = qr_data

        self.profiles[user_id] = profile
        return profile

    def get_emergency_view(self, user_id: str) -> Dict[str, Any]:
        """Get emergency-first responder view of medical ID."""
        profile = self.profiles.get(user_id)
        if not profile:
            return {"error": "No medical ID found"}

        return {
            "header": f"⚠️ MEDICAL ID — {profile['full_name']}",
            "critical_info": {
                "blood_type": profile["blood_type"],
                "allergies": profile["allergies"],
                "medications": profile["medications"],
                "conditions": profile["medical_conditions"],
                "emergency_contacts": profile["emergency_contacts"],
                "organ_donor": profile["organ_donor"],
                "dnr_order": profile["dnr_order"],
            },
            "full_profile": profile,
            "display_format": "emergency_card",
            "qr_code": profile.get("qr_code_hash"),
        }

    def get_wallet_card(self, user_id: str) -> Dict[str, Any]:
        """Generate wallet card data for printing/display."""
        profile = self.profiles.get(user_id)
        if not profile:
            return {"error": "No medical ID found"}

        return {
            "card_type": "Medical ID",
            "name": profile["full_name"],
            "blood_type": profile["blood_type"],
            "allergies": profile["allergies"][:5],
            "medications": profile["medications"][:5],
            "conditions": profile["medical_conditions"][:3],
            "emergency_contact": profile["emergency_contacts"][0] if profile["emergency_contacts"] else {},
            "physician": profile.get("primary_physician"),
            "insurance": profile.get("insurance"),
            "qr_code": profile.get("qr_code_hash"),
            "disclaimer": "This is not a substitute for professional medical advice",
        }

    def add_emergency_contact(self, user_id: str, contact: Dict[str, Any]) -> Dict[str, Any]:
        """Add an emergency contact."""
        profile = self.profiles.get(user_id)
        if not profile:
            return {"error": "No medical ID found"}

        entry = {
            "name": contact.get("name"),
            "relationship": contact.get("relationship"),
            "phone": contact.get("phone"),
            "is_primary": contact.get("is_primary", False),
        }

        profile["emergency_contacts"].append(entry)
        return entry

    def get_health_summary_for_provider(self, user_id: str) -> Dict[str, Any]:
        """Generate health summary for sharing with healthcare providers."""
        profile = self.profiles.get(user_id)
        if not profile:
            return {"error": "No medical ID found"}

        return {
            "patient": profile["full_name"],
            "dob": profile["date_of_birth"],
            "demographics": {"height": profile["height"], "weight": profile["weight"], "blood_type": profile["blood_type"]},
            "active_conditions": profile["medical_conditions"],
            "current_medications": profile["medications"],
            "allergies": profile["allergies"],
            "surgical_history": profile["surgical_history"],
            "implants": profile["implants"],
            "primary_physician": profile["primary_physician"],
            "insurance": profile["insurance"],
            "generated_at": time.time(),
            "format": "FHIR_R4_compatible",
        }

    def update_medical_id(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update medical ID with new information."""
        profile = self.profiles.get(user_id)
        if not profile:
            return {"error": "No medical ID found"}

        for key, value in updates.items():
            if key in profile:
                profile[key] = value

        profile["last_updated"] = time.time()

        # Regenerate QR
        qr_data = {
            "name": profile["full_name"],
            "blood_type": profile["blood_type"],
            "allergies": profile["allergies"],
            "medications": profile["medications"],
            "conditions": profile["medical_conditions"],
            "contacts": profile["emergency_contacts"],
        }
        profile["qr_code_hash"] = hashlib.sha256(json.dumps(qr_data, sort_keys=True).encode()).hexdigest()[:16]
        profile["qr_code_data"] = qr_data

        return {"updated": True, "last_updated": profile["last_updated"]}


medical_id_service = MedicalIDService()

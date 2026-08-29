"""
Health Passport — Digital vaccination records, travel health certificates, and verification
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
import hashlib


class HealthPassportService:
    VACCINE_DATABASE = {
        "covid19_pfizer": {"name": "COVID-19 (Pfizer-BioNTech)", "doses": 2, "boosters": 3, "interval_days": 21, "validity_days": 180, "who_approved": True},
        "covid19_moderna": {"name": "COVID-19 (Moderna)", "doses": 2, "boosters": 3, "interval_days": 28, "validity_days": 180, "who_approved": True},
        "covid19_janssen": {"name": "COVID-19 (Janssen)", "doses": 1, "boosters": 2, "interval_days": 0, "validity_days": 180, "who_approved": True},
        "influenza": {"name": "Influenza (Flu)", "doses": 1, "boosters": 1, "interval_days": 0, "validity_days": 365, "who_approved": True},
        "hepatitis_a": {"name": "Hepatitis A", "doses": 2, "boosters": 0, "interval_days": 180, "validity_days": 3650, "who_approved": True},
        "hepatitis_b": {"name": "Hepatitis B", "doses": 3, "boosters": 0, "interval_days": 28, "validity_days": 3650, "who_approved": True},
        "mmr": {"name": "Measles, Mumps, Rubella", "doses": 2, "boosters": 0, "interval_days": 28, "validity_days": 36500, "who_approved": True},
        "yellow_fever": {"name": "Yellow Fever", "doses": 1, "boosters": 0, "interval_days": 0, "validity_days": 36500, "who_approved": True},
        "typhoid": {"name": "Typhoid", "doses": 1, "boosters": 0, "interval_days": 0, "validity_days": 1095, "who_approved": True},
        "tetanus": {"name": "Tetanus (Tdap)", "doses": 1, "boosters": 1, "interval_days": 0, "validity_days": 3650, "who_approved": True},
        "hpv": {"name": "HPV (Gardasil)", "doses": 3, "boosters": 0, "interval_days": 60, "validity_days": 36500, "who_approved": True},
        "rabies": {"name": "Rabies", "doses": 3, "boosters": 0, "interval_days": 7, "validity_days": 1095, "who_approved": True},
        "meningococcal": {"name": "Meningococcal", "doses": 2, "boosters": 0, "interval_days": 0, "validity_days": 3650, "who_approved": True},
        "pneumococcal": {"name": "Pneumococcal (PCV13)", "doses": 4, "boosters": 0, "interval_days": 60, "validity_days": 36500, "who_approved": True},
    }

    TRAVEL_REQUIREMENTS = {
        "africa": {"required": ["yellow_fever", "hepatitis_a"], "recommended": ["typhoid", "rabies", "meningococcal", "hepatitis_b", "tetanus"]},
        "southeast_asia": {"required": [], "recommended": ["hepatitis_a", "typhoid", "hepatitis_b", "rabies", "japanese_encephalitis", "tetanus"]},
        "south_america": {"required": ["yellow_fever"], "recommended": ["hepatitis_a", "typhoid", "rabies", "tetanus"]},
        "middle_east": {"required": [], "recommended": ["hepatitis_a", "typhoid", "meningococcal", "hepatitis_b", "tetanus"]},
        "europe": {"required": [], "recommended": ["hepatitis_a", "hepatitis_b", "meningococcal", "tetanus"]},
        "central_america": {"required": [], "recommended": ["yellow_fever", "hepatitis_a", "typhoid", "rabies", "tetanus"]},
        "australia": {"required": [], "recommended": ["hepatitis_a", "hepatitis_b", "meningococcal", "tetanus"]},
        "pacific_islands": {"required": [], "recommended": ["hepatitis_a", "typhoid", "hepatitis_b", "tetanus"]},
    }

    def __init__(self):
        self.passports: Dict[str, dict] = {}
        self.vaccinations: Dict[str, List[dict]] = {}
        self.lab_results: Dict[str, List[dict]] = {}
        self.certificates: Dict[str, dict] = {}
        self.travel_plans: Dict[str, dict] = {}

    def create_passport(self, user_id: str, full_name: str, dob: str, nationality: str, passport_number: str = "") -> dict:
        passport_id = str(uuid.uuid4())[:8]
        passport = {
            "id": passport_id,
            "user_id": user_id,
            "full_name": full_name,
            "date_of_birth": dob,
            "nationality": nationality,
            "passport_number": passport_number,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "verification_hash": hashlib.sha256(f"{user_id}_{full_name}_{dob}".encode()).hexdigest()[:16],
        }
        self.passports[user_id] = passport
        self.vaccinations[user_id] = []
        self.lab_results[user_id] = []
        return passport

    def add_vaccination(self, user_id: str, vaccine_key: str, dose_number: int, date_administered: str, lot_number: str = "", provider: str = "", location: str = "") -> dict:
        vaccine = self.VACCINE_DATABASE.get(vaccine_key)
        if not vaccine:
            return {"error": f"Unknown vaccine: {vaccine_key}"}
        
        record = {
            "id": str(uuid.uuid4()),
            "vaccine_key": vaccine_key,
            "vaccine_name": vaccine["name"],
            "dose_number": dose_number,
            "date_administered": date_administered,
            "lot_number": lot_number,
            "provider": provider,
            "location": location,
            "valid_until": (datetime.fromisoformat(date_administered) + timedelta(days=vaccine["validity_days"])).isoformat(),
            "recorded_at": datetime.now().isoformat(),
        }
        self.vaccinations.setdefault(user_id, []).append(record)
        return record

    def get_vaccination_status(self, user_id: str) -> List[dict]:
        vaccinations = self.vaccinations.get(user_id, [])
        status = []
        for vkey, vinfo in self.VACCINE_DATABASE.items():
            user_vax = [v for v in vaccinations if v["vaccine_key"] == vkey]
            status.append({
                "vaccine": vinfo["name"],
                "vaccine_key": vkey,
                "doses_received": len(user_vax),
                "doses_required": vinfo["doses"],
                "boosters_received": max(0, len(user_vax) - vinfo["doses"]),
                "boosters_recommended": vinfo["boosters"],
                "is_complete": len(user_vax) >= vinfo["doses"],
                "latest_date": user_vax[-1]["date_administered"] if user_vax else None,
                "valid_until": user_vax[-1]["valid_until"] if user_vax else None,
                "is_valid": datetime.fromisoformat(user_vax[-1]["valid_until"]) > datetime.now() if user_vax else False,
            })
        return status

    def check_travel_requirements(self, user_id: str, region: str) -> dict:
        requirements = self.TRAVEL_REQUIREMENTS.get(region.lower(), {})
        user_vax = self.vaccinations.get(user_id, [])
        user_vaccine_keys = {v["vaccine_key"] for v in user_vax}
        
        missing_required = [r for r in requirements.get("required", []) if r not in user_vaccine_keys]
        missing_recommended = [r for r in requirements.get("recommended", []) if r not in user_vaccine_keys]
        
        return {
            "region": region,
            "missing_required": [{"key": r, "name": self.VACCINE_DATABASE.get(r, {}).get("name", r)} for r in missing_required],
            "missing_recommended": [{"key": r, "name": self.VACCINE_DATABASE.get(r, {}).get("name", r)} for r in missing_recommended],
            "is_travel_ready": len(missing_required) == 0,
            "completion_percent": round((len(requirements.get("required", [])) - len(missing_required)) / max(len(requirements.get("required", [])), 1) * 100, 1),
        }

    def add_lab_result(self, user_id: str, test_name: str, result: str, reference_range: str, date: str, provider: str = "") -> dict:
        record = {
            "id": str(uuid.uuid4()),
            "test_name": test_name,
            "result": result,
            "reference_range": reference_range,
            "date": date,
            "provider": provider,
            "recorded_at": datetime.now().isoformat(),
        }
        self.lab_results.setdefault(user_id, []).append(record)
        return record

    def generate_certificate(self, user_id: str, purpose: str, validity_days: int = 365) -> dict:
        passport = self.passports.get(user_id)
        if not passport:
            return {"error": "No passport found"}
        
        cert_id = str(uuid.uuid4())[:8]
        certificate = {
            "cert_id": cert_id,
            "passport_id": passport["id"],
            "holder_name": passport["full_name"],
            "purpose": purpose,
            "vaccinations": self.vaccinations.get(user_id, []),
            "issued_at": datetime.now().isoformat(),
            "valid_until": (datetime.now() + timedelta(days=validity_days)).isoformat(),
            "verification_code": hashlib.sha256(f"{cert_id}_{user_id}_{datetime.now().isoformat()}".encode()).hexdigest()[:12].upper(),
        }
        self.certificates[cert_id] = certificate
        return certificate

    def get_passport(self, user_id: str) -> dict:
        return self.passports.get(user_id, {"error": "No passport found"})

    def get_regions(self) -> List[str]:
        return list(self.TRAVEL_REQUIREMENTS.keys())


health_passport = HealthPassportService()

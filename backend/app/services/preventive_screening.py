"""Preventive Screening & Cancer Early Detection Service.

Based on 2025 ACS/CDC/NCI guidelines:
- Age/gender-based screening schedules
- Cancer risk assessment calculators
- Screening result tracking
- Follow-up reminders
- Family history risk evaluation
"""

import time
from typing import Dict, List, Any


class PreventiveScreeningService:
    """Preventive health screenings and cancer risk assessment."""

    def __init__(self):
        self.profiles: Dict[str, Dict] = {}
        self.screening_history: Dict[str, List] = {}
        self._init_screening_guidelines()

    def _init_screening_guidelines(self):
        self.screenings = {
            "breast_cancer": {
                "name": "Breast Cancer (Mammogram)",
                "start_age": 40, "end_age": 74,
                "frequency_years": 2,
                "gender": "female",
                "risk_factors": ["family_history", "BRCA mutation", "dense_breasts", "obesity", "alcohol"],
            },
            "cervical_cancer": {
                "name": "Cervical Cancer (Pap/HPV)",
                "start_age": 21, "end_age": 65,
                "frequency_years": 3,
                "gender": "female",
                "risk_factors": ["HPV", "smoking", "immunosuppression"],
            },
            "colorectal_cancer": {
                "name": "Colorectal Cancer (Colonoscopy)",
                "start_age": 45, "end_age": 75,
                "frequency_years": 10,
                "gender": "all",
                "risk_factors": ["family_history", "IBD", "polyps", "obesity", "smoking"],
            },
            "lung_cancer": {
                "name": "Lung Cancer (Low-dose CT)",
                "start_age": 50, "end_age": 80,
                "frequency_years": 1,
                "gender": "all",
                "risk_factors": ["smoking_30_pack_years", "radon", "asbestos"],
            },
            "prostate_cancer": {
                "name": "Prostate Cancer (PSA)",
                "start_age": 50, "end_age": 70,
                "frequency_years": 2,
                "gender": "male",
                "risk_factors": ["family_history", "African_descent", "obesity"],
            },
            "blood_pressure": {
                "name": "Blood Pressure Screening",
                "start_age": 18, "end_age": 100,
                "frequency_years": 1,
                "gender": "all",
                "risk_factors": ["obesity", "sodium", "family_history"],
            },
            "cholesterol": {
                "name": "Cholesterol (Lipid Panel)",
                "start_age": 20, "end_age": 65,
                "frequency_years": 5,
                "gender": "all",
                "risk_factors": ["obesity", "diabetes", "smoking", "family_history"],
            },
            "diabetes": {
                "name": "Diabetes (A1C/Fasting Glucose)",
                "start_age": 35, "end_age": 70,
                "frequency_years": 3,
                "gender": "all",
                "risk_factors": ["BMI_30_plus", "family_history", "gestational_diabetes"],
            },
            "eye_exam": {
                "name": "Eye Exam (Comprehensive)",
                "start_age": 40, "end_age": 100,
                "frequency_years": 2,
                "gender": "all",
                "risk_factors": ["diabetes", "hypertension", "family_history"],
            },
            "bone_density": {
                "name": "Bone Density (DEXA)",
                "start_age": 65, "end_age": 85,
                "frequency_years": 2,
                "gender": "female",
                "risk_factors": ["postmenopausal", "steroid_use", "thin_frame", "family_history"],
            },
        }

    def create_profile(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create screening profile."""
        self.profiles[user_id] = {
            "user_id": user_id,
            "age": data.get("age", 40),
            "gender": data.get("gender", "all"),
            "family_history": data.get("family_history", []),
            "personal_history": data.get("personal_history", []),
            "risk_factors": data.get("risk_factors", []),
            "lifestyle": data.get("lifestyle", {}),
            "created_at": time.time(),
        }
        return self.get_screening_schedule(user_id)

    def get_screening_schedule(self, user_id: str) -> Dict[str, Any]:
        """Get personalized screening schedule."""
        profile = self.profiles.get(user_id, {})
        age = profile.get("age", 40)
        gender = profile.get("gender", "all")

        due_soon = []
        completed = []
        not_yet = []

        for screening_id, info in self.screenings.items():
            if info["gender"] != "all" and info["gender"] != gender:
                continue

            if age < info["start_age"]:
                not_yet.append({"screening": info["name"], "starts_at_age": info["start_age"]})
            elif age > info["end_age"]:
                continue
            else:
                is_risk = any(r in profile.get("risk_factors", []) or r in profile.get("family_history", []) for r in info["risk_factors"])
                due_soon.append({
                    "screening": info["name"],
                    "frequency": f"Every {info['frequency_years']} year(s)",
                    "high_risk": is_risk,
                    "recommendation": "Start early due to risk factors" if is_risk else "Routine screening",
                })

        return {
            "user_id": user_id,
            "age": age,
            "gender": gender,
            "screenings_due": due_soon,
            "not_yet_due": not_yet,
            "total_recommended": len(due_soon),
        }

    def assess_cancer_risk(self, user_id: str) -> Dict[str, Any]:
        """Assess cancer risk based on factors."""
        profile = self.profiles.get(user_id, {})
        family = profile.get("family_history", [])
        lifestyle = profile.get("lifestyle", {})
        age = profile.get("age", 40)

        risks = {}
        if "breast_cancer" in family or "BRCA" in str(profile.get("risk_factors", [])):
            risks["breast"] = {"level": "elevated", "score": 25, "action": "Genetic counseling recommended"}
        if "colorectal_cancer" in family:
            risks["colorectal"] = {"level": "moderate", "score": 18, "action": "Start colonoscopy earlier"}
        if lifestyle.get("smoking"):
            risks["lung"] = {"level": "elevated", "score": 22, "action": "Annual low-dose CT scan"}
        if lifestyle.get("alcohol_heavy"):
            risks["liver"] = {"level": "moderate", "score": 15, "action": "Limit alcohol, liver function tests"}
        if age > 50:
            risks["general"] = {"level": "age_related", "score": 10, "action": "Stay current with age-appropriate screenings"}

        overall = sum(r.get("score", 0) for r in risks.values()) / max(1, len(risks))

        return {
            "overall_risk": "low" if overall < 10 else "moderate" if overall < 20 else "elevated",
            "specific_risks": risks,
            "recommendation": "Continue routine screenings" if overall < 10 else "Discuss enhanced screening with doctor",
        }

    def log_screening(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log a completed screening."""
        if user_id not in self.screening_history:
            self.screening_history[user_id] = []

        entry = {
            "screening": data.get("screening"),
            "date": data.get("date", time.strftime("%Y-%m-%d")),
            "result": data.get("result", "normal"),
            "provider": data.get("provider"),
            "notes": data.get("notes", ""),
            "next_due": data.get("next_due"),
            "logged_at": time.time(),
        }
        self.screening_history[user_id].append(entry)
        return entry


preventive_screening_service = PreventiveScreeningService()

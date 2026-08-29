"""
Government Health Schemes Knowledge Base — Core schemes only.
"""
import time
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class HealthScheme:
    id: str
    name: str
    country: str
    category: str
    description: str
    eligibility: dict = field(default_factory=dict)
    benefits: dict = field(default_factory=dict)
    application_process: list = field(default_factory=list)
    required_documents: list = field(default_factory=list)
    official_portal: str = ""
    helpline: str = ""
    disclaimer: str = "Possible eligibility — verify with official source"


class GovernmentSchemesService:
    def __init__(self):
        self._schemes: dict[str, HealthScheme] = {}
        self._load_schemes()

    def _load_schemes(self):
        schemes = [
            HealthScheme(
                id="pmjay",
                name="Ayushman Bharat — PM-JAY",
                country="IN",
                category="insurance",
                description="Health insurance covering hospitalization up to ₹5 lakh/year for economically vulnerable families.",
                eligibility={"income_limit_annual": 500000, "family_coverage": True},
                benefits={"coverage_amount": 500000, "cashless_treatment": True, "pre_existing_diseases": "From day 1"},
                application_process=["Visit empanelled hospital or CSC", "Carry Aadhaar + ration card", "Check eligibility at pmjay.gov.in"],
                required_documents=["Aadhaar card", "Ration card"],
                official_portal="https://pmjay.gov.in",
                helpline="14555",
            ),
            HealthScheme(
                id="esic",
                name="Employees' State Insurance (ESIC)",
                country="IN",
                category="insurance",
                description="Social security for employees earning up to ₹21,000/month — medical, sickness, maternity benefits.",
                eligibility={"monthly_wage_limit": 21000, "employee_contribution": "0.75%"},
                benefits={"medical_benefit": "Self and family", "maternity_benefit": "26 weeks paid leave"},
                application_process=["Employer registers with ESIC", "Employee receives e-Pehchan card"],
                required_documents=["Aadhaar card", "PAN card"],
                official_portal="https://www.esic.gov.in",
                helpline="1800-11-2526",
            ),
            HealthScheme(
                id="nhm",
                name="National Health Mission (NHM)",
                country="IN",
                category="preventive",
                description="Public health program covering immunization, maternal health, child health, and disease control.",
                eligibility={"target_population": "All citizens", "focus": ["pregnant_women", "children_under_5"]},
                benefits={"immunization": "Free vaccination", "maternal_health": "Free institutional delivery"},
                application_process=["Visit nearest PHC or CHC", "No registration needed for basic services"],
                required_documents=["Aadhaar (preferred, not mandatory)"],
                official_portal="https://nhm.gov.in",
                helpline="104",
            ),
        ]
        for s in schemes:
            self._schemes[s.id] = s

    def get_all_schemes(self, country: str = "IN") -> list[dict]:
        return [self._to_dict(s) for s in self._schemes.values() if s.country == country]

    def get_scheme(self, scheme_id: str) -> Optional[dict]:
        s = self._schemes.get(scheme_id)
        return self._to_dict(s) if s else None

    def search_schemes(self, query: str, country: str = "IN") -> list[dict]:
        q = query.lower()
        return [self._to_dict(s) for s in self._schemes.values()
                if s.country == country and q in (s.name + s.description + s.category).lower()]

    def check_eligibility(self, country: str = "IN", income_annual: Optional[float] = None,
                          is_bpl: Optional[bool] = None, **kwargs) -> list[dict]:
        results = []
        for s in self._schemes.values():
            if s.country != country:
                continue
            score = 0
            reasons = []
            if income_annual and s.eligibility.get("income_limit_annual"):
                if income_annual <= s.eligibility["income_limit_annual"]:
                    score += 2
                    reasons.append(f"Income below ₹{s.eligibility['income_limit_annual']:,} limit")
            if is_bpl:
                score += 1
                reasons.append("BPL families are eligible")
            if score:
                d = self._to_dict(s)
                d["eligibility_score"] = score
                d["eligibility_reasons"] = reasons
                results.append(d)
        results.sort(key=lambda x: x.get("eligibility_score", 0), reverse=True)
        return results

    def get_categories(self) -> list[dict]:
        cats = {}
        for s in self._schemes.values():
            cats[s.category] = cats.get(s.category, 0) + 1
        return [{"id": k, "name": k.replace("_", " ").title(), "count": v} for k, v in cats.items()]

    def _to_dict(self, s: HealthScheme) -> dict:
        return {
            "id": s.id, "name": s.name, "country": s.country, "category": s.category,
            "description": s.description, "eligibility": s.eligibility, "benefits": s.benefits,
            "application_process": s.application_process, "required_documents": s.required_documents,
            "official_portal": s.official_portal, "helpline": s.helpline, "disclaimer": s.disclaimer,
        }


government_schemes_service = GovernmentSchemesService()

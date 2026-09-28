"""
Indian public health schemes and helplines, with a conservative eligibility check.

Eligibility here is only ever "likely, confirm at the official portal". PM-JAY
in particular is decided by the SECC 2011 deprivation lists (and, since
October 2024, age 70+), not by income, so no income test is applied to it.
"""
from dataclasses import asdict, dataclass, field
from typing import Optional

VERIFY = "Confirm on the official portal or helpline before relying on this."


@dataclass
class HealthScheme:
    id: str
    name: str
    category: str
    description: str
    who: str
    official_portal: str
    helpline: str = ""
    how_to_apply: list[str] = field(default_factory=list)


SCHEMES = [
    HealthScheme(
        "pmjay", "Ayushman Bharat PM-JAY", "insurance",
        "Cashless hospital treatment up to ₹5 lakh per family per year at empanelled public and private hospitals.",
        "Families listed under the SECC 2011 deprivation criteria, and since October 2024 every person aged 70 "
        "or over regardless of income (Ayushman Vay Vandana card).",
        "https://beneficiary.nha.gov.in", "14555",
        ["Check your name at the beneficiary portal or any empanelled hospital's Ayushman Mitra desk",
         "Carry Aadhaar; create your Ayushman card on the portal or app"]),
    HealthScheme(
        "esic", "Employees' State Insurance (ESIC)", "insurance",
        "Medical care for you and your family at ESI dispensaries and hospitals, plus cash benefits during sickness and maternity.",
        "Employees of covered establishments earning up to ₹21,000 a month (₹25,000 for persons with disability).",
        "https://www.esic.gov.in", "1800-11-2526",
        ["Your employer registers you; ask HR for your ESIC (IP) number and e-Pehchan card"]),
    HealthScheme(
        "cghs", "Central Government Health Scheme (CGHS)", "insurance",
        "Outpatient and inpatient care for central government employees, pensioners and their dependants in CGHS cities.",
        "Central government employees, pensioners and eligible dependants.",
        "https://cghs.mohfw.gov.in", "1800-208-8900",
        ["Apply through your department or, for pensioners, the CGHS portal"]),
    HealthScheme(
        "jsy", "Janani Suraksha Yojana (JSY)", "maternity",
        "Cash assistance for giving birth in a government or accredited private facility.",
        "Pregnant women; the amount and conditions vary by state and area.",
        "https://nhm.gov.in", "104",
        ["Register your pregnancy with the ASHA worker or at the nearest government health centre"]),
    HealthScheme(
        "pmsma", "Pradhan Mantri Surakshit Matritva Abhiyan (PMSMA)", "maternity",
        "A free antenatal check-up by a doctor on the 9th of every month at government facilities.",
        "Pregnant women in the second and third trimester.",
        "https://pmsma.mohfw.gov.in", "104",
        ["Go to the nearest government health facility on the 9th of the month"]),
    HealthScheme(
        "esanjeevani", "eSanjeevani", "telemedicine",
        "Free video consultations with government doctors from your phone.",
        "Everyone in India.",
        "https://esanjeevani.mohfw.gov.in", "",
        ["Register with your mobile number in the eSanjeevani app or website"]),
    HealthScheme(
        "telemanas", "Tele-MANAS", "mental_health",
        "Free 24/7 mental health counselling by phone in Indian languages.",
        "Everyone in India.",
        "https://telemanas.mohfw.gov.in", "14416",
        ["Call 14416 or 1-800-891-4416"]),
    HealthScheme(
        "abha", "ABHA (Ayushman Bharat Health Account)", "records",
        "A free health ID that lets you link and share your health records across hospitals and apps.",
        "Everyone in India.",
        "https://abha.abdm.gov.in", "1800-11-4477",
        ["Create it with Aadhaar or a driving licence on the ABHA portal"]),
    HealthScheme(
        "helplines", "104 health helpline and 108 ambulance", "emergency",
        "104 gives medical advice and information; 108 sends a free ambulance in most states. 112 is the national emergency number.",
        "Everyone in India.",
        "https://nhm.gov.in", "108",
        ["Call 108 for an ambulance, 104 for health advice, 112 for any emergency"]),
]

EVERYONE = {"esanjeevani", "telemanas", "abha", "helplines"}


class GovernmentSchemesService:
    def get_all_schemes(self, country: str = "IN") -> list[dict]:
        return [asdict(s) for s in SCHEMES] if country == "IN" else []

    def get_scheme(self, scheme_id: str) -> Optional[dict]:
        return next((asdict(s) for s in SCHEMES if s.id == scheme_id), None)

    def search_schemes(self, query: str, country: str = "IN") -> list[dict]:
        q = query.lower()
        return [d for d in self.get_all_schemes(country) if q in (d["name"] + d["description"] + d["category"]).lower()]

    def get_categories(self) -> list[dict]:
        cats: dict[str, int] = {}
        for s in SCHEMES:
            cats[s.category] = cats.get(s.category, 0) + 1
        return [{"id": k, "name": k.replace("_", " ").title(), "count": v} for k, v in cats.items()]

    def check_eligibility(self, country: str = "IN", age: Optional[int] = None, is_pregnant: Optional[bool] = None,
                          monthly_wage: Optional[float] = None, formal_employee: Optional[bool] = None,
                          central_govt: Optional[bool] = None, in_secc_list: Optional[bool] = None, **_) -> list[dict]:
        """Schemes the answers point to, each with the reason. Never a guarantee."""
        if country != "IN":
            return []
        reasons: dict[str, str] = {}
        if age is not None and age >= 70:
            reasons["pmjay"] = "Everyone aged 70 or over is covered under Ayushman Vay Vandana."
        elif in_secc_list:
            reasons["pmjay"] = "Your family may be on the PM-JAY list; check the beneficiary portal."
        if formal_employee and monthly_wage is not None and monthly_wage <= 21000:
            reasons["esic"] = "Your wage is within the ESIC limit if your employer is covered."
        if central_govt:
            reasons["cghs"] = "Central government employees and pensioners are covered."
        if is_pregnant:
            reasons["jsy"] = "Cash support for a hospital delivery."
            reasons["pmsma"] = "A free check-up on the 9th of each month."
        for sid in EVERYONE:
            reasons.setdefault(sid, "Open to everyone in India.")
        return [{**self.get_scheme(sid), "reason": why, "note": VERIFY} for sid, why in reasons.items()]


government_schemes_service = GovernmentSchemesService()

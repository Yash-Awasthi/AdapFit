"""
Telemedicine: where to consult a registered practitioner, and a check that a
doctor is on the National Medical Commission's Indian Medical Register.

Under the Telemedicine Practice Guidelines 2020 only a registered medical
practitioner may consult. AdapFit has no provider contract, so it does not
book or host consultations: it links out to real services and lets the user
verify the doctor they were given.
"""
import re
import time
from typing import Optional

import httpx

NMC_SEARCH_URL = "https://nmc.org.in/indian-medical-register/search"
NMC_REGISTER_PAGE = "https://www.nmc.org.in/information-desk/indian-medical-register"
TIMEOUT_SECONDS = 15
HEADERS = {"User-Agent": "AdapFit/2.0 (health app; registration check)"}

SERVICES = [
    {
        "id": "esanjeevani", "name": "eSanjeevani", "kind": "government",
        "description": "Free video consultation with government doctors, run by the Ministry of Health.",
        "cost": "Free", "url": "https://esanjeevani.mohfw.gov.in", "phone": None,
    },
    {
        "id": "telemanas", "name": "Tele-MANAS", "kind": "government",
        "description": "Free 24/7 mental health counselling by phone in Indian languages.",
        "cost": "Free", "url": "https://telemanas.mohfw.gov.in", "phone": "14416",
    },
    {
        "id": "practo", "name": "Practo", "kind": "private",
        "description": "Online consultations with doctors across specialties.",
        "cost": "Fee set by the doctor on the platform", "url": "https://www.practo.com/consult", "phone": None,
    },
    {
        "id": "apollo247", "name": "Apollo 24|7", "kind": "private",
        "description": "Online consultations with Apollo Hospitals doctors.",
        "cost": "Fee set by the platform", "url": "https://www.apollo247.com/specialties", "phone": None,
    },
    {
        "id": "tata1mg", "name": "Tata 1mg", "kind": "private",
        "description": "Online doctor consultations alongside the 1mg pharmacy.",
        "cost": "Fee set by the platform", "url": "https://www.1mg.com/online-doctor-consultation", "phone": None,
    },
]

# Which kind of doctor handles a concern. Routing only: it names a
# specialty and a timeframe, never a cause.
SPECIALTY_GUIDE = [
    {"concern": "General symptoms, fever, first opinion", "see": "General physician", "when": "Within a few days, sooner if worsening"},
    {"concern": "A mole or skin spot that changed", "see": "Dermatologist", "when": "Within 2-4 weeks; within a week if it bleeds or grows fast"},
    {"concern": "Blood sugar readings or diabetes care", "see": "General physician or endocrinologist", "when": "At your next review; same day if very high with vomiting or drowsiness"},
    {"concern": "Chest discomfort on exertion, palpitations", "see": "Cardiologist", "when": "Within days; call 108 now if pain is severe or at rest"},
    {"concern": "Pregnancy questions", "see": "Obstetrician (your ANC doctor)", "when": "Per your antenatal schedule; same day for bleeding, fluid loss or reduced movement"},
    {"concern": "Low mood, anxiety, sleep trouble lasting weeks", "see": "Psychiatrist or clinical psychologist", "when": "Within 1-2 weeks; call 14416 any time"},
    {"concern": "Joint, back or sports injury", "see": "Orthopaedic surgeon or physiotherapist", "when": "Within a week; same day if you cannot bear weight"},
    {"concern": "Medicines and side effects", "see": "The prescribing doctor or a pharmacist", "when": "Before changing anything"},
    {"concern": "Genetic test results", "see": "Clinical geneticist or genetic counsellor", "when": "Before acting on any result"},
]

EMERGENCY_NOTE = "For an emergency call 108 (ambulance) or 112. Online consultation is not for emergencies."

_REG_NO = re.compile(r"^[A-Za-z0-9/\-. ]{1,30}$")


def _public_fields(row: dict) -> dict:
    """Only what identifies the registration; the register also returns address and birth date."""
    return {
        "name": " ".join((row.get("name") or "").split()),
        "registration_no": row.get("registration_no"),
        "council": row.get("state_medical_council"),
        "registration_date": row.get("registration_date"),
        "qualification": row.get("qualification"),
        "removed": bool(row.get("removed_status")),
    }


def _name_matches(given: str, registered: str) -> bool:
    want = {w for w in given.lower().replace("dr.", " ").replace("dr ", " ").split() if len(w) > 1}
    have = set(registered.lower().split())
    return bool(want) and want <= have


class TelemedicineService:
    """Per-user list of doctors the user has checked; the rest is reference data."""

    def __init__(self):
        self._doctors: list[dict] = []

    def overview(self) -> dict:
        return {
            "services": SERVICES,
            "specialty_guide": SPECIALTY_GUIDE,
            "emergency": EMERGENCY_NOTE,
            "register_url": NMC_REGISTER_PAGE,
            "my_doctors": list(self._doctors),
        }

    async def verify_registration(self, registration_no: str, council_code: str = "",
                                  name: str = "", client: Optional[httpx.AsyncClient] = None) -> dict:
        reg = registration_no.strip()
        if not _REG_NO.match(reg):
            return {"status": "invalid", "message": "Enter the registration number as printed on the prescription."}
        params = {"reg_no": reg, "page": 1, "per_page": 25}
        if council_code:
            params["state"] = council_code.strip().upper()
        try:
            if client is None:
                async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS, headers=HEADERS, follow_redirects=True) as c:
                    resp = await c.get(NMC_SEARCH_URL, params=params)
            else:
                resp = await client.get(NMC_SEARCH_URL, params=params)
            body = resp.json()
        except (httpx.HTTPError, ValueError):
            return {"status": "unavailable", "register_url": NMC_REGISTER_PAGE,
                    "message": "The NMC register could not be reached. Check it directly on the NMC website."}

        rows = [_public_fields(r) for r in (body.get("data") or [])] if body.get("success") else []
        if name:
            rows = [r for r in rows if _name_matches(name, r["name"])]
        if not rows:
            return {"status": "not_found", "register_url": NMC_REGISTER_PAGE,
                    "message": ("No matching entry on the Indian Medical Register. Check the number and council, "
                                "or ask the doctor. Recent registrations may appear only on the state council's list.")}
        return {"status": "found", "matches": rows[:5], "register_url": NMC_REGISTER_PAGE,
                "message": ("Registration found. A listed registration alone does not confirm the person you "
                            "are talking to is this doctor." if not any(r["removed"] for r in rows) else
                            "This registration is marked as removed on the register. Do not consult with it.")}

    def save_doctor(self, name: str, registration_no: str, council: str, specialty: str = "",
                    verified: bool = False, notes: str = "") -> dict:
        entry = {"name": name.strip(), "registration_no": registration_no.strip(), "council": council.strip(),
                 "specialty": specialty.strip(), "verified_on_register": verified, "notes": notes.strip(),
                 "saved_at": time.time()}
        self._doctors = [d for d in self._doctors if d["registration_no"] != entry["registration_no"]] + [entry]
        return entry

    def remove_doctor(self, registration_no: str) -> bool:
        before = len(self._doctors)
        self._doctors = [d for d in self._doctors if d["registration_no"] != registration_no]
        return len(self._doctors) < before


from app.core.per_user import per_user, register  # noqa: E402

telemedicine_service = register("telemedicine.telemedicine_service", per_user(TelemedicineService))

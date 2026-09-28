"""
Check-ups due for an adult in India, by age and sex, and when each was last done.

Built on the Government of India's population-based NCD screening (everyone 30+,
free at Ayushman Arogya Mandirs and government centres) plus widely accepted
adult check-ups. It lists what to ask for; a doctor decides what applies.
"""
import time
from datetime import date
from typing import Optional

# (id, name, who: "all"|"female"|"male", start_age, end_age, every_years, where)
CHECKS = [
    ("blood_pressure", "Blood pressure", "all", 18, 120, 1, "Any clinic, pharmacy or Ayushman Arogya Mandir; free NCD screening from 30"),
    ("blood_sugar", "Blood sugar (fasting or HbA1c)", "all", 30, 120, 1, "Free NCD screening from 30; earlier if your IDRS score is high"),
    ("oral_cancer", "Mouth check for oral cancer", "all", 30, 120, 1, "Free NCD screening; yearly if you use tobacco or areca nut"),
    ("cervical_cancer", "Cervical cancer screening (VIA or HPV test)", "female", 30, 65, 5, "Free NCD screening at government centres"),
    ("breast_exam", "Clinical breast examination", "female", 30, 120, 1, "Free NCD screening; see a doctor any time you notice a change"),
    ("cholesterol", "Cholesterol (lipid profile)", "all", 20, 120, 5, "Any lab; yearly if raised, diabetic or with heart disease in the family"),
    ("eyes", "Eye examination", "all", 40, 120, 2, "Eye clinic or government hospital; yearly with diabetes"),
    ("dental", "Dental check-up", "all", 18, 120, 1, "Any dentist"),
]


class PreventiveScreeningService:
    def __init__(self):
        self.profile: dict = {}
        self.history: list[dict] = []

    def set_profile(self, age: int, sex: str) -> dict:
        self.profile = {"age": age, "sex": sex, "set_at": time.time()}
        return self.profile

    def log(self, check_id: str, done_on: str, note: str = "") -> dict:
        if check_id not in {c[0] for c in CHECKS}:
            raise ValueError("Unknown check")
        date.fromisoformat(done_on)
        entry = {"check_id": check_id, "done_on": done_on, "note": note}
        self.history.append(entry)
        return entry

    def schedule(self) -> dict:
        if not self.profile:
            return {"status": "needs_profile", "message": "Add your age and sex to see which check-ups are due."}
        age, sex = self.profile["age"], self.profile["sex"]
        today = date.today()
        items = []
        for cid, name, who, start, end, every, where in CHECKS:
            if who not in ("all", sex) or not start <= age <= end:
                continue
            done = sorted(h["done_on"] for h in self.history if h["check_id"] == cid)
            last: Optional[date] = date.fromisoformat(done[-1]) if done else None
            due = last is None or (today - last).days >= every * 365
            items.append({"id": cid, "name": name, "every_years": every, "where": where,
                          "last_done": last.isoformat() if last else None, "due": due})
        items.sort(key=lambda i: not i["due"])
        return {"status": "ok", "age": age, "sex": sex, "checks": items,
                "note": "A general guide. Your doctor may advise different timing based on your history."}


from app.core.per_user import per_user, register  # noqa: E402

preventive_screening_service = register("preventive_screening.preventive_screening_service", per_user(PreventiveScreeningService))

"""
Activity pacing for ME/CFS and long-lasting post-viral fatigue.

For people a doctor has already assessed: the app tracks energy, activity and
crashes (post-exertional malaise) and keeps activity under a heart-rate ceiling.
The ceiling is the user's measured resting heart rate plus 15 bpm, the Workwell
Foundation's pacing guidance; without a measured resting rate there is no ceiling.
"""
import time
from typing import Optional

CEILING_ABOVE_RESTING = 15

PACING_RULES = [
    "Stop activities before you feel tired, not after.",
    "Break tasks into short blocks with lying-down rest between them.",
    "Count thinking, screens and social time as exertion too.",
    "After a good day, keep the next day the same; a jump in activity often brings a crash 1-2 days later.",
    "During a crash, rest fully. Pushing through makes crashes longer.",
]
SEE_A_DOCTOR = (
    "See your doctor if fatigue is new, getting steadily worse, or comes with weight loss, fever, "
    "breathlessness, chest pain or low mood; these need checking in their own right."
)


class ChronicFatigueService:
    def __init__(self):
        self.resting_hr: Optional[int] = None
        self.resting_hr_source: Optional[str] = None
        self.days: list[dict] = []
        self.crashes: list[dict] = []

    def set_resting_hr(self, bpm: int, source: str = "entered") -> dict:
        self.resting_hr, self.resting_hr_source = int(bpm), source
        return self.plan()

    @property
    def ceiling(self) -> Optional[int]:
        return None if self.resting_hr is None else self.resting_hr + CEILING_ABOVE_RESTING

    def log_day(self, date: str, energy: int, activity_minutes: int, peak_hr: Optional[int] = None,
                symptoms: Optional[list[str]] = None, notes: str = "") -> dict:
        over = None if peak_hr is None or self.ceiling is None else peak_hr > self.ceiling
        entry = {"date": date, "energy": energy, "activity_minutes": activity_minutes, "peak_hr": peak_hr,
                 "over_ceiling": over, "symptoms": symptoms or [], "notes": notes, "logged_at": time.time()}
        self.days = [d for d in self.days if d["date"] != date] + [entry]
        self.days.sort(key=lambda d: d["date"])
        advice = []
        if over:
            advice.append(f"Your heart rate reached {peak_hr}, above your ceiling of {self.ceiling}. Rest today and tomorrow.")
        if len(self.days) >= 2 and activity_minutes > 1.5 * max(1, self.days[-2]["activity_minutes"]):
            advice.append("Much more activity than yesterday. Watch for a crash over the next two days.")
        return {"entry": entry, "advice": advice}

    def log_crash(self, date: str, severity: str, trigger: str = "", notes: str = "") -> dict:
        crash = {"date": date, "severity": severity, "trigger": trigger, "notes": notes, "logged_at": time.time()}
        self.crashes.append(crash)
        return {"crash": crash, "guidance": [
            "Rest fully: only essential self-care.",
            "Keep water and simple food within reach; dim lights and noise if they bother you.",
            "Return to your usual level slowly over days, not all at once.",
            SEE_A_DOCTOR,
        ]}

    def plan(self) -> dict:
        return {
            "resting_hr": self.resting_hr, "resting_hr_source": self.resting_hr_source,
            "heart_rate_ceiling": self.ceiling,
            "ceiling_note": ("Resting heart rate plus 15 bpm. Measure resting rate on waking, lying down, for a week."
                             if self.ceiling else "Enter your resting heart rate to get a ceiling."),
            "rules": PACING_RULES,
            "see_a_doctor": SEE_A_DOCTOR,
        }

    def summary(self, days: int = 14) -> dict:
        recent = self.days[-days:]
        if not recent:
            return {"status": "no_data", "plan": self.plan(), "crashes": self.crashes[-5:]}
        crash_dates = {c["date"] for c in self.crashes}
        # A crash one or two days after the most active logged day is the boom-bust pattern.
        booms = []
        for i, d in enumerate(recent[:-1]):
            later = [x["date"] for x in recent[i + 1:i + 3]]
            prev = recent[i - 1]["activity_minutes"] if i else None
            if prev is not None and d["activity_minutes"] > 1.5 * max(1, prev) and crash_dates & set(later):
                booms.append(d["date"])
        with_hr = [d for d in recent if d["over_ceiling"] is not None]
        return {
            "status": "ok",
            "days_logged": len(recent),
            "average_energy": round(sum(d["energy"] for d in recent) / len(recent), 1),
            "average_activity_minutes": round(sum(d["activity_minutes"] for d in recent) / len(recent)),
            "days_over_ceiling": sum(1 for d in with_hr if d["over_ceiling"]),
            "days_with_heart_rate": len(with_hr),
            "crashes": [c for c in self.crashes if c["date"] >= recent[0]["date"]],
            "boom_bust_days": booms,
            "days": recent,
            "plan": self.plan(),
        }


from app.core.per_user import per_user, register  # noqa: E402

chronic_fatigue_service = register("chronic_fatigue.chronic_fatigue_service", per_user(ChronicFatigueService))

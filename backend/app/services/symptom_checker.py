"""
Symptom triage: how urgently to get care, never what the cause is.

Red flags are the published warning signs for each symptom; any one of them
means emergency care. Severity is taken as the user reports it; it is never
narrowed to a "typical" range, since a 10/10 headache is itself the warning.
"""
import time

from app.services.safety_policy import CRISIS_LINES

RED_FLAGS = {
    "headache": ["Sudden, severe 'worst ever' headache", "Fever with a stiff neck", "After a blow to the head",
                 "Weakness, numbness, confusion or trouble speaking", "Loss of vision"],
    "fever": ["Stiff neck, or a rash that does not fade when pressed with a glass", "Confusion or very hard to wake",
              "Trouble breathing", "A baby under 3 months old"],
    "cough": ["Coughing up blood", "Trouble breathing or chest pain", "Lips or face turning blue"],
    "fatigue": ["Chest pain or breathlessness with it", "Fainting"],
    "chest_pain": ["Any chest pain, pressure or tightness"],
    "shortness_of_breath": ["Breathless at rest", "Lips or face turning blue", "Chest pain with it"],
    "back_pain": ["Loss of bladder or bowel control, or numbness around the groin", "New weakness in the legs",
                  "After a fall or injury", "Fever with it"],
    "stomach_pain": ["Severe pain with a hard, rigid belly", "Vomiting blood or passing black stools",
                     "Pain and you are pregnant", "Pain low on the right with fever"],
    "dizziness": ["Fainted", "Chest pain or a racing heartbeat", "Face drooping, arm weakness or slurred speech"],
    "joint_pain": ["Hot, swollen joint with fever", "Cannot put weight on it after an injury"],
    "skin_rash": ["Swelling of the lips, tongue or face, or trouble breathing", "Rash that does not fade when pressed, with fever"],
    "anxiety": ["Thoughts of harming yourself", "Chest pain"],
}
# Symptoms that need a doctor if they last this long, whatever the severity.
SEE_DOCTOR_AFTER_DAYS = {"cough": 14, "fever": 3, "fatigue": 14, "headache": 7, "back_pain": 42, "stomach_pain": 3,
                         "dizziness": 7, "joint_pain": 14, "skin_rash": 14, "anxiety": 14, "shortness_of_breath": 1}

LEVELS = {
    "self_care": ("Can usually be looked after at home.", "Rest, drink fluids and watch how it changes. See a doctor if it gets worse or does not improve."),
    "doctor": ("See a doctor in the next few days.", "Book a GP or clinic visit; eSanjeevani offers free video consultations. Note when it started and what makes it better or worse."),
    "urgent": ("Get seen today.", "Go to a clinic or hospital today, or call 104 for advice on where to go."),
    "emergency": ("This needs emergency care now.", "Call 108 for an ambulance or 112, or go to the nearest emergency department. Do not drive yourself."),
}


def _key(symptom: str) -> str:
    return symptom.strip().lower().replace(" ", "_")


class SymptomCheckerService:
    def __init__(self):
        self._history: list[dict] = []

    def get_symptoms(self) -> list[dict]:
        return [{"id": k, "name": k.replace("_", " ").capitalize(), "red_flags": v} for k, v in RED_FLAGS.items()]

    def check_symptom(self, symptom: str, severity: int, days: float = 0, red_flags: list[str] | None = None) -> dict:
        key = _key(symptom)
        if key not in RED_FLAGS:
            return {"error": f"Choose one of: {', '.join(k.replace('_', ' ') for k in RED_FLAGS)}"}
        flagged = [f for f in (red_flags or []) if f in RED_FLAGS[key]]
        if flagged or key == "chest_pain" or severity >= 9:
            level = "emergency"
        elif severity >= 7:
            level = "urgent"
        elif severity >= 4 or days >= SEE_DOCTOR_AFTER_DAYS.get(key, 14):
            level = "doctor"
        else:
            level = "self_care"
        message, action = LEVELS[level]
        result = {
            "symptom": key.replace("_", " ").capitalize(), "severity": severity, "days": days,
            "level": level, "message": message, "action": action, "red_flags_reported": flagged,
            "note": "This tells you how soon to get care. It does not diagnose.",
        }
        if key == "cough" and days >= 14:
            result["action"] += " A cough lasting two weeks or more should be checked for TB; testing is free at government centres."
        if key == "anxiety" and "Thoughts of harming yourself" in flagged:
            result["crisis_lines"] = CRISIS_LINES
        self._history.append({**result, "timestamp": time.time()})
        self._history = self._history[-100:]
        return result

    def get_history(self, limit: int = 10) -> list[dict]:
        return list(reversed(self._history[-limit:]))


from app.core.per_user import per_user, register  # noqa: E402

symptom_checker_service = register("symptom_checker.symptom_checker_service", per_user(SymptomCheckerService))

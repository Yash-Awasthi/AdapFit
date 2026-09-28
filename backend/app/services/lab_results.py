"""
Lab results over time, read against the range printed on the user's own report.

Labs differ, and many ranges depend on sex and age, so the report's range is
the reference. Typical adult ranges fill in only for tests where they do not
depend on sex, and are labelled as such.
"""
import time
import uuid
from datetime import date
from typing import Optional

# name: (label, unit, typical_low, typical_high); None where the range depends on sex or the lab.
CATALOG = {
    "hba1c": ("HbA1c", "%", 4.0, 5.6),
    "fasting_glucose": ("Fasting blood sugar", "mg/dL", 70, 99),
    "total_cholesterol": ("Total cholesterol", "mg/dL", None, 199),
    "ldl": ("LDL cholesterol", "mg/dL", None, 99),
    "hdl": ("HDL cholesterol", "mg/dL", None, None),
    "triglycerides": ("Triglycerides", "mg/dL", None, 149),
    "hemoglobin": ("Haemoglobin", "g/dL", None, None),
    "vitamin_d": ("Vitamin D (25-OH)", "ng/mL", 30, 100),
    "vitamin_b12": ("Vitamin B12", "pg/mL", 200, 900),
    "tsh": ("TSH", "mIU/L", 0.4, 4.0),
    "creatinine": ("Creatinine", "mg/dL", None, None),
    "uric_acid": ("Uric acid", "mg/dL", None, None),
    "alt": ("ALT (SGPT)", "U/L", None, None),
}


class LabResults:
    def __init__(self):
        self.readings: list[dict] = []

    def add(self, test: str, value: float, taken_on: str, ref_low: Optional[float] = None,
            ref_high: Optional[float] = None, lab: str = "", unit: Optional[str] = None) -> dict:
        date.fromisoformat(taken_on)
        label, default_unit, typ_low, typ_high = CATALOG.get(test, (test, unit or "", None, None))
        range_source = "your report" if ref_low is not None or ref_high is not None else "typical adult range"
        if range_source == "typical adult range":
            ref_low, ref_high = typ_low, typ_high
        entry = {"id": uuid.uuid4().hex[:8], "test": test, "label": label, "value": value,
                 "unit": unit or default_unit, "taken_on": taken_on, "ref_low": ref_low, "ref_high": ref_high,
                 "range_source": range_source if (ref_low is not None or ref_high is not None) else None,
                 "lab": lab, "added_at": time.time()}
        entry["status"] = self._status(entry)
        self.readings.append(entry)
        return entry

    @staticmethod
    def _status(r: dict) -> str:
        if r["ref_low"] is not None and r["value"] < r["ref_low"]:
            return "below_range"
        if r["ref_high"] is not None and r["value"] > r["ref_high"]:
            return "above_range"
        if r["ref_low"] is None and r["ref_high"] is None:
            return "no_range"
        return "in_range"

    def delete(self, reading_id: str) -> bool:
        before = len(self.readings)
        self.readings = [r for r in self.readings if r["id"] != reading_id]
        return len(self.readings) < before

    def summary(self) -> list[dict]:
        by_test: dict[str, list[dict]] = {}
        for r in sorted(self.readings, key=lambda r: r["taken_on"]):
            by_test.setdefault(r["test"], []).append(r)
        out = []
        for test, rs in by_test.items():
            latest, prev = rs[-1], rs[-2] if len(rs) > 1 else None
            out.append({
                "test": test, "label": latest["label"], "unit": latest["unit"], "latest": latest,
                "change": round(latest["value"] - prev["value"], 2) if prev else None,
                "history": [{"taken_on": r["taken_on"], "value": r["value"]} for r in rs],
                "next_step": "Show this result to your doctor." if latest["status"] in ("above_range", "below_range") else None,
            })
        out.sort(key=lambda t: t["latest"]["status"] not in ("above_range", "below_range"))
        return out


from app.core.per_user import per_user, register  # noqa: E402

lab_results = register("lab_results.lab_results", per_user(LabResults))

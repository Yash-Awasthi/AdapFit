"""
Blood pressure readings, grouped into the published ranges with a next step.

A single reading is never labelled as a condition; the 7-day home average
(two readings morning and evening, as ISH 2020 advises) is what a doctor uses,
so advice beyond "very high" is given on the average.
"""
from dataclasses import dataclass
from statistics import mean

URGENT_SYMPTOMS = ("chest pain", "shortness of breath", "weakness or numbness", "trouble speaking",
                   "vision changes", "severe headache", "confusion")


@dataclass(frozen=True)
class Range:
    key: str
    label: str
    next_step: str


VERY_HIGH = Range("very_high", "Very high (above 180/120)",
                  "Sit quietly for 5 minutes and measure again. If it stays this high, see a doctor today. "
                  "If you also have chest pain, breathlessness, weakness, trouble speaking or vision changes, call 112 now.")
HIGH_2 = Range("high_140", "High (140/90 or above)",
               "Measure twice a day for 7 days, then show the average to your doctor.")
HIGH_1 = Range("high_130", "Raised (130-139 / 80-89)",
               "Cut down on salt, stay active and check again in a few weeks; mention it at your next check-up.")
ELEVATED = Range("elevated", "Slightly raised (120-129 / under 80)", "Keep active, watch salt, and check every few months.")
NORMAL = Range("normal", "Normal (under 120/80)", "Keep it up; check at least once a year.")
LOW = Range("low", "Low (under 90/60)", "If you feel dizzy or faint, sit or lie down and tell your doctor.")


def classify(systolic: float, diastolic: float) -> Range:
    if systolic > 180 or diastolic > 120:
        return VERY_HIGH
    if systolic >= 140 or diastolic >= 90:
        return HIGH_2
    if systolic >= 130 or diastolic >= 80:
        return HIGH_1
    if systolic < 90 or diastolic < 60:
        return LOW
    if systolic >= 120:
        return ELEVATED
    return NORMAL


def summary(readings: list[dict]) -> dict:
    if not readings:
        return {"count": 0}
    sys_avg = round(mean(r["systolic"] for r in readings))
    dia_avg = round(mean(r["diastolic"] for r in readings))
    band = classify(sys_avg, dia_avg)
    return {"count": len(readings), "average": f"{sys_avg}/{dia_avg}", "range": band.label, "next_step": band.next_step,
            "enough_for_doctor": len(readings) >= 12}

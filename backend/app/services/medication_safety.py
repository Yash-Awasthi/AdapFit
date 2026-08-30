"""
Medication safety for geriatric patients from medication-safety-guideline-for-geriatric.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import math


@dataclass
class Medication:
    name: str
    dose: str
    frequency: str
    route: str = "oral"
    category: str = ""


@dataclass
class PatientProfile:
    age: int = 65
    weight_kg: float = 70.0
    kidney_function: str = "normal"  # normal, mild, moderate, severe
    liver_function: str = "normal"
    conditions: List[str] = field(default_factory=list)
    fall_risk: bool = False
    cognitive_impairment: bool = False


@dataclass
class SafetyAlert:
    severity: str  # critical, high, moderate, low
    medication: str
    message: str
    recommendation: str


BEERS_CRITERIA = {
    "benzodiazepines": {"risk": "high", "reason": "Increased fall risk, cognitive impairment", "alternative": "Melatonin, trazodone"},
    "anticholinergics": {"risk": "high", "reason": "Cognitive decline, urinary retention", "alternative": "Darifenacin (for overactive bladder)"},
    "nsaids": {"risk": "moderate", "reason": "GI bleeding, kidney damage", "alternative": "Acetaminophen, topical analgesics"},
    "antipsychotics": {"risk": "high", "reason": "Increased mortality in dementia", "alternative": "Non-pharmacological approaches"},
    "muscle relaxants": {"risk": "high", "reason": "Sedation, fall risk", "alternative": "Physical therapy"},
    "opioids": {"risk": "high", "reason": "Respiratory depression, falls", "alternative": "Acetaminophen, duloxetine"},
    "sulfonylureas": {"risk": "moderate", "reason": "Hypoglycemia risk", "alternative": "DPP-4 inhibitors"},
    "iron supplements": {"risk": "low", "reason": "Constipation", "alternative": "Take with food, stool softener"},
}

RENAL_ADJUSTMENTS = {
    "metformin": {"severe": "contraindicated", "moderate": "reduce 50%", "mild": "monitor"},
    "gabapentin": {"severe": "300mg/day max", "moderate": "300mg BID", "mild": "normal dose"},
    "dapagliflozin": {"severe": "contraindicated", "moderate": "use with caution", "mild": "normal dose"},
    "enoxaparin": {"severe": "reduce dose", "moderate": "reduce dose", "mild": "normal dose"},
}


def assess_medications(medications: List[Medication], patient: PatientProfile) -> List[SafetyAlert]:
    alerts = []
    for med in medications:
        name_lower = med.name.lower()
        for category, info in BEERS_CRITERIA.items():
            if category in name_lower:
                alerts.append(SafetyAlert(
                    severity=info["risk"],
                    medication=med.name,
                    message=info["reason"],
                    recommendation=info["alternative"],
                ))

        if patient.kidney_function in RENAL_ADJUSTMENTS and name_lower in RENAL_ADJUSTMENTS:
            adjustment = RENAL_ADJUSTMENTS[name_lower][patient.kidney_function]
            if adjustment != "normal dose":
                alerts.append(SafetyAlert(
                    severity="high" if "contraindicated" in adjustment else "moderate",
                    medication=med.name,
                    message=f"Kidney function: {patient.kidney_function} — {adjustment}",
                    recommendation=adjustment,
                ))

    if patient.age >= 80:
        for med in medications:
            alerts.append(SafetyAlert(
                severity="low",
                medication=med.name,
                message="Patient over 80 — consider dose reduction for all medications",
                recommendation="Start low, go slow approach",
            ))

    return alerts


def compute_frailty_risk(patient: PatientProfile, medications: List[Medication]) -> float:
    score = 0.0
    if patient.age >= 80: score += 0.3
    elif patient.age >= 70: score += 0.15
    if patient.cognitive_impairment: score += 0.2
    if patient.fall_risk: score += 0.15
    if len(medications) >= 5: score += 0.15
    if len(medications) >= 10: score += 0.1
    if patient.kidney_function != "normal": score += 0.1
    return min(1.0, score)


def suggest_simplification(medications: List[Medication]) -> List[Dict[str, str]]:
    suggestions = []
    categories = {}
    for med in medications:
        cat = med.category or "other"
        categories.setdefault(cat, []).append(med)

    for cat, meds in categories.items():
        if len(meds) > 1 and cat != "other":
            suggestions.append({
                "category": cat,
                "current": ", ".join(m.name for m in meds),
                "suggestion": f"Review {cat} polypharmacy — consider reducing to single agent",
            })

    return suggestions

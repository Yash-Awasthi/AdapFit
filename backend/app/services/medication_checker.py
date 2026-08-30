"""
Medication risk analysis and drug interaction checking.

Extracted from clinical-decision-support-system — clinical decision support patterns.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict


class RiskLevel(Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class DrugInteraction:
    drugs: List[str]
    severity: str  # MILD, MODERATE, SEVERE
    description: str
    recommendation: str


@dataclass
class Contraindication:
    drug: str
    condition: str
    description: str
    recommendation: str


@dataclass
class DosageWarning:
    drug: str
    concern: str
    recommendation: str


@dataclass
class MedicationReport:
    risk_level: RiskLevel
    summary: str
    interactions: List[DrugInteraction]
    contraindications: List[Contraindication]
    dosage_warnings: List[DosageWarning]
    safer_alternatives: List[Dict[str, str]]
    monitoring_recommendations: List[str]


# Known drug interactions database
INTERACTION_DB = {
    ("warfarin", "aspirin"): {
        "severity": "SEVERE",
        "description": "Increased bleeding risk when combined",
        "recommendation": "Avoid combination or monitor INR closely",
    },
    ("warfarin", "ibuprofen"): {
        "severity": "SEVERE",
        "description": "NSAIDs increase bleeding risk with anticoagulants",
        "recommendation": "Use acetaminophen instead of NSAIDs",
    },
    ("metformin", "alcohol"): {
        "severity": "MODERATE",
        "description": "Alcohol increases risk of lactic acidosis",
        "recommendation": "Limit alcohol intake while on metformin",
    },
    ("lisinopril", "potassium"): {
        "severity": "MODERATE",
        "description": "ACE inhibitors can cause potassium retention",
        "recommendation": "Monitor potassium levels regularly",
    },
    ("sertraline", "tramadol"): {
        "severity": "SEVERE",
        "description": "Serotonin syndrome risk with combined serotonergic agents",
        "recommendation": "Avoid combination, use alternative pain management",
    },
    ("metoprolol", "verapamil"): {
        "severity": "SEVERE",
        "description": "Combined bradycardia and heart block risk",
        "recommendation": "Avoid combination without cardiac monitoring",
    },
    ("lithium", "ibuprofen"): {
        "severity": "SEVERE",
        "description": "NSAIDs increase lithium levels, risk of toxicity",
        "recommendation": "Use acetaminophen, monitor lithium levels if unavoidable",
    },
    ("digoxin", "amiodarone"): {
        "severity": "SEVERE",
        "description": "Amiodarone increases digoxin levels significantly",
        "recommendation": "Reduce digoxin dose by 50% when starting amiodarone",
    },
}

CONTRAINDICATION_DB = {
    "metformin": [
        {"condition": "severe kidney disease", "description": "Risk of lactic acidosis", "recommendation": "Use insulin or alternative"},
        {"condition": "liver failure", "description": "Impaired lactate metabolism", "recommendation": "Avoid metformin"},
    ],
    "warfarin": [
        {"condition": "pregnancy", "description": "Teratogenic, crosses placenta", "recommendation": "Use heparin instead"},
        {"condition": "active bleeding", "description": "Worsens hemorrhage", "recommendation": "Stop warfarin, give vitamin K"},
    ],
    "lisinopril": [
        {"condition": "pregnancy", "description": "Teratogenic in 2nd/3rd trimester", "recommendation": "Switch to methyldopa or labetalol"},
        {"condition": "bilateral renal artery stenosis", "description": "Can cause acute kidney failure", "recommendation": "Contraindicated"},
    ],
    "sertraline": [
        {"condition": "MAO inhibitor use", "description": "Serotonin syndrome risk", "recommendation": "Wait 14 days after MAOI washout"},
    ],
}

DOSAGE_RULES = {
    "metformin": {"max_daily_mg": 2550, "elderly_max_mg": 1000, "kidney_adjustment": True},
    "warfarin": {"typical_range_mg": "2-10", "inr_target": "2.0-3.0", "monitoring": "INR every 1-4 weeks"},
    "lisinopril": {"max_daily_mg": 80, "starting_mg": 10, "kidney_adjustment": True},
    "digoxin": {"max_daily_mg": 0.25, "therapeutic_range": "0.5-2.0 ng/mL", "narrow_index": True},
}

SAFER_ALTERNATIVES = {
    "ibuprofen": {"consider": "acetaminophen", "reason": "Lower GI bleeding risk"},
    "aspirin": {"consider": "acetaminophen", "reason": "Lower bleeding risk"},
    "tramadol": {"consider": "gabapentin", "reason": "Lower serotonin syndrome risk"},
}


def check_interactions(medications: List[str]) -> List[DrugInteraction]:
    """Check for drug-drug interactions among a list of medications."""
    interactions = []
    meds_lower = [m.lower().strip() for m in medications]

    for i, med1 in enumerate(meds_lower):
        for med2 in meds_lower[i + 1:]:
            key = (med1, med2)
            rev_key = (med2, med1)
            interaction = INTERACTION_DB.get(key) or INTERACTION_DB.get(rev_key)
            if interaction:
                interactions.append(DrugInteraction(
                    drugs=[med1, med2],
                    severity=interaction["severity"],
                    description=interaction["description"],
                    recommendation=interaction["recommendation"],
                ))

    return interactions


def check_contraindications(
    medications: List[str], conditions: List[str]
) -> List[Contraindication]:
    """Check for drug-condition contraindications."""
    contraindications = []
    meds_lower = [m.lower().strip() for m in medications]
    conditions_lower = [c.lower().strip() for c in conditions]

    for med in meds_lower:
        rules = CONTRAINDICATION_DB.get(med, [])
        for rule in rules:
            if any(rule["condition"] in cond for cond in conditions_lower):
                contraindications.append(Contraindication(
                    drug=med,
                    condition=rule["condition"],
                    description=rule["description"],
                    recommendation=rule["recommendation"],
                ))

    return contraindications


def check_dosage(medications: List[str]) -> List[DosageWarning]:
    """Check for dosage-related concerns."""
    warnings = []
    meds_lower = [m.lower().strip() for m in medications]

    for med in meds_lower:
        rules = DOSAGE_RULES.get(med)
        if rules:
            if rules.get("narrow_index"):
                warnings.append(DosageWarning(
                    drug=med,
                    concern=f"Narrow therapeutic index. Therapeutic range: {rules.get('therapeutic_range', 'N/A')}",
                    recommendation=f"Regular monitoring required: {rules.get('monitoring', 'Consult physician')}",
                ))
            if rules.get("kidney_adjustment"):
                warnings.append(DosageWarning(
                    drug=med,
                    concern="Dose adjustment may be needed for kidney impairment",
                    recommendation="Check eGFR before prescribing, adjust dose accordingly",
                ))

    return warnings


def suggest_alternatives(medications: List[str]) -> List[Dict[str, str]]:
    """Suggest safer alternatives for known problematic drugs."""
    alternatives = []
    meds_lower = [m.lower().strip() for m in medications]

    for med in meds_lower:
        alt = SAFER_ALTERNATIVES.get(med)
        if alt:
            alternatives.append({
                "instead_of": med,
                **alt,
            })

    return alternatives


def generate_medication_report(
    medications: List[str],
    conditions: Optional[List[str]] = None,
) -> MedicationReport:
    """Generate a comprehensive medication risk report."""
    interactions = check_interactions(medications)
    contraindications = check_contraindications(medications, conditions or [])
    dosage_warnings = check_dosage(medications)
    alternatives = suggest_alternatives(medications)

    severity_map = {"MILD": 1, "MODERATE": 2, "SEVERE": 3}
    max_severity = 0
    for interaction in interactions:
        s = severity_map.get(interaction.severity, 0)
        max_severity = max(max_severity, s)

    if contraindications:
        max_severity = max(max_severity, 3)

    if max_severity >= 3:
        risk_level = RiskLevel.CRITICAL
    elif max_severity >= 2:
        risk_level = RiskLevel.HIGH
    elif max_severity >= 1:
        risk_level = RiskLevel.MODERATE
    else:
        risk_level = RiskLevel.LOW

    summary_parts = []
    if interactions:
        summary_parts.append(f"{len(interactions)} drug interaction(s) detected")
    if contraindications:
        summary_parts.append(f"{len(contraindications)} contraindication(s) found")
    if dosage_warnings:
        summary_parts.append(f"{len(dosage_warnings)} dosage concern(s)")
    if alternatives:
        summary_parts.append(f"{len(alternatives)} alternative(s) suggested")

    summary = "; ".join(summary_parts) if summary_parts else "No significant medication risks detected"

    monitoring = []
    if any(m.lower() in DOSAGE_RULES and DOSAGE_RULES[m.lower()].get("monitoring") for m in medications):
        monitoring.append("Regular lab monitoring recommended")
    if interactions:
        monitoring.append("Close clinical observation advised")
    if not monitoring:
        monitoring.append("Routine follow-up sufficient")

    return MedicationReport(
        risk_level=risk_level,
        summary=summary,
        interactions=interactions,
        contraindications=contraindications,
        dosage_warnings=dosage_warnings,
        safer_alternatives=alternatives,
        monitoring_recommendations=monitoring,
    )

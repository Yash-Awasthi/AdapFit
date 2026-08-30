"""
Drug Interaction Checker for ZFIT
Extracted from: ddinter-main (drug-drug interaction website)
Patterns: Medication interaction database, severity classification,
          multi-drug interaction matrix, safety warnings
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class InteractionSeverity(Enum):
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    MAJOR = "major"
    CONTRAINDICATED = "contraindicated"


@dataclass
class DrugInteraction:
    drug_a: str
    drug_b: str
    severity: InteractionSeverity
    description: str
    recommendation: str
    evidence_level: str = "moderate"  # high, moderate, low


@dataclass
class Medication:
    name: str
    generic_name: str
    category: str
    common_dosages: list[str] = field(default_factory=list)
    side_effects: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ─── Common Drug Interactions Database ─────────────────────────────────

KNOWN_INTERACTIONS = [
    DrugInteraction("warfarin", "aspirin", InteractionSeverity.MAJOR,
        "Increased risk of bleeding when combined",
        "Avoid combination or monitor INR closely", "high"),
    DrugInteraction("metformin", "alcohol", InteractionSeverity.MODERATE,
        "Alcohol increases risk of lactic acidosis",
        "Limit alcohol intake while on metformin", "high"),
    DrugInteraction("lisinopril", "potassium", InteractionSeverity.MODERATE,
        "ACE inhibitors can increase potassium levels",
        "Monitor potassium levels regularly", "moderate"),
    DrugInteraction("ibuprofen", "lisinopril", InteractionSeverity.MODERATE,
        "NSAIDs can reduce effectiveness of ACE inhibitors",
        "Use alternative pain relief if possible", "high"),
    DrugInteraction("sertraline", "tramadol", InteractionSeverity.MAJOR,
        "Increased risk of serotonin syndrome",
        "Avoid combination, use alternative analgesic", "high"),
    DrugInteraction("metoprolol", "verapamil", InteractionSeverity.MAJOR,
        "Combined risk of severe bradycardia and heart block",
        "Avoid combination or use with extreme caution", "high"),
    DrugInteraction("omeprazole", "clopidogrel", InteractionSeverity.MODERATE,
        "PPIs reduce antiplatelet effect of clopidogrel",
        "Use pantoprazole instead if dual therapy needed", "moderate"),
    DrugInteraction("levothyroxine", "calcium", InteractionSeverity.MILD,
        "Calcium supplements can reduce levothyroxine absorption",
        "Take levothyroxine 4 hours apart from calcium", "moderate"),
    DrugInteraction("simvastatin", "amiodarone", InteractionSeverity.MAJOR,
        "Increased risk of rhabdomyolysis",
        "Limit simvastatin dose to 20mg/day", "high"),
    DrugInteraction("metformin", "contrast dye", InteractionSeverity.CONTRAINDICATED,
        "Risk of acute kidney injury and lactic acidosis",
        "Stop metformin 48 hours before and after contrast", "high"),
]


# ─── Interaction Checking ──────────────────────────────────────────────

def check_interactions(medications: list[str]) -> list[DrugInteraction]:
    """Check for interactions between a list of medications."""
    med_names = [m.lower().strip() for m in medications]
    found_interactions = []

    for interaction in KNOWN_INTERACTIONS:
        if interaction.drug_a in med_names and interaction.drug_b in med_names:
            found_interactions.append(interaction)
        elif interaction.drug_b in med_names and interaction.drug_a in med_names:
            found_interactions.append(interaction)

    return found_interactions


def get_severity_summary(interactions: list[DrugInteraction]) -> dict:
    """Get a summary of interaction severities."""
    counts = {s: 0 for s in InteractionSeverity}
    for interaction in interactions:
        counts[interaction.severity] += 1

    max_severity = InteractionSeverity.NONE
    for interaction in interactions:
        if interaction.severity.value > max_severity.value:
            max_severity = interaction.severity

    return {
        "total_interactions": len(interactions),
        "by_severity": {s.value: c for s, c in counts.items() if c > 0},
        "max_severity": max_severity.value,
        "has_contraindication": any(i.severity == InteractionSeverity.CONTRAINDICATED for i in interactions),
        "has_major": any(i.severity == InteractionSeverity.MAJOR for i in interactions),
    }


def get_safety_recommendations(interactions: list[DrugInteraction]) -> list[str]:
    """Generate safety recommendations based on interactions."""
    recommendations = []

    if any(i.severity == InteractionSeverity.CONTRAINDICATED for i in interactions):
        recommendations.append("⚠️ CONTRAINDICATED combination detected — do NOT take these together without physician approval")

    major = [i for i in interactions if i.severity == InteractionSeverity.MAJOR]
    if major:
        recommendations.append(f"🔴 {len(major)} major interaction(s) — consult your pharmacist or doctor")

    moderate = [i for i in interactions if i.severity == InteractionSeverity.MODERATE]
    if moderate:
        recommendations.append(f"🟡 {len(moderate)} moderate interaction(s) — monitor for side effects")

    for interaction in major + moderate:
        recommendations.append(f"• {interaction.drug_a} + {interaction.drug_b}: {interaction.recommendation}")

    if not recommendations:
        recommendations.append("✅ No significant interactions found between these medications")

    return recommendations


def format_interaction_report(medications: list[str]) -> dict:
    """Generate a complete interaction report."""
    interactions = check_interactions(medications)
    severity = get_severity_summary(interactions)
    recommendations = get_safety_recommendations(interactions)

    return {
        "medications": medications,
        "interactions": [
            {
                "drug_a": i.drug_a,
                "drug_b": i.drug_b,
                "severity": i.severity.value,
                "description": i.description,
                "recommendation": i.recommendation,
            }
            for i in interactions
        ],
        "severity_summary": severity,
        "recommendations": recommendations,
    }

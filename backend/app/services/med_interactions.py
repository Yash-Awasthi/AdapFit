"""Medication Interaction Checker — checks new meds against existing ones and exercise.

Cross-references medications for:
- Drug-drug interactions (common pairs)
- Drug-exercise interactions (effects on training)
- Drug-food interactions (timing with meals)
- Side effects that affect workout performance
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class InteractionWarning:
    medication_a: str
    medication_b: str
    severity: str  # mild, moderate, severe, contraindicated
    interaction_type: str  # drug_drug, drug_exercise, drug_food
    description: str
    recommendation: str


# Drug-drug interaction database (common pairs)
DRUG_INTERACTIONS: list[tuple[str, str, str, str, str]] = [
    # (drug_a, drug_b, severity, description, recommendation)
    ("statin", "fibrate", "moderate", "Increased risk of rhabdomyolysis", "Monitor for muscle pain; avoid intense exercise"),
    ("beta_blocker", "calcium_channel_blocker", "moderate", "Additive hypotension and bradycardia", "Monitor heart rate; avoid sudden position changes"),
    ("ace_inhibitor", "potassium_sparing_diuretic", "severe", "Risk of hyperkalemia", "Regular blood tests; avoid potassium supplements"),
    ("ssri", "maoi", "contraindicated", "Serotonin syndrome risk — potentially fatal", "NEVER combine. Seek immediate medical help."),
    ("ssri", "tramadol", "severe", "Increased serotonin syndrome risk", "Avoid combination; use alternative pain relief"),
    ("warfarin", "aspirin", "severe", "Increased bleeding risk", "Only under strict medical supervision"),
    ("metformin", "alcohol", "moderate", "Increased lactic acidosis risk", "Limit alcohol; stay hydrated"),
    ("levothyroxine", "calcium_supplement", "moderate", "Calcium reduces thyroid absorption", "Take levothyroxine 4h apart from calcium"),
    ("levothyroxine", "iron_supplement", "moderate", "Iron reduces thyroid absorption", "Take levothyroxine 4h apart from iron"),
    ("corticosteroid", "nsaid", "moderate", "Increased GI ulcer risk", "Take with food; limit duration"),
    ("lithium", "nsaid", "severe", "NSAIDs increase lithium levels", "Avoid ibuprofen; use acetaminophen instead"),
    ("methotrexate", "nsaid", "severe", "NSAIDs increase methotrexate toxicity", "Avoid NSAIDs; consult rheumatologist"),
    ("diuretic", "lithium", "moderate", "Diuretics increase lithium concentration", "Monitor lithium levels closely"),
    ("anticoagulant", "nsaid", "severe", "Tripled bleeding risk", "Avoid NSAIDs; use acetaminophen for pain"),
    ("ace_inhibitor", "nsaid", "mild", "NSAIDs reduce ACE inhibitor effectiveness", "Use lowest NSAID dose for shortest time"),
]

# Drug-exercise interactions
DRUG_EXERCISE_INTERACTIONS: dict[str, dict] = {
    "beta_blocker": {
        "effect": "Blunts heart rate response — HR-based intensity zones unreliable",
        "adjustment": "Use RPE (Rate of Perceived Exertion) instead of heart rate zones",
        "risk": "May mask overexertion; dizziness on standing",
        "timing": "Take 30min before exercise for consistent effect",
    },
    "statin": {
        "effect": "Can cause muscle pain, weakness, and elevated CK levels",
        "adjustment": "Reduce exercise intensity if muscle pain occurs; avoid eccentric overload",
        "risk": "Rhabdomyolysis in rare cases with extreme exercise",
        "timing": "Evening dosing may reduce daytime muscle symptoms",
    },
    "corticosteroid": {
        "effect": "Weakens tendons and ligaments; increases injury risk",
        "adjustment": "Avoid heavy eccentrics and plyometrics; extended warmup essential",
        "risk": "Tendon rupture, stress fractures with high-dose long-term use",
        "timing": "Morning dosing aligns with natural cortisol rhythm",
    },
    "insulin": {
        "effect": "Risk of exercise-induced hypoglycemia",
        "adjustment": "Check blood sugar before/during/after; carry fast-acting carbs",
        "risk": "Severe hypoglycemia during prolonged exercise",
        "timing": "Exercise 1-3 hours after insulin injection; reduce dose if intense",
    },
    "anticoagulant": {
        "effect": "Increased bleeding risk from trauma or falls",
        "adjustment": "Avoid contact sports, high fall-risk activities, heavy lifting with Valsalva",
        "risk": "Internal bleeding from impact; prolonged bleeding from cuts",
        "timing": "No specific timing needed; consistent effect",
    },
    "antidepressant_ssri": {
        "effect": "May cause fatigue, dizziness, and reduced motivation",
        "adjustment": "Start exercise gradually; lower initial intensity targets",
        "risk": "Hyponatremia in extreme endurance events",
        "timing": "Morning dosing may reduce daytime sedation",
    },
    "diuretic": {
        "effect": "Increased dehydration and electrolyte imbalance risk",
        "adjustment": "Extra hydration; monitor for cramps and dizziness; electrolyte supplementation",
        "risk": "Heat stroke, muscle cramps, cardiac arrhythmia",
        "timing": "Morning dosing avoids nocturia; hydrate extra before exercise",
    },
    "muscle_relaxant": {
        "effect": "Impaired coordination, drowsiness, reduced reaction time",
        "adjustment": "NO heavy lifting, no barbell overhead, no complex movements",
        "risk": "Falls, dropped weights, impaired proprioception",
        "timing": "Avoid exercise until effects wear off (4-8 hours)",
    },
    "opioid_painkiller": {
        "effect": "Masks pain signals — risk of training through injury",
        "adjustment": "Use significantly reduced loads; monitor for unusual fatigue",
        "risk": "Injury from masked pain; respiratory depression with intense exercise",
        "timing": "Do not exercise while opioid effects are active",
    },
    "thyroid_medication": {
        "effect": "Can alter heart rate and metabolic rate",
        "adjustment": "Monitor resting HR; titrate exercise intensity gradually",
        "risk": "Cardiac arrhythmia if overmedicated; fatigue if undermedicated",
        "timing": "Take on empty stomach 30-60min before breakfast",
    },
    "asthma_inhaler": {
        "effect": "Short-acting inhaler can cause tachycardia; long-acting improves exercise tolerance",
        "adjustment": "Always carry rescue inhaler; extended warmup; avoid cold dry air",
        "risk": "Exercise-induced bronchospasm",
        "timing": "Use rescue inhaler 15min before exercise if needed",
    },
}


def check_drug_interactions(new_med: str, existing_meds: list[str]) -> list[InteractionWarning]:
    """Check a new medication against existing ones."""
    warnings = []
    new_lower = new_med.lower()

    for med_b in existing_meds:
        med_b_lower = med_b.lower()

        for drug_a, drug_b, severity, desc, rec in DRUG_INTERACTIONS:
            if (drug_a in new_lower and drug_b in med_b_lower) or \
               (drug_b in new_lower and drug_a in med_b_lower):
                warnings.append(InteractionWarning(
                    medication_a=new_med, medication_b=med_b,
                    severity=severity, interaction_type="drug_drug",
                    description=desc, recommendation=rec,
                ))

    return warnings


def check_exercise_interactions(medication_name: str) -> list[dict]:
    """Check a medication against exercise rules."""
    med_lower = medication_name.lower()
    warnings = []

    for drug_key, info in DRUG_EXERCISE_INTERACTIONS.items():
        if drug_key.replace("_", " ") in med_lower or drug_key in med_lower:
            warnings.append({
                "medication": medication_name,
                "drug_class": drug_key,
                "effect": info["effect"],
                "adjustment": info["adjustment"],
                "risk": info["risk"],
                "timing": info["timing"],
            })

    return warnings


def check_all_interactions(
    new_med: str,
    existing_meds: list[str],
    user_conditions: list[str] = None,
) -> dict:
    """Comprehensive interaction check for a new medication."""
    drug_warnings = check_drug_interactions(new_med, existing_meds)
    exercise_warnings = check_exercise_interactions(new_med)

    # Condition-specific considerations
    condition_notes = []
    conditions = user_conditions or []
    med_lower = new_med.lower()

    if "diabetes" in " ".join(conditions) and "beta" in med_lower:
        condition_notes.append("Beta blockers may mask hypoglycemia symptoms in diabetics")
    if "heart" in " ".join(conditions) and "nsaid" in med_lower:
        condition_notes.append("NSAIDs can worsen heart failure — use with caution")
    if "kidney" in " ".join(conditions) and "metformin" in med_lower:
        condition_notes.append("Metformin contraindicated in severe kidney disease")

    has_severe = any(w.severity in ("severe", "contraindicated") for w in drug_warnings)

    return {
        "medication": new_med,
        "drug_interactions": [
            {"with": w.medication_b, "severity": w.severity, "description": w.description, "recommendation": w.recommendation}
            for w in drug_warnings
        ],
        "exercise_interactions": exercise_warnings,
        "condition_notes": condition_notes,
        "overall_risk": "high" if has_severe else ("moderate" if drug_warnings else "low"),
        "requires_doctor_review": has_severe or len(exercise_warnings) > 0,
    }

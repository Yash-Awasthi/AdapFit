"""
Drug interaction engine from pharmexpert-drug-interactions.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import math


@dataclass
class DrugInfo:
    name: str
    generic_name: str = ""
    category: str = ""
    half_life_hours: float = 0.0
    protein_binding: float = 0.0
    metabolism: str = ""  # CYP3A4, CYP2D6, etc.
    contraindications: List[str] = field(default_factory=list)
    side_effects: List[str] = field(default_factory=list)


@dataclass
class InteractionResult:
    drug1: str
    drug2: str
    severity: str  # minor, moderate, major, contraindicated
    mechanism: str
    effect: str
    management: str
    evidence_level: str  # established, probable, suspected


INTERACTION_DATABASE = {
    ("warfarin", "aspirin"): InteractionResult("warfarin", "aspirin", "major", "Additive anticoagulant effect", "Increased bleeding risk", "Avoid combination or monitor INR closely", "established"),
    ("warfarin", "amiodarone"): InteractionResult("warfarin", "amiodarone", "major", "CYP2C9 inhibition", "Increased warfarin levels", "Reduce warfarin dose by 30-50%", "established"),
    ("metformin", "alcohol"): InteractionResult("metformin", "alcohol", "major", "Lactic acidosis risk", "Impaired lactate metabolism", "Limit alcohol intake", "established"),
    ("lisinopril", "potassium"): InteractionResult("lisinopril", "potassium", "moderate", "Potassium retention", "Hyperkalemia risk", "Monitor potassium levels", "established"),
    ("sertraline", "tramadol"): InteractionResult("sertraline", "tramadol", "major", "Serotonin syndrome risk", "Combined serotonergic effect", "Avoid combination", "established"),
    ("metoprolol", "verapamil"): InteractionResult("metoprolol", "verapamil", "major", "Additive cardiac depression", "Bradycardia and heart block", "Avoid combination without monitoring", "established"),
    ("lithium", "ibuprofen"): InteractionResult("lithium", "ibuprofen", "major", "Reduced renal clearance", "Increased lithium levels", "Monitor lithium levels closely", "established"),
    ("digoxin", "amiodarone"): InteractionResult("digoxin", "amiodarone", "major", "P-glycoprotein inhibition", "Increased digoxin levels", "Reduce digoxin dose by 50%", "established"),
    ("clopidogrel", "omeprazole"): InteractionResult("clopidogrel", "omeprazole", "moderate", "CYP2C19 inhibition", "Reduced antiplatelet effect", "Use pantoprazole instead", "established"),
    ("simvastatin", "amiodarone"): InteractionResult("simvastatin", "amiodarone", "major", "CYP3A4 inhibition", "Increased statin levels", "Limit simvastatin to 20mg", "established"),
}


def check_interaction(drug1: str, drug2: str) -> Optional[InteractionResult]:
    key = (drug1.lower(), drug2.lower())
    rev_key = (drug2.lower(), drug1.lower())
    return INTERACTION_DATABASE.get(key) or INTERACTION_DATABASE.get(rev_key)


def check_all_interactions(medications: List[str]) -> List[InteractionResult]:
    results = []
    meds = [m.lower() for m in medications]
    for i in range(len(meds)):
        for j in range(i + 1, len(meds)):
            interaction = check_interaction(meds[i], meds[j])
            if interaction:
                results.append(interaction)
    return sorted(results, key=lambda r: {"contraindicated": 0, "major": 1, "moderate": 2, "minor": 3}.get(r.severity, 4))


def compute_polypharmacy_risk(medications: List[str]) -> Dict:
    interactions = check_all_interactions(medications)
    count = len(medications)
    risk_score = 0.0
    if count >= 5: risk_score += 0.2
    if count >= 10: risk_score += 0.3
    if count >= 15: risk_score += 0.2
    major_interactions = sum(1 for i in interactions if i.severity in ("major", "contraindicated"))
    risk_score += major_interactions * 0.15
    return {"medication_count": count, "interaction_count": len(interactions), "major_interactions": major_interactions, "risk_score": min(1.0, risk_score), "recommendations": ["Review medications with pharmacist"] if count >= 5 else []}

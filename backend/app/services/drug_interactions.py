"""
Drug-drug and food-drug interaction lookup over a small reviewed table.

Names may be generics or Indian brands; brands resolve to their ingredients
through `indian_medicines`. The "action" text is written for prescribers and
the API replaces it with a next step for the user.
"""

from typing import Dict, List, Any


class DrugInteractionService:
    """Interaction lookup; never suggests a dose."""

    def __init__(self):
        self._init_interaction_database()

    def _init_interaction_database(self):
        self.interactions = {
            ("warfarin", "aspirin"): {"severity": "major", "effect": "Increased bleeding risk", "action": "Avoid combination or monitor INR closely"},
            ("warfarin", "ibuprofen"): {"severity": "major", "effect": "Increased bleeding risk", "action": "Use acetaminophen instead of ibuprofen"},
            ("metformin", "alcohol"): {"severity": "major", "effect": "Risk of lactic acidosis", "action": "Limit alcohol intake"},
            ("lisinopril", "potassium"): {"severity": "moderate", "effect": "Hyperkalemia risk", "action": "Monitor potassium levels"},
            ("metoprolol", "verapamil"): {"severity": "major", "effect": "Severe bradycardia, heart block", "action": "Avoid combination"},
            ("sertraline", "tramadol"): {"severity": "major", "effect": "Serotonin syndrome risk", "action": "Use alternative pain medication"},
            ("simvastatin", "amiodarone"): {"severity": "major", "effect": "Increased risk of rhabdomyolysis", "action": "Limit simvastatin to 20mg/day"},
            ("omeprazole", "clopidogrel"): {"severity": "major", "effect": "Reduced clopidogrel efficacy", "action": "Use pantoprazole instead"},
            ("metformin", "contrast_dye"): {"severity": "major", "effect": "Acute kidney injury risk", "action": "Hold metformin 48h before/after contrast"},
            ("digoxin", "amiodarone"): {"severity": "major", "effect": "Digoxin toxicity", "action": "Reduce digoxin dose by 50%"},
            ("lithium", "ibuprofen"): {"severity": "major", "effect": "Lithium toxicity", "action": "Use acetaminophen instead"},
            ("methotrexate", "nsaids"): {"severity": "major", "effect": "Methotrexate toxicity", "action": "Avoid NSAIDs during methotrexate therapy"},
            ("fluoxetine", "maoi"): {"severity": "contraindicated", "effect": "Fatal serotonin syndrome", "action": "NEVER combine — 14-day washout required"},
            ("ciprofloxacin", "antacids"): {"severity": "moderate", "effect": "Reduced antibiotic absorption", "action": "Separate by 2 hours"},
            ("levothyroxine", "calcium"): {"severity": "moderate", "effect": "Reduced thyroid hormone absorption", "action": "Separate by 4 hours"},
        }

    # Indian and international spellings, and classes the table is keyed by.
    ALIASES = {
        "thyroxine": {"levothyroxine"}, "paracetamol": {"acetaminophen"}, "salbutamol": {"albuterol"},
        "acetylsalicylic acid": {"aspirin"}, "aspirin": {"nsaids"},
        "ibuprofen": {"nsaids"}, "diclofenac": {"nsaids"}, "naproxen": {"nsaids"}, "aceclofenac": {"nsaids"},
        "nimesulide": {"nsaids"}, "etoricoxib": {"nsaids"}, "ketorolac": {"nsaids"}, "mefenamic acid": {"nsaids"},
        "calcium carbonate": {"calcium", "antacids"}, "aluminium hydroxide": {"antacids"},
        "magnesium hydroxide": {"antacids"}, "potassium chloride": {"potassium"},
        "selegiline": {"maoi"}, "rasagiline": {"maoi"}, "linezolid": {"maoi"},
        "metoprolol succinate": {"metoprolol"}, "metoprolol tartrate": {"metoprolol"},
    }

    def _terms(self, generic: str) -> set:
        return {generic} | self.ALIASES.get(generic, set())

    def check_interactions(self, medications: List[str]) -> Dict[str, Any]:
        """Check a list of names; each may be a generic or an Indian brand, resolved to its ingredients."""
        from app.services import indian_medicines

        resolved = [indian_medicines.resolve(m) for m in medications]
        items = [(r["name"], set().union(*(self._terms(g) for g in r["generics"]))) for r in resolved]
        found_interactions = []
        seen = set()
        for i, (name1, terms1) in enumerate(items):
            for name2, terms2 in items[i + 1:]:
                for t1 in terms1:
                    for t2 in terms2:
                        interaction = self.interactions.get((t1, t2)) or self.interactions.get((t2, t1))
                        key = (name1, name2, interaction and interaction["effect"])
                        if interaction and key not in seen:
                            seen.add(key)
                            found_interactions.append({
                                "drug_1": name1, "drug_2": name2, "severity": interaction["severity"],
                                "effect": interaction["effect"], "action": interaction["action"],
                            })

        major = sum(1 for i in found_interactions if i["severity"] == "major")
        moderate = sum(1 for i in found_interactions if i["severity"] == "moderate")
        contraindicated = sum(1 for i in found_interactions if i["severity"] == "contraindicated")

        return {
            "medications_checked": len(medications),
            "resolved": [{k: r[k] for k in ("name", "kind", "generics", "message") if k in r} for r in resolved],
            "interactions_found": len(found_interactions),
            "interactions": found_interactions,
            "risk_summary": {"major": major, "moderate": moderate, "contraindicated": contraindicated},
            "overall_risk": "critical" if contraindicated > 0 else "high" if major > 0 else "moderate" if moderate > 0 else "low",
            "source": indian_medicines.SOURCE,
        }

    # === Food-Drug Interactions ===

    FOOD_DRUG_INTERACTIONS = {
        "warfarin": {"food": "Vitamin K-rich foods (leafy greens, broccoli)", "effect": "Reduced anticoagulant effect", "advice": "Maintain consistent vitamin K intake daily"},
        "maoi": {"food": "Tyramine-rich foods (aged cheese, cured meats, fermented foods)", "effect": "Hypertensive crisis risk", "advice": "Avoid tyramine-rich foods completely"},
        "metformin": {"food": "Alcohol", "effect": "Increased lactic acidosis risk", "advice": "Limit or avoid alcohol"},
        "tetracycline": {"food": "Dairy products, calcium-rich foods", "effect": "Reduced antibiotic absorption", "advice": "Take 2 hours before or after dairy"},
        "levothyroxine": {"food": "Soy products, high-fiber foods", "effect": "Reduced thyroid hormone absorption", "advice": "Take on empty stomach, wait 4 hours"},
        "statin": {"food": "Grapefruit juice", "effect": "Increased statin levels, muscle damage risk", "advice": "Avoid grapefruit juice"},
        "lisinopril": {"food": "High-potassium foods (bananas, oranges, potatoes)", "effect": "Hyperkalemia risk", "advice": "Monitor potassium intake"},
        "nsaids": {"food": "Alcohol", "effect": "Increased GI bleeding risk", "advice": "Avoid alcohol with NSAIDs"},
        "aspirin": {"food": "Alcohol", "effect": "Increased bleeding risk", "advice": "Limit alcohol intake"},
        "lithium": {"food": "Sodium-rich foods, caffeine", "effect": "Altered lithium levels", "advice": "Maintain consistent sodium and caffeine intake"},
        "iron": {"food": "Tea, coffee, dairy", "effect": "Reduced iron absorption by up to 60%", "advice": "Take iron 1-2 hours before meals, with vitamin C"},
        "calcium": {"food": "High-oxalate foods (spinach, rhubarb)", "effect": "Reduced calcium absorption", "advice": "Separate calcium from high-oxalate foods"},
    }

    def check_food_interactions(self, medications: List[str]) -> Dict[str, Any]:
        """Check for food-drug interactions."""
        found = []
        for med in medications:
            med_lower = med.lower()
            for drug_key, info in self.FOOD_DRUG_INTERACTIONS.items():
                if drug_key in med_lower:
                    found.append({
                        "medication": med,
                        "food": info["food"],
                        "effect": info["effect"],
                        "advice": info["advice"],
                    })
        return {
            "medications_checked": len(medications),
            "food_interactions_found": len(found),
            "interactions": found,
        }


drug_interaction_service = DrugInteractionService()

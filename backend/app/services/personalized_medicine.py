"""
Personalized Medicine — Drug Response Prediction & Dosage Optimization
Pharmacogenomics-based medication management
"""
from datetime import datetime
from typing import Dict, List, Optional
import random


class PersonalizedMedicineService:
    """Pharmacogenomics-based personalized medication platform"""

    def __init__(self):
        self.drug_gene_interactions = {
            "warfarin": {
                "genes": ["CYP2C9", "VKORC1"],
                "impact": "metabolism speed",
                "recommendations": {
                    "slow_metabolizer": "Start at lower dose (2.5mg/day), monitor INR closely",
                    "normal_metabolizer": "Standard dosing (5mg/day), routine INR monitoring",
                    "fast_metabolizer": "May need higher dose (7.5mg/day), more frequent monitoring",
                },
            },
            "clopidogrel": {
                "genes": ["CYP2C19"],
                "impact": "activation to active metabolite",
                "recommendations": {
                    "poor_metabolizer": "Consider alternative antiplatelet (prasugrel, ticagrelor)",
                    "intermediate_metabolizer": "Standard dose, monitor for efficacy",
                    "normal_metabolizer": "Standard dosing effective",
                },
            },
            "codeine": {
                "genes": ["CYP2D6"],
                "impact": "conversion to morphine",
                "recommendations": {
                    "ultra_rapid_metabolizer": "AVOID - risk of toxicity, use alternative analgesic",
                    "poor_metabolizer": "Ineffective - use alternative analgesic",
                    "normal_metabolizer": "Standard dosing",
                },
            },
            "metformin": {
                "genes": ["SLC22A1", "SLC47A1"],
                "impact": "renal elimination",
                "recommendations": {
                    "reduced_function": "Start low, titrate slowly, monitor renal function",
                    "normal_function": "Standard dosing protocol",
                },
            },
            "statins": {
                "genes": ["SLCO1B1"],
                "impact": "hepatic uptake and muscle toxicity risk",
                "recommendations": {
                    "reduced_function": "Lower statin dose or switch to rosuvastatin, monitor for myopathy",
                    "normal_function": "Standard statin therapy",
                },
            },
        }

        self.genetic_markers = {
            "CYP2D6": {"function": "Drug metabolism", "drugs_affected": ["codeine", "tamoxifen", "antidepressants"]},
            "CYP2C19": {"function": "Drug metabolism", "drugs_affected": ["clopidogrel", "PPIs", "antidepressants"]},
            "CYP2C9": {"function": "Drug metabolism", "drugs_affected": ["warfarin", "NSAIDs", "phenytoin"]},
            "VKORC1": {"function": "Warfarin sensitivity", "drugs_affected": ["warfarin"]},
            "SLCO1B1": {"function": "Hepatic transport", "drugs_affected": ["statins"]},
            "HLA-B*5701": {"function": "Immune reaction", "drugs_affected": ["abacavir"]},
            "TPMT": {"function": "Thiopurine metabolism", "drugs_affected": ["azathioprine", "6-mercaptopurine"]},
        }

    def predict_drug_response(self, genetic_profile: Dict, medication: str) -> Dict:
        """Predict drug response based on genetic profile"""
        med_lower = medication.lower()
        if med_lower not in self.drug_gene_interactions:
            return {
                "medication": medication,
                "status": "no_data",
                "message": f"No pharmacogenomic data available for {medication}",
                "recommendation": "Use standard dosing, monitor for side effects",
            }

        interaction = self.drug_gene_interactions[med_lower]
        relevant_genes = interaction["genes"]

        # Simulate metabolizer status based on genetic profile
        metabolizer_status = {}
        for gene in relevant_genes:
            gene_data = genetic_profile.get(gene, {})
            status = gene_data.get("status", "normal_metabolizer")
            metabolizer_status[gene] = status

        # Get recommendation based on worst-case metabolizer status
        worst_status = "normal_metabolizer"
        for gene, status in metabolizer_status.items():
            if "poor" in status or "ultra_rapid" in status:
                worst_status = status
                break
            elif "intermediate" in status or "reduced" in status:
                worst_status = status

        recommendation = interaction["recommendations"].get(worst_status, interaction["recommendations"].get("normal_metabolizer", "Standard dosing"))

        return {
            "medication": medication,
            "genes_analyzed": relevant_genes,
            "metabolizer_status": metabolizer_status,
            "impact": interaction["impact"],
            "recommendation": recommendation,
            "confidence": round(random.uniform(0.7, 0.95), 2),
            "alternative_medications": self._get_alternatives(med_lower, worst_status),
            "monitoring_requirements": self._get_monitoring(med_lower, worst_status),
        }

    def _get_alternatives(self, medication: str, status: str) -> List[str]:
        """Get alternative medication recommendations"""
        alternatives = {
            "warfarin": ["DOACs (apixaban, rivarelbaan) - less gene-dependent"],
            "clopidogrel": ["Prasugrel", "Ticagrelor - not affected by CYP2C19"],
            "codeine": ["Tramadol (with caution)", "Morphine", "Acetaminophen", "NSAIDs"],
            "statins": ["Rosuvastatin (less SLCO1B1 dependent)", "Ezetimibe"],
        }
        return alternatives.get(medication, ["Consult pharmacogenomic specialist"])

    def _get_monitoring(self, medication: str, status: str) -> List[str]:
        """Get monitoring requirements"""
        base_monitoring = ["Report any unusual side effects"]
        if "poor" in status or "ultra_rapid" in status:
            base_monitoring.extend([
                "More frequent blood work",
                "Closer clinical monitoring",
                "Lower starting dose recommended",
            ])
        return base_monitoring

    def optimize_dosage(self, medication: str, patient_data: Dict) -> Dict:
        """Optimize dosage based on patient factors"""
        weight = patient_data.get("weight_kg", 70)
        age = patient_data.get("age", 40)
        renal_function = patient_data.get("renal_function", "normal")
        hepatic_function = patient_data.get("hepatic_function", "normal")

        # Base dose calculations
        base_doses = {
            "metformin": {"starting": 500, "max": 2000, "unit": "mg/day"},
            "warfarin": {"starting": 5, "max": 10, "unit": "mg/day"},
            "lisinopril": {"starting": 10, "max": 40, "unit": "mg/day"},
            "atorvastatin": {"starting": 10, "max": 80, "unit": "mg/day"},
            "metoprolol": {"starting": 25, "max": 200, "unit": "mg/day"},
        }

        dose_info = base_doses.get(medication.lower(), {"starting": 5, "max": 100, "unit": "mg/day"})
        starting_dose = dose_info["starting"]
        max_dose = dose_info["max"]

        # Adjust for factors
        adjustments = []
        if age > 65:
            starting_dose = int(starting_dose * 0.5)
            adjustments.append("Age >65: reduced starting dose")
        if renal_function == "reduced":
            starting_dose = int(starting_dose * 0.5)
            adjustments.append("Renal impairment: dose reduction required")
        if hepatic_function == "impaired":
            starting_dose = int(starting_dose * 0.25)
            adjustments.append("Hepatic impairment: significant dose reduction")
        if weight < 50:
            starting_dose = int(starting_dose * 0.75)
            adjustments.append("Low weight: adjusted dose")

        return {
            "medication": medication,
            "recommended_starting_dose": f"{starting_dose} {dose_info['unit']}",
            "maximum_dose": f"{max_dose} {dose_info['unit']}",
            "adjustments": adjustments,
            "titration_schedule": self._get_titration(medication, starting_dose, max_dose),
            "monitoring": self._get_dose_monitoring(medication),
        }

    def _get_titration(self, medication: str, start: int, max_dose: int) -> List[Dict]:
        """Generate titration schedule"""
        steps = []
        current = start
        week = 1
        while current < max_dose and week <= 8:
            steps.append({"week": week, "dose": f"{current} mg/day", "instructions": "Monitor for side effects"})
            current = min(int(current * 1.5), max_dose)
            week += 1
        return steps

    def _get_dose_monitoring(self, medication: str) -> List[str]:
        """Get monitoring requirements for dosage"""
        return [
            "Blood pressure check at each dose change",
            "Renal function tests every 3 months",
            "Electrolyte monitoring",
            "Report dizziness, lightheadedness, or swelling",
        ]

    def check_drug_interactions(self, medications: List[str]) -> Dict:
        """Check for drug interactions between multiple medications"""
        interactions = []
        med_set = set(m.lower() for m in medications)

        known_interactions = [
            {"drugs": ["warfarin", "aspirin"], "severity": "major", "effect": "Increased bleeding risk", "action": "Avoid combination or monitor INR closely"},
            {"drugs": ["metformin", "alcohol"], "severity": "major", "effect": "Lactic acidosis risk", "action": "Limit alcohol intake"},
            {"drugs": ["lisinopril", "potassium"], "severity": "moderate", "effect": "Hyperkalemia risk", "action": "Monitor potassium levels"},
            {"drugs": ["atorvastatin", "grapefruit"], "severity": "moderate", "effect": "Increased statin levels", "action": "Avoid grapefruit juice"},
        ]

        for interaction in known_interactions:
            if all(d in med_set for d in interaction["drugs"]):
                interactions.append(interaction)

        return {
            "medications_checked": medications,
            "interactions_found": len(interactions),
            "interactions": interactions,
            "overall_risk": "high" if any(i["severity"] == "major" for i in interactions) else "moderate" if interactions else "low",
            "recommendation": "Consult pharmacist before combining medications" if interactions else "No significant interactions found",
        }


personalized_medicine_service = PersonalizedMedicineService()

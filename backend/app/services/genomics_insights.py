"""Genomics & Pharmacogenomics Insights Service.

Based on 2025-2026 precision medicine research:
- Genetic disease risk scoring from uploaded data
- Pharmacogenomic drug interaction analysis
- Nutrigenomics dietary recommendations
- Genetic trait reporting
- Personalized medicine insights
"""

import time
import random
from typing import Dict, List, Optional, Any


class GenomicsInsightsService:
    """Genetic health insights and pharmacogenomics."""

    def __init__(self):
        self.profiles: Dict[str, Dict] = {}
        self._init_disease_risks()

    def _init_disease_risks(self):
        self.genetic_risks = {
            "cardiovascular": {
                "genes": ["APOE", "LPA", "PCSK9", "LDLR"],
                "risk_variants": {"APOE_e4": 0.3, "LPA_risk": 0.25, "PCSK9_gain": 0.2},
                "modifiers": {"exercise": -0.15, "diet": -0.1, "smoking": 0.2},
            },
            "type2_diabetes": {
                "genes": ["TCF7L2", "PPARG", "KCNJ11", "FTO"],
                "risk_variants": {"TCF7L2_risk": 0.25, "FTO_risk": 0.15},
                "modifiers": {"exercise": -0.2, "diet": -0.15, "obesity": 0.3},
            },
            "alzheimers": {
                "genes": ["APOE", "BIN1", "CLU", "PICALM"],
                "risk_variants": {"APOE_e4_homo": 0.5, "APOE_e4_hetero": 0.25},
                "modifiers": {"exercise": -0.1, "cognitive_activity": -0.1, "social_engagement": -0.05},
            },
            "breast_cancer": {
                "genes": ["BRCA1", "BRCA2", "PALB2", "CHEK2"],
                "risk_variants": {"BRCA1": 0.4, "BRCA2": 0.3, "PALB2": 0.15},
                "modifiers": {"regular_screening": -0.1},
            },
            "depression": {
                "genes": ["5-HTTLPR", "BDNF", "FKBP5", "COMT"],
                "risk_variants": {"5HTTLPR_ss": 0.15, "BDNF_val66met": 0.1},
                "modifiers": {"exercise": -0.15, "therapy": -0.2, "social_support": -0.1},
            },
        }

        self.drug_metabolism = {
            "CYP2D6": {
                "drugs": ["codeine", "tramadol", "tamoxifen", "metoprolol", "dextromethorphan"],
                "metabolizer_types": {
                    "poor": {"action": "Reduce dose or avoid", "risk": "Toxicity"},
                    "intermediate": {"action": "Standard dose with monitoring", "risk": "Mild effects"},
                    "normal": {"action": "Standard dosing", "risk": "Normal"},
                    "ultra_rapid": {"action": "May need higher dose", "risk": "Inefficacy"},
                },
            },
            "CYP2C19": {
                "drugs": ["clopidogrel", "omeprazole", "escitalopram", "diazepam"],
                "metabolizer_types": {
                    "poor": {"action": "Avoid clopidogrel, use alternatives", "risk": "Treatment failure"},
                    "intermediate": {"action": "Consider dose adjustment", "risk": "Reduced efficacy"},
                    "normal": {"action": "Standard dosing", "risk": "Normal"},
                    "ultra_rapid": {"action": "May need higher dose of prodrugs", "risk": "Increased activation"},
                },
            },
            "CYP3A4": {
                "drugs": ["atorvastatin", "simvastatin", "amlodipine", "midazolam"],
                "metabolizer_types": {
                    "poor": {"action": "Reduce dose 50%", "risk": "Drug accumulation"},
                    "normal": {"action": "Standard dosing", "risk": "Normal"},
                },
            },
        }

        self.nutrigenomics = {
            "MTHFR": {
                "variant": "C677T",
                "impact": "Reduced folate metabolism",
                "recommendation": "Take methylfolate (L-MTHF) instead of folic acid",
                "foods": ["leafy greens", "liver", "legumes"],
            },
            "FTO": {
                "variant": "rs9939609",
                "impact": "Increased appetite, obesity risk",
                "recommendation": "Higher protein diet, mindful eating",
                "foods": ["lean proteins", "fiber-rich foods"],
            },
            "APOA5": {
                "variant": "rs662799",
                "impact": "Higher triglyceride response to fat",
                "recommendation": "Limit saturated fat, increase omega-3",
                "foods": ["fatty fish", "walnuts", "flaxseed"],
            },
            "LCT": {
                "variant": "MCM6",
                "impact": "Lactose tolerance/intolerance",
                "recommendation": "If intolerant, avoid or use lactase",
                "foods": ["lactose-free dairy", "calcium-fortified alternatives"],
            },
        }

    def analyze_genetic_data(self, user_id: str, genetic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze uploaded genetic data for health insights."""
        profile_id = f"gen_{user_id}_{int(time.time())}"

        # Extract variants from data
        variants = genetic_data.get("variants", {})
        ancestry = genetic_data.get("ancestry", "unknown")

        # Calculate disease risks
        disease_risks = {}
        for disease, info in self.genetic_risks.items():
            risk_score = 0.1  # baseline
            detected_variants = []

            for gene in info["genes"]:
                if gene in variants:
                    variant_val = variants[gene]
                    if variant_val in info.get("risk_variants", {}):
                        risk_score += info["risk_variants"][variant_val]
                        detected_variants.append(f"{gene}:{variant_val}")

            risk_score = min(1.0, risk_score)
            disease_risks[disease] = {
                "risk_score": round(risk_score, 3),
                "risk_level": "high" if risk_score > 0.5 else "moderate" if risk_score > 0.25 else "low",
                "genes_analyzed": info["genes"],
                "risk_variants_found": detected_variants,
                "modifiable_factors": list(info.get("modifiers", {}).keys()),
                "recommendations": self._get_disease_recommendations(disease, risk_score),
            }

        # Pharmacogenomics
        pgx_results = self._analyze_pharmacogenomics(variants)

        # Nutrigenomics
        nutrition_results = self._analyze_nutrigenomics(variants)

        # Genetic traits
        traits = self._analyze_traits(variants)

        profile = {
            "profile_id": profile_id,
            "user_id": user_id,
            "timestamp": time.time(),
            "ancestry": ancestry,
            "total_variants_analyzed": len(variants),
            "disease_risks": disease_risks,
            "pharmacogenomics": pgx_results,
            "nutrigenomics": nutrition_results,
            "genetic_traits": traits,
            "actionable_insights": self._generate_actionable_insights(disease_risks, pgx_results, nutrition_results),
            "genetic_health_score": self._calculate_genetic_health_score(disease_risks),
        }

        self.profiles[profile_id] = profile
        return profile

    def check_drug_safety(self, user_id: str, medications: List[str]) -> Dict[str, Any]:
        """Check genetic compatibility with medications."""
        user_profiles = [p for p in self.profiles.values() if p["user_id"] == user_id]
        if not user_profiles:
            return {"error": "No genetic profile found. Upload genetic data first."}

        variants = {}
        for p in user_profiles:
            for k, v in p.get("pharmacogenomics", {}).items():
                variants[k] = v

        results = []
        for drug in medications:
            drug_info = None
            gene = None
            for g, info in self.drug_metabolism.items():
                if drug.lower() in [d.lower() for d in info["drugs"]]:
                    drug_info = info
                    gene = g
                    break

            if drug_info:
                metabolizer = variants.get(gene, {}).get("type", "normal")
                metabolism_info = drug_info["metabolizer_types"].get(metabolizer, {"action": "Consult pharmacist", "risk": "Unknown"})
                results.append({
                    "drug": drug,
                    "gene": gene,
                    "metabolizer_status": metabolizer,
                    "recommended_action": metabolism_info["action"],
                    "risk_level": metabolism_info["risk"],
                })
            else:
                results.append({
                    "drug": drug,
                    "gene": "Not pharmacogenomically tested",
                    "metabolizer_status": "N/A",
                    "recommended_action": "No genetic interaction known",
                    "risk_level": "Unknown",
                })

        return {
            "user_id": user_id,
            "medications_checked": len(results),
            "results": results,
            "warnings": [r for r in results if r["risk_level"] not in ("Normal", "Unknown")],
        }

    def _analyze_pharmacogenomics(self, variants: Dict) -> Dict[str, Any]:
        results = {}
        for gene, info in self.drug_metabolism.items():
            gene_variant = variants.get(gene, "normal")
            results[gene] = {
                "type": gene_variant,
                "affected_drugs": info["drugs"],
                "action": info["metabolizer_types"].get(gene_variant, {}).get("action", "Consult specialist"),
            }
        return results

    def _analyze_nutrigenomics(self, variants: Dict) -> Dict[str, Any]:
        results = {}
        for gene, info in self.nutrigenomics.items():
            has_variant = gene in variants
            results[gene] = {
                "variant_present": has_variant,
                "impact": info["impact"] if has_variant else "Normal",
                "recommendation": info["recommendation"] if has_variant else "No dietary modification needed",
                "recommended_foods": info["foods"] if has_variant else [],
            }
        return results

    def _analyze_traits(self, variants: Dict) -> List[Dict]:
        return [
            {"trait": "Lactose Tolerance", "status": variants.get("LCT", "tolerant"), "confidence": 0.95},
            {"trait": "Caffeine Metabolism", "status": variants.get("CYP1A2", "normal"), "confidence": 0.9},
            {"trait": "Alcohol Flush", "status": variants.get("ALDH2", "normal"), "confidence": 0.92},
            {"trait": "Vitamin D Synthesis", "status": variants.get("VDR", "normal"), "confidence": 0.85},
        ]

    def _get_disease_recommendations(self, disease: str, risk: float) -> List[str]:
        if risk < 0.2:
            return ["Continue healthy lifestyle", "Routine screening per age guidelines"]
        elif risk < 0.5:
            return ["Consider genetic counseling", "Increase preventive screenings", "Lifestyle optimization recommended"]
        else:
            return ["Genetic counseling strongly recommended", "Enhanced screening protocol", "Discuss preventive options with physician", "Consider genetic testing for family members"]

    def _generate_actionable_insights(self, risks: Dict, pgx: Dict, nutrition: Dict) -> List[Dict]:
        insights = []
        for disease, data in risks.items():
            if data["risk_level"] in ("moderate", "high"):
                insights.append({
                    "type": "disease_risk",
                    "priority": "high" if data["risk_level"] == "high" else "medium",
                    "message": f"Elevated {disease.replace('_', ' ')} risk - consider preventive measures",
                })
        for gene, data in pgx.items():
            if data["type"] != "normal":
                insights.append({
                    "type": "pharmacogenomics",
                    "priority": "high",
                    "message": f"{gene}: {data['type']} metabolizer - affects {len(data['affected_drugs'])} medications",
                })
        for gene, data in nutrition.items():
            if data["variant_present"]:
                insights.append({
                    "type": "nutrition",
                    "priority": "medium",
                    "message": f"{gene} variant: {data['recommendation']}",
                })
        return sorted(insights, key=lambda x: 0 if x["priority"] == "high" else 1)

    def _calculate_genetic_health_score(self, risks: Dict) -> int:
        avg_risk = sum(d["risk_score"] for d in risks.values()) / max(1, len(risks))
        return max(20, min(100, int(100 - avg_risk * 100)))


genomics_insights_service = GenomicsInsightsService()

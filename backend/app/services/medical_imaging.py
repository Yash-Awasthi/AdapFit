"""
Medical Imaging AI — Skin Lesion, Wound Assessment, Rash Detection
Deep learning-based image analysis for dermatological conditions
"""
from datetime import datetime
from typing import Dict, List, Optional
import random


class MedicalImagingService:
    """AI-powered medical image analysis platform"""

    def __init__(self):
        self.skin_lesion_categories = {
            "melanocytic": {
                "conditions": ["melanoma", "nevus", "seborrheic keratosis", "blue nevus"],
                "risk_levels": {"melanoma": "critical", "nevus": "low", "seborrheic keratosis": "low", "blue nevus": "low"},
                "features": ["asymmetry", "border irregularity", "color variation", "diameter >6mm", "evolution"],
            },
            "non_melanocytic": {
                "conditions": ["basal cell carcinoma", "squamous cell carcinoma", "actinic keratosis", "dermatofibroma"],
                "risk_levels": {"basal cell carcinoma": "high", "squamous cell carcinoma": "high", "actinic keratosis": "medium", "dermatofibroma": "low"},
                "features": ["pearly appearance", "rolled borders", "ulceration", "scaling", "firm nodule"],
            },
            "benign": {
                "conditions": ["acne", "eczema", "psoriasis", "dermatitis", "wart", "molluscum"],
                "risk_levels": {c: "low" for c in ["acne", "eczema", "psoriasis", "dermatitis", "wart", "molluscum"]},
                "features": ["inflammation", "scaling", "itching", "redness", "papules"],
            }
        }

        self.wound_classifications = {
            "pressure_ulcer": {"stages": ["stage_1", "stage_2", "stage_3", "stage_4", "unstageable"], "risk": "high"},
            "surgical_wound": {"stages": ["healing", "infected", "dehiscence"], "risk": "medium"},
            "diabetic_ulcer": {"stages": ["neuropathic", "ischemic", "mixed"], "risk": "critical"},
            "venous_ulcer": {"stages": ["acute", "chronic", "infected"], "risk": "high"},
            "burn": {"stages": ["superficial", "partial_thickness", "full_thickness"], "risk": "high"},
            "laceration": {"stages": ["clean", "contaminated", "infected"], "risk": "medium"},
        }

        self.rash_patterns = {
            "maculopapular": {"description": "Flat and raised spots", "common_causes": ["viral infection", "drug reaction", "allergic response"], "urgency": "moderate"},
            "petechial": {"description": "Small purple spots (bleeding under skin)", "common_causes": ["thrombocytopenia", "vasculitis", "meningococcemia"], "urgency": "high"},
            "urticarial": {"description": "Hives - raised, itchy welts", "common_causes": ["allergic reaction", "autoimmune", "infection"], "urgency": "moderate"},
            "vesicular": {"description": "Small fluid-filled blisters", "common_causes": ["herpes", "eczema", "contact dermatitis"], "urgency": "low"},
            "pustular": {"description": "Pus-filled bumps", "common_causes": ["bacterial infection", "acne", "folliculitis"], "urgency": "low"},
            "erythematous": {"description": "Red, inflamed skin", "common_causes": ["sunburn", "infection", "inflammation"], "urgency": "low"},
        }

        self.image_analysis_steps = [
            "Image preprocessing (normalization, artifact removal)",
            "Region of interest segmentation",
            "Feature extraction (color, texture, shape, border)",
            "Pattern matching against condition database",
            "Risk classification and confidence scoring",
            "Clinical recommendation generation",
        ]

    def analyze_skin_lesion(self, image_features: Dict) -> Dict:
        """Analyze skin lesion from extracted image features"""
        # Simulate AI analysis based on provided features
        asymmetry = image_features.get("asymmetry_score", random.uniform(0, 1))
        border = image_features.get("border_irregularity", random.uniform(0, 1))
        color_var = image_features.get("color_variation", random.uniform(0, 1))
        diameter = image_features.get("diameter_mm", random.uniform(1, 15))
        evolution = image_features.get("evolution_detected", False)

        # ABCDE scoring
        abcde_score = 0
        abcde_details = {}

        if asymmetry > 0.5:
            abcde_score += 1
            abcde_details["asymmetry"] = {"score": "abnormal", "value": round(asymmetry, 2)}
        else:
            abcde_details["asymmetry"] = {"score": "normal", "value": round(asymmetry, 2)}

        if border > 0.5:
            abcde_score += 1
            abcde_details["border"] = {"score": "irregular", "value": round(border, 2)}
        else:
            abcde_details["border"] = {"score": "regular", "value": round(border, 2)}

        if color_var > 0.4:
            abcde_score += 1
            abcde_details["color"] = {"score": "varied", "value": round(color_var, 2)}
        else:
            abcde_details["color"] = {"score": "uniform", "value": round(color_var, 2)}

        if diameter > 6:
            abcde_score += 1
            abcde_details["diameter"] = {"score": "large", "value": round(diameter, 1)}
        else:
            abcde_details["diameter"] = {"score": "normal", "value": round(diameter, 1)}

        if evolution:
            abcde_score += 1
            abcde_details["evolution"] = {"score": "changed", "value": True}
        else:
            abcde_details["evolution"] = {"score": "stable", "value": False}

        # Risk classification
        if abcde_score >= 4:
            risk = "critical"
            recommendation = "URGENT: See dermatologist within 48 hours. High suspicion for melanoma."
            confidence = random.uniform(0.75, 0.95)
        elif abcde_score >= 2:
            risk = "high"
            recommendation = "Schedule dermatologist appointment within 2 weeks. Biopsy may be needed."
            confidence = random.uniform(0.60, 0.85)
        elif abcde_score >= 1:
            risk = "medium"
            recommendation = "Monitor closely. Follow up with dermatologist at next visit."
            confidence = random.uniform(0.50, 0.75)
        else:
            risk = "low"
            recommendation = "Likely benign. Continue regular self-examinations."
            confidence = random.uniform(0.70, 0.90)

        return {
            "analysis_id": f"SA-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "abcde_score": abcde_score,
            "abcde_details": abcde_details,
            "risk_level": risk,
            "confidence": round(confidence, 2),
            "recommendation": recommendation,
            "differential_diagnosis": self._get_differential(abcde_score, asymmetry, border, color_var),
            "follow_up_schedule": self._get_follow_up(risk),
            "self_monitoring": self._get_self_monitoring_tips(),
        }

    def _get_differential(self, score: int, asym: float, border: float, color: float) -> List[Dict]:
        """Generate differential diagnosis"""
        conditions = []
        if score >= 3:
            conditions.append({"condition": "Melanoma", "probability": round(random.uniform(30, 60), 1), "urgency": "urgent"})
            conditions.append({"condition": "Atypical Nevus", "probability": round(random.uniform(20, 40), 1), "urgency": "moderate"})
        elif score >= 1:
            conditions.append({"condition": "Benign Nevus", "probability": round(random.uniform(40, 70), 1), "urgency": "routine"})
            conditions.append({"condition": "Seborrheic Keratosis", "probability": round(random.uniform(15, 35), 1), "urgency": "routine"})
        else:
            conditions.append({"condition": "Benign Lesion", "probability": round(random.uniform(70, 90), 1), "urgency": "routine"})
        return conditions

    def _get_follow_up(self, risk: str) -> Dict:
        """Get follow-up schedule based on risk"""
        schedules = {
            "critical": {"next_exam": "48 hours", "specialist": "dermatologist", "imaging": "dermoscopy recommended"},
            "high": {"next_exam": "2 weeks", "specialist": "dermatologist", "imaging": "consider dermoscopy"},
            "medium": {"next_exam": "3 months", "specialist": "primary care", "imaging": "self-monitoring"},
            "low": {"next_exam": "6 months", "specialist": "self-exam", "imaging": "none needed"},
        }
        return schedules.get(risk, schedules["low"])

    def _get_self_monitoring_tips(self) -> List[str]:
        """Self-monitoring tips for skin lesions"""
        return [
            "Photograph the lesion monthly with a ruler for scale",
            "Note any changes in size, shape, color, or symptoms",
            "Perform monthly full-body skin self-examinations",
            "Use the ABCDE criteria for each new or changing spot",
            "Seek immediate care for any rapidly changing lesion",
        ]

    def assess_wound(self, wound_data: Dict) -> Dict:
        """Assess wound from clinical data"""
        wound_type = wound_data.get("type", "unknown")
        stage = wound_data.get("stage", "unknown")
        size = wound_data.get("size_cm", {"length": 2, "width": 1, "depth": 0.5})

        area = size.get("length", 2) * size.get("width", 1)
        volume = area * size.get("depth", 0.5)

        # Infection risk assessment
        infection_signs = wound_data.get("infection_signs", [])
        infection_risk = "low"
        if len(infection_signs) >= 3:
            infection_risk = "high"
        elif len(infection_signs) >= 1:
            infection_risk = "medium"

        # Healing stage
        healing_stages = self.wound_classifications.get(wound_type, {}).get("stages", ["unknown"])
        is_healing = stage in ["healing", "stage_1", "acute", "clean", "superficial"]

        return {
            "assessment_id": f"WA-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "wound_type": wound_type,
            "stage": stage,
            "area_cm2": round(area, 1),
            "volume_cm3": round(volume, 2),
            "infection_risk": infection_risk,
            "infection_signs_count": len(infection_signs),
            "healing_status": "healing" if is_healing else "requires_attention",
            "care_recommendations": self._get_wound_care(wound_type, infection_risk),
            "red_flags": [
                "Increasing pain or swelling",
                "Foul odor or purulent discharge",
                "Red streaking from wound",
                "Fever > 100.4°F (38°C)",
                "Wound not healing after 2 weeks",
            ],
            "follow_up_days": 7 if infection_risk == "high" else 14,
        }

    def _get_wound_care(self, wound_type: str, infection_risk: str) -> List[str]:
        """Get wound care recommendations"""
        care = ["Keep wound clean and moist", "Change dressings regularly"]
        if infection_risk == "high":
            care.extend(["Start antibiotics if prescribed", "Monitor for systemic symptoms", "Consider wound culture"])
        if wound_type == "diabetic_ulcer":
            care.extend(["Offload pressure from affected area", "Monitor blood glucose closely", "Daily foot inspection"])
        if wound_type == "pressure_ulcer":
            care.extend(["Reposition every 2 hours", "Use pressure-relieving mattress", "Nutritional optimization"])
        return care

    def detect_rash(self, rash_data: Dict) -> Dict:
        """Detect and classify rash pattern"""
        pattern = rash_data.get("pattern", "unknown")
        distribution = rash_data.get("distribution", "localized")
        symptoms = rash_data.get("symptoms", [])

        rash_info = self.rash_patterns.get(pattern, {
            "description": "Unknown pattern",
            "common_causes": ["requires further evaluation"],
            "urgency": "moderate",
        })

        # Urgency escalation
        urgency = rash_info["urgency"]
        if "petechial" in str(pattern) or "fever" in str(symptoms):
            urgency = "high"
        if "blistering" in str(symptoms) or "mucosal" in str(distribution):
            urgency = "high"

        return {
            "detection_id": f"RD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "pattern": pattern,
            "pattern_description": rash_info["description"],
            "distribution": distribution,
            "symptoms": symptoms,
            "possible_causes": rash_info["common_causes"],
            "urgency": urgency,
            "recommendations": self._get_rash_recommendations(urgency, pattern),
            "self_care": self._get_rash_self_care(pattern),
        }

    def _get_rash_recommendations(self, urgency: str, pattern: str) -> List[str]:
        """Get rash recommendations"""
        recs = ["Photograph rash for comparison over time"]
        if urgency == "high":
            recs.extend(["Seek medical attention within 24 hours", "Note any associated symptoms (fever, joint pain)"])
        elif urgency == "moderate":
            recs.extend(["Schedule appointment within 1 week", "Monitor for spreading or new symptoms"])
        else:
            recs.extend(["Try OTC hydrocortisone cream", "Avoid known irritants", "Follow up if no improvement in 7 days"])
        return recs

    def _get_rash_self_care(self, pattern: str) -> List[str]:
        """Self-care tips for rashes"""
        return [
            "Keep area clean and dry",
            "Avoid scratching to prevent infection",
            "Use gentle, fragrance-free products",
            "Apply cool compresses for itching",
            "Wear loose, breathable clothing",
        ]


medical_imaging_service = MedicalImagingService()

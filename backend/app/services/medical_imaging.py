"""
Medical Imaging AI — Skin Lesion, Wound Assessment, Rash Detection
Deep learning-based image analysis for dermatological conditions
"""
from datetime import datetime
from typing import Dict, List, Optional


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


class MedicalImagingService:
    """ABCDE screening and rash triage."""

    def __init__(self):
        self.rash_patterns = {
            "maculopapular": {"description": "Flat and raised spots", "urgency": "moderate"},
            "petechial": {"description": "Small purple spots (bleeding under skin)", "urgency": "high"},
            "urticarial": {"description": "Hives - raised, itchy welts", "urgency": "moderate"},
            "vesicular": {"description": "Small fluid-filled blisters", "urgency": "low"},
            "pustular": {"description": "Pus-filled bumps", "urgency": "low"},
            "erythematous": {"description": "Red, inflamed skin", "urgency": "low"},
        }

    # Diameter needs a scale in the photo and evolution a previous photo, so
    # both may be absent; absent means not assessed, never defaulted.
    REQUIRED_FEATURES = ("asymmetry_score", "border_irregularity", "color_variation")

    def analyze_skin_lesion(self, image_features: Dict) -> Dict:
        """
        Score a lesion against the ABCDE criteria from measured image features.

        Every feature must be supplied. These defaulted to random values, so a
        request carrying no measurements at all could return "High suspicion
        for melanoma" — or miss one — purely by chance.
        """
        missing = [f for f in self.REQUIRED_FEATURES if not _is_number(image_features.get(f))]
        if image_features.get("diameter_mm") is not None and not _is_number(image_features["diameter_mm"]):
            missing.append("diameter_mm")
        if missing:
            return {
                "status": "insufficient_data",
                "missing_features": missing,
                "message": (
                    "Cannot score this lesion: " + ", ".join(missing) + " were not measured. "
                    "A lesion that cannot be measured needs a clinician to look at it, not a score."
                ),
                "self_monitoring": self._get_self_monitoring_tips(),
            }

        asymmetry = float(image_features["asymmetry_score"])
        border = float(image_features["border_irregularity"])
        color_var = float(image_features["color_variation"])
        diameter = image_features.get("diameter_mm")
        evolution = bool(image_features.get("evolution_detected"))

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

        if diameter is None:
            abcde_details["diameter"] = {"score": "not_measured", "value": None}
        elif diameter > 6:
            abcde_score += 1
            abcde_details["diameter"] = {"score": "large", "value": round(float(diameter), 1)}
        else:
            abcde_details["diameter"] = {"score": "normal", "value": round(float(diameter), 1)}

        if image_features.get("evolution_detected") is None:
            abcde_details["evolution"] = {"score": "not_assessed", "value": None}
        elif evolution:
            abcde_score += 1
            abcde_details["evolution"] = {"score": "changed", "value": True}
        else:
            abcde_details["evolution"] = {"score": "stable", "value": False}

        # Risk classification
        if abcde_score >= 4:
            risk = "critical"
            recommendation = "See a dermatologist within 48 hours. Four or more ABCDE criteria are met."
        elif abcde_score >= 2:
            risk = "high"
            recommendation = "Book a dermatologist appointment within two weeks. Several ABCDE criteria are met."
        elif abcde_score >= 1:
            risk = "medium"
            recommendation = "Monitor and mention it at your next appointment. One ABCDE criterion is met."
        else:
            risk = "low"
            recommendation = "No ABCDE criterion is met. Keep up regular self-examination."

        return {
            "analysis_id": f"SA-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "status": "scored",
            "abcde_score": abcde_score,
            "abcde_details": abcde_details,
            "risk_level": risk,
            "criteria_met": abcde_score,
            "criteria_assessed": 3 + (diameter is not None) + (image_features.get("evolution_detected") is not None),
            "recommendation": recommendation,
            # ABCDE is a screening prompt to get a lesion looked at, not a
            # classifier, so no probability is offered for it.
            "disclaimer": (
                "An ABCDE screening score from the supplied measurements. It does not "
                "diagnose or rule out skin cancer; only a clinician can."
            ),
            "follow_up_schedule": self._get_follow_up(risk),
            "self_monitoring": self._get_self_monitoring_tips(),
        }

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

    # Signs that need emergency care now, whatever the rash looks like:
    # non-blanching spots with fever (meningococcal sepsis), swelling of lips
    # or tongue or breathing trouble (anaphylaxis), skin peeling with mouth sores.
    EMERGENCY_SYMPTOMS = {"fever", "breathing_difficulty", "lip_or_tongue_swelling", "skin_peeling", "mouth_sores", "drowsy_or_confused"}

    def detect_rash(self, rash_data: Dict) -> Dict:
        """Urgency and next step for a described rash; names no condition."""
        pattern = rash_data.get("pattern", "unknown")
        distribution = rash_data.get("distribution", "localized")
        symptoms = {str(x).lower() for x in rash_data.get("symptoms", [])}
        info = self.rash_patterns.get(pattern, {"description": "Not one of the listed patterns", "urgency": "moderate"})

        urgency = info["urgency"]
        if pattern == "petechial" or "blistering" in symptoms or distribution == "mucosal":
            urgency = "high"
        red = sorted(symptoms & self.EMERGENCY_SYMPTOMS)
        if red == ["fever"] and urgency != "high":
            urgency = "high"
        elif red:
            urgency = "emergency"

        return {
            "pattern": pattern,
            "pattern_description": info["description"],
            "distribution": distribution,
            "urgency": urgency,
            "emergency_signs_reported": red,
            "recommendations": self._get_rash_recommendations(urgency),
            "self_care": self._get_rash_self_care(pattern) if urgency in ("low", "moderate") else [],
            "glass_test": "Press a clear glass on the spots. If they do not fade, call 108 now, especially with fever.",
        }

    def _get_rash_recommendations(self, urgency: str) -> List[str]:
        if urgency == "emergency":
            return ["Call 108 or go to the nearest emergency department now"]
        recs = ["Photograph the rash to compare over time"]
        if urgency == "high":
            recs.append("See a doctor today")
        elif urgency == "moderate":
            recs.extend(["See a doctor within a week", "Sooner if it spreads or you develop fever"])
        else:
            recs.extend(["Avoid anything that seems to trigger it", "A pharmacist can suggest a soothing cream",
                         "See a doctor if it is not better in 7 days"])
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


from app.core.per_user import per_user, register

medical_imaging_service = register("medical_imaging.medical_imaging_service", per_user(MedicalImagingService))
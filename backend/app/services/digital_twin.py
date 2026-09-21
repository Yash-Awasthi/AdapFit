"""AI Digital Twin / Health Avatar Service.

Based on 2025-2026 digital twin healthcare research:
- Virtual body model simulation
- What-if health scenario modeling
- Personalized health predictions
- Body system visualization
- Treatment outcome simulation
- Risk factor impact analysis
"""

import time
from typing import Dict, List, Any, Optional


class DigitalTwinService:
    """AI-powered digital health twin for personalized simulation."""

    def __init__(self):
        self.twins: Dict[str, Dict] = {}

    def create_twin(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a digital health twin from user data."""
        twin = {
            "user_id": user_id,
            "age": data.get("age", 35),
            "gender": data.get("gender", "unknown"),
            "height_cm": data.get("height", 170),
            "weight_kg": data.get("weight", 70),
            "bmi": round(data.get("weight", 70) / (data.get("height", 170) / 100) ** 2, 1),
            "body_systems": self._init_body_systems(data),
            "health_score": self._calculate_health_score(data),
            "risk_factors": self._assess_risk_factors(data),
            "vital_baselines": {
                "resting_hr": data.get("resting_hr", 72),
                "blood_pressure": data.get("bp", "120/80"),
                "spo2": data.get("spo2", 98),
                "blood_glucose": data.get("glucose", 95),
                "bmr": self._calculate_bmr(data),
            },
            "created_at": time.time(),
        }
        self.twins[user_id] = twin
        return twin

    def simulate_scenario(self, user_id: str, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate a health scenario on the digital twin."""
        twin = self.twins.get(user_id)
        if not twin:
            return {"error": "Create a digital twin first"}

        scenario_type = scenario.get("type", "lifestyle_change")
        duration_weeks = scenario.get("duration_weeks", 12)

        if scenario_type == "weight_loss":
            target_loss_kg = scenario.get("target_loss_kg", 5)
            weekly_loss = target_loss_kg / duration_weeks
            new_weight = twin["weight_kg"] - target_loss_kg
            new_bmi = round(new_weight / (twin["height_cm"] / 100) ** 2, 1)

            return {
                "scenario": "Weight Loss",
                "duration_weeks": duration_weeks,
                "changes": {
                    "weight": f"{twin['weight_kg']}kg → {round(new_weight, 1)}kg",
                    "bmi": f"{twin['bmi']} → {new_bmi}",
                    "health_score_improvement": round(target_loss_kg * 2, 1),
                    "risk_reduction": {
                        "cardiovascular": f"-{round(target_loss_kg * 1.5, 1)}%",
                        "diabetes": f"-{round(target_loss_kg * 2, 1)}%",
                        "joint_pressure": f"-{round(target_loss_kg * 3, 1)}%",
                    },
                },
                "expected_outcomes": [
                    f"Reduced cardiovascular risk by {round(target_loss_kg * 1.5, 1)}%",
                    "Improved energy levels",
                    "Better sleep quality",
                    "Reduced joint pain",
                ],
            }

        elif scenario_type == "exercise_program":
            intensity = scenario.get("intensity", "moderate")
            multiplier = {"low": 0.5, "moderate": 1.0, "high": 1.5}[intensity]
            return {
                "scenario": f"Exercise Program ({intensity})",
                "duration_weeks": duration_weeks,
                "changes": {
                    "cardio_fitness": f"+{round(15 * multiplier, 0)}%",
                    "muscle_mass": f"+{round(3 * multiplier, 1)}%",
                    "resting_hr": f"-{round(5 * multiplier, 0)} bpm",
                    "stress_level": f"-{round(20 * multiplier, 0)}%",
                    "sleep_quality": f"+{round(15 * multiplier, 0)}%",
                },
                "expected_outcomes": [
                    "Improved cardiovascular health",
                    "Increased muscle strength",
                    "Better stress management",
                    "Enhanced sleep quality",
                ],
            }

        elif scenario_type == "stress_reduction":
            return {
                "scenario": "Stress Reduction Program",
                "duration_weeks": duration_weeks,
                "changes": {
                    "cortisol": f"-{round(25, 0)}%",
                    "blood_pressure": "-5/3 mmHg",
                    "sleep_quality": "+20%",
                    "immune_function": "+15%",
                    "mental_health_score": "+18 points",
                },
                "expected_outcomes": [
                    "Reduced chronic inflammation",
                    "Improved immune response",
                    "Better emotional regulation",
                    "Lower cardiovascular risk",
                ],
            }

        return {"error": "Unknown scenario type"}

    def get_body_overview(self, user_id: str) -> Dict[str, Any]:
        """Get body system overview from the digital twin."""
        twin = self.twins.get(user_id, {})
        systems = twin.get("body_systems", {})

        return {
            "user_id": user_id,
            "overall_health": twin.get("health_score", 75),
            "body_systems": systems,
            "vitals": twin.get("vital_baselines", {}),
            "age": twin.get("age"),
            # Biological age needs a validated model over real biomarkers.
            # It was chronological age minus a random 0-5 years.
            "biological_age_estimate": None,
            "biological_age_note": "Not estimated: this needs biomarker data the app does not hold.",
        }

    def get_prediction(self, user_id: str, metric: str, months: int = 12) -> Dict[str, Any]:
        """
        Where a metric is heading.

        This returned a twelve-month forecast built by adding a random offset
        to the current value, each point carrying a confidence that fell with
        distance as though a model were behind it. Forecasting a metric needs
        a history to fit against, so this reports what is on record instead.
        """
        twin = self.twins.get(user_id, {})
        current = twin.get("vital_baselines", {}).get(metric)
        if current is None:
            return {
                "status": "unavailable",
                "metric": metric,
                "message": f"No recorded baseline for {metric}, so there is nothing to project from.",
            }
        return {
            "status": "current_only",
            "metric": metric,
            "current_value": current,
            "months_requested": months,
            "message": (
                "Projection is not available: it needs a fitted model over your own "
                "history, which this does not have."
            ),
        }

    BODY_SYSTEMS = (
        "cardiovascular", "respiratory", "musculoskeletal",
        "nervous", "digestive", "endocrine", "immune",
    )

    def _init_body_systems(self, data: Dict) -> Dict[str, Any]:
        """
        Per-system scores, only where the profile carries something to score.

        Every system used to open at roughly 80 with a random spread and the
        status "good" — an organ-by-organ clean bill of health for a profile
        that had just been created.
        """
        supplied = data.get("body_systems") or {}
        return {
            system: (
                {"score": supplied[system], "status": "reported"}
                if isinstance(supplied.get(system), (int, float))
                else {"score": None, "status": "not_assessed"}
            )
            for system in self.BODY_SYSTEMS
        }

    def _calculate_health_score(self, data: Dict) -> Optional[int]:
        """Average of the system scores actually reported, or None."""
        scores = [
            value for value in (data.get("body_systems") or {}).values()
            if isinstance(value, (int, float))
        ]
        if not scores:
            return None
        return int(round(sum(scores) / len(scores)))

    def _assess_risk_factors(self, data: Dict) -> List[str]:
        risks = []
        if data.get("smoking"): risks.append("Smoking")
        if data.get("bmi", 25) > 30: risks.append("Obesity")
        if data.get("age", 40) > 55: risks.append("Age")
        return risks

    def _calculate_bmr(self, data: Dict) -> int:
        weight = data.get("weight", 70)
        height = data.get("height", 170)
        age = data.get("age", 35)
        return int(10 * weight + 6.25 * height - 5 * age + 5)


digital_twin_service = DigitalTwinService()

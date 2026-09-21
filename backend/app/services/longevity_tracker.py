"""Longevity Tracker Service - Biological age estimation, health span optimization.

Based on 2025-2026 research on epigenetic clocks and wearable-based aging:
- Biological age estimation from lifestyle/wearable data
- Health span vs lifespan optimization
- Longevity intervention tracking
- Anti-aging recommendations
- Longevity score and ranking
"""

import time
import math
import random
from typing import Dict, List, Optional, Any


class LongevityTrackerService:
    """Track and optimize biological age and health span."""

    def __init__(self):
        self.profiles: Dict[str, Dict] = {}
        self.interventions: Dict[str, List] = {}
        self._init_longevity_factors()

    def _init_longevity_factors(self):
        """Initialize longevity factor weights and scoring."""
        self.factors = {
            "exercise": {
                "weight": 0.20,
                "optimal_range": {"min": 150, "max": 300},  # min/week
                "unit": "minutes/week",
                "impact": {
                    "below_min": 0.3,
                    "optimal": 1.0,
                    "above_optimal": 0.85,
                    "extreme": 0.6,
                },
            },
            "sleep": {
                "weight": 0.18,
                "optimal_range": {"min": 7, "max": 9},  # hours/night
                "unit": "hours/night",
                "impact": {"below_min": 0.4, "optimal": 1.0, "above_optimal": 0.7},
            },
            "nutrition": {
                "weight": 0.17,
                "optimal_range": {"min": 70, "max": 100},  # diet quality score
                "unit": "quality_score",
                "impact": {"below_min": 0.3, "optimal": 1.0, "above_optimal": 0.9},
            },
            "stress": {
                "weight": 0.12,
                "optimal_range": {"min": 0, "max": 30},  # perceived stress score
                "unit": "stress_score",
                "impact": {"below_min": 1.0, "optimal": 1.0, "above_optimal": 0.5},
            },
            "social_connection": {
                "weight": 0.10,
                "optimal_range": {"min": 60, "max": 100},  # social score
                "unit": "connection_score",
                "impact": {"below_min": 0.4, "optimal": 1.0, "above_optimal": 0.9},
            },
            "smoking": {
                "weight": 0.15,
                "optimal_range": {"min": 0, "max": 0},  # 0 = non-smoker
                "unit": "cigarettes/day",
                "impact": {"below_min": 0.0, "optimal": 1.0, "above_optimal": 0.3},
            },
            "alcohol": {
                "weight": 0.08,
                "optimal_range": {"min": 0, "max": 7},  # drinks/week
                "unit": "drinks/week",
                "impact": {"below_min": 1.0, "optimal": 0.9, "above_optimal": 0.5},
            },
        }

        self.blue_zones_habits = [
            "natural_movement", "sense_of_purpose", "downshift",
            "80_percent_rule", "plant_slant", "wine_at_5",
            "belong_to_tribe", "loved_ones_first",
        ]

    # Factors needed before the weighted score means anything. Below this the
    # weights no longer sum to one and the score is not comparable.
    MIN_FACTORS_ANSWERED = 4

    def assess_longevity(self, user_id: str, lifestyle_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score the lifestyle factors the user reported.

        Every unanswered factor used to default to the bottom of its optimal
        range — that is, to count as already optimal — so an assessment with no
        answers came back with a flattering score, a biological age four years
        below the user's own, and a life expectancy. Unanswered factors are now
        left out of the score and named in `unanswered`.
        """
        answered = {
            name: float(lifestyle_data[name])
            for name in self.factors
            if isinstance(lifestyle_data.get(name), (int, float))
            and not isinstance(lifestyle_data.get(name), bool)
        }
        unanswered = [name for name in self.factors if name not in answered]

        if len(answered) < self.MIN_FACTORS_ANSWERED:
            return {
                "status": "insufficient_data",
                "answered": len(answered),
                "needed": self.MIN_FACTORS_ANSWERED,
                "unanswered": unanswered,
                "factors": {
                    name: {"unit": factor["unit"], "optimal_range": factor["optimal_range"]}
                    for name, factor in self.factors.items()
                },
                "message": (
                    f"Answer at least {self.MIN_FACTORS_ANSWERED} lifestyle factors to get a score. "
                    "Unanswered factors are left out rather than assumed to be good."
                ),
            }

        factor_scores = {}
        for name, value in answered.items():
            factor = self.factors[name]
            score = self._score_factor(name, value, factor)
            factor_scores[name] = {
                "value": value,
                "score": round(score, 3),
                "unit": factor["unit"],
                "status": self._factor_status(value, factor["optimal_range"]),
            }

        # Renormalised over the answered factors, so a partial assessment is
        # not penalised for the questions it did not cover.
        total_weight = sum(self.factors[name]["weight"] for name in factor_scores)
        weighted_score = sum(
            factor_scores[name]["score"] * self.factors[name]["weight"] for name in factor_scores
        ) / total_weight

        longevity_score = round(weighted_score * 100, 1)
        chronological_age = lifestyle_data.get("age")

        profile = {
            "profile_id": f"long_{user_id}_{int(time.time())}",
            "user_id": user_id,
            "status": "scored",
            "timestamp": time.time(),
            "chronological_age": chronological_age,
            "longevity_score": longevity_score,
            "factors_answered": len(factor_scores),
            "factors_total": len(self.factors),
            "unanswered": unanswered,
            "factor_scores": factor_scores,
            "blue_zones_alignment": self._assess_blue_zones(lifestyle_data),
            "top_interventions": self._prioritize_interventions(factor_scores),
            "longevity_tier": self._get_tier(longevity_score),
            # Biological age and life expectancy are deliberately absent.
            # Biological age needs biomarkers — methylation, or a panel — not a
            # lifestyle questionnaire, and this reported one by adding a
            # modifier to the user's real age and then subtracting a flat four
            # years, so everybody came out younger than they are.
            "biological_age": None,
            "biological_age_note": (
                "Not estimated from lifestyle answers alone; it needs biomarker testing."
            ),
            "disclaimer": (
                "A score over the lifestyle factors you reported, useful for comparing "
                "with your own later answers. It does not predict lifespan."
            ),
        }

        self.profiles[profile["profile_id"]] = profile
        return profile

    def track_intervention(self, user_id: str, intervention: Dict[str, Any]) -> Dict[str, Any]:
        """Track a longevity intervention being followed."""
        if user_id not in self.interventions:
            self.interventions[user_id] = []

        entry = {
            "intervention_id": f"int_{int(time.time())}",
            "type": intervention.get("type", "lifestyle"),
            "name": intervention.get("name", "Unknown"),
            "start_date": time.time(),
            "expected_benefit_years": intervention.get("benefit_years", 0.5),
            "status": "active",
            "compliance": [],
        }

        self.interventions[user_id].append(entry)
        return entry

    def get_longevity_recommendations(self, user_id: str) -> List[Dict]:
        """Get personalized longevity recommendations."""
        user_profiles = [p for p in self.profiles.values() if p["user_id"] == user_id]
        if not user_profiles:
            return [{"category": "general", "recommendation": "Complete a longevity assessment first", "priority": "high"}]

        latest = user_profiles[-1]
        recommendations = []

        for factor_name, data in latest["factor_scores"].items():
            if data["score"] < 0.6:
                recs = self._get_factor_recommendations(factor_name, data)
                recommendations.extend(recs)

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 4))

        return recommendations[:10]

    def get_longevity_comparison(self, user_id: str) -> Dict[str, Any]:
        """Compare user's longevity metrics against population averages."""
        user_profiles = [p for p in self.profiles.values() if p["user_id"] == user_id]
        if not user_profiles:
            return {"error": "No assessment data available"}

        latest = user_profiles[-1]
        # Biological age is not compared: it is no longer estimated, because a
        # lifestyle questionnaire cannot produce one.
        population_averages = {
            "longevity_score": 55,
            "exercise_score": 0.45,
            "sleep_score": 0.5,
            "nutrition_score": 0.5,
        }

        comparison = {
            "longevity_score": {
                "yours": latest["longevity_score"],
                "population_avg": population_averages["longevity_score"],
                "percentile": self._calculate_percentile(latest["longevity_score"], population_averages["longevity_score"], lower_better=False),
            },
        }

        return comparison

    def _score_factor(self, name: str, value: float, factor: Dict) -> float:
        rng = factor["optimal_range"]
        impact = factor["impact"]

        if name == "stress":
            if value <= rng["max"]:
                return impact["optimal"]
            else:
                excess = (value - rng["max"]) / 30
                return max(0.2, impact["above_optimal"] - excess)

        if value < rng["min"]:
            return impact["below_min"]
        elif value <= rng["max"]:
            return impact["optimal"]
        else:
            return impact.get("above_optimal", 0.8)

    def _factor_status(self, value: float, optimal_range: Dict) -> str:
        if value < optimal_range["min"]:
            return "below_optimal"
        elif value <= optimal_range["max"]:
            return "optimal"
        else:
            return "above_optimal"

    def _assess_blue_zones(self, data: Dict) -> Dict[str, Any]:
        habits_present = []
        habits_missing = []

        habit_checks = {
            "natural_movement": data.get("daily_movement", 0) > 30,
            "sense_of_purpose": data.get("has_purpose", False),
            "downshift": data.get("stress_management", False),
            "80_percent_rule": data.get("eat_until_80_percent", False),
            "plant_slant": data.get("plant_based_ratio", 0) > 0.5,
            "wine_at_5": 0 < data.get("alcohol", 0) <= 7,
            "belong_to_tribe": data.get("social_connection", 0) > 60,
            "loved_ones_first": data.get("family_priority", False),
        }

        for habit, present in habit_checks.items():
            if present:
                habits_present.append(habit)
            else:
                habits_missing.append(habit)

        return {
            "habits_present": len(habits_present),
            "habits_total": len(habit_checks),
            "score": round(len(habits_present) / len(habit_checks), 2),
            "present": habits_present,
            "missing": habits_missing,
        }

    def _prioritize_interventions(self, factor_scores: Dict) -> List[Dict]:
        interventions = []
        sorted_factors = sorted(factor_scores.items(), key=lambda x: x[1]["score"])

        intervention_map = {
            "exercise": {"action": "Increase weekly exercise to 150+ minutes", "benefit_years": 3.5},
            "sleep": {"action": "Optimize sleep to 7-9 hours nightly", "benefit_years": 2.8},
            "nutrition": {"action": "Adopt Mediterranean or plant-forward diet", "benefit_years": 3.2},
            "stress": {"action": "Implement daily stress reduction practice", "benefit_years": 2.0},
            "social_connection": {"action": "Strengthen social bonds and community ties", "benefit_years": 2.5},
            "smoking": {"action": "Quit smoking completely", "benefit_years": 5.0},
            "alcohol": {"action": "Reduce alcohol to ≤7 drinks/week", "benefit_years": 1.5},
        }

        for factor_name, data in sorted_factors[:5]:
            if factor_name in intervention_map and data["score"] < 0.7:
                intervention = intervention_map[factor_name]
                interventions.append({
                    "factor": factor_name,
                    "current_score": data["score"],
                    "action": intervention["action"],
                    "potential_benefit_years": intervention["benefit_years"],
                    "priority": "critical" if data["score"] < 0.3 else "high" if data["score"] < 0.5 else "medium",
                })

        return interventions

    def _get_tier(self, score: float) -> Dict[str, str]:
        if score >= 85:
            return {"tier": "Elite", "label": "Exceptional longevity", "emoji": "🏆"}
        elif score >= 70:
            return {"tier": "Advanced", "label": "Above average health span", "emoji": "⭐"}
        elif score >= 55:
            return {"tier": "Optimal", "label": "Good health trajectory", "emoji": "✅"}
        elif score >= 40:
            return {"tier": "Developing", "label": "Room for improvement", "emoji": "📈"}
        else:
            return {"tier": "Foundation", "label": "Significant opportunities", "emoji": "🌱"}

    def _get_factor_recommendations(self, factor: str, data: Dict) -> List[Dict]:
        recs = {
            "exercise": [
                {"recommendation": "Start with 30-min brisk walks 5x/week", "priority": "high", "category": "exercise"},
                {"recommendation": "Add 2 strength training sessions/week", "priority": "medium", "category": "exercise"},
            ],
            "sleep": [
                {"recommendation": "Maintain consistent sleep/wake schedule", "priority": "high", "category": "sleep"},
                {"recommendation": "Avoid screens 1hr before bed", "priority": "medium", "category": "sleep"},
            ],
            "nutrition": [
                {"recommendation": "Increase vegetable intake to 5+ servings/day", "priority": "high", "category": "nutrition"},
                {"recommendation": "Add omega-3 rich foods (fish, walnuts, flax)", "priority": "medium", "category": "nutrition"},
            ],
            "stress": [
                {"recommendation": "Practice 10-min daily meditation", "priority": "high", "category": "stress"},
                {"recommendation": "Try box breathing (4-4-4-4) during stressful moments", "priority": "medium", "category": "stress"},
            ],
        }
        return recs.get(factor, [{"recommendation": f"Optimize your {factor} levels", "priority": "medium", "category": factor}])

    def _calculate_percentile(self, value: float, average: float, lower_better: bool) -> int:
        diff = value - average
        if lower_better:
            return min(99, max(1, int(50 - diff * 3)))
        else:
            return min(99, max(1, int(50 + diff * 3)))


longevity_tracker_service = LongevityTrackerService()

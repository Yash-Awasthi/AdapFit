"""
Health Data Aggregation & Unified Dashboard API
Combines data from all services into unified health profiles.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid


class HealthDataAggregator:
    def __init__(self):
        self.user_profiles: Dict[str, dict] = {}
        self.health_scores: Dict[str, List[dict]] = {}
        self.correlations: Dict[str, dict] = {}

    def create_unified_profile(self, user_id: str, demographics: dict = None) -> dict:
        profile = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "demographics": demographics or {},
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
        }
        self.user_profiles[user_id] = profile
        return profile

    def calculate_health_score(self, user_id: str, data: dict) -> dict:
        """Calculate a comprehensive health score from multiple data sources."""
        weights = {
            "sleep_quality": 0.15,
            "activity_level": 0.15,
            "nutrition_quality": 0.15,
            "stress_level": 0.12,
            "hydration": 0.08,
            "mental_health": 0.10,
            "bpm_resting": 0.08,
            "weight_status": 0.07,
            "medication_adherence": 0.05,
            "social_connection": 0.05,
        }
        component_scores = {}
        total = 0
        total_weight = 0

        for metric, weight in weights.items():
            if metric in data:
                value = data[metric]
                if metric == "sleep_quality":
                    score = min(value / 9 * 100, 100)
                elif metric == "activity_level":
                    score = min(value / 10000 * 100, 100)
                elif metric == "nutrition_quality":
                    score = min(value, 100)
                elif metric == "stress_level":
                    score = max(0, 100 - (value / 10 * 100))
                elif metric == "hydration":
                    score = min(value / 8 * 100, 100)
                elif metric == "mental_health":
                    score = min(value, 100)
                elif metric == "bpm_resting":
                    if 50 <= value <= 80:
                        score = 100 - abs(value - 65) / 15 * 30
                    else:
                        score = max(0, 70 - abs(value - 65))
                elif metric == "weight_status":
                    score = value
                elif metric == "medication_adherence":
                    score = min(value, 100)
                elif metric == "social_connection":
                    score = min(value, 100)
                else:
                    score = 50
                component_scores[metric] = {"score": round(score, 1), "weight": weight, "weighted_score": round(score * weight, 2)}
                total += score * weight
                total_weight += weight

        overall = round(total / max(total_weight, 0.01), 1)
        grade = "A+" if overall >= 95 else "A" if overall >= 90 else "B+" if overall >= 85 else "B" if overall >= 80 else "C+" if overall >= 75 else "C" if overall >= 70 else "D" if overall >= 60 else "F"

        result = {
            "user_id": user_id,
            "overall_score": overall,
            "grade": grade,
            "components": component_scores,
            "score_breakdown": {
                "physical": round(sum(component_scores.get(m, {}).get("weighted_score", 0) for m in ["sleep_quality", "activity_level", "bpm_resting", "weight_status"]) / 0.45, 1) if total_weight > 0 else 0,
                "mental": round(sum(component_scores.get(m, {}).get("weighted_score", 0) for m in ["stress_level", "mental_health", "social_connection"]) / 0.27, 1) if total_weight > 0 else 0,
                "lifestyle": round(sum(component_scores.get(m, {}).get("weighted_score", 0) for m in ["nutrition_quality", "hydration", "medication_adherence"]) / 0.28, 1) if total_weight > 0 else 0,
            },
            "timestamp": datetime.now().isoformat(),
        }

        self.health_scores.setdefault(user_id, []).append(result)
        return result

    def find_correlations(self, user_id: str, data_points: List[dict]) -> dict:
        """Find correlations between different health metrics."""
        if len(data_points) < 5:
            return {"status": "insufficient_data", "message": "Need at least 5 data points for correlation analysis"}
        
        metrics = {}
        for dp in data_points:
            for k, v in dp.items():
                if isinstance(v, (int, float)):
                    metrics.setdefault(k, []).append(v)

        correlations = {}
        metric_names = list(metrics.keys())
        for i in range(len(metric_names)):
            for j in range(i + 1, len(metric_names)):
                m1, m2 = metric_names[i], metric_names[j]
                if len(metrics[m1]) == len(metrics[m2]) and len(metrics[m1]) > 2:
                    n = len(metrics[m1])
                    mean1 = sum(metrics[m1]) / n
                    mean2 = sum(metrics[m2]) / n
                    num = sum((a - mean1) * (b - mean2) for a, b in zip(metrics[m1], metrics[m2]))
                    den1 = sum((a - mean1) ** 2 for a in metrics[m1]) ** 0.5
                    den2 = sum((b - mean2) ** 2 for b in metrics[m2]) ** 0.5
                    if den1 * den2 > 0:
                        r = num / (den1 * den2)
                        strength = "strong" if abs(r) > 0.7 else "moderate" if abs(r) > 0.4 else "weak"
                        direction = "positive" if r > 0 else "negative"
                        correlations[f"{m1}_vs_{m2}"] = {"correlation": round(r, 3), "strength": strength, "direction": direction}

        self.correlations[user_id] = correlations
        return {"correlations": correlations, "data_points_analyzed": len(data_points)}

    def get_wellness_summary(self, user_id: str, period: str = "7d") -> dict:
        scores = self.health_scores.get(user_id, [])
        period_days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 7)
        cutoff = datetime.now() - timedelta(days=period_days)
        recent = [s for s in scores if datetime.fromisoformat(s["timestamp"]) >= cutoff]

        if not recent:
            return {"status": "no_data", "message": "No health scores calculated yet"}

        avg_score = sum(s["overall_score"] for s in recent) / len(recent)
        trend = "improving" if len(recent) > 1 and recent[-1]["overall_score"] > recent[0]["overall_score"] else "declining" if len(recent) > 1 and recent[-1]["overall_score"] < recent[0]["overall_score"] else "stable"

        return {
            "user_id": user_id,
            "period": period,
            "average_score": round(avg_score, 1),
            "latest_score": recent[-1]["overall_score"],
            "trend": trend,
            "data_points": len(recent),
            "best_score": max(s["overall_score"] for s in recent),
            "lowest_score": min(s["overall_score"] for s in recent),
            "score_history": [{"score": s["overall_score"], "grade": s["grade"], "date": s["timestamp"]} for s in recent],
        }


health_aggregator = HealthDataAggregator()

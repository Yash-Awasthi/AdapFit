"""
Predictive Health Analytics & Early Disease Detection
AI-powered risk prediction, health trend analysis, and early intervention recommendations.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
import math


class PredictiveHealthService:
    DISEASE_RISK_MODELS = {
        "diabetes_type2": {
            "name": "Type 2 Diabetes Risk",
            "factors": ["bmi", "fasting_glucose", "family_history", "age", "activity_level", "waist_circumference"],
            "risk_factors": ["obesity", "sedentary_lifestyle", "family_history", "pcos", "gestational_diabetes"],
            "screening_start_age": 35,
        },
        "cardiovascular": {
            "name": "Cardiovascular Disease Risk",
            "factors": ["blood_pressure_systolic", "cholesterol_total", "hdl", "smoking", "age", "diabetes"],
            "risk_factors": ["hypertension", "high_cholesterol", "smoking", "obesity", "family_history"],
            "screening_start_age": 20,
        },
        "osteoporosis": {
            "name": "Osteoporosis Risk",
            "factors": ["bone_density_t_score", "age", "gender", "vitamin_d", "calcium_intake", "smoking"],
            "risk_factors": ["post_menopause", "low_calcium", "sedentary", "family_history", "corticosteroid_use"],
            "screening_start_age": 65,
        },
        "kidney_disease": {
            "name": "Chronic Kidney Disease Risk",
            "factors": ["egfr", "albumin_creatinine_ratio", "diabetes", "hypertension", "age"],
            "risk_factors": ["diabetes", "hypertension", "family_history", "obesity", "smoking"],
            "screening_start_age": 40,
        },
        "depression": {
            "name": "Depression Risk",
            "factors": ["phq9_score", "sleep_quality", "social_isolation", "stress_level", "physical_activity"],
            "risk_factors": ["previous_episode", "trauma", "chronic_pain", "substance_use", "family_history"],
            "screening_start_age": 12,
        },
        "fall_risk_elderly": {
            "name": "Fall Risk (Elderly)",
            "factors": ["age", "balance_score", "medication_count", "vision", "muscle_strength"],
            "risk_factors": ["polypharmacy", "poor_vision", "muscle_weakness", "cognitive_decline", "environmental_hazards"],
            "screening_start_age": 65,
        },
        "burnout": {
            "name": "Burnout Risk",
            "factors": ["work_hours", "sleep_quality", "stress_level", "satisfaction_score", "social_support"],
            "risk_factors": ["overwork", "low_control", "high_demands", "low_reward", "poor_boundaries"],
            "screening_start_age": 18,
        },
    }

    HEALTH_TREND_PERIODS = ["7d", "30d", "90d", "1y"]

    def __init__(self):
        self.health_snapshots: Dict[str, List[dict]] = {}
        self.risk_assessments: Dict[str, List[dict]] = {}
        self.alerts: Dict[str, List[dict]] = {}
        self.predictions: Dict[str, List[dict]] = {}

    def record_health_snapshot(self, user_id: str, metrics: dict) -> dict:
        snapshot = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
        }
        self.health_snapshots.setdefault(user_id, []).append(snapshot)
        return snapshot

    def assess_disease_risk(self, user_id: str, disease_key: str, user_metrics: dict) -> dict:
        model = self.DISEASE_RISK_MODELS.get(disease_key)
        if not model:
            return {"error": f"Unknown disease model: {disease_key}"}

        score = 0.0
        matched_factors = []
        missing_factors = []

        for factor in model["factors"]:
            if factor in user_metrics:
                matched_factors.append(factor)
                value = user_metrics[factor]
                if isinstance(value, (int, float)):
                    if factor in ("bmi", "fasting_glucose", "blood_pressure_systolic", "cholesterol_total", "age", "waist_circumference", "medication_count", "work_hours", "stress_level"):
                        if factor == "bmi" and value > 30:
                            score += 0.2
                        elif factor == "fasting_glucose" and value > 100:
                            score += 0.15
                        elif factor == "blood_pressure_systolic" and value > 140:
                            score += 0.2
                        elif factor == "cholesterol_total" and value > 240:
                            score += 0.15
                        elif factor == "age" and value > 50:
                            score += 0.1
                        elif factor == "medication_count" and value > 4:
                            score += 0.15
                        elif factor == "stress_level" and value > 7:
                            score += 0.1
                    elif isinstance(value, bool) and value:
                        score += 0.15
            else:
                missing_factors.append(factor)

        risk_level = "low" if score < 0.25 else "moderate" if score < 0.5 else "high" if score < 0.75 else "very_high"
        confidence = len(matched_factors) / max(len(model["factors"]), 1) * 100

        assessment = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "disease": disease_key,
            "disease_name": model["name"],
            "risk_score": round(min(score, 1.0), 3),
            "risk_level": risk_level,
            "confidence": round(confidence, 1),
            "matched_factors": matched_factors,
            "missing_factors": missing_factors,
            "risk_factors_present": [f for f in model["risk_factors"] if f in user_metrics],
            "recommendations": self._get_recommendations(disease_key, risk_level, matched_factors),
            "timestamp": datetime.now().isoformat(),
        }
        self.risk_assessments.setdefault(user_id, []).append(assessment)
        return assessment

    def _get_recommendations(self, disease_key: str, risk_level: str, factors: List[str]) -> List[str]:
        recs = {
            "diabetes_type2": ["Monitor fasting glucose quarterly", "Maintain healthy BMI", "Exercise 150 min/week", "Limit refined sugars"],
            "cardiovascular": ["Monitor blood pressure regularly", "Maintain healthy cholesterol", "Cardiovascular exercise 3x/week", "Reduce sodium intake"],
            "osteoporosis": ["Weight-bearing exercises", "Calcium + Vitamin D supplementation", "Bone density scan recommended", "Avoid smoking"],
            "kidney_disease": ["Monitor kidney function labs", "Stay hydrated", "Limit NSAID use", "Control blood pressure"],
            "depression": ["Regular physical activity", "Maintain social connections", "Sleep hygiene", "Consider professional screening"],
            "fall_risk_elderly": ["Balance training exercises", "Home safety assessment", "Vision check", "Medication review"],
            "burnout": ["Set work-life boundaries", "Practice stress management", "Prioritize sleep", "Seek social support"],
        }
        base = recs.get(disease_key, ["Maintain healthy lifestyle"])
        if risk_level in ("high", "very_high"):
            return base + ["Consult healthcare provider promptly", "Schedule comprehensive screening"]
        elif risk_level == "moderate":
            return base + ["Schedule screening within 3 months", "Monitor symptoms closely"]
        return base[:3]

    def analyze_health_trends(self, user_id: str, period: str = "30d") -> dict:
        snapshots = self.health_snapshots.get(user_id, [])
        if not snapshots:
            return {"status": "no_data", "message": "No health data recorded yet"}

        now = datetime.now()
        period_days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}.get(period, 30)
        cutoff = now - timedelta(days=period_days)
        recent = [s for s in snapshots if datetime.fromisoformat(s["timestamp"]) >= cutoff]

        if not recent:
            return {"status": "no_data", "message": f"No data in the last {period}"}

        metric_trends = {}
        all_keys = set()
        for snap in recent:
            all_keys.update(snap["metrics"].keys())

        for key in all_keys:
            values = [s["metrics"].get(key) for s in recent if key in s["metrics"] and isinstance(s["metrics"][key], (int, float))]
            if len(values) >= 2:
                change = values[-1] - values[0]
                pct_change = (change / abs(values[0]) * 100) if values[0] != 0 else 0
                direction = "improving" if change < 0 and key not in ("hrv", "sleep_quality", "muscle_strength", "bone_density") else "worsening" if change > 0 else "stable"
                metric_trends[key] = {
                    "current": values[-1],
                    "previous": values[0],
                    "change": round(change, 2),
                    "percent_change": round(pct_change, 1),
                    "direction": direction,
                    "min": round(min(values), 2),
                    "max": round(max(values), 2),
                    "avg": round(sum(values) / len(values), 2),
                    "data_points": len(values),
                }

        improving = [k for k, v in metric_trends.items() if v["direction"] == "improving"]
        worsening = [k for k, v in metric_trends.items() if v["direction"] == "worsening"]

        return {
            "period": period,
            "data_points": len(recent),
            "metric_trends": metric_trends,
            "improving_metrics": improving,
            "worsening_metrics": worsening,
            "overall_trajectory": "positive" if len(improving) > len(worsening) else "negative" if len(worsening) > len(improving) else "mixed",
            "generated_at": datetime.now().isoformat(),
        }

    def generate_health_predictions(self, user_id: str) -> List[dict]:
        snapshots = self.health_snapshots.get(user_id, [])
        if len(snapshots) < 5:
            return [{"message": "Need at least 5 health snapshots for predictions", "status": "insufficient_data"}]

        trends = self.analyze_health_trends(user_id, "30d")
        predictions = []

        for metric, trend in trends.get("metric_trends", {}).items():
            if trend["data_points"] >= 3 and abs(trend["percent_change"]) > 5:
                change_per_day = trend["change"] / 30
                future_30 = trend["current"] + change_per_day * 30
                future_90 = trend["current"] + change_per_day * 90
                predictions.append({
                    "metric": metric,
                    "current_value": trend["current"],
                    "projected_30d": round(future_30, 2),
                    "projected_90d": round(future_90, 2),
                    "trend_direction": trend["direction"],
                    "confidence": min(trend["data_points"] * 10, 90),
                })

        self.predictions[user_id] = predictions
        return predictions

    def generate_alerts(self, user_id: str, current_metrics: dict) -> List[dict]:
        alerts = []
        thresholds = {
            "bpm": {"high": 100, "low": 50, "severity": "urgent"},
            "blood_pressure_systolic": {"high": 140, "low": 90, "severity": "warning"},
            "blood_pressure_diastolic": {"high": 90, "low": 60, "severity": "warning"},
            "fasting_glucose": {"high": 126, "low": 70, "severity": "warning"},
            "spo2": {"low_threshold": 94, "severity": "urgent"},
            "stress_level": {"high": 8, "severity": "info"},
            "sleep_quality": {"low_threshold": 4, "severity": "info"},
            "body_temperature": {"high": 38.0, "low": 35.5, "severity": "urgent"},
        }
        for metric, value in current_metrics.items():
            if metric in thresholds and isinstance(value, (int, float)):
                t = thresholds[metric]
                if "high" in t and value > t["high"]:
                    alerts.append({
                        "metric": metric, "value": value, "threshold": t["high"],
                        "type": "above_normal", "severity": t["severity"],
                        "message": f"{metric} is elevated at {value}",
                        "timestamp": datetime.now().isoformat(),
                    })
                if "low" in t and value < t["low"]:
                    alerts.append({
                        "metric": metric, "value": value, "threshold": t["low"],
                        "type": "below_normal", "severity": t["severity"],
                        "message": f"{metric} is low at {value}",
                        "timestamp": datetime.now().isoformat(),
                    })
                if "low_threshold" in t and value < t["low_threshold"]:
                    alerts.append({
                        "metric": metric, "value": value, "threshold": t["low_threshold"],
                        "type": "critical_low", "severity": t["severity"],
                        "message": f"{metric} critically low at {value}",
                        "timestamp": datetime.now().isoformat(),
                    })
        self.alerts.setdefault(user_id, []).extend(alerts)
        return alerts

    def get_comprehensive_health_report(self, user_id: str) -> dict:
        snapshots = self.health_snapshots.get(user_id, [])
        assessments = self.risk_assessments.get(user_id, [])
        predictions = self.predictions.get(user_id, [])
        alerts = self.alerts.get(user_id, [])

        trends = self.analyze_health_trends(user_id, "30d") if snapshots else {}
        risk_summary = {}
        for a in assessments:
            disease = a["disease"]
            if disease not in risk_summary or a["timestamp"] > risk_summary[disease]["timestamp"]:
                risk_summary[disease] = a

        return {
            "user_id": user_id,
            "generated_at": datetime.now().isoformat(),
            "total_snapshots": len(snapshots),
            "health_trends": trends,
            "risk_assessments": list(risk_summary.values()),
            "predictions": predictions,
            "active_alerts": [a for a in alerts if a["severity"] in ("urgent", "warning")][-10:],
            "recommendations": self._aggregate_recommendations(list(risk_summary.values())),
        }

    def _aggregate_recommendations(self, assessments: List[dict]) -> List[str]:
        all_recs = []
        for a in assessments:
            all_recs.extend(a.get("recommendations", []))
        seen = set()
        unique = []
        for rec in all_recs:
            if rec not in seen:
                seen.add(rec)
                unique.append(rec)
        return unique[:10]


predictive_health_service = PredictiveHealthService()

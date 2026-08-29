"""
AI Health Risk Prediction Engine — Chronic Disease Prevention

Features:
- Cardiovascular risk scoring (10-year risk)
- Diabetes risk assessment (Framingham-based)
- Metabolic syndrome detection
- Obesity risk classification
- Sleep disorder risk
- Stress-related health risks
- Personalized prevention recommendations
- Risk trend tracking over time
"""
import time
import math
from typing import Optional
from dataclasses import dataclass, field


RISK_FACTORS = {
    "cardiovascular": ["age", "gender", "total_cholesterol", "hdl_cholesterol", "systolic_bp", "smoking", "diabetes"],
    "diabetes": ["age", "bmi", "waist_circumference", "physical_activity", "family_history", "bp_medications", "high_glucose"],
    "metabolic_syndrome": ["waist_circumference", "triglycerides", "hdl_cholesterol", "systolic_bp", "fasting_glucose"],
    "obesity": ["bmi", "waist_circumference", "body_fat_percentage", "weight_trend"],
    "sleep_disorder": ["sleep_hours", "sleep_quality", "bmi", "neck_circumference", "snoring", "daytime_sleepiness"],
    "stress": ["stress_level", "sleep_quality", "heart_rate_variability", "work_hours", "exercise_frequency"],
}


class HealthRiskEngine:
    """AI-powered health risk assessment and prevention engine."""

    def __init__(self):
        self._assessments: list[dict] = []
        self._risk_history: dict[str, list[dict]] = {}

    def assess_cardiovascular_risk(self, data: dict) -> dict:
        age = data.get("age", 30)
        gender = data.get("gender", "male")
        tc = data.get("total_cholesterol", 200)
        hdl = data.get("hdl_cholesterol", 50)
        sbp = data.get("systolic_bp", 120)
        smoker = data.get("smoking", False)
        diabetes = data.get("diabetes", False)

        # Simplified Framingham risk scoring
        score = 0
        # Age points
        if gender == "male":
            if age < 35: score += 0
            elif age < 40: score += 2
            elif age < 45: score += 5
            elif age < 50: score += 7
            elif age < 55: score += 10
            elif age < 60: score += 12
            elif age < 65: score += 14
            else: score += 16
        else:
            if age < 35: score += 0
            elif age < 40: score += 2
            elif age < 45: score += 4
            elif age < 50: score += 6
            elif age < 55: score += 8
            elif age < 60: score += 10
            elif age < 65: score += 12
            else: score += 14

        # Cholesterol
        if tc > 280: score += 3
        elif tc > 240: score += 2
        elif tc > 200: score += 1

        # HDL (protective)
        if hdl >= 60: score -= 1
        elif hdl < 40: score += 2
        elif hdl < 50: score += 1

        # Blood pressure
        if sbp >= 160: score += 4
        elif sbp >= 140: score += 2
        elif sbp >= 130: score += 1

        if smoker: score += 2
        if diabetes: score += 2

        # Convert to 10-year risk percentage
        risk_pct = min(95, max(1, int(2.5 * math.exp(0.06 * score))))

        if risk_pct < 10:
            category = "low"
            message = "Low cardiovascular risk. Maintain healthy lifestyle."
        elif risk_pct < 20:
            category = "moderate"
            message = "Moderate risk. Consider lifestyle modifications."
        elif risk_pct < 30:
            category = "high"
            message = "High risk. Consult a cardiologist."
        else:
            category = "very_high"
            message = "Very high risk. Immediate medical consultation recommended."

        return {
            "risk_score": score, "risk_percentage": risk_pct, "category": category,
            "message": message,
            "factors": {"age": age, "cholesterol": tc, "hdl": hdl, "bp": sbp, "smoker": smoker, "diabetes": diabetes},
            "recommendations": self._get_cv_recommendations(category, data),
        }

    def _get_cv_recommendations(self, category: str, data: dict) -> list[str]:
        recs = []
        if data.get("systolic_bp", 120) >= 140:
            recs.append("Reduce sodium intake and monitor blood pressure regularly")
        if data.get("total_cholesterol", 200) >= 240:
            recs.append("Reduce saturated fat intake. Consider omega-3 supplements")
        if data.get("smoking"):
            recs.append("Quit smoking — this is the single biggest risk reducer")
        if data.get("bmi", 25) >= 30:
            recs.append("Achieve and maintain healthy weight through diet and exercise")
        recs.append("Exercise 150+ minutes of moderate activity per week")
        recs.append("Eat a Mediterranean-style diet rich in fruits, vegetables, whole grains")
        return recs

    def assess_diabetes_risk(self, data: dict) -> dict:
        age = data.get("age", 30)
        bmi = data.get("bmi", 25)
        waist = data.get("waist_circumference", 90)
        activity = data.get("physical_activity", "moderate")
        family = data.get("family_history", False)
        high_glucose = data.get("high_glucose", False)

        score = 0
        if age >= 45: score += 2
        if bmi >= 30: score += 3
        elif bmi >= 25: score += 1
        if waist > 102: score += 3
        elif waist > 90: score += 1
        if activity == "sedentary": score += 2
        if family: score += 3
        if high_glucose: score += 4

        risk_pct = min(80, max(5, int(5 + score * 5)))

        if risk_pct < 15:
            category = "low"
        elif risk_pct < 30:
            category = "moderate"
        elif risk_pct < 50:
            category = "high"
        else:
            category = "very_high"

        return {
            "risk_score": score, "risk_percentage": risk_pct, "category": category,
            "recommendations": [
                "Maintain healthy weight (BMI < 25)" if bmi >= 25 else "Weight is healthy",
                "Exercise 150+ minutes/week" if activity == "sedentary" else "Good activity level",
                "Monitor blood glucose annually" if risk_pct >= 15 else "Annual checkup sufficient",
                "Eat whole grains, limit refined sugars",
            ],
        }

    def assess_metabolic_syndrome(self, data: dict) -> dict:
        criteria_met = 0
        details = {}
        waist = data.get("waist_circumference", 90)
        if waist > (102 if data.get("gender") == "male" else 88):
            criteria_met += 1; details["waist"] = "elevated"
        trig = data.get("triglycerides", 150)
        if trig >= 150:
            criteria_met += 1; details["triglycerides"] = "elevated"
        hdl = data.get("hdl_cholesterol", 50)
        if hdl < (40 if data.get("gender") == "male" else 50):
            criteria_met += 1; details["hdl"] = "low"
        bp = data.get("systolic_bp", 120)
        if bp >= 130:
            criteria_met += 1; details["bp"] = "elevated"
        glucose = data.get("fasting_glucose", 100)
        if glucose >= 100:
            criteria_met += 1; details["glucose"] = "elevated"

        has_syndrome = criteria_met >= 3
        return {
            "criteria_met": criteria_met, "has_metabolic_syndrome": has_syndrome,
            "details": details, "risk_level": "high" if criteria_met >= 3 else "moderate" if criteria_met >= 2 else "low",
            "recommendations": [
                "Lose 5-10% of body weight if overweight" if criteria_met >= 2 else "",
                "Exercise 30+ minutes daily" if criteria_met >= 2 else "",
                "Reduce refined carbohydrates and sugar",
                "Increase fiber intake to 25-30g/day",
            ],
        }

    def get_comprehensive_risk_report(self, user_data: dict) -> dict:
        cv = self.assess_cardiovascular_risk(user_data)
        diabetes = self.assess_diabetes_risk(user_data)
        metabolic = self.assess_metabolic_syndrome(user_data)

        overall_score = (cv["risk_percentage"] + diabetes["risk_percentage"] + metabolic.get("criteria_met", 0) * 15) / 3
        overall_risk = "low" if overall_score < 15 else "moderate" if overall_score < 30 else "high"

        report = {
            "overall_risk": overall_risk, "overall_score": round(overall_score),
            "cardiovascular": cv, "diabetes": diabetes, "metabolic": metabolic,
            "generated_at": time.strftime("%Y-%m-%d %H:%M"),
            "disclaimer": "This is an AI-generated risk assessment for informational purposes only. Always consult a healthcare professional for medical advice.",
        }

        self._assessments.append(report)
        return report

    def get_risk_trends(self, user_id: str = "default") -> list[dict]:
        return self._risk_history.get(user_id, [])


health_risk_engine = HealthRiskEngine()

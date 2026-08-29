"""
Recovery Engine V2 — Cross-Domain Intelligence

Combines multiple data sources into explainable recovery recommendations:
- Sleep quality and duration
- HRV trends (RMSSD, LF/HF ratio)
- Training load (ACWR, session RPE)
- Subjective fatigue and mood
- Stress levels
- Resting heart rate trends
- Nutrition and hydration status

Every recommendation includes:
- Recovery score (0-100)
- Individual domain scores
- Cross-domain insights ("Your poor sleep combined with high training load suggests...")
- Specific, actionable recommendations
- Confidence level based on data availability
"""
import time
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class RecoveryInput:
    """All inputs for recovery calculation."""
    # Sleep
    sleep_hours: Optional[float] = None
    sleep_quality: Optional[float] = None  # 0-100
    deep_sleep_pct: Optional[float] = None
    sleep_consistency: Optional[float] = None  # 0-100

    # Heart Rate
    hrv_rmssd: Optional[float] = None
    resting_hr: Optional[float] = None
    resting_hr_trend: Optional[str] = None  # 'rising', 'stable', 'falling'

    # Training
    training_load_today: Optional[float] = None
    acwr: Optional[float] = None
    session_rpe: Optional[float] = None  # 1-10
    days_since_rest: Optional[int] = None

    # Subjective
    fatigue_level: Optional[float] = None  # 1-10
    mood_score: Optional[float] = None  # 1-10
    stress_level: Optional[float] = None  # 0-100

    # Nutrition
    calories_consumed: Optional[float] = None
    water_ml: Optional[int] = None
    protein_g: Optional[float] = None

    # Context
    age: Optional[int] = None
    fitness_level: str = "intermediate"
    training_goal: str = "general_fitness"


@dataclass
class DomainScore:
    name: str
    score: float  # 0-100
    weight: float
    weighted_score: float
    status: str  # excellent, good, fair, poor, critical
    insight: str
    data_available: bool


@dataclass
class RecoveryResult:
    overall_score: float
    recovery_level: str  # excellent, good, moderate, poor, critical
    domains: list
    cross_domain_insights: list
    recommendations: list
    training_recommendation: str
    confidence: str  # high, medium, low
    data_completeness: float  # percentage of data available


class RecoveryEngineV2:
    """
    Cross-domain recovery engine that combines multiple health signals
    into explainable recovery scores and recommendations.
    """

    # Domain weights for overall score
    DOMAIN_WEIGHTS = {
        "sleep": 0.25,
        "hrv": 0.20,
        "training_load": 0.20,
        "subjective": 0.15,
        "nutrition": 0.10,
        "heart_rate": 0.10,
    }

    # HRV thresholds (RMSSD in ms)
    HRV_RANGES = {
        "excellent": (70, 200),
        "good": (50, 70),
        "fair": (30, 50),
        "poor": (15, 30),
        "critical": (0, 15),
    }

    # Resting HR thresholds (bpm)
    RHR_RANGES = {
        "excellent": (40, 55),
        "good": (55, 65),
        "fair": (65, 75),
        "poor": (75, 85),
        "critical": (85, 120),
    }

    def calculate_recovery(self, data: RecoveryInput) -> RecoveryResult:
        """Calculate comprehensive recovery score from all available data."""
        domains = []

        # Calculate each domain score
        domains.append(self._score_sleep(data))
        domains.append(self._score_hrv(data))
        domains.append(self._score_training_load(data))
        domains.append(self._score_subjective(data))
        domains.append(self._score_nutrition(data))
        domains.append(self._score_heart_rate(data))

        # Calculate overall score
        available_domains = [d for d in domains if d.data_available]
        if not available_domains:
            overall_score = 50.0
            confidence = "low"
            completeness = 0.0
        else:
            total_weight = sum(d.weight for d in available_domains)
            overall_score = sum(d.weighted_score for d in available_domains) / total_weight if total_weight > 0 else 50.0
            completeness = len(available_domains) / len(domains)
            confidence = "high" if completeness >= 0.6 else "medium" if completeness >= 0.3 else "low"

        # Generate cross-domain insights
        insights = self._generate_cross_domain_insights(data, domains)

        # Generate recommendations
        recommendations = self._generate_recommendations(data, domains, overall_score)

        # Training recommendation
        training_rec = self._get_training_recommendation(overall_score, data)

        # Determine recovery level
        if overall_score >= 80:
            level = "excellent"
        elif overall_score >= 65:
            level = "good"
        elif overall_score >= 45:
            level = "moderate"
        elif overall_score >= 25:
            level = "poor"
        else:
            level = "critical"

        return RecoveryResult(
            overall_score=round(overall_score, 1),
            recovery_level=level,
            domains=domains,
            cross_domain_insights=insights,
            recommendations=recommendations,
            training_recommendation=training_rec,
            confidence=confidence,
            data_completeness=round(completeness * 100),
        )

    def _score_sleep(self, data: RecoveryInput) -> DomainScore:
        """Score sleep quality and duration."""
        weight = self.DOMAIN_WEIGHTS["sleep"]

        if data.sleep_hours is None and data.sleep_quality is None:
            return DomainScore("sleep", 0, weight, 0, "no_data",
                             "Sleep data not available", False)

        score = 50  # Base

        if data.sleep_hours is not None:
            if data.sleep_hours >= 8:
                score += 20
            elif data.sleep_hours >= 7:
                score += 10
            elif data.sleep_hours >= 6:
                score -= 5
            else:
                score -= 20

        if data.sleep_quality is not None:
            score += (data.sleep_quality - 50) * 0.3

        if data.deep_sleep_pct is not None:
            if data.deep_sleep_pct >= 20:
                score += 10
            elif data.deep_sleep_pct >= 15:
                score += 5
            else:
                score -= 5

        if data.sleep_consistency is not None:
            score += (data.sleep_consistency - 50) * 0.1

        score = max(0, min(100, score))
        status = self._score_to_status(score)

        insight = self._sleep_insight(data)
        return DomainScore("sleep", score, weight, score * weight, status, insight, True)

    def _score_hrv(self, data: RecoveryInput) -> DomainScore:
        """Score HRV recovery status."""
        weight = self.DOMAIN_WEIGHTS["hrv"]

        if data.hrv_rmssd is None:
            return DomainScore("hrv", 0, weight, 0, "no_data",
                             "HRV data not available", False)

        hrv = data.hrv_rmssd
        if hrv >= 70:
            score = 90
        elif hrv >= 50:
            score = 70 + (hrv - 50) * 1
        elif hrv >= 30:
            score = 40 + (hrv - 30) * 1.5
        elif hrv >= 15:
            score = 15 + (hrv - 15) * 1.67
        else:
            score = max(0, hrv * 1)

        status = self._score_to_status(score)
        insight = f"HRV of {hrv:.0f}ms indicates {'good' if score >= 70 else 'moderate' if score >= 40 else 'low'} autonomic nervous system recovery."
        return DomainScore("hrv", score, weight, score * weight, status, insight, True)

    def _score_training_load(self, data: RecoveryInput) -> DomainScore:
        """Score training load appropriateness."""
        weight = self.DOMAIN_WEIGHTS["training_load"]

        if data.acwr is None and data.training_load_today is None:
            return DomainScore("training_load", 0, weight, 0, "no_data",
                             "Training load data not available", False)

        score = 70  # Base

        if data.acwr is not None:
            if 0.8 <= data.acwr <= 1.3:
                score = 90  # Optimal zone
            elif data.acwr < 0.8:
                score = 60  # Undertraining
            elif data.acwr <= 1.5:
                score = 50  # Getting high
            elif data.acwr <= 2.0:
                score = 30  # Too high
            else:
                score = 15  # Dangerous

        if data.days_since_rest is not None:
            if data.days_since_rest >= 7:
                score -= 20
            elif data.days_since_rest >= 5:
                score -= 10

        score = max(0, min(100, score))
        status = self._score_to_status(score)
        insight = self._training_insight(data, score)
        return DomainScore("training_load", score, weight, score * weight, status, insight, True)

    def _score_subjective(self, data: RecoveryInput) -> DomainScore:
        """Score subjective wellness indicators."""
        weight = self.DOMAIN_WEIGHTS["subjective"]

        if data.fatigue_level is None and data.mood_score is None and data.stress_level is None:
            return DomainScore("subjective", 0, weight, 0, "no_data",
                             "Subjective data not available", False)

        score = 50

        if data.fatigue_level is not None:
            # Low fatigue = good (1 is best, 10 is worst)
            score += (10 - data.fatigue_level) * 4

        if data.mood_score is not None:
            score += (data.mood_score - 5) * 4

        if data.stress_level is not None:
            score += (100 - data.stress_level) * 0.2

        score = max(0, min(100, score))
        status = self._score_to_status(score)
        insight = self._subjective_insight(data)
        return DomainScore("subjective", score, weight, score * weight, status, insight, True)

    def _score_nutrition(self, data: RecoveryInput) -> DomainScore:
        """Score nutrition and hydration status."""
        weight = self.DOMAIN_WEIGHTS["nutrition"]

        if data.calories_consumed is None and data.water_ml is None:
            return DomainScore("nutrition", 0, weight, 0, "no_data",
                             "Nutrition data not available", False)

        score = 60

        if data.water_ml is not None:
            if data.water_ml >= 2500:
                score += 15
            elif data.water_ml >= 1500:
                score += 5
            else:
                score -= 10

        if data.calories_consumed is not None:
            if 1500 <= data.calories_consumed <= 3000:
                score += 10
            elif data.calories_consumed < 1000:
                score -= 15
            elif data.calories_consumed > 4000:
                score -= 5

        if data.protein_g is not None:
            if data.protein_g >= 100:
                score += 5
            elif data.protein_g >= 60:
                score += 0
            else:
                score -= 5

        score = max(0, min(100, score))
        status = self._score_to_status(score)
        insight = self._nutrition_insight(data)
        return DomainScore("nutrition", score, weight, score * weight, status, insight, True)

    def _score_heart_rate(self, data: RecoveryInput) -> DomainScore:
        """Score resting heart rate and trends."""
        weight = self.DOMAIN_WEIGHTS["heart_rate"]

        if data.resting_hr is None:
            return DomainScore("heart_rate", 0, weight, 0, "no_data",
                             "Heart rate data not available", False)

        rhr = data.resting_hr
        if rhr <= 55:
            score = 95
        elif rhr <= 65:
            score = 80
        elif rhr <= 75:
            score = 60
        elif rhr <= 85:
            score = 40
        else:
            score = 20

        # Adjust for trend
        if data.resting_hr_trend == "rising":
            score -= 10
        elif data.resting_hr_trend == "falling":
            score += 5

        score = max(0, min(100, score))
        status = self._score_to_status(score)
        insight = f"Resting HR of {rhr:.0f} bpm is {'excellent' if score >= 80 else 'good' if score >= 60 else 'elevated'}."
        if data.resting_hr_trend == "rising":
            insight += " Rising trend may indicate incomplete recovery or illness."
        return DomainScore("heart_rate", score, weight, score * weight, status, insight, True)

    def _generate_cross_domain_insights(self, data: RecoveryInput, domains: list) -> list[str]:
        """Generate insights from cross-domain correlations."""
        insights = []
        available = {d.name: d for d in domains if d.data_available}

        # Sleep + Training Load
        if "sleep" in available and "training_load" in available:
            sleep_score = available["sleep"].score
            load_score = available["training_load"].score
            if sleep_score < 50 and load_score < 50:
                insights.append(
                    "Your poor sleep combined with high training load significantly increases "
                    "injury risk. Consider a rest day or very light activity."
                )
            elif sleep_score >= 70 and load_score >= 70:
                insights.append(
                    "Good sleep quality and appropriate training load — your body is "
                    "well-positioned for recovery and adaptation."
                )

        # HRV + Subjective
        if "hrv" in available and "subjective" in available:
            hrv_score = available["hrv"].score
            subj_score = available["subjective"].score
            if hrv_score < 40 and subj_score < 40:
                insights.append(
                    "Both your HRV and subjective wellness are low, suggesting "
                    "accumulated fatigue. Prioritize rest and stress management."
                )

        # Training Load + HRV
        if "training_load" in available and "hrv" in available:
            load = available["training_load"]
            hrv = available["hrv"]
            if load.score < 40 and hrv.score >= 70:
                insights.append(
                    "Despite high training load, your HRV indicates good autonomic "
                    "recovery — you may handle continued training well."
                )
            elif load.score >= 70 and hrv.score < 40:
                insights.append(
                    "Training load is high but your HRV hasn't recovered. "
                    "Reduce intensity to prevent overtraining."
                )

        # Nutrition + Training
        if "nutrition" in available and "training_load" in available:
            nut = available["nutrition"]
            if nut.score < 50 and data.training_load_today and data.training_load_today > 500:
                insights.append(
                    "High training demand with poor nutrition/hydration. "
                    "Increase calorie and protein intake to support recovery."
                )

        # Sleep + Heart Rate
        if "sleep" in available and "heart_rate" in available:
            if available["sleep"].score < 50 and data.resting_hr and data.resting_hr_trend == "rising":
                insights.append(
                    "Poor sleep and rising resting HR together may indicate "
                    "onset of illness or significant overtraining. Monitor closely."
                )

        return insights

    def _generate_recommendations(self, data: RecoveryInput, domains: list, overall: float) -> list[dict]:
        """Generate prioritized, actionable recommendations."""
        recs = []
        available = {d.name: d for d in domains if d.data_available}

        if overall < 40:
            recs.append({
                "priority": "high",
                "category": "recovery",
                "message": "Your body needs significant recovery. Consider a complete rest day with gentle stretching only.",
                "rationale": f"Overall recovery: {overall:.0f}/100. Multiple domains indicate fatigue.",
            })

        if "sleep" in available and available["sleep"].score < 50:
            recs.append({
                "priority": "high",
                "category": "sleep",
                "message": "Prioritize sleep tonight — aim for 8+ hours with consistent bedtime. Avoid screens 1 hour before bed.",
                "rationale": available["sleep"].insight,
            })

        if "training_load" in available and available["training_load"].score < 40:
            recs.append({
                "priority": "high",
                "category": "training",
                "message": "Reduce training intensity today. Focus on mobility, stretching, or light cardio instead.",
                "rationale": available["training_load"].insight,
            })

        if "hrv" in available and available["hrv"].score < 40:
            recs.append({
                "priority": "medium",
                "category": "recovery",
                "message": "Try a 10-minute breathing exercise to activate your parasympathetic nervous system and improve HRV.",
                "rationale": available["hrv"].insight,
            })

        if "nutrition" in available and available["nutrition"].score < 50:
            recs.append({
                "priority": "medium",
                "category": "nutrition",
                "message": "Focus on hydration and balanced nutrition today. Include protein with each meal.",
                "rationale": available["nutrition"].insight,
            })

        if "subjective" in available and data.fatigue_level and data.fatigue_level >= 7:
            recs.append({
                "priority": "medium",
                "category": "wellness",
                "message": "Your fatigue is high. Consider a mindfulness session or light walk in nature.",
                "rationale": available["subjective"].insight,
            })

        if overall >= 80:
            recs.append({
                "priority": "low",
                "category": "training",
                "message": "Excellent recovery! This is a great day for intense training or pushing for personal records.",
                "rationale": f"Overall recovery: {overall:.0f}/100. Your body is primed for performance.",
            })

        return recs

    def _get_training_recommendation(self, score: float, data: RecoveryInput) -> str:
        """Get specific training recommendation based on recovery score."""
        if score >= 80:
            return "HIGH INTENSITY — Great day for heavy lifting, HIIT, or competition. Your body is well-recovered."
        elif score >= 65:
            return "MODERATE INTENSITY — Good for standard training sessions. Maintain form focus and progressive overload."
        elif score >= 45:
            return "LIGHT INTENSITY — Focus on technique, mobility, and light cardio. Avoid heavy compounds or max efforts."
        elif score >= 25:
            return "ACTIVE RECOVERY — Gentle yoga, walking, or stretching only. Prioritize sleep and nutrition."
        else:
            return "REST DAY — Complete rest or very light movement only. Your body needs time to recover."

    def _sleep_insight(self, data: RecoveryInput) -> str:
        if data.sleep_hours is not None and data.sleep_hours < 6:
            return f"Sleep debt detected ({data.sleep_hours:.1f}h). This significantly impacts recovery."
        if data.sleep_hours is not None and data.sleep_hours >= 8:
            return f"Good sleep duration ({data.sleep_hours:.1f}h). Adequate rest supports recovery."
        return "Sleep data indicates moderate quality."

    def _training_insight(self, data: RecoveryInput, score: float) -> str:
        if data.acwr is not None:
            if data.acwr > 1.5:
                return f"ACWR of {data.acwr:.2f} is above safe limits. Reduce training load to prevent injury."
            elif data.acwr > 1.3:
                return f"ACWR of {data.acwr:.2f} is approaching the danger zone. Monitor closely."
            elif 0.8 <= data.acwr <= 1.3:
                return f"ACWR of {data.acwr:.2f} is in the optimal training zone."
            else:
                return f"ACWR of {data.acwr:.2f} is below optimal — consider increasing training stimulus."
        return "Training load data indicates current status."

    def _subjective_insight(self, data: RecoveryInput) -> str:
        if data.fatigue_level and data.fatigue_level >= 7:
            return f"Self-reported fatigue is high ({data.fatigue_level}/10). Listen to your body."
        if data.mood_score and data.mood_score <= 4:
            return f"Mood is low ({data.mood_score}/10). Consider stress management activities."
        if data.stress_level and data.stress_level >= 70:
            return f"Stress is elevated ({data.stress_level}/100). Breathing exercises can help."
        return "Subjective wellness indicators are within normal range."

    def _nutrition_insight(self, data: RecoveryInput) -> str:
        if data.water_ml is not None and data.water_ml < 1500:
            return f"Hydration is low ({data.water_ml}ml). Dehydration impairs recovery."
        if data.calories_consumed is not None and data.calories_consumed < 1200:
            return f"Calorie intake is low ({data.calories_consumed:.0f}kcal). Undereating delays recovery."
        return "Nutrition status is adequate for recovery."

    def _score_to_status(self, score: float) -> str:
        if score >= 80: return "excellent"
        if score >= 65: return "good"
        if score >= 45: return "fair"
        if score >= 25: return "poor"
        return "critical"

    def _domain_to_dict(self, d: DomainScore) -> dict:
        return {
            "name": d.name,
            "score": round(d.score, 1),
            "weight": d.weight,
            "weighted_score": round(d.weighted_score, 1),
            "status": d.status,
            "insight": d.insight,
            "data_available": d.data_available,
        }

    def result_to_dict(self, result: RecoveryResult) -> dict:
        return {
            "overall_score": result.overall_score,
            "recovery_level": result.recovery_level,
            "domains": [self._domain_to_dict(d) for d in result.domains],
            "cross_domain_insights": result.cross_domain_insights,
            "recommendations": result.recommendations,
            "training_recommendation": result.training_recommendation,
            "confidence": result.confidence,
            "data_completeness": result.data_completeness,
            "calculated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }


recovery_engine_v2 = RecoveryEngineV2()

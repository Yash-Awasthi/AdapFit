"""
AI Health Insights Engine — Cross-service correlation, weekly reports, anomaly detection
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid
import math


class AIInsightsEngine:
    INSIGHT_TYPES = {
        "correlation": {"icon": "🔗", "priority": 3, "description": "Cross-service metric correlations"},
        "anomaly": {"icon": "⚠️", "priority": 5, "description": "Unusual pattern detection"},
        "recommendation": {"icon": "💡", "priority": 4, "description": "Personalized health recommendations"},
        "trend": {"icon": "📈", "priority": 2, "description": "Health trend analysis"},
        "risk": {"icon": "🚨", "priority": 5, "description": "Risk factor identification"},
        "achievement": {"icon": "🏆", "priority": 1, "description": "Health achievements and milestones"},
    }

    WEEKLY_REPORT_SECTIONS = [
        "health_score_summary",
        "sleep_analysis",
        "activity_summary",
        "nutrition_overview",
        "mental_health_check",
        "stress_patterns",
        "medication_adherence",
        "community_engagement",
        "top_insights",
        "action_items",
        "goals_progress",
    ]

    def __init__(self):
        self.insights_cache: Dict[str, List[dict]] = {}
        self.weekly_reports: Dict[str, List[dict]] = {}
        self.correlations: Dict[str, dict] = {}
        self.anomalies: Dict[str, List[dict]] = {}

    def analyze_cross_service_correlations(self, user_id: str, service_data: Dict[str, Any]) -> List[dict]:
        correlations = []
        metric_sets = {}
        
        for service, data in service_data.items():
            if isinstance(data, dict):
                for metric, value in data.items():
                    if isinstance(value, (int, float)):
                        metric_sets[f"{service}.{metric}"] = value
        
        metric_list = list(metric_sets.keys())
        for i in range(len(metric_list)):
            for j in range(i + 1, len(metric_list)):
                m1, m2 = metric_list[i], metric_list[j]
                v1, v2 = metric_sets[m1], metric_sets[m2]
                
                if v1 != 0 and v2 != 0:
                    ratio = v1 / v2
                    if 0.8 <= ratio <= 1.2:
                        strength = "strong"
                    elif 0.5 <= ratio <= 2.0:
                        strength = "moderate"
                    else:
                        strength = "weak"
                    
                    correlations.append({
                        "id": str(uuid.uuid4())[:8],
                        "metric1": m1,
                        "metric2": m2,
                        "value1": v1,
                        "value2": v2,
                        "strength": strength,
                        "insight": self._generate_correlation_insight(m1, m2, v1, v2),
                        "timestamp": datetime.now().isoformat(),
                    })
        
        return sorted(correlations, key=lambda x: {"strong": 3, "moderate": 2, "weak": 1}.get(x["strength"], 0), reverse=True)[:10]

    def _generate_correlation_insight(self, m1: str, m2: str, v1: float, v2: float) -> str:
        insights = {
            "sleep.sleep_quality_vs_stress.stress_level": "Better sleep correlates with lower stress levels",
            "activity.steps_vs_sleep.sleep_quality": "More daily steps are associated with improved sleep",
            "nutrition.calories_vs_activity.steps": "Calorie intake aligns with activity level",
            "stress.stress_level_vs_mental.mood_score": "Higher stress impacts mood negatively",
            "hydration.water_intake_vs_energy.fatigue_level": "Adequate hydration reduces fatigue",
        }
        key = f"{m1}_vs_{m2}"
        return insights.get(key, f"Relationship detected between {m1.split('.')[-1]} and {m2.split('.')[-1]}")

    def detect_anomalies(self, user_id: str, metric_history: List[dict]) -> List[dict]:
        if len(metric_history) < 5:
            return []
        
        anomalies = []
        values = [h["value"] for h in metric_history if isinstance(h.get("value"), (int, float))]
        
        if not values:
            return []
        
        mean = sum(values) / len(values)
        std_dev = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values)) if len(values) > 1 else 0
        
        for entry in metric_history:
            if isinstance(entry.get("value"), (int, float)):
                z_score = (entry["value"] - mean) / max(std_dev, 0.001)
                if abs(z_score) > 2:
                    anomalies.append({
                        "id": str(uuid.uuid4())[:8],
                        "metric": entry.get("metric", "unknown"),
                        "value": entry["value"],
                        "expected_range": [round(mean - 2 * std_dev, 2), round(mean + 2 * std_dev, 2)],
                        "z_score": round(z_score, 2),
                        "severity": "high" if abs(z_score) > 3 else "moderate",
                        "timestamp": entry.get("timestamp", datetime.now().isoformat()),
                        "message": f"{entry.get('metric', 'Value')} of {entry['value']} is {'significantly above' if z_score > 0 else 'significantly below'} normal",
                    })
        
        self.anomalies[user_id] = anomalies
        return anomalies

    def generate_weekly_report(self, user_id: str, weekly_data: dict) -> dict:
        report_id = str(uuid.uuid4())
        
        health_score = weekly_data.get("health_score", 75)
        steps_avg = weekly_data.get("avg_steps", 7000)
        sleep_avg = weekly_data.get("avg_sleep_hours", 7)
        water_avg = weekly_data.get("avg_water_glasses", 6)
        mood_avg = weekly_data.get("avg_mood", 6)
        stress_avg = weekly_data.get("avg_stress", 5)
        
        report = {
            "id": report_id,
            "user_id": user_id,
            "period": {
                "start": (datetime.now() - timedelta(days=7)).isoformat(),
                "end": datetime.now().isoformat(),
            },
            "sections": {
                "health_score_summary": {
                    "title": "Health Score Summary",
                    "score": health_score,
                    "grade": "A" if health_score >= 90 else "B" if health_score >= 80 else "C" if health_score >= 70 else "D" if health_score >= 60 else "F",
                    "trend": "improving" if health_score > 70 else "needs_attention",
                    "highlights": [
                        f"Your health score is {health_score}/100",
                        f"Grade: {'A' if health_score >= 90 else 'B' if health_score >= 80 else 'C' if health_score >= 70 else 'D'}",
                    ],
                },
                "sleep_analysis": {
                    "title": "Sleep Analysis",
                    "avg_hours": sleep_avg,
                    "quality": "good" if sleep_avg >= 7 else "fair" if sleep_avg >= 6 else "poor",
                    "insights": [
                        f"Average sleep: {sleep_avg} hours/night",
                        "Consistent bedtime improves sleep quality" if sleep_avg < 7 else "Great sleep duration!",
                    ],
                    "recommendation": "Aim for 7-9 hours nightly" if sleep_avg < 7 else "Maintain your current sleep schedule",
                },
                "activity_summary": {
                    "title": "Activity Summary",
                    "avg_steps": steps_avg,
                    "goal_met": steps_avg >= 10000,
                    "insights": [
                        f"Average steps: {steps_avg:,}/day",
                        "Great activity level!" if steps_avg >= 10000 else "Try to reach 10,000 steps daily",
                    ],
                },
                "nutrition_overview": {
                    "title": "Nutrition Overview",
                    "avg_calories": weekly_data.get("avg_calories", 2000),
                    "water_intake": water_avg,
                    "insights": [
                        f"Average water intake: {water_avg} glasses/day",
                        "Hydration on track!" if water_avg >= 8 else "Try to drink more water",
                    ],
                },
                "mental_health_check": {
                    "title": "Mental Health Check",
                    "avg_mood": mood_avg,
                    "avg_stress": stress_avg,
                    "insights": [
                        f"Average mood: {mood_avg}/10",
                        f"Average stress: {stress_avg}/10",
                        "Keep up the positive mindset!" if mood_avg >= 7 else "Consider stress management techniques",
                    ],
                },
                "medication_adherence": {
                    "title": "Medication Adherence",
                    "adherence_rate": weekly_data.get("medication_adherence", 95),
                    "insights": ["Excellent medication adherence!" if weekly_data.get("medication_adherence", 95) >= 90 else "Try to improve medication consistency"],
                },
                "top_insights": {
                    "title": "Top Insights This Week",
                    "insights": self._generate_top_insights(weekly_data),
                },
                "action_items": {
                    "title": "Action Items for Next Week",
                    "items": self._generate_action_items(weekly_data),
                },
            },
            "generated_at": datetime.now().isoformat(),
        }
        
        self.weekly_reports.setdefault(user_id, []).append(report)
        return report

    def _generate_top_insights(self, data: dict) -> List[str]:
        insights = []
        if data.get("avg_steps", 0) < 5000:
            insights.append("Your daily steps are below the recommended 10,000. Try short walks after meals.")
        if data.get("avg_sleep_hours", 0) < 7:
            insights.append("Sleep duration is below optimal. Consider establishing a consistent bedtime routine.")
        if data.get("avg_water_glasses", 0) < 8:
            insights.append("Water intake is below target. Carry a water bottle as a reminder.")
        if data.get("avg_stress", 0) > 7:
            insights.append("Stress levels are elevated. Try daily meditation or breathing exercises.")
        if data.get("medication_adherence", 100) < 90:
            insights.append("Medication adherence dropped. Set reminders to stay on track.")
        if not insights:
            insights.append("Great week! Keep maintaining your healthy habits.")
        return insights[:5]

    def _generate_action_items(self, data: dict) -> List[str]:
        items = []
        if data.get("avg_steps", 0) < 8000:
            items.append("Increase daily steps by 2,000 this week")
        if data.get("avg_sleep_hours", 0) < 7:
            items.append("Set a consistent bedtime 30 minutes earlier")
        if data.get("avg_water_glasses", 0) < 8:
            items.append("Add 2 more glasses of water to your daily routine")
        if data.get("avg_stress", 0) > 6:
            items.append("Practice 5 minutes of meditation daily")
        items.append("Log at least one meal per day for better nutrition tracking")
        return items[:5]

    def get_user_insights(self, user_id: str, limit: int = 20) -> List[dict]:
        return self.insights_cache.get(user_id, [])[:limit]

    def get_latest_report(self, user_id: str) -> Optional[dict]:
        reports = self.weekly_reports.get(user_id, [])
        return reports[-1] if reports else None


ai_insights_engine = AIInsightsEngine()

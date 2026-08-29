"""
Health Recommendations V2 — AI-powered personalized health recommendations
"""
from datetime import datetime
from typing import Dict, List, Optional
import uuid


class HealthRecommendationsV2:
    RECOMMENDATION_CATEGORIES = {
        "exercise": {"icon": "💪", "color": "#4CAF50", "priority_weight": 0.25},
        "nutrition": {"icon": "🥗", "color": "#FF9800", "priority_weight": 0.20},
        "sleep": {"icon": "😴", "color": "#9C27B0", "priority_weight": 0.20},
        "mental_health": {"icon": "🧠", "color": "#2196F3", "priority_weight": 0.15},
        "hydration": {"icon": "💧", "color": "#00BCD4", "priority_weight": 0.10},
        "social": {"icon": "👥", "color": "#E91E63", "priority_weight": 0.05},
        "medical": {"icon": "🏥", "color": "#F44336", "priority_weight": 0.05},
    }

    RECOMMENDATION_DATABASE = {
        "exercise": [
            {"id": "ex1", "title": "Daily 30-Minute Walk", "description": "A 30-minute brisk walk improves cardiovascular health, mood, and energy levels", "difficulty": "beginner", "impact": "high", "evidence_level": "strong"},
            {"id": "ex2", "title": "Strength Training 2x/Week", "description": "Resistance training builds muscle mass, boosts metabolism, and strengthens bones", "difficulty": "intermediate", "impact": "high", "evidence_level": "strong"},
            {"id": "ex3", "title": "Stretching Routine", "description": "10 minutes of daily stretching improves flexibility and reduces injury risk", "difficulty": "beginner", "impact": "moderate", "evidence_level": "strong"},
            {"id": "ex4", "title": "HIIT Workout", "description": "20-minute high-intensity interval training for maximum calorie burn", "difficulty": "advanced", "impact": "high", "evidence_level": "strong"},
            {"id": "ex5", "title": "Yoga Practice", "description": "30 minutes of yoga for flexibility, balance, and stress reduction", "difficulty": "beginner", "impact": "moderate", "evidence_level": "moderate"},
        ],
        "nutrition": [
            {"id": "nu1", "title": "Eat 5 Servings of Fruits/Vegetables", "description": "Aim for at least 5 servings of colorful fruits and vegetables daily", "difficulty": "beginner", "impact": "high", "evidence_level": "strong"},
            {"id": "nu2", "title": "Increase Fiber Intake", "description": "25-30g of fiber daily for digestive health and blood sugar control", "difficulty": "beginner", "impact": "high", "evidence_level": "strong"},
            {"id": "nu3", "title": "Reduce Processed Foods", "description": "Limit processed foods, added sugars, and trans fats", "difficulty": "intermediate", "impact": "high", "evidence_level": "strong"},
            {"id": "nu4", "title": "Meal Prep Sundays", "description": "Prepare healthy meals in advance to avoid unhealthy choices during the week", "difficulty": "intermediate", "impact": "moderate", "evidence_level": "moderate"},
            {"id": "nu5", "title": "Mindful Eating Practice", "description": "Eat slowly, chew thoroughly, and pay attention to hunger/fullness cues", "difficulty": "beginner", "impact": "moderate", "evidence_level": "moderate"},
        ],
        "sleep": [
            {"id": "sl1", "title": "Consistent Sleep Schedule", "description": "Go to bed and wake up at the same time every day, even weekends", "difficulty": "beginner", "impact": "high", "evidence_level": "strong"},
            {"id": "sl2", "title": "Screen-Free Wind Down", "description": "No screens 1 hour before bed — read, meditate, or take a warm bath", "difficulty": "beginner", "impact": "high", "evidence_level": "strong"},
            {"id": "sl3", "title": "Optimize Sleep Environment", "description": "Keep bedroom cool (65-68°F), dark, and quiet", "difficulty": "beginner", "impact": "high", "evidence_level": "strong"},
            {"id": "sl4", "title": "Limit Caffeine After 2 PM", "description": "Avoid caffeine 6+ hours before bedtime for better sleep quality", "difficulty": "beginner", "impact": "moderate", "evidence_level": "strong"},
            {"id": "sl5", "title": "Relaxation Before Bed", "description": "Practice deep breathing or progressive muscle relaxation before sleep", "difficulty": "beginner", "impact": "moderate", "evidence_level": "moderate"},
        ],
        "mental_health": [
            {"id": "mh1", "title": "Daily Gratitude Practice", "description": "Write 3 things you're grateful for each day to boost mood", "difficulty": "beginner", "impact": "high", "evidence_level": "strong"},
            {"id": "mh2", "title": "5-Minute Meditation", "description": "Daily mindfulness meditation reduces stress and improves focus", "difficulty": "beginner", "impact": "high", "evidence_level": "strong"},
            {"id": "mh3", "title": "Social Connection", "description": "Reach out to a friend or family member daily for emotional support", "difficulty": "beginner", "impact": "high", "evidence_level": "strong"},
            {"id": "mh4", "title": "Digital Detox Hour", "description": "Take 1 hour daily away from all screens for mental clarity", "difficulty": "intermediate", "impact": "moderate", "evidence_level": "moderate"},
            {"id": "mh5", "title": "Journaling", "description": "Spend 10 minutes writing about your thoughts and feelings", "difficulty": "beginner", "impact": "moderate", "evidence_level": "moderate"},
        ],
        "hydration": [
            {"id": "hy1", "title": "Drink 8 Glasses of Water Daily", "description": "Aim for at least 64 oz of water throughout the day", "difficulty": "beginner", "impact": "high", "evidence_level": "strong"},
            {"id": "hy2", "title": "Morning Hydration Ritual", "description": "Start each day with a glass of water to rehydrate after sleep", "difficulty": "beginner", "impact": "moderate", "evidence_level": "strong"},
            {"id": "hy3", "title": "Carry a Water Bottle", "description": "Keep a reusable water bottle with you as a reminder to drink", "difficulty": "beginner", "impact": "moderate", "evidence_level": "moderate"},
        ],
    }

    def __init__(self):
        self.user_recommendations: Dict[str, List[dict]] = {}
        self.user_feedback: Dict[str, List[dict]] = {}
        self.dismissed: Dict[str, List[str]] = {}

    def get_recommendations(self, user_id: str, health_data: dict = None, count: int = 5) -> List[dict]:
        data = health_data or {}
        recommendations = []
        
        if data.get("steps", 0) < 5000:
            recommendations.extend(self.RECOMMENDATION_DATABASE["exercise"][:2])
        if data.get("sleep_quality", 10) < 7:
            recommendations.extend(self.RECOMMENDATION_DATABASE["sleep"][:2])
        if data.get("stress_level", 0) > 6:
            recommendations.extend(self.RECOMMENDATION_DATABASE["mental_health"][:2])
        if data.get("water_intake", 8) < 6:
            recommendations.extend(self.RECOMMENDATION_DATABASE["hydration"][:1])
        if data.get("fruit_veggie_servings", 5) < 3:
            recommendations.extend(self.RECOMMENDATION_DATABASE["nutrition"][:2])
        
        if not recommendations:
            for cat in self.RECOMMENDATION_DATABASE:
                recommendations.append(self.RECOMMENDATION_DATABASE[cat][0])
        
        dismissed_ids = set(self.dismissed.get(user_id, []))
        recommendations = [r for r in recommendations if r["id"] not in dismissed_ids]
        
        seen_ids = set()
        unique_recs = []
        for r in recommendations:
            if r["id"] not in seen_ids:
                seen_ids.add(r["id"])
                unique_recs.append(r)
        
        result = unique_recs[:count]
        self.user_recommendations[user_id] = result
        return result

    def dismiss_recommendation(self, user_id: str, recommendation_id: str) -> dict:
        self.dismissed.setdefault(user_id, []).append(recommendation_id)
        return {"dismissed": recommendation_id}

    def provide_feedback(self, user_id: str, recommendation_id: str, helpful: bool, notes: str = "") -> dict:
        feedback = {"id": str(uuid.uuid4()), "recommendation_id": recommendation_id, "helpful": helpful, "notes": notes, "timestamp": datetime.now().isoformat()}
        self.user_feedback.setdefault(user_id, []).append(feedback)
        return feedback

    def get_recommendation_stats(self, user_id: str) -> dict:
        recs = self.user_recommendations.get(user_id, [])
        feedback = self.user_feedback.get(user_id, [])
        helpful = sum(1 for f in feedback if f["helpful"])
        return {"total_recommended": len(recs), "total_feedback": len(feedback), "helpful_count": helpful, "helpful_rate": round(helpful / max(len(feedback), 1) * 100, 1), "dismissed_count": len(self.dismissed.get(user_id, []))}


health_recommendations_v2 = HealthRecommendationsV2()

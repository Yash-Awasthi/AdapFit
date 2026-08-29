"""
Personalization Engine — AI-Driven Hyper-Personalization

Features:
- User preference learning from behavior patterns
- Adaptive content recommendations
- Workout personalization based on progress
- Schedule optimization based on energy patterns
- Health goal tracking with adaptive milestones
- Behavioral pattern recognition
- Notification timing optimization
- Cross-feature correlation insights

Inspired by: Spotify Discover, YouTube recommendations, Samsung Health AI
"""
import time
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class PreferenceWeight(Enum):
    STRONG_POSITIVE = 2.0
    POSITIVE = 1.0
    NEUTRAL = 0.0
    NEGATIVE = -1.0
    STRONG_NEGATIVE = -2.0


@dataclass
class UserPreference:
    category: str
    item: str
    weight: float
    source: str  # "explicit", "behavioral", "inferred"
    confidence: float
    last_updated: float = field(default_factory=time.time)


@dataclass
class UserProfile:
    user_id: str
    fitness_level: str
    goals: list[str]
    preferred_workout_time: str
    preferred_workout_duration: int  # minutes
    equipment_available: list[str]
    health_conditions: list[str]
    stress_sensitivity: float
    sleep_quality_avg: float
    activity_level: str  # "sedentary", "light", "moderate", "active", "very_active"
    content_preferences: dict[str, float]
    notification_preference: str  # "minimal", "moderate", "frequent"


@dataclass
class PersonalizedInsight:
    category: str
    title: str
    detail: str
    confidence: float
    action: str
    priority: str  # "high", "medium", "low"


class PersonalizationEngine:
    """
    AI-driven personalization system that learns from user behavior
    to provide increasingly accurate recommendations across all features.
    
    Uses:
    - Explicit feedback (likes, ratings, bookmarks)
    - Behavioral signals (view time, completion rates, usage patterns)
    - Physiological data (HRV, sleep, activity correlations)
    - Temporal patterns (time-of-day preferences, weekly rhythms)
    """

    def __init__(self):
        self._user_profiles: dict[str, UserProfile] = {}
        self._preferences: dict[str, list[UserPreference]] = {}
        self._behavior_log: dict[str, list[dict]] = {}
        self._insight_cache: dict[str, list[PersonalizedInsight]] = {}

    def create_or_update_profile(self, user_id: str, data: dict) -> dict:
        """Create or update user profile with new data."""
        if user_id in self._user_profiles:
            p = self._user_profiles[user_id]
            for key, value in data.items():
                if hasattr(p, key):
                    setattr(p, key, value)
        else:
            self._user_profiles[user_id] = UserProfile(
                user_id=user_id,
                fitness_level=data.get("fitness_level", "beginner"),
                goals=data.get("goals", ["general_fitness"]),
                preferred_workout_time=data.get("preferred_workout_time", "morning"),
                preferred_workout_duration=data.get("preferred_workout_duration", 45),
                equipment_available=data.get("equipment_available", []),
                health_conditions=data.get("health_conditions", []),
                stress_sensitivity=data.get("stress_sensitivity", 1.0),
                sleep_quality_avg=data.get("sleep_quality_avg", 70),
                activity_level=data.get("activity_level", "moderate"),
                content_preferences={},
                notification_preference=data.get("notification_preference", "moderate"),
            )
        
        return {"updated": True, "user_id": user_id}

    def record_behavior(self, user_id: str, event_type: str, data: dict) -> dict:
        """Record a user behavior event for learning."""
        if user_id not in self._behavior_log:
            self._behavior_log[user_id] = []
        
        self._behavior_log[user_id].append({
            "event_type": event_type,
            "data": data,
            "timestamp": time.time(),
            "hour_of_day": time.localtime().tm_hour,
            "day_of_week": time.localtime().tm_wday,
        })
        
        # Update preferences based on behavior
        self._update_preferences_from_behavior(user_id, event_type, data)
        
        return {"recorded": True, "total_events": len(self._behavior_log[user_id])}

    def get_personalized_recommendations(self, user_id: str, context: dict = None) -> dict:
        """Get comprehensive personalized recommendations."""
        profile = self._user_profiles.get(user_id)
        if not profile:
            return self._get_default_recommendations()
        
        context = context or {}
        current_hour = context.get("hour_of_day", time.localtime().tm_hour)
        current_stress = context.get("stress_level", 50)
        sleep_quality = context.get("sleep_quality", 70)
        
        recommendations = {
            "workout": self._recommend_workout(profile, current_hour, current_stress, sleep_quality),
            "content": self._recommend_content(profile),
            "schedule": self._recommend_schedule(profile),
            "nutrition": self._recommend_nutrition(profile, current_hour),
            "recovery": self._recommend_recovery(profile, sleep_quality, current_stress),
            "notification_timing": self._recommend_notification_timing(user_id),
        }
        
        return recommendations

    def get_optimal_workout_time(self, user_id: str) -> dict:
        """Determine the best time for user to work out."""
        profile = self._user_profiles.get(user_id)
        behaviors = self._behavior_log.get(user_id, [])
        
        # Analyze historical workout performance by hour
        hour_performance = {}
        for event in behaviors:
            if event["event_type"] == "workout_completed":
                hour = event["hour_of_day"]
                quality = event["data"].get("quality_score", 5)
                if hour not in hour_performance:
                    hour_performance[hour] = []
                hour_performance[hour].append(quality)
        
        if hour_performance:
            best_hour = max(hour_performance, key=lambda h: sum(hour_performance[h]) / len(hour_performance[h]))
        else:
            # Default based on stated preference
            time_map = {"morning": 7, "afternoon": 14, "evening": 19, "night": 21}
            best_hour = time_map.get(profile.preferred_workout_time if profile else "morning", 7)
        
        return {
            "optimal_hour": best_hour,
            "optimal_time": f"{best_hour:02d}:00",
            "confidence": min(0.9, len(behaviors) / 30),
            "reasoning": "Based on your historical workout performance patterns",
            "alternatives": [best_hour - 1, best_hour + 1, best_hour + 2],
        }

    def get_notification_optimization(self, user_id: str) -> dict:
        """Optimize notification timing for maximum engagement."""
        behaviors = self._behavior_log.get(user_id, [])
        
        # Find hours when user engages most
        hour_engagement = {}
        for event in behaviors:
            if event["event_type"] in ("notification_opened", "app_opened"):
                hour = event["hour_of_day"]
                hour_engagement[hour] = hour_engagement.get(hour, 0) + 1
        
        # Find top 3 engagement hours
        sorted_hours = sorted(hour_engagement.items(), key=lambda x: x[1], reverse=True)[:3]
        optimal_hours = [h[0] for h in sorted_hours] if sorted_hours else [8, 12, 18]
        
        profile = self._user_profiles.get(user_id)
        freq = profile.notification_preference if profile else "moderate"
        
        return {
            "optimal_send_hours": sorted(optimal_hours),
            "frequency": freq,
            "quiet_hours_start": 22,
            "quiet_hours_end": 7,
            "batch_notifications": freq == "minimal",
            "daily_notification_limit": {"minimal": 3, "moderate": 6, "frequent": 12}.get(freq, 6),
        }

    def get_cross_feature_insights(self, user_id: str) -> list[PersonalizedInsight]:
        """Generate insights from cross-feature data correlation."""
        profile = self._user_profiles.get(user_id)
        if not profile:
            return []
        
        insights = []
        
        # Sleep ↔ Performance correlation
        if profile.sleep_quality_avg < 60:
            insights.append(PersonalizedInsight(
                category="sleep_performance",
                title="Sleep Quality Impacting Performance",
                detail=f"Your avg sleep quality ({profile.sleep_quality_avg:.0f}%) is below optimal. Users with >75% sleep quality see 23% better workout performance.",
                confidence=0.85,
                action="Try the Sleep Education content in the Content Hub. Use the screen time tracker to reduce pre-bed phone use.",
                priority="high",
            ))
        
        # Stress ↔ Recovery correlation
        if profile.stress_sensitivity > 1.2:
            insights.append(PersonalizedInsight(
                category="stress_recovery",
                title="High Stress Sensitivity Detected",
                detail="Your stress response is above average. Consider adding daily breathing exercises and checking the Stress Manager regularly.",
                confidence=0.8,
                action="Use the Stress Manager before workouts for better performance.",
                priority="medium",
            ))
        
        # Activity level recommendations
        if profile.activity_level == "sedentary":
            insights.append(PersonalizedInsight(
                category="activity",
                title="Increase Daily Movement",
                detail="Being sedentary for extended periods increases health risk. Even 30 minutes of walking makes a significant difference.",
                confidence=0.95,
                action="Set a goal to walk 7,000 steps daily. Use the Walk Tracker to monitor progress.",
                priority="high",
            ))
        
        # Content engagement insights
        preferences = self._preferences.get(user_id, [])
        if preferences:
            top_prefs = sorted(preferences, key=lambda p: p.weight, reverse=True)[:3]
            insights.append(PersonalizedInsight(
                category="content",
                title="Your Top Interests",
                detail=f"You engage most with: {', '.join(p.item for p in top_prefs)}",
                confidence=0.7,
                action="We'll prioritize similar content in your feed.",
                priority="low",
            ))
        
        # Goal progress insights
        for goal in profile.goals:
            if goal == "weight_loss":
                insights.append(PersonalizedInsight(
                    category="goal_progress",
                    title="Weight Loss Strategy",
                    detail="Combining cardio, strength training, and nutrition tracking gives the best results for weight loss.",
                    confidence=0.9,
                    action="Check the Content Hub for nutrition tips and cardio workout tutorials.",
                    priority="medium",
                ))
        
        self._insight_cache[user_id] = insights
        return insights

    def get_user_analytics(self, user_id: str) -> dict:
        """Get comprehensive user analytics and patterns."""
        profile = self._user_profiles.get(user_id)
        behaviors = self._behavior_log.get(user_id, [])
        
        if not behaviors:
            return {"message": "Not enough data yet. Keep using the app to see your analytics!"}
        
        # Time patterns
        active_hours = {}
        for event in behaviors:
            hour = event["hour_of_day"]
            active_hours[hour] = active_hours.get(hour, 0) + 1
        
        peak_hour = max(active_hours, key=active_hours.get) if active_hours else 12
        
        # Feature usage
        feature_usage = {}
        for event in behaviors:
            feat = event["data"].get("feature", "unknown")
            feature_usage[feat] = feature_usage.get(feat, 0) + 1
        
        return {
            "total_events": len(behaviors),
            "peak_activity_hour": peak_hour,
            "active_hours_distribution": active_hours,
            "feature_usage": feature_usage,
            "most_used_feature": max(feature_usage, key=feature_usage.get) if feature_usage else "none",
            "engagement_score": min(100, len(behaviors) * 2),
            "personalization_confidence": min(0.95, len(behaviors) / 50),
        }

    # === Private helpers ===

    def _update_preferences_from_behavior(self, user_id: str, event_type: str, data: dict):
        """Update user preferences based on observed behavior."""
        if user_id not in self._preferences:
            self._preferences[user_id] = []
        
        if event_type in ("content_viewed", "content_liked", "content_bookmarked"):
            category = data.get("category", "unknown")
            weight = 1.0 if event_type == "content_liked" else 0.5 if event_type == "content_bookmarked" else 0.2
            
            existing = next((p for p in self._preferences[user_id] if p.item == category), None)
            if existing:
                existing.weight = (existing.weight + weight) / 2
                existing.confidence = min(0.95, existing.confidence + 0.05)
                existing.last_updated = time.time()
            else:
                self._preferences[user_id].append(UserPreference(
                    category="content",
                    item=category,
                    weight=weight,
                    source="behavioral",
                    confidence=0.3,
                ))
        
        elif event_type == "workout_completed":
            workout_type = data.get("workout_type", "unknown")
            quality = data.get("quality_score", 5)
            weight = quality / 5.0
            
            existing = next((p for p in self._preferences[user_id] if p.item == workout_type), None)
            if existing:
                existing.weight = (existing.weight + weight) / 2
                existing.confidence = min(0.95, existing.confidence + 0.08)
            else:
                self._preferences[user_id].append(UserPreference(
                    category="workout",
                    item=workout_type,
                    weight=weight,
                    source="behavioral",
                    confidence=0.2,
                ))

    def _recommend_workout(self, profile: UserProfile, hour: int, stress: float, sleep: float) -> dict:
        """Recommend workout type based on current state."""
        readiness = (sleep / 100) * 0.4 + ((100 - stress) / 100) * 0.4 + 0.2
        
        if readiness > 0.7:
            workout_type = "high_intensity"
            duration = min(profile.preferred_workout_duration + 10, 60)
            message = "Great readiness! Perfect for high-intensity training."
        elif readiness > 0.4:
            workout_type = "moderate"
            duration = profile.preferred_workout_duration
            message = "Moderate readiness. Moderate intensity recommended."
        else:
            workout_type = "low_intensity"
            duration = min(profile.preferred_workout_duration, 30)
            message = "Lower readiness today. Focus on mobility and light cardio."
        
        return {
            "type": workout_type,
            "duration_minutes": duration,
            "intensity": "high" if readiness > 0.7 else "moderate" if readiness > 0.4 else "low",
            "readiness_score": round(readiness * 100),
            "message": message,
            "focus_areas": profile.goals[:3],
        }

    def _recommend_content(self, profile: UserProfile) -> dict:
        top_goals = profile.goals[:2]
        return {
            "primary_categories": top_goals,
            "difficulty": profile.fitness_level,
            "message": f"Showing content for {', '.join(top_goals)} at {profile.fitness_level} level",
        }

    def _recommend_schedule(self, profile: UserProfile) -> dict:
        return {
            "preferred_time": profile.preferred_workout_time,
            "suggested_rest_days": 2 if profile.fitness_level == "beginner" else 1,
            "message": "Schedule based on your preferred workout time",
        }

    def _recommend_nutrition(self, profile: UserProfile, hour: int) -> dict:
        if 6 <= hour <= 10:
            return {"meal": "breakdown", "message": "Time for a protein-rich breakfast"}
        elif 12 <= hour <= 14:
            return {"meal": "lunch", "message": "Balanced lunch with lean protein and complex carbs"}
        elif 17 <= hour <= 19:
            return {"meal": "dinner", "message": "Light dinner with protein and vegetables"}
        return {"meal": "snack", "message": "Stay hydrated and consider a healthy snack"}

    def _recommend_recovery(self, profile: UserProfile, sleep: float, stress: float) -> dict:
        if sleep < 60 or stress > 70:
            return {"priority": "high", "activities": ["meditation", "stretching", "early bedtime"], "message": "Recovery is a priority today"}
        return {"priority": "normal", "activities": ["light stretching"], "message": "Keep up your recovery routine"}

    def _recommend_notification_timing(self, user_id: str) -> dict:
        return {"optimal_hours": [8, 12, 18], "quiet_hours": [22, 7]}

    def _get_default_recommendations(self) -> dict:
        return {
            "workout": {"type": "moderate", "duration_minutes": 45, "message": "Complete your profile for personalized recommendations"},
            "content": {"primary_categories": ["general_fitness"], "message": "Explore the Content Hub to build your profile"},
            "schedule": {"message": "Set your preferred workout time in settings"},
            "nutrition": {"message": "Log your meals for personalized nutrition tips"},
            "recovery": {"message": "Track your sleep for recovery insights"},
        }


# Singleton
personalization_engine = PersonalizationEngine()

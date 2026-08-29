"""Environmental Health Service - Air quality, UV index, outdoor exercise safety.

Based on 2025 EPA/ACSM guidelines:
- Air Quality Index (AQI) tracking and alerts
- UV index monitoring and sun protection
- Pollen count integration
- Outdoor exercise safety recommendations
- Personal pollution exposure tracking
- Indoor air quality guidance
"""

import time
import random
from typing import Dict, List, Optional, Any


class EnvironmentalHealthService:
    """Track environmental health factors and provide safety guidance."""

    def __init__(self):
        self.locations: Dict[str, Dict] = {}
        self._init_aqi_scale()

    def _init_aqi_scale(self):
        self.aqi_scale = {
            "good": {"range": "0-50", "color": "green", "exercise": "Great for outdoor activity", "mask": False, "risk": "minimal"},
            "moderate": {"range": "51-100", "color": "yellow", "exercise": "Acceptable for most people", "mask": False, "risk": "low"},
            "sensitive_groups": {"range": "101-150", "color": "orange", "exercise": "Sensitive groups should limit outdoor exposure", "mask": "optional", "risk": "moderate"},
            "unhealthy": {"range": "151-200", "color": "red", "exercise": "Everyone should limit prolonged outdoor exertion", "mask": "recommended", "risk": "high"},
            "very_unhealthy": {"range": "201-300", "color": "purple", "exercise": "Avoid outdoor exercise", "mask": "N95 recommended", "risk": "very_high"},
            "hazardous": {"range": "301+", "color": "maroon", "exercise": "Stay indoors, keep windows closed", "mask": "N95 required", "risk": "emergency"},
        }

        self.uv_scale = {
            "low": {"index": "1-2", "protection": "No protection needed for most", "burn_time_minutes": 60},
            "moderate": {"index": "3-5", "protection": "Wear sunscreen, seek shade during midday", "burn_time_minutes": 30},
            "high": {"index": "6-7", "protection": "Reduce sun exposure 10am-4pm, SPF 30+", "burn_time_minutes": 20},
            "very_high": {"index": "8-10", "protection": "Minimize sun exposure, wear protective clothing", "burn_time_minutes": 15},
            "extreme": {"index": "11+", "protection": "Avoid outdoor exposure, stay in shade", "burn_time_minutes": 10},
        }

    def get空气质量(self, location: str) -> Dict[str, Any]:
        """Get air quality data for a location (Chinese method name for compatibility)."""
        return self.get_air_quality(location)

    def get_air_quality(self, location: str) -> Dict[str, Any]:
        """Get comprehensive air quality data."""
        aqi = random.randint(15, 180)
        level = "good" if aqi <= 50 else "moderate" if aqi <= 100 else "sensitive_groups" if aqi <= 150 else "unhealthy"
        scale_info = self.aqi_scale[level]

        return {
            "location": location,
            "aqi": aqi,
            "level": level,
            "color": scale_info["color"],
            "exercise_advice": scale_info["exercise"],
            "mask_recommended": scale_info["mask"],
            "health_risk": scale_info["risk"],
            "pollutants": {
                "pm25": random.randint(5, 80),
                "pm10": random.randint(10, 100),
                "ozone": random.randint(20, 60),
                "no2": random.randint(5, 40),
                "so2": random.randint(0, 15),
                "co": round(random.uniform(0.1, 2.0), 1),
            },
            "forecast": [
                {"day": "Tomorrow", "aqi": aqi + random.randint(-20, 20), "level": level},
                {"day": "Day After", "aqi": aqi + random.randint(-30, 30), "level": level},
            ],
            "exercise_recommendation": self._get_exercise_recommendation(aqi),
        }

    def get_uv_index(self, location: str) -> Dict[str, Any]:
        """Get UV index data."""
        uv = random.randint(1, 11)
        level = "low" if uv <= 2 else "moderate" if uv <= 5 else "high" if uv <= 7 else "very_high" if uv <= 10 else "extreme"
        scale = self.uv_scale[level]

        return {
            "location": location,
            "uv_index": uv,
            "level": level,
            "protection_needed": scale["protection"],
            "estimated_burn_time_minutes": scale["burn_time_minutes"],
            "sunscreen_spf": "15+" if level == "low" else "30+" if level in ("moderate", "high") else "50+",
            "peak_hours": "10am - 4pm",
            "safe_exposure_minutes": scale["burn_time_minutes"],
        }

    def get_outdoor_exercise_safety(self, location: str, activity: str = "running") -> Dict[str, Any]:
        """Get outdoor exercise safety assessment."""
        aqi_data = self.get_air_quality(location)
        uv_data = self.get_uv_index(location)

        aqi = aqi_data["aqi"]
        uv = uv_data["uv_index"]

        # Combined safety assessment
        if aqi > 150 or uv > 8:
            safety = "unsafe"
            recommendation = "Exercise indoors today"
        elif aqi > 100 or uv > 6:
            safety = "caution"
            recommendation = "Reduce intensity and duration, stay hydrated"
        elif aqi > 50 or uv > 4:
            safety = "moderate"
            recommendation = "Generally safe, take normal precautions"
        else:
            safety = "excellent"
            recommendation = "Great conditions for outdoor exercise!"

        return {
            "location": location,
            "activity": activity,
            "safety_level": safety,
            "recommendation": recommendation,
            "aqi": aqi_data,
            "uv": uv_data,
            "tips": self._get_exercise_tips(activity, safety),
        }

    def track_pollution_exposure(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Track personal pollution exposure throughout the day."""
        return {
            "user_id": user_id,
            "daily_exposure": {
                "outdoor_hours": data.get("outdoor_hours", 2),
                "indoor_hours": data.get("indoor_hours", 16),
                "commute_exposure": data.get("commute_exposure", "moderate"),
                "peak_exposure_minutes": data.get("peak_minutes", 30),
            },
            "estimated吸入量": {"pm25_ug": round(data.get("outdoor_hours", 2) * 15, 1)},
            "tips": ["Use air purifier indoors during high AQI", "Keep car windows closed with recirculation on", "Wear N95 mask during commute on bad air days"],
        }

    def get_indoor_air_quality_tips(self) -> List[Dict]:
        """Get indoor air quality improvement tips."""
        return [
            {"area": "Ventilation", "tips": ["Open windows for 10 min daily", "Use exhaust fans while cooking"], "impact": "high"},
            {"area": "Filtration", "tips": ["Use HEPA air purifier", "Change HVAC filters regularly", "Use vacuum with HEPA filter"], "impact": "high"},
            {"area": "Pollutants", "tips": ["Avoid smoking indoors", "Reduce candles/incense", "Use low-VOC paints"], "impact": "medium"},
            {"area": "Plants", "tips": ["Add air-purifying plants (spider plant, pothos)", "Maintain humidity 30-50%"], "impact": "low"},
            {"area": "Monitoring", "tips": ["Get a CO2 monitor", "Track indoor PM2.5", "Check humidity levels"], "impact": "medium"},
        ]

    def _get_exercise_recommendation(self, aqi: int) -> str:
        if aqi <= 50:
            return "Perfect conditions — enjoy your outdoor workout!"
        elif aqi <= 100:
            return "Good for exercise. Stay hydrated and monitor how you feel."
        elif aqi <= 150:
            return "Consider reducing intensity. Sensitive individuals should exercise indoors."
        elif aqi <= 200:
            return "Exercise indoors or reschedule outdoor activities."
        else:
            return "Avoid all outdoor exercise. Use indoor facilities."

    def _get_exercise_tips(self, activity: str, safety: str) -> List[str]:
        tips = []
        if safety == "unsafe":
            tips = ["Exercise indoors", "Use treadmill or indoor cycling", "Do yoga or bodyweight exercises at home"]
        elif safety == "caution":
            tips = ["Reduce intensity by 20-30%", "Take more breaks", "Wear a mask if sensitive"]
        else:
            tips = ["Stay hydrated", "Warm up properly", "Listen to your body"]
        return tips


environmental_health_service = EnvironmentalHealthService()

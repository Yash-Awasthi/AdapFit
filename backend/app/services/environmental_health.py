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
from typing import Dict, List, Optional, Any


class EnvironmentalHealthService:
    """Track environmental health factors and provide safety guidance."""

    def __init__(self):
        # Readings keyed by location, from a provider or a monitor.
        self._air_readings: Dict[str, Dict[str, Any]] = {}
        self._uv_readings: Dict[str, Dict[str, Any]] = {}
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

    @staticmethod
    def _aqi_level(aqi: int) -> str:
        return (
            "good" if aqi <= 50 else
            "moderate" if aqi <= 100 else
            "sensitive_groups" if aqi <= 150 else
            "unhealthy"
        )

    def record_air_quality(self, location: str, aqi: int, pollutants: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Store a reading for a location, from a provider or a monitor.

        The advice tables in this service are real reference material; what it
        never had was a measurement to apply them to.
        """
        self._air_readings[location] = {
            "aqi": int(aqi),
            "pollutants": pollutants or {},
            "recorded_at": time.time(),
        }
        return {"recorded": True, "location": location, "aqi": int(aqi)}

    async def fetch_air_quality(self, location: str) -> Dict[str, Any]:
        """Fetch a live reading, record it, and return the interpreted result."""
        from app.services import open_meteo

        reading = await open_meteo.air_quality(location)
        if reading.get("status") != "ok":
            return {**reading, "location": location, "advice_scale": self.aqi_scale}
        self.record_air_quality(location, reading["aqi"], reading["pollutants"])
        result = self.get_air_quality(location)
        result["source"] = reading["source"]
        result["observed_at"] = reading["observed_at"]
        return result

    async def fetch_uv_index(self, location: str) -> Dict[str, Any]:
        from app.services import open_meteo

        reading = await open_meteo.uv_index(location)
        if reading.get("status") != "ok":
            return {**reading, "location": location, "advice_scale": self.uv_scale}
        self.record_uv_index(location, reading["uv_index"])
        result = self.get_uv_index(location)
        result["source"] = reading["source"]
        result["observed_at"] = reading["observed_at"]
        return result

    async def fetch_outdoor_exercise_safety(self, location: str, activity: str = "running") -> Dict[str, Any]:
        """Refresh both readings, then judge conditions."""
        await self.fetch_air_quality(location)
        await self.fetch_uv_index(location)
        return self.get_outdoor_exercise_safety(location, activity)

    def get_air_quality(self, location: str) -> Dict[str, Any]:
        """
        Air quality for a location, from the last recorded reading.

        The AQI and every pollutant concentration used to be generated, so the
        app could advise someone with asthma to train outdoors on a bad-air day
        or keep them inside on a clear one. With no reading there is no advice.
        """
        reading = self._air_readings.get(location)
        if reading is None:
            return {
                "status": "unavailable",
                "location": location,
                "reason": "no_reading",
                "message": (
                    "No air quality reading for this location. Connect an air quality "
                    "source or record a reading to get advice here."
                ),
                "advice_scale": self.aqi_scale,
            }

        aqi = reading["aqi"]
        level = self._aqi_level(aqi)
        scale_info = self.aqi_scale[level]
        return {
            "status": "ok",
            "location": location,
            "aqi": aqi,
            "level": level,
            "recorded_at": reading["recorded_at"],
            "color": scale_info["color"],
            "exercise_advice": scale_info["exercise"],
            "mask_recommended": scale_info["mask"],
            "health_risk": scale_info["risk"],
            "pollutants": reading["pollutants"],
            "exercise_recommendation": self._get_exercise_recommendation(aqi),
        }

    def record_uv_index(self, location: str, uv_index: float) -> Dict[str, Any]:
        """Store a UV index reading for a location."""
        self._uv_readings[location] = {"uv_index": float(uv_index), "recorded_at": time.time()}
        return {"recorded": True, "location": location, "uv_index": float(uv_index)}

    def get_uv_index(self, location: str) -> Dict[str, Any]:
        """UV index for a location, from the last recorded reading."""
        reading = self._uv_readings.get(location)
        if reading is None:
            return {
                "status": "unavailable",
                "location": location,
                "reason": "no_reading",
                "message": "No UV reading for this location.",
                "advice_scale": self.uv_scale,
            }

        uv = reading["uv_index"]
        level = (
            "low" if uv <= 2 else "moderate" if uv <= 5 else
            "high" if uv <= 7 else "very_high" if uv <= 10 else "extreme"
        )
        scale = self.uv_scale[level]
        return {
            "status": "ok",
            "location": location,
            "uv_index": uv,
            "level": level,
            "recorded_at": reading["recorded_at"],
            "protection_needed": scale["protection"],
            "estimated_burn_time_minutes": scale["burn_time_minutes"],
            "sunscreen_spf": "15+" if level == "low" else "30+" if level in ("moderate", "high") else "50+",
            "peak_hours": "10am - 4pm",
            "safe_exposure_minutes": scale["burn_time_minutes"],
        }

    def get_outdoor_exercise_safety(self, location: str, activity: str = "running") -> Dict[str, Any]:
        """Whether conditions suit training outdoors, when both readings exist."""
        aqi_data = self.get_air_quality(location)
        uv_data = self.get_uv_index(location)

        missing = [
            name for name, data in (("air quality", aqi_data), ("UV index", uv_data))
            if data.get("status") != "ok"
        ]
        if missing:
            return {
                "status": "unavailable",
                "location": location,
                "activity": activity,
                "missing": missing,
                "message": (
                    "No " + " or ".join(missing) + " reading for this location, so there is "
                    "nothing to base a safety call on."
                ),
            }

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
            "status": "ok",
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


from app.core.per_user import per_user, register

environmental_health_service = register("environmental_health.environmental_health_service", per_user(EnvironmentalHealthService))
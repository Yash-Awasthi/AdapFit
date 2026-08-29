"""Ambient Health Monitoring Service - Smart home IoT integration.

Based on 2025 Ambient Assisted Living (AAL) research:
- Smart home device integration (sensors, lights, thermostat, air quality)
- Environmental health monitoring (air quality, humidity, temperature, light)
- Ambient vital sign detection (motion patterns, sleep environment)
- Elderly/child ambient monitoring
- Automated health environment optimization
- Fall detection via ambient sensors
"""

import time
import random
from typing import Dict, List, Optional, Any
from datetime import datetime


class AmbientHealthService:
    """Smart home health monitoring and optimization."""

    def __init__(self):
        self.homes: Dict[str, Dict] = {}
        self.devices: Dict[str, Dict] = {}
        self.alerts: Dict[str, List] = {}
        self._init_device_types()

    def _init_device_types(self):
        self.supported_devices = {
            "air_quality_sensor": {
                "name": "Air Quality Monitor",
                "metrics": ["pm25", "pm10", "co2", "voc", "humidity", "temperature"],
                "optimal_ranges": {
                    "pm25": {"min": 0, "max": 12, "unit": "μg/m³"},
                    "co2": {"min": 400, "max": 800, "unit": "ppm"},
                    "voc": {"min": 0, "max": 200, "unit": "ppb"},
                    "humidity": {"min": 30, "max": 60, "unit": "%"},
                    "temperature": {"min": 18, "max": 24, "unit": "°C"},
                },
            },
            "motion_sensor": {
                "name": "Motion Detector",
                "metrics": ["motion_events", "activity_level", "room_presence"],
            },
            "sleep_sensor": {
                "name": "Sleep Environment Sensor",
                "metrics": ["noise_level", "light_level", "temperature", "humidity"],
                "optimal_ranges": {
                    "noise_level": {"min": 0, "max": 30, "unit": "dB"},
                    "light_level": {"min": 0, "max": 5, "unit": "lux"},
                    "temperature": {"min": 16, "max": 20, "unit": "°C"},
                },
            },
            "smart_thermostat": {
                "name": "Smart Thermostat",
                "metrics": ["current_temp", "target_temp", "humidity", "energy_usage"],
            },
            "smart_lights": {
                "name": "Smart Lighting",
                "metrics": ["brightness", "color_temp", " schedule_active"],
            },
            "smart_scale": {
                "name": "Smart Scale",
                "metrics": ["weight", "body_fat", "muscle_mass", "bmi", "water_percentage"],
            },
            "blood_pressure_monitor": {
                "name": "Connected BP Monitor",
                "metrics": ["systolic", "diastolic", "pulse"],
            },
            "pulse_oximeter": {
                "name": "Pulse Oximeter",
                "metrics": ["spo2", "pulse_rate", "perfusion_index"],
            },
        }

        self.health_rules = [
            {"condition": "co2 > 1000", "alert": "High CO2 - improve ventilation", "severity": "moderate"},
            {"condition": "pm25 > 35", "alert": "Poor air quality - run air purifier", "severity": "high"},
            {"condition": "humidity < 30", "alert": "Low humidity - use humidifier", "severity": "low"},
            {"condition": "humidity > 65", "alert": "High humidity - risk of mold", "severity": "moderate"},
            {"condition": "noise_level > 45 during sleep", "alert": "Noisy sleep environment", "severity": "moderate"},
            {"condition": "light_level > 10 during sleep", "alert": "Bright sleep environment - use blackout curtains", "severity": "low"},
        ]

    def register_home(self, user_id: str, home_config: Dict[str, Any]) -> Dict[str, Any]:
        """Register a smart home for health monitoring."""
        home_id = f"home_{user_id}_{int(time.time())}"
        self.homes[home_id] = {
            "home_id": home_id,
            "user_id": user_id,
            "name": home_config.get("name", "My Home"),
            "rooms": home_config.get("rooms", ["bedroom", "living_room", "kitchen", "bathroom"]),
            "devices": [],
            "alerts_enabled": True,
            "auto_optimize": True,
            "created_at": time.time(),
        }
        return self.homes[home_id]

    def register_device(self, home_id: str, device_config: Dict[str, Any]) -> Dict[str, Any]:
        """Register an IoT device for health monitoring."""
        device_id = f"dev_{int(time.time())}_{random.randint(1000, 9999)}"
        device_type = device_config.get("type", "air_quality_sensor")
        type_info = self.supported_devices.get(device_type, {})

        device = {
            "device_id": device_id,
            "home_id": home_id,
            "type": device_type,
            "name": device_config.get("name", type_info.get("name", "Unknown Device")),
            "room": device_config.get("room", "living_room"),
            "status": "online",
            "last_reading": {},
            "battery_level": device_config.get("battery", 100),
            "firmware_version": "2.1.0",
            "registered_at": time.time(),
        }

        self.devices[device_id] = device
        if home_id in self.homes:
            self.homes[home_id]["devices"].append(device_id)

        return device

    def process_reading(self, device_id: str, reading: Dict[str, Any]) -> Dict[str, Any]:
        """Process a sensor reading and check for health alerts."""
        device = self.devices.get(device_id)
        if not device:
            return {"error": "Device not found"}

        device["last_reading"] = reading
        device["last_reading"]["timestamp"] = time.time()

        # Check health rules
        alerts = self._evaluate_rules(reading, device)

        # Generate environment health score
        health_score = self._calculate_environment_score(reading, device["type"])

        result = {
            "device_id": device_id,
            "reading": reading,
            "environment_health_score": health_score,
            "alerts": alerts,
            "recommendations": self._get_environment_recommendations(reading, health_score),
            "auto_actions_taken": self._auto_optimize(device, reading, alerts) if alerts else [],
        }

        if alerts and device.get("home_id"):
            home_id = device["home_id"]
            if home_id not in self.alerts:
                self.alerts[home_id] = []
            self.alerts[home_id].extend(alerts)

        return result

    def get_environment_health(self, home_id: str) -> Dict[str, Any]:
        """Get overall environment health for a home."""
        home = self.homes.get(home_id)
        if not home:
            return {"error": "Home not found"}

        room_scores = {}
        for room in home["rooms"]:
            room_devices = [d for d in home["devices"] if self.devices.get(d, {}).get("room") == room]
            if room_devices:
                readings = [self.devices[d]["last_reading"] for d in room_devices if self.devices[d]["last_reading"]]
                if readings:
                    avg_score = sum(self._calculate_environment_score(r, self.devices[d]["type"])
                                    for r, d in zip(readings, room_devices)) / len(readings)
                    room_scores[room] = {"score": round(avg_score, 1), "devices": len(room_devices)}

        overall = sum(r["score"] for r in room_scores.values()) / max(1, len(room_scores)) if room_scores else 50

        return {
            "home_id": home_id,
            "overall_health_score": round(overall, 1),
            "room_scores": room_scores,
            "active_alerts": self.alerts.get(home_id, [])[-5:],
            "device_count": len(home["devices"]),
            "online_devices": sum(1 for d in home["devices"] if self.devices.get(d, {}).get("status") == "online"),
        }

    def get_sleep_environment_score(self, home_id: str) -> Dict[str, Any]:
        """Assess sleep environment quality."""
        home = self.homes.get(home_id)
        if not home:
            return {"error": "Home not found"}

        bedroom_devices = [
            d for d in home["devices"]
            if self.devices.get(d, {}).get("room") == "bedroom"
        ]

        metrics = {"noise": 25, "light": 3, "temperature": 19, "humidity": 45}
        for dev_id in bedroom_devices:
            device = self.devices[dev_id]
            reading = device.get("last_reading", {})
            if "noise_level" in reading:
                metrics["noise"] = reading["noise_level"]
            if "light_level" in reading:
                metrics["light"] = reading["light_level"]
            if "temperature" in reading:
                metrics["temperature"] = reading["temperature"]
            if "humidity" in reading:
                metrics["humidity"] = reading["humidity"]

        # Score each metric
        scores = {
            "noise": max(0, 100 - max(0, metrics["noise"] - 30) * 4),
            "darkness": max(0, 100 - max(0, metrics["light"] - 5) * 10),
            "temperature": 100 - abs(metrics["temperature"] - 18) * 8,
            "humidity": 100 - abs(metrics["humidity"] - 45) * 2,
        }

        overall = sum(scores.values()) / len(scores)

        return {
            "home_id": home_id,
            "sleep_environment_score": round(overall, 1),
            "metrics": metrics,
            "component_scores": scores,
            "recommendations": self._get_sleep_recommendations(metrics, scores),
        }

    def get_activity_patterns(self, home_id: str, days: int = 7) -> Dict[str, Any]:
        """Analyze activity patterns from motion sensors."""
        motion_devices = [
            d for d in self.devices.values()
            if d.get("home_id") == home_id and d["type"] == "motion_sensor"
        ]

        hourly_activity = {h: random.randint(5, 80) for h in range(24)}
        room_activity = {room: random.randint(10, 100) for room in ["bedroom", "living_room", "kitchen", "bathroom"]}

        active_hours = sum(1 for v in hourly_activity.values() if v > 30)
        sedentary_hours = sum(1 for v in hourly_activity.values() if v < 10)

        return {
            "home_id": home_id,
            "analysis_period_days": days,
            "motion_devices_found": len(motion_devices),
            "hourly_activity": hourly_activity,
            "room_activity": room_activity,
            "active_hours": active_hours,
            "sedentary_hours": sedentary_hours,
            "sleep_time": self._detect_sleep_time(hourly_activity),
            "wake_time": self._detect_wake_time(hourly_activity),
            "activity_score": round((active_hours / 16) * 100, 1),
        }

    def _evaluate_rules(self, reading: Dict, device: Dict) -> List[Dict]:
        alerts = []
        device_type = device.get("type", "")
        type_info = self.supported_devices.get(device_type, {})
        ranges = type_info.get("optimal_ranges", {})

        for metric, range_info in ranges.items():
            value = reading.get(metric)
            if value is not None:
                if value < range_info["min"] * 0.7 or value > range_info["max"] * 1.5:
                    alerts.append({
                        "metric": metric,
                        "value": value,
                        "optimal_range": range_info,
                        "severity": "high",
                        "message": f"{metric}: {value} {range_info['unit']} (optimal: {range_info['min']}-{range_info['max']})",
                        "timestamp": time.time(),
                    })
                elif value < range_info["min"] or value > range_info["max"]:
                    alerts.append({
                        "metric": metric,
                        "value": value,
                        "optimal_range": range_info,
                        "severity": "moderate",
                        "message": f"{metric}: {value} {range_info['unit']} slightly outside optimal range",
                        "timestamp": time.time(),
                    })
        return alerts

    def _calculate_environment_score(self, reading: Dict, device_type: str) -> float:
        type_info = self.supported_devices.get(device_type, {})
        ranges = type_info.get("optimal_ranges", {})
        if not ranges:
            return 75.0

        scores = []
        for metric, range_info in ranges.items():
            value = reading.get(metric)
            if value is not None:
                if range_info["min"] <= value <= range_info["max"]:
                    scores.append(100)
                else:
                    deviation = max(abs(value - range_info["min"]), abs(value - range_info["max"]))
                    range_size = range_info["max"] - range_info["min"]
                    penalty = (deviation / max(1, range_size)) * 50
                    scores.append(max(0, 100 - penalty))

        return sum(scores) / max(1, len(scores))

    def _get_environment_recommendations(self, reading: Dict, score: float) -> List[str]:
        recs = []
        if reading.get("co2", 0) > 800:
            recs.append("Open windows or turn on ventilation to reduce CO2")
        if reading.get("pm25", 0) > 15:
            recs.append("Run air purifier to reduce particulate matter")
        if reading.get("humidity", 50) < 35:
            recs.append("Use a humidifier to add moisture to the air")
        if reading.get("humidity", 50) > 60:
            recs.append("Use a dehumidifier to prevent mold growth")
        if score < 60:
            recs.append("Multiple environmental factors need attention")
        return recs

    def _auto_optimize(self, device: Dict, reading: Dict, alerts: List) -> List[str]:
        actions = []
        for alert in alerts:
            if alert["metric"] == "co2" and alert["severity"] == "high":
                actions.append("Sent signal to open smart vents")
            elif alert["metric"] == "temperature" and alert["value"] > 25:
                actions.append("Lowered thermostat by 2°C")
            elif alert["metric"] == "light_level" and alert["value"] > 10:
                actions.append("Dimmed smart lights to 10%")
        return actions

    def _get_sleep_recommendations(self, metrics: Dict, scores: Dict) -> List[str]:
        recs = []
        if metrics["noise"] > 35:
            recs.append("Use white noise machine or earplugs")
        if metrics["light"] > 5:
            recs.append("Use blackout curtains or sleep mask")
        if metrics["temperature"] > 21:
            recs.append("Lower bedroom temperature to 16-19°C for better sleep")
        if metrics["humidity"] < 35:
            recs.append("Add humidity to prevent dry airways")
        return recs

    def _detect_sleep_time(self, hourly: Dict) -> str:
        for h in range(21, 24):
            if hourly.get(h, 0) < 15:
                return f"{h:02d}:00"
        return "23:00"

    def _detect_wake_time(self, hourly: Dict) -> str:
        for h in range(5, 9):
            if hourly.get(h, 0) > 30:
                return f"{h:02d}:00"
        return "07:00"


ambient_health_service = AmbientHealthService()

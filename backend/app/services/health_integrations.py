"""
Health Integrations — Connect to third-party health services and APIs
"""
from datetime import datetime
from typing import Dict, List, Optional
import uuid


class HealthIntegrations:
    AVAILABLE_INTEGRATIONS = {
        "apple_health": {"name": "Apple HealthKit", "platform": "iOS", "icon": "🍎", "status": "available", "data_types": ["steps", "heart_rate", "sleep", "nutrition", "workouts", "weight"]},
        "google_fit": {"name": "Google Fit", "platform": "Android", "icon": "💙", "status": "available", "data_types": ["steps", "heart_rate", "sleep", "activity", "weight"]},
        "fitbit": {"name": "Fitbit", "platform": "Cross-platform", "icon": "📱", "status": "available", "data_types": ["steps", "heart_rate", "sleep", "spo2", "stress"]},
        "samsung_health": {"name": "Samsung Health", "platform": "Samsung", "icon": "📱", "status": "available", "data_types": ["steps", "heart_rate", "sleep", "blood_pressure", "weight"]},
        "garmin": {"name": "Garmin Connect", "platform": "Garmin", "icon": "⌚", "status": "available", "data_types": ["steps", "heart_rate", "spo2", "stress", "body_battery"]},
        "oura": {"name": "Oura Ring", "platform": "Oura", "icon": "💍", "status": "available", "data_types": ["sleep", "readiness", "activity", "spo2", "hrv"]},
        "whoop": {"name": "WHOOP", "platform": "WHOOP", "icon": "⌚", "status": "available", "data_types": ["strain", "recovery", "sleep", "hrv", "spo2"]},
        "strava": {"name": "Strava", "platform": "Cross-platform", "icon": "🏃", "status": "available", "data_types": ["runs", "rides", "swims", "routes"]},
        "myfitnesspal": {"name": "MyFitnessPal", "platform": "Cross-platform", "icon": "🍽️", "status": "available", "data_types": ["nutrition", "calories", "macros", "water"]},
        "withings": {"name": "Withings", "platform": "Withings", "icon": "⚖️", "status": "available", "data_types": ["weight", "blood_pressure", "spo2", "ecg", "temperature"]},
        "dexcom": {"name": "Dexcom CGM", "platform": "Dexcom", "icon": "🩸", "status": "available", "data_types": ["glucose_continuous", "trends", "alerts"]},
        "freestyle_libre": {"name": "FreeStyle Libre", "platform": "Abbott", "icon": "🩸", "status": "available", "data_types": ["glucose_continuous", "trends", "patterns"]},
    }

    def __init__(self):
        self.connections: Dict[str, List[dict]] = {}
        self.sync_logs: Dict[str, List[dict]] = {}

    def connect_service(self, user_id: str, service_key: str, auth_token: str = "", permissions: List[str] = None) -> dict:
        service = self.AVAILABLE_INTEGRATIONS.get(service_key)
        if not service:
            return {"error": f"Unknown service: {service_key}"}
        
        connection = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "service": service_key,
            "service_name": service["name"],
            "permissions": permissions or service["data_types"],
            "status": "connected",
            "connected_at": datetime.now().isoformat(),
            "last_sync": None,
        }
        self.connections.setdefault(user_id, []).append(connection)
        return connection

    def disconnect_service(self, user_id: str, connection_id: str) -> dict:
        for conn in self.connections.get(user_id, []):
            if conn["id"] == connection_id:
                conn["status"] = "disconnected"
                conn["disconnected_at"] = datetime.now().isoformat()
                return {"status": "disconnected", "service": conn["service_name"]}
        return {"error": "Connection not found"}

    def get_connections(self, user_id: str) -> List[dict]:
        return self.connections.get(user_id, [])

    def sync_data(self, user_id: str, connection_id: str) -> dict:
        for conn in self.connections.get(user_id, []):
            if conn["id"] == connection_id:
                sync_log = {
                    "id": str(uuid.uuid4()),
                    "connection_id": connection_id,
                    "service": conn["service_name"],
                    "records_synced": 42,
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                }
                self.sync_logs.setdefault(user_id, []).append(sync_log)
                conn["last_sync"] = datetime.now().isoformat()
                return sync_log
        return {"error": "Connection not found"}

    def get_available_integrations(self) -> List[dict]:
        return [{"key": k, **v} for k, v in self.AVAILABLE_INTEGRATIONS.items()]


health_integrations = HealthIntegrations()

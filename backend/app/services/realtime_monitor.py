"""
Real-Time Health Monitoring — WebSocket streaming, threshold alerts, emergency detection
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid
import math


class RealtimeHealthMonitor:
    VITAL_THRESHOLDS = {
        "heart_rate": {
            "critical_low": 40, "low": 50, "normal_low": 60, "normal_high": 100, "high": 120, "critical_high": 150,
            "unit": "bpm", "name": "Heart Rate",
        },
        "blood_pressure_systolic": {
            "critical_low": 70, "low": 90, "normal_low": 100, "normal_high": 130, "high": 140, "critical_high": 180,
            "unit": "mmHg", "name": "Systolic BP",
        },
        "blood_pressure_diastolic": {
            "critical_low": 40, "low": 60, "normal_low": 70, "normal_high": 85, "high": 90, "critical_high": 120,
            "unit": "mmHg", "name": "Diastolic BP",
        },
        "spo2": {
            "critical_low": 85, "low": 90, "normal_low": 95, "normal_high": 100, "high": None, "critical_high": None,
            "unit": "%", "name": "Blood Oxygen",
        },
        "blood_glucose": {
            "critical_low": 50, "low": 70, "normal_low": 70, "normal_high": 140, "high": 200, "critical_high": 300,
            "unit": "mg/dL", "name": "Blood Glucose",
        },
        "body_temperature": {
            "critical_low": 34.0, "low": 36.0, "normal_low": 36.1, "normal_high": 37.2, "high": 38.0, "critical_high": 40.0,
            "unit": "°C", "name": "Body Temperature",
        },
        "respiratory_rate": {
            "critical_low": 8, "low": 12, "normal_low": 12, "normal_high": 20, "high": 25, "critical_high": 30,
            "unit": "breaths/min", "name": "Respiratory Rate",
        },
        "stress_level": {
            "critical_low": None, "low": None, "normal_low": 0, "normal_high": 5, "high": 7, "critical_high": 9,
            "unit": "/10", "name": "Stress Level",
        },
    }

    ALERT_SEVERITY = {
        "info": {"color": "#2196F3", "icon": "ℹ️", "notify": False},
        "warning": {"color": "#FF9800", "icon": "⚠️", "notify": True},
        "critical": {"color": "#F44336", "icon": "🚨", "notify": True},
        "emergency": {"color": "#B71C1C", "icon": "🆘", "notify": True},
    }

    def __init__(self):
        self.active_sessions: Dict[str, dict] = {}
        self.vital_buffers: Dict[str, List[dict]] = {}
        self.alerts: Dict[str, List[dict]] = {}
        self.care_team_notifications: Dict[str, List[dict]] = {}
        self.connected_devices: Dict[str, List[dict]] = {}

    def start_monitoring_session(self, user_id: str, device_id: str = "phone") -> dict:
        session_id = str(uuid.uuid4())
        session = {
            "id": session_id,
            "user_id": user_id,
            "device_id": device_id,
            "status": "active",
            "started_at": datetime.now().isoformat(),
            "vitals_received": 0,
            "alerts_triggered": 0,
        }
        self.active_sessions[session_id] = session
        self.vital_buffers[session_id] = []
        self.alerts[session_id] = []
        return session

    def process_vital_reading(self, session_id: str, vital_type: str, value: float, timestamp: str = None) -> dict:
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        reading = {
            "id": str(uuid.uuid4()),
            "vital_type": vital_type,
            "value": value,
            "timestamp": timestamp or datetime.now().isoformat(),
            "session_id": session_id,
        }
        
        self.vital_buffers.setdefault(session_id, []).append(reading)
        session["vitals_received"] += 1
        
        alert = self._check_threshold(vital_type, value, session["user_id"])
        if alert:
            self.alerts.setdefault(session_id, []).append(alert)
            session["alerts_triggered"] += 1
            
            if alert["severity"] in ("critical", "emergency"):
                self._trigger_care_team_notification(session["user_id"], alert)
        
        return {"reading": reading, "alert": alert}

    def _check_threshold(self, vital_type: str, value: float, user_id: str) -> Optional[dict]:
        thresholds = self.VITAL_THRESHOLDS.get(vital_type)
        if not thresholds:
            return None
        
        severity = None
        message = None
        
        if thresholds["critical_high"] is not None and value >= thresholds["critical_high"]:
            severity = "emergency"
            message = f"CRITICAL: {thresholds['name']} is dangerously high at {value} {thresholds['unit']}"
        elif thresholds["high"] is not None and value >= thresholds["high"]:
            severity = "critical"
            message = f"ALERT: {thresholds['name']} is elevated at {value} {thresholds['unit']}"
        elif thresholds["critical_low"] is not None and value <= thresholds["critical_low"]:
            severity = "emergency"
            message = f"CRITICAL: {thresholds['name']} is dangerously low at {value} {thresholds['unit']}"
        elif thresholds["low"] is not None and value <= thresholds["low"]:
            severity = "critical"
            message = f"ALERT: {thresholds['name']} is low at {value} {thresholds['unit']}"
        
        if severity:
            return {
                "id": str(uuid.uuid4()),
                "vital_type": vital_type,
                "value": value,
                "severity": severity,
                "message": message,
                "thresholds": thresholds,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
            }
        return None

    def _trigger_care_team_notification(self, user_id: str, alert: dict):
        notification = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "alert": alert,
            "status": "sent",
            "timestamp": datetime.now().isoformat(),
        }
        self.care_team_notifications.setdefault(user_id, []).append(notification)

    def get_session_data(self, session_id: str) -> dict:
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        vitals = self.vital_buffers.get(session_id, [])
        alerts = self.alerts.get(session_id, [])
        
        vital_summary = {}
        for v in vitals:
            vt = v["vital_type"]
            if vt not in vital_summary:
                vital_summary[vt] = {"values": [], "latest": None}
            vital_summary[vt]["values"].append(v["value"])
            vital_summary[vt]["latest"] = v["value"]
        
        for vt in vital_summary:
            vals = vital_summary[vt]["values"]
            vital_summary[vt]["avg"] = round(sum(vals) / len(vals), 2)
            vital_summary[vt]["min"] = min(vals)
            vital_summary[vt]["max"] = max(vals)
            vital_summary[vt]["count"] = len(vals)
            del vital_summary[vt]["values"]
        
        return {
            "session": session,
            "vital_summary": vital_summary,
            "recent_alerts": alerts[-5:],
            "total_readings": len(vitals),
        }

    def stop_monitoring_session(self, session_id: str) -> dict:
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        session["status"] = "completed"
        session["ended_at"] = datetime.now().isoformat()
        
        return self.get_session_data(session_id)

    def get_user_monitoring_history(self, user_id: str, limit: int = 10) -> List[dict]:
        sessions = [s for s in self.active_sessions.values() if s["user_id"] == user_id]
        return sorted(sessions, key=lambda x: x["started_at"], reverse=True)[:limit]

    def get_care_team_notifications(self, user_id: str, limit: int = 20) -> List[dict]:
        return self.care_team_notifications.get(user_id, [])[-limit:]

    def register_device(self, user_id: str, device_type: str, device_name: str) -> dict:
        device = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": device_type,
            "name": device_name,
            "registered_at": datetime.now().isoformat(),
            "status": "connected",
        }
        self.connected_devices.setdefault(user_id, []).append(device)
        return device


realtime_monitor = RealtimeHealthMonitor()

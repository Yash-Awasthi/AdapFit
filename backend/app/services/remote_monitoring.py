"""
Remote Patient Monitoring — IoT Device Integration & Vital Trends
Continuous monitoring, alert thresholds, care team notifications
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random


class RemoteMonitoringService:
    """IoT-based remote patient monitoring platform"""

    def __init__(self):
        self.device_types = {
            "blood_pressure_monitor": {
                "metrics": ["systolic", "diastolic", "pulse"],
                "normal_range": {"systolic": (90, 120), "diastolic": (60, 80), "pulse": (60, 100)},
                "alert_thresholds": {"systolic_high": 140, "systolic_low": 90, "diastolic_high": 90, "diastolic_low": 60},
                "frequency": "twice_daily",
            },
            "glucose_meter": {
                "metrics": ["blood_glucose"],
                "normal_range": {"fasting": (70, 100), "postprandial": (70, 140)},
                "alert_thresholds": {"high": 180, "low": 70, "critical_high": 250, "critical_low": 54},
                "frequency": "as_directed",
            },
            "pulse_oximeter": {
                "metrics": ["oxygen_saturation", "pulse_rate"],
                "normal_range": {"oxygen_saturation": (95, 100), "pulse_rate": (60, 100)},
                "alert_thresholds": {"o2_low": 92, "pulse_high": 120, "pulse_low": 50},
                "frequency": "as_needed",
            },
            "smart_scale": {
                "metrics": ["weight", "body_fat", "bmi"],
                "normal_range": {},
                "alert_thresholds": {"weight_change_3day": 3},
                "frequency": "daily",
            },
            "wearable_tracker": {
                "metrics": ["steps", "heart_rate", "sleep", "activity_minutes"],
                "normal_range": {"steps": (5000, 10000), "sleep_hours": (7, 9)},
                "alert_thresholds": {"low_activity_steps": 2000},
                "frequency": "continuous",
            },
            "ecg_monitor": {
                "metrics": ["heart_rate", "rhythm", "hrv"],
                "normal_range": {"heart_rate": (60, 100)},
                "alert_thresholds": {"irregular_rhythm": True, "hrv_low": 20},
                "frequency": "daily_or_symptoms",
            },
        }

        self.care_team_roles = [
            {"role": "primary_physician", "notifications": ["critical_alerts", "weekly_summary", "trend_changes"]},
            {"role": "nurse", "notifications": ["daily_alerts", "medication_non_adherence", "vital_out_of_range"]},
            {"role": "pharmacist", "notifications": ["medication_interactions", "refill_reminders"]},
            {"role": "caregiver", "notifications": ["critical_alerts", "daily_check_in"]},
        ]

    def register_device(self, patient_id: str, device_type: str, device_info: Dict) -> Dict:
        """Register a monitoring device for a patient"""
        if device_type not in self.device_types:
            return {"success": False, "error": f"Unknown device type: {device_type}"}

        device_config = self.device_types[device_type]

        return {
            "success": True,
            "device_id": f"DEV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "patient_id": patient_id,
            "device_type": device_type,
            "metrics_tracked": device_config["metrics"],
            "measurement_frequency": device_config["frequency"],
            "alert_thresholds": device_config["alert_thresholds"],
            "setup_instructions": self._get_setup_instructions(device_type),
            "data_sync_enabled": True,
        }

    def _get_setup_instructions(self, device_type: str) -> List[str]:
        """Get device setup instructions"""
        instructions = {
            "blood_pressure_monitor": [
                "Sit quietly for 5 minutes before measurement",
                "Place cuff on bare upper arm at heart level",
                "Take 2 readings 1 minute apart",
                "Record both readings in the app",
            ],
            "glucose_meter": [
                "Wash hands with warm water before testing",
                "Use test strip within 3 minutes of opening",
                "Apply blood drop to correct end of strip",
                "Record reading with time and meal context",
            ],
            "pulse_oximeter": [
                "Remove nail polish from test finger",
                "Warm hands if cold for better reading",
                "Stay still during measurement",
                "Wait 10 seconds for stable reading",
            ],
            "wearable_tracker": [
                "Charge device fully before first use",
                "Pair with smartphone via Bluetooth",
                "Wear snugly on wrist, 2 fingers above wrist bone",
                "Enable continuous heart rate monitoring",
            ],
        }
        return instructions.get(device_type, ["Follow manufacturer instructions", "Pair with app via Bluetooth"])

    def process_vital_reading(self, patient_id: str, device_type: str, readings: Dict) -> Dict:
        """Process a vital sign reading and check for alerts"""
        config = self.device_types.get(device_type, {})
        alerts = []
        status = "normal"

        # Check each metric against thresholds
        for metric, value in readings.items():
            thresholds = config.get("alert_thresholds", {})

            if metric == "systolic" and isinstance(value, (int, float)):
                if value >= thresholds.get("systolic_high", 140):
                    alerts.append({"metric": "systolic", "value": value, "threshold": thresholds["systolic_high"], "severity": "high", "message": f"Systolic BP elevated: {value} mmHg"})
                    status = "alert"
                elif value <= thresholds.get("systolic_low", 90):
                    alerts.append({"metric": "systolic", "value": value, "threshold": thresholds["systolic_low"], "severity": "medium", "message": f"Systolic BP low: {value} mmHg"})
                    status = "alert"

            if metric == "blood_glucose" and isinstance(value, (int, float)):
                if value >= thresholds.get("critical_high", 250):
                    alerts.append({"metric": "glucose", "value": value, "severity": "critical", "message": f"CRITICAL: Blood glucose {value} mg/dL"})
                    status = "critical"
                elif value >= thresholds.get("high", 180):
                    alerts.append({"metric": "glucose", "value": value, "severity": "high", "message": f"Blood glucose elevated: {value} mg/dL"})
                    status = "alert"
                elif value <= thresholds.get("low", 70):
                    alerts.append({"metric": "glucose", "value": value, "severity": "high", "message": f"Blood glucose low: {value} mg/dL"})
                    status = "alert"

            if metric == "oxygen_saturation" and isinstance(value, (int, float)):
                if value < thresholds.get("o2_low", 92):
                    alerts.append({"metric": "SpO2", "value": value, "severity": "high", "message": f"Oxygen saturation low: {value}%"})
                    status = "alert"

        return {
            "patient_id": patient_id,
            "device_type": device_type,
            "readings": readings,
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "alerts": alerts,
            "alerts_count": len(alerts),
            "care_team_notified": status in ["alert", "critical"],
            "next_scheduled_reading": self._get_next_reading(device_type),
        }

    def _get_next_reading(self, device_type: str) -> str:
        """Get next scheduled reading time"""
        freq = self.device_types.get(device_type, {}).get("frequency", "daily")
        now = datetime.now()
        if freq == "twice_daily":
            return (now + timedelta(hours=12)).isoformat()
        elif freq == "daily":
            return (now + timedelta(days=1)).isoformat()
        return (now + timedelta(hours=4)).isoformat()

    def get_vital_trends(self, patient_id: str, metric: str, days: int = 30) -> Dict:
        """Get trends for a specific vital metric"""
        # Simulate trend data
        base_values = {
            "systolic": 125, "diastolic": 82, "heart_rate": 72,
            "blood_glucose": 110, "oxygen_saturation": 97, "weight": 75,
        }
        base = base_values.get(metric, 50)

        readings = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=days - i)).strftime("%Y-%m-%d")
            value = base + random.uniform(-5, 5)
            readings.append({"date": date, "value": round(value, 1)})

        values = [r["value"] for r in readings]
        avg = sum(values) / len(values)
        trend = "stable"
        if len(values) >= 7:
            recent = sum(values[-7:]) / 7
            earlier = sum(values[:7]) / 7
            if recent > earlier + 3:
                trend = "increasing"
            elif recent < earlier - 3:
                trend = "decreasing"

        return {
            "patient_id": patient_id,
            "metric": metric,
            "period_days": days,
            "readings": readings,
            "average": round(avg, 1),
            "min": round(min(values), 1),
            "max": round(max(values), 1),
            "trend": trend,
            "data_points": len(readings),
        }

    def get_monitoring_dashboard(self, patient_id: str) -> Dict:
        """Get comprehensive monitoring dashboard"""
        return {
            "patient_id": patient_id,
            "connected_devices": 3,
            "active_alerts": 0,
            "measurements_today": 6,
            "adherence_rate": 92,
            "last_sync": datetime.now().isoformat(),
            "vital_summary": {
                "blood_pressure": {"latest": "122/78", "trend": "stable", "status": "normal"},
                "heart_rate": {"latest": "72 bpm", "trend": "stable", "status": "normal"},
                "blood_glucose": {"latest": "105 mg/dL", "trend": "decreasing", "status": "normal"},
                "oxygen_saturation": {"latest": "97%", "trend": "stable", "status": "normal"},
                "weight": {"latest": "74.5 kg", "trend": "decreasing", "status": "normal"},
            },
            "upcoming_appointments": [
                {"date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"), "type": "Follow-up", "provider": "Dr. Smith"},
            ],
        }


remote_monitoring_service = RemoteMonitoringService()

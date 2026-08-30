"""
Personal Health Assistant for ZFIT
Extracted from: Jackie (healthcare assistance app)
Patterns: Vitals monitoring, medication tracking, appointment management,
          prescription management, inventory alerts, doctor notifications
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class VitalType(Enum):
    GLUCOSE = "glucose"
    BLOOD_PRESSURE = "blood_pressure"
    PULSE = "pulse"
    TEMPERATURE = "temperature"
    WEIGHT = "weight"
    OXYGEN_SATURATION = "oxygen_saturation"


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class VitalReading:
    vital_type: VitalType
    value: float
    unit: str
    timestamp: datetime
    notes: str = ""


@dataclass
class Medication:
    name: str
    dosage: str
    frequency: str  # "daily", "twice_daily", "weekly", etc.
    time_of_day: list[str] = field(default_factory=list)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    refills_remaining: int = 0
    pills_remaining: int = 0


@dataclass
class Appointment:
    id: str
    doctor_name: str
    specialty: str
    datetime: datetime
    location: str = ""
    notes: str = ""
    reminder_sent: bool = False


@dataclass
class Prescription:
    id: str
    doctor_name: str
    medication: str
    dosage: str
    instructions: str
    date_issued: datetime
    refills_allowed: int = 0
    refills_used: int = 0


@dataclass
class HealthAlert:
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    vital_type: Optional[VitalType] = None
    acknowledged: bool = False


# ─── Vital Thresholds ─────────────────────────────────────────────────

VITAL_THRESHOLDS = {
    VitalType.GLUCOSE: {
        "low": 70, "normal_low": 70, "normal_high": 140, "high": 200,
        "unit": "mg/dL", "critical_low": 54, "critical_high": 300,
    },
    VitalType.BLOOD_PRESSURE: {
        "normal_systolic": 120, "normal_diastolic": 80,
        "high_systolic": 140, "high_diastolic": 90,
        "critical_systolic": 180, "critical_diastolic": 120,
    },
    VitalType.PULSE: {
        "low": 50, "normal_low": 60, "normal_high": 100, "high": 120,
        "unit": "bpm", "critical_low": 40, "critical_high": 150,
    },
    VitalType.TEMPERATURE: {
        "low": 35.5, "normal_low": 36.1, "normal_high": 37.2, "high": 38.0,
        "unit": "°C", "critical_low": 35.0, "critical_high": 40.0,
    },
    VitalType.OXYGEN_SATURATION: {
        "critical_low": 90, "low": 94, "normal_low": 95, "normal_high": 100,
        "unit": "%",
    },
}


# ─── Personal Health Assistant ─────────────────────────────────────────

class PersonalHealthAssistant:
    def __init__(self):
        self.vitals: list[VitalReading] = []
        self.medications: list[Medication] = []
        self.appointments: list[Appointment] = []
        self.prescriptions: list[Prescription] = []
        self.alerts: list[HealthAlert] = []

    def log_vital(self, vital_type: VitalType, value: float, unit: str = "", notes: str = "") -> HealthAlert:
        """Log a vital reading and check for alerts."""
        if not unit:
            unit = VITAL_THRESHOLDS.get(vital_type, {}).get("unit", "")

        reading = VitalReading(vital_type=vital_type, value=value, unit=unit,
                               timestamp=datetime.now(), notes=notes)
        self.vitals.append(reading)

        # Check thresholds
        alert = self._check_vital_alert(vital_type, value)
        if alert:
            self.alerts.append(alert)
        return alert

    def add_medication(self, medication: Medication):
        self.medications.append(medication)

    def log_medication_taken(self, medication_name: str):
        """Record that a medication was taken."""
        for med in self.medications:
            if med.name.lower() == medication_name.lower():
                if med.pills_remaining > 0:
                    med.pills_remaining -= 1
                    if med.pills_remaining <= 5:
                        self.alerts.append(HealthAlert(
                            severity=AlertSeverity.WARNING,
                            title="Low Medication Supply",
                            message=f"{med.name} has only {med.pills_remaining} pills remaining",
                            timestamp=datetime.now(),
                        ))

    def schedule_appointment(self, appointment: Appointment):
        self.appointments.append(appointment)

    def get_upcoming_appointments(self, days: int = 7) -> list[Appointment]:
        cutoff = datetime.now() + timedelta(days=days)
        return [a for a in self.appointments if datetime.now() <= a.datetime <= cutoff]

    def add_prescription(self, prescription: Prescription):
        self.prescriptions.append(prescription)

    def get_vital_trend(self, vital_type: VitalType, days: int = 30) -> list[dict]:
        """Get trend data for a vital type."""
        cutoff = datetime.now() - timedelta(days=days)
        relevant = [v for v in self.vitals if v.vital_type == vital_type and v.timestamp >= cutoff]
        return [
            {"timestamp": v.timestamp.isoformat(), "value": v.value, "unit": v.unit}
            for v in sorted(relevant, key=lambda x: x.timestamp)
        ]

    def get_active_alerts(self) -> list[HealthAlert]:
        return [a for a in self.alerts if not a.acknowledged]

    def acknowledge_alert(self, index: int):
        if 0 <= index < len(self.alerts):
            self.alerts[index].acknowledged = True

    def generate_health_summary(self) -> dict:
        """Generate a comprehensive health summary."""
        active_alerts = self.get_active_alerts()
        upcoming = self.get_upcoming_appointments()
        low_stock = [m for m in self.medications if m.pills_remaining <= 5]

        latest_vitals = {}
        for vt in VitalType:
            readings = [v for v in self.vitals if v.vital_type == vt]
            if readings:
                latest = max(readings, key=lambda x: x.timestamp)
                latest_vitals[vt.value] = {"value": latest.value, "unit": latest.unit, "timestamp": latest.timestamp.isoformat()}

        return {
            "latest_vitals": latest_vitals,
            "active_alerts": len(active_alerts),
            "upcoming_appointments": len(upcoming),
            "medications_tracked": len(self.medications),
            "low_stock_medications": [m.name for m in low_stock],
            "total_vitals_logged": len(self.vitals),
        }

    def _check_vital_alert(self, vital_type: VitalType, value: float) -> Optional[HealthAlert]:
        """Check if a vital reading triggers an alert."""
        thresholds = VITAL_THRESHOLDS.get(vital_type)
        if not thresholds:
            return None

        if vital_type == VitalType.BLOOD_PRESSURE:
            return None  # Handled separately

        critical_low = thresholds.get("critical_low")
        critical_high = thresholds.get("critical_high")
        high = thresholds.get("high")
        low = thresholds.get("low")

        if critical_low is not None and value <= critical_low:
            return HealthAlert(AlertSeverity.CRITICAL, f"Critical Low {vital_type.value}",
                             f"{vital_type.value} is critically low: {value}", datetime.now(), vital_type)
        if critical_high is not None and value >= critical_high:
            return HealthAlert(AlertSeverity.CRITICAL, f"Critical High {vital_type.value}",
                             f"{vital_type.value} is critically high: {value}", datetime.now(), vital_type)
        if high is not None and value >= high:
            return HealthAlert(AlertSeverity.WARNING, f"Elevated {vital_type.value}",
                             f"{vital_type.value} is elevated: {value}", datetime.now(), vital_type)
        if low is not None and value <= low:
            return HealthAlert(AlertSeverity.WARNING, f"Low {vital_type.value}",
                             f"{vital_type.value} is low: {value}", datetime.now(), vital_type)

        return None

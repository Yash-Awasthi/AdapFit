"""
Hospital at Home — Acute care monitoring, nurse escalation, discharge planning
Enables hospital-level care in the patient's home with remote monitoring.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid


class HospitalAtHomeService:
    ACUTE_CONDITIONS = {
        "pneumonia": {"name": "Community-Acquired Pneumonia", "monitoring_vitals": ["temperature", "spo2", "respiratory_rate", "heart_rate"], "typical_days": 7, "escalation_thresholds": {"spo2": 90, "temperature": 39.5}},
        "copd_exacerbation": {"name": "COPD Exacerbation", "monitoring_vitals": ["spo2", "respiratory_rate", "peak_flow", "heart_rate"], "typical_days": 10, "escalation_thresholds": {"spo2": 88, "respiratory_rate": 28}},
        "heart_failure": {"name": "Heart Failure Decompensation", "monitoring_vitals": ["weight", "spo2", "heart_rate", "blood_pressure"], "typical_days": 14, "escalation_thresholds": {"weight_gain_kg": 2, "spo2": 90}},
        "cellulitis": {"name": "Cellulitis", "monitoring_vitals": ["temperature", "wound_photo", "pain_level"], "typical_days": 10, "escalation_thresholds": {"temperature": 39.0, "pain_level": 8}},
        "uti": {"name": "Urinary Tract Infection", "monitoring_vitals": ["temperature", "fluid_intake", "pain_level"], "typical_days": 7, "escalation_thresholds": {"temperature": 39.5}},
        "dka": {"name": "Diabetic Ketoacidosis (Stable)", "monitoring_vitals": ["blood_glucose", "ketones", "fluid_intake", "vitals"], "typical_days": 5, "escalation_thresholds": {"blood_glucose": 350, "ketones": 3.0}},
    }

    ESCALATION_LEVELS = [
        {"level": 1, "name": "Nurse Phone", "response_time_min": 15, "action": "Phone assessment by nurse"},
        {"level": 2, "name": "Nurse Visit", "response_time_min": 60, "action": "In-home nurse assessment"},
        {"level": 3, "name": "Telehealth Physician", "response_time_min": 30, "action": "Virtual physician consultation"},
        {"level": 4, "name": "Physician Home Visit", "response_time_min": 120, "action": "Physician in-home visit"},
        {"level": 5, "name": "Emergency Transfer", "response_time_min": 15, "action": "Transfer to emergency department"},
    ]

    DISCHARGE_CRITERIA = {
        "stable_vitals": "All monitored vitals within normal range for 24+ hours",
        "no_escalation": "No escalation events in past 48 hours",
        "functional_status": "Patient can perform ADLs independently",
        "medication_adherence": "Patient taking all medications as prescribed",
        "support_system": "Caregiver available and trained",
        "follow_up_scheduled": "Follow-up appointment within 7 days",
    }

    def __init__(self):
        self.patients: Dict[str, dict] = {}
        self.monitoring_sessions: Dict[str, List[dict]] = {}
        self.escalation_events: Dict[str, List[dict]] = {}
        self.care_plans: Dict[str, dict] = {}
        self.discharge_plans: Dict[str, dict] = {}

    def admit_patient(self, user_id: str, condition: str, physician: str, admission_date: str = None) -> dict:
        config = self.ACUTE_CONDITIONS.get(condition)
        if not config:
            return {"error": f"Unknown condition: {condition}"}
        
        admission = admission_date or datetime.now().isoformat()
        discharge_target = (datetime.fromisoformat(admission) + timedelta(days=config["typical_days"])).isoformat()
        
        patient = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "condition": condition,
            "condition_name": config["name"],
            "physician": physician,
            "admission_date": admission,
            "expected_discharge": discharge_target,
            "status": "active",
            "monitoring_vitals": config["monitoring_vitals"],
            "escalation_thresholds": config["escalation_thresholds"],
            "admitted_at": datetime.now().isoformat(),
        }
        self.patients[user_id] = patient
        self.monitoring_sessions[user_id] = []
        self.escalation_events[user_id] = []
        self._create_care_plan(user_id)
        return patient

    def _create_care_plan(self, user_id: str):
        patient = self.patients.get(user_id, {})
        config = self.ACUTE_CONDITIONS.get(patient.get("condition"), {})
        
        self.care_plans[user_id] = {
            "condition": patient.get("condition"),
            "vital_schedule": {"frequency_hours": 4, "night_check": True},
            "medications": [],
            "activity_restrictions": ["No heavy lifting", "Rest as needed"],
            "dietary_restrictions": ["Increase fluid intake", "Balanced meals"],
            "telehealth_checkins": {"frequency": "daily", "physician": patient.get("physician")},
            "red_flags": ["Fever above 39.5°C", "SpO2 below 90%", "Severe pain", "Confusion", "Difficulty breathing"],
        }

    def log_vital_reading(self, user_id: str, vital_type: str, value: float, timestamp: str = None) -> dict:
        patient = self.patients.get(user_id)
        if not patient:
            return {"error": "Patient not found"}
        
        reading = {
            "id": str(uuid.uuid4()),
            "vital_type": vital_type,
            "value": value,
            "timestamp": timestamp or datetime.now().isoformat(),
        }
        self.monitoring_sessions.setdefault(user_id, []).append(reading)
        
        threshold = patient["escalation_thresholds"].get(vital_type)
        escalation_needed = False
        
        if vital_type == "spo2" and value < threshold:
            escalation_needed = True
        elif vital_type == "temperature" and value > threshold:
            escalation_needed = True
        elif vital_type == "respiratory_rate" and value > threshold:
            escalation_needed = True
        elif vital_type == "heart_rate" and (value > 120 or value < 50):
            escalation_needed = True
        
        if escalation_needed:
            escalation = self._trigger_escalation(user_id, f"Abnormal {vital_type}: {value}", 2)
            reading["escalation"] = escalation
        
        return reading

    def _trigger_escalation(self, user_id: str, reason: str, level: int) -> dict:
        escalation_level = self.ESCALATION_LEVELS[min(level, len(self.ESCALATION_LEVELS) - 1)]
        event = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "level": escalation_level["level"],
            "level_name": escalation_level["name"],
            "reason": reason,
            "response_time_min": escalation_level["response_time_min"],
            "action": escalation_level["action"],
            "status": "triggered",
            "timestamp": datetime.now().isoformat(),
        }
        self.escalation_events.setdefault(user_id, []).append(event)
        return event

    def get_patient_status(self, user_id: str) -> dict:
        patient = self.patients.get(user_id)
        if not patient:
            return {"error": "Patient not found"}
        
        vitals = self.monitoring_sessions.get(user_id, [])
        escalations = self.escalation_events.get(user_id, [])
        care_plan = self.care_plans.get(user_id, {})
        
        latest_vitals = {}
        for v in reversed(vitals):
            if v["vital_type"] not in latest_vitals:
                latest_vitals[v["vital_type"]] = v
        
        discharge_readiness = self._assess_discharge_readiness(user_id)
        
        return {
            "patient": patient,
            "latest_vitals": latest_vitals,
            "total_vitals_logged": len(vitals),
            "escalation_count": len(escalations),
            "recent_escalations": escalations[-3:],
            "care_plan": care_plan,
            "discharge_readiness": discharge_readiness,
        }

    def _assess_discharge_readiness(self, user_id: str) -> dict:
        vitals = self.monitoring_sessions.get(user_id, [])
        escalations = self.escalation_events.get(user_id, [])
        recent_escalations = [e for e in escalations if (datetime.now() - datetime.fromisoformat(e["timestamp"])).total_seconds() < 48 * 3600]
        
        criteria_met = []
        if len(recent_escalations) == 0:
            criteria_met.append("no_escalation")
        
        last_24h = [v for v in vitals if (datetime.now() - datetime.fromisoformat(v["timestamp"])).total_seconds() < 24 * 3600]
        if len(last_24h) >= 6:
            criteria_met.append("stable_vitals")
        
        score = len(criteria_met) / len(self.DISCHARGE_CRITERIA) * 100
        
        return {
            "score": round(score, 1),
            "criteria_met": criteria_met,
            "criteria_missing": [c for c in self.DISCHARGE_CRITERIA if c not in criteria_met],
            "ready_for_discharge": score >= 80,
        }

    def create_discharge_plan(self, user_id: str, physician_notes: str = "", follow_up_date: str = "") -> dict:
        readiness = self._assess_discharge_readiness(user_id)
        if not readiness["ready_for_discharge"]:
            return {"error": "Patient not yet ready for discharge", "readiness_score": readiness["score"], "missing": readiness["criteria_missing"]}
        
        plan = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "physician_notes": physician_notes,
            "follow_up_date": follow_up_date,
            "instructions": [
                "Continue prescribed medications",
                "Monitor temperature twice daily",
                "Call if fever returns or symptoms worsen",
                "Follow-up appointment in 7 days",
                "Gradual return to normal activities",
            ],
            "medications_at_discharge": [],
            "follow_up_needed": True,
            "discharged_at": datetime.now().isoformat(),
        }
        self.discharge_plans[user_id] = plan
        patient = self.patients.get(user_id, {})
        patient["status"] = "discharged"
        return plan

    def get_escalation_history(self, user_id: str, limit: int = 20) -> List[dict]:
        return self.escalation_events.get(user_id, [])[-limit:]

    def get_conditions(self) -> List[dict]:
        return [{"key": k, **v} for k, v in self.ACUTE_CONDITIONS.items()]


hospital_at_home = HospitalAtHomeService()

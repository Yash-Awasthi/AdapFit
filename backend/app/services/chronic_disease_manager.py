"""
Chronic Disease Management Platform
Tracks multiple chronic conditions, medication adherence, symptom patterns, and care plans.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid


class ChronicDiseaseManager:
    SUPPORTED_CONDITIONS = {
        "hypertension": {
            "name": "Hypertension",
            "icon": "❤️",
            "target_ranges": {"systolic": (90, 130), "diastolic": (60, 80)},
            "key_metrics": ["blood_pressure_systolic", "blood_pressure_diastolic", "sodium_intake", "weight", "stress_level"],
            "medications": ["lisinopril", "amlodipine", "losartan", "metoprolol", "hydrochlorothiazide"],
            "lifestyle_recommendations": ["Reduce sodium to <2300mg/day", "DASH diet", "Exercise 30 min/day", "Limit alcohol", "Manage stress"],
        },
        "diabetes_type2": {
            "name": "Type 2 Diabetes",
            "icon": "🩸",
            "target_ranges": {"fasting_glucose": (70, 130), "hba1c": (4.0, 7.0), "postprandial_glucose": (70, 180)},
            "key_metrics": ["fasting_glucose", "hba1c", "weight", "carb_intake", "activity_minutes"],
            "medications": ["metformin", "glipizide", "empagliflozin", "sitagliptin", "insulin"],
            "lifestyle_recommendations": ["Carb counting", "Blood glucose monitoring", "Foot care", "Eye exams annually", "Regular exercise"],
        },
        "copd": {
            "name": "COPD",
            "icon": "🫁",
            "target_ranges": {"spo2": (92, 100), "fev1_percent": (60, 100)},
            "key_metrics": ["spo2", "peak_flow", "breathlessness_score", "exercise_tolerance", "cough_frequency"],
            "medications": ["albuterol", "fluticasone", "tiotropium", "budesonide"],
            "lifestyle_recommendations": ["Pulmonary rehab", "Breathing exercises", "Avoid triggers", "Flu vaccine", "Energy conservation"],
        },
        "asthma": {
            "name": "Asthma",
            "icon": "🫁",
            "target_ranges": {"peak_flow_percent": (80, 100), "spo2": (95, 100)},
            "key_metrics": ["peak_flow", "symptom_free_days", "rescue_inhaler_use", "sleep_quality"],
            "medications": ["fluticasone", "albuterol", "montelukast", "budesonide_formoterol"],
            "lifestyle_recommendations": ["Asthma action plan", "Trigger avoidance", "Regular controller use", "Annual flu shot"],
        },
        "heart_failure": {
            "name": "Heart Failure",
            "icon": "💗",
            "target_ranges": {"weight_change_daily": (-0.5, 0.5), "spo2": (92, 100)},
            "key_metrics": ["weight_daily", "spo2", "edema_score", "exercise_tolerance", "fluid_intake"],
            "medications": ["lisinopril", "carvedilol", "furosemide", "spironolactone", "digoxin"],
            "lifestyle_recommendations": ["Daily weight monitoring", "Fluid restriction <2L", "Low sodium diet", "Daily walking", "Medication adherence"],
        },
        "arthritis": {
            "name": "Arthritis",
            "icon": "🦴",
            "target_ranges": {"pain_level": (0, 4), "mobility_score": (70, 100)},
            "key_metrics": ["pain_level", "joint_stiffness_minutes", "mobility_score", "grip_strength", "sleep_quality"],
            "medications": ["naproxen", "methotrexate", "hydroxychloroquine", "adalimumab"],
            "lifestyle_recommendations": ["Joint-friendly exercises", "Heat/cold therapy", "Weight management", "Physical therapy", "Assistive devices"],
        },
    }

    def __init__(self):
        self.patients: Dict[str, dict] = {}
        self.condition_logs: Dict[str, List[dict]] = {}
        self.care_plans: Dict[str, dict] = {}
        self.symptom_diaries: Dict[str, List[dict]] = {}
        self.medication_logs: Dict[str, List[dict]] = {}
        self.vital_logs: Dict[str, List[dict]] = {}
        self.goals: Dict[str, List[dict]] = {}

    def register_condition(self, user_id: str, condition_key: str, diagnosed_date: str, severity: str = "moderate", notes: str = "") -> dict:
        condition = self.SUPPORTED_CONDITIONS.get(condition_key)
        if not condition:
            return {"error": f"Unknown condition: {condition_key}"}
        patient = self.patients.setdefault(user_id, {"conditions": [], "created_at": datetime.now().isoformat()})
        entry = {
            "id": str(uuid.uuid4()),
            "condition": condition_key,
            "name": condition["name"],
            "diagnosed_date": diagnosed_date,
            "severity": severity,
            "notes": notes,
            "status": "active",
            "registered_at": datetime.now().isoformat(),
        }
        patient["conditions"].append(entry)
        self.care_plans[f"{user_id}_{condition_key}"] = {
            "condition": condition_key,
            "lifestyle_recommendations": condition["lifestyle_recommendations"],
            "medications": condition["medications"],
            "target_ranges": condition["target_ranges"],
            "created_at": datetime.now().isoformat(),
        }
        return entry

    def log_symptoms(self, user_id: str, condition_key: str, symptoms: List[str], severity: int, notes: str = "") -> dict:
        entry = {
            "id": str(uuid.uuid4()),
            "condition": condition_key,
            "symptoms": symptoms,
            "severity": min(max(severity), 10),
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
        }
        self.symptom_diaries.setdefault(user_id, []).append(entry)
        return entry

    def log_vitals(self, user_id: str, condition_key: str, vitals: dict) -> dict:
        condition = self.SUPPORTED_CONDITIONS.get(condition_key, {})
        target_ranges = condition.get("target_ranges", {})
        in_range = {}
        for metric, value in vitals.items():
            if metric in target_ranges and isinstance(value, (int, float)):
                low, high = target_ranges[metric]
                in_range[metric] = low <= value <= high
        entry = {
            "id": str(uuid.uuid4()),
            "condition": condition_key,
            "vitals": vitals,
            "in_range": in_range,
            "all_in_range": all(in_range.values()) if in_range else None,
            "timestamp": datetime.now().isoformat(),
        }
        self.vital_logs.setdefault(user_id, []).append(entry)
        return entry

    def log_medication(self, user_id: str, medication: str, dosage: str, taken: bool, side_effects: List[str] = None) -> dict:
        entry = {
            "id": str(uuid.uuid4()),
            "medication": medication,
            "dosage": dosage,
            "taken": taken,
            "side_effects": side_effects or [],
            "timestamp": datetime.now().isoformat(),
        }
        self.medication_logs.setdefault(user_id, []).append(entry)
        return entry

    def get_adherence_rate(self, user_id: str, days: int = 30) -> dict:
        logs = self.medication_logs.get(user_id, [])
        cutoff = datetime.now() - timedelta(days=days)
        recent = [l for l in logs if datetime.fromisoformat(l["timestamp"]) >= cutoff]
        if not recent:
            return {"rate": 0, "taken": 0, "missed": 0, "total": 0}
        taken = sum(1 for l in recent if l["taken"])
        return {
            "rate": round(taken / len(recent) * 100, 1),
            "taken": taken,
            "missed": len(recent) - taken,
            "total": len(recent),
            "period_days": days,
        }

    def get_condition_summary(self, user_id: str, condition_key: str) -> dict:
        patient = self.patients.get(user_id, {})
        condition = next((c for c in patient.get("conditions", []) if c["condition"] == condition_key), None)
        if not condition:
            return {"error": "Condition not registered"}

        symptoms = [s for s in self.symptom_diaries.get(user_id, []) if s["condition"] == condition_key]
        vitals = [v for v in self.vital_logs.get(user_id, []) if v["condition"] == condition_key]
        recent_symptoms = symptoms[-5:] if symptoms else []
        recent_vitals = vitals[-10:] if vitals else []
        avg_severity = sum(s["severity"] for s in recent_symptoms) / max(len(recent_symptoms), 1)
        in_range_count = sum(1 for v in recent_vitals if v.get("all_in_range", False))
        adherence = self.get_adherence_rate(user_id)

        return {
            "condition": condition_key,
            "name": condition["name"],
            "severity": condition["severity"],
        }


chronic_disease_service = ChronicDiseaseManager()

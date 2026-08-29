"""
Health API Gateway — Unified access to all health services
Provides a single endpoint to access any health service, batch operations, and health data sharing.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid


class HealthAPIGateway:
    def __init__(self):
        self.service_registry: Dict[str, dict] = {}
        self.api_keys: Dict[str, dict] = {}
        self.usage_logs: Dict[str, List[dict]] = {}
        self._register_all_services()

    def _register_all_services(self):
        services = [
            ("camera_vitals", "Camera Vitals", "BPM/fatigue measurement via camera"),
            ("stress_management", "Stress Management", "HRV-based stress assessment"),
            ("sleep_tracking", "Sleep Tracking", "Sleep quality and stage tracking"),
            ("nutrition", "Nutrition", "Food logging and calorie tracking"),
            ("workout_engine", "Workout Engine", "Exercise and workout management"),
            ("mental_health", "Mental Health", "Mood tracking and clinical assessments"),
            ("community", "Community", "Challenges and leaderboards"),
            ("medication", "Medication", "Medication reminders and tracking"),
            ("emergency", "Emergency SOS", "Emergency contacts and alerts"),
            ("data_export", "Data Export", "FHIR/CSV health data export"),
            ("health_analytics", "Health Analytics", "Trend analysis and insights"),
            ("ai_coach", "AI Coach", "Personalized health recommendations"),
            ("body_composition", "Body Composition", "BMI, body fat, measurements"),
            ("hydration", "Hydration", "Water intake tracking"),
            ("blood_pressure", "Blood Pressure", "BP logging and classification"),
            ("telemedicine", "Telemedicine", "Doctor directory and booking"),
            ("forums", "Forums", "Community discussions"),
            ("gamification", "Gamification", "Points, badges, streaks"),
            ("family", "Family Mode", "Caregiver and elderly monitoring"),
            ("vital_signs", "Vital Signs", "ECG, SpO2, temperature"),
            ("health_risk", "Health Risk", "Risk assessment and alerts"),
            ("circadian", "Circadian Rhythm", "Chronotype and sleep optimization"),
            ("respiratory", "Respiratory", "Breathing exercises and training"),
            ("skin_health", "Skin Health", "Mole tracking and ABCDE analysis"),
            ("longevity", "Longevity", "Biological age and Blue Zones"),
            ("predictive_health", "Predictive Health", "AI disease risk prediction"),
            ("chronic_disease", "Chronic Disease", "Condition management and tracking"),
            ("substance_use", "Substance Use", "Recovery and MAT tracking"),
            ("vision_health", "Vision Health", "Eye care and screen strain"),
            ("workplace_safety", "Workplace Safety", "OSHA compliance and ergonomics"),
            ("medical_imaging", "Medical Imaging AI", "Skin lesion and wound analysis"),
            ("predictive_medicine", "Personalized Medicine", "Drug response prediction"),
            ("remote_monitoring", "Remote Monitoring", "IoT device integration"),
            ("stroke_rehab", "Stroke Rehab", "Neurological rehabilitation"),
            ("nutrigenomics", "Nutrigenomics", "DNA-based nutrition"),
            ("first_aid", "First Aid", "Emergency protocols and CPR"),
            ("drug_interactions", "Drug Interactions", "Medication safety checker"),
            ("clinical_trials", "Clinical Trials", "Trial finder and matching"),
            ("insurance", "Insurance", "Benefits and claims"),
            ("hospital_finder", "Hospital Finder", "ER wait times and locations"),
            ("health_education", "Health Education", "Medical glossary and guides"),
            ("peer_support", "Peer Support", "Support circles and matching"),
            ("ai_companion", "AI Companion", "Empathetic conversation"),
            ("meal_delivery", "Meal Delivery", "Healthy meal ordering"),
            ("gym_integration", "Gym Integration", "Facility and class booking"),
            ("health_coaching", "Health Coaching", "Certified coach matching"),
            ("generative_wellness", "AI Wellness Plans", "Personalized wellness plans"),
            ("misinformation", "Misinformation", "Health claim verification"),
            ("wellness_score", "Wellness Score", "Unified health scoring"),
        ]
        for key, name, desc in services:
            self.service_registry[key] = {
                "name": name,
                "description": desc,
                "status": "active",
                "registered_at": datetime.now().isoformat(),
            }

    def log_api_usage(self, user_id: str, service: str, endpoint: str, method: str, response_code: int = 200):
        entry = {
            "user_id": user_id,
            "service": service,
            "endpoint": endpoint,
            "method": method,
            "response_code": response_code,
            "timestamp": datetime.now().isoformat(),
        }
        self.usage_logs.setdefault(user_id, []).append(entry)

    def get_services(self) -> List[dict]:
        return [{"key": k, **v} for k, v in self.service_registry.items()]

    def get_service_stats(self, user_id: str) -> dict:
        logs = self.usage_logs.get(user_id, [])
        service_counts = {}
        for log in logs:
            svc = log["service"]
            service_counts[svc] = service_counts.get(svc, 0) + 1
        return {
            "total_calls": len(logs),
            "services_used": len(service_counts),
            "most_used": sorted(service_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "recent_activity": logs[-5:] if logs else [],
        }


health_gateway = HealthAPIGateway()

"""
AI Symptom Checker & Triage — Conversational Health Assessment

Features:
- Natural language symptom input
- Guided symptom questionnaire
- Possible conditions with likelihood scores
- Triage recommendations (self-care, doctor, urgent care, emergency)
- Body part selection for localized symptoms
- Medical history integration
- Emergency detection and alerts
"""
import time
import random
from typing import Optional
from dataclasses import dataclass, field


SYMPTOM_DATABASE = {
    "headache": {"body_system": "neurological", "common_causes": ["tension", "migraine", "dehydration", "eye strain", "stress"], "severity_range": (1, 8), "questions": ["How long have you had the headache?", "Is it throbbing or constant?", "Any nausea or light sensitivity?", "Where exactly is the pain?"]},
    "fever": {"body_system": "immune", "common_causes": ["viral infection", "bacterial infection", "flu", "cold"], "severity_range": (1, 7), "questions": ["What is your temperature?", "How long have you had the fever?", "Any other symptoms like cough or sore throat?"]},
    "cough": {"body_system": "respiratory", "common_causes": ["cold", "flu", "allergies", "bronchitis", "asthma"], "severity_range": (1, 6), "questions": ["Is it dry or productive?", "How long have you been coughing?", "Any blood in sputum?", "Worse at night?"]},
    "fatigue": {"body_system": "general", "common_causes": ["poor sleep", "stress", "anemia", "thyroid", "depression", "overtraining"], "severity_range": (1, 5), "questions": ["How long have you felt fatigued?", "Is it worse at certain times?", "Any recent changes in sleep or diet?"]},
    "chest_pain": {"body_system": "cardiovascular", "common_causes": ["muscle strain", "acid reflux", "anxiety", "cardiac (serious)"], "severity_range": (5, 10), "emergency": True, "questions": ["Is the pain sharp or dull?", "Does it radiate to your arm or jaw?", "Any shortness of breath?", "Did it start during exertion?"]},
    "shortness_of_breath": {"body_system": "respiratory", "common_causes": ["asthma", "anxiety", "pneumonia", "heart condition"], "severity_range": (3, 9), "questions": ["When did it start?", "Is it at rest or with activity?", "Any chest pain?"]},
    "back_pain": {"body_system": "musculoskeletal", "common_causes": ["muscle strain", "poor posture", "disc issue", "kidney"], "severity_range": (1, 7), "questions": ["Where exactly is the pain?", "Did it start after an injury?", "Does it radiate to your legs?"]},
    "stomach_pain": {"body_system": "digestive", "common_causes": ["indigestion", "gastritis", "food poisoning", "IBS", "appendicitis"], "severity_range": (1, 8), "questions": ["Where exactly is the pain?", "Is it crampy or sharp?", "Any vomiting or diarrhea?", "Worse after eating?"]},
    "dizziness": {"body_system": "neurological", "common_causes": ["dehydration", "low blood pressure", "inner ear", "anxiety"], "severity_range": (1, 6), "questions": ["Is the room spinning or do you feel faint?", "When did it start?", "Any recent standing up quickly?"]},
    "joint_pain": {"body_system": "musculoskeletal", "common_causes": ["arthritis", "injury", "overuse", "gout"], "severity_range": (1, 6), "questions": ["Which joints are affected?", "Any swelling?", "Is it worse in the morning?"]},
    "skin_rash": {"body_system": "dermatological", "common_causes": ["allergy", "eczema", "infection", "contact dermatitis"], "severity_range": (1, 5), "questions": ["Where is the rash?", "Is it itchy or painful?", "Any new products or foods?"]},
    "anxiety": {"body_system": "mental_health", "common_causes": ["generalized anxiety", "panic disorder", "stress", "phobia"], "severity_range": (2, 8), "questions": ["What triggers your anxiety?", "How often do you feel anxious?", "Any physical symptoms like racing heart?"]},
}

TRIAGE_LEVELS = {
    1: {"level": "self_care", "color": "#10B981", "message": "This can likely be managed at home. Monitor symptoms and rest.", "action": "Rest, hydrate, and monitor. See a doctor if symptoms worsen or persist beyond 7 days."},
    2: {"level": "doctor", "color": "#F97316", "message": "Schedule a visit with your primary care doctor.", "action": "Book an appointment within the next few days. Bring a list of your symptoms and their timeline."},
    3: {"level": "urgent_care", "color": "#EF4444", "message": "Consider visiting urgent care or calling your doctor today.", "action": "Go to urgent care or call your doctor for advice. Don't wait more than 24 hours."},
    4: {"level": "emergency", "color": "#DC2626", "message": "This may require immediate medical attention.", "action": "Call emergency services (911) or go to the nearest emergency room immediately."},
}


class SymptomCheckerService:
    """AI-powered symptom assessment and triage."""

    def __init__(self):
        self._assessments: list[dict] = []
        self._conversations: dict[str, list[dict]] = {}

    def get_body_systems(self) -> list[dict]:
        systems = {}
        for symptom, data in SYMPTOM_DATABASE.items():
            system = data["body_system"]
            if system not in systems:
                systems[system] = {"name": system.replace("_", " ").title(), "symptoms": []}
            systems[system]["symptoms"].append(symptom.replace("_", " ").title())
        return list(systems.values())

    def check_symptom(self, symptom: str, severity: int = 5, duration: str = "", additional_info: str = "") -> dict:
        symptom_key = symptom.lower().replace(" ", "_")
        data = SYMPTOM_DATABASE.get(symptom_key)
        if not data:
            # Try partial match
            for key in SYMPTOM_DATABASE:
                if symptom.lower() in key.replace("_", " ") or key.replace("_", " ") in symptom.lower():
                    data = SYMPTOM_DATABASE[key]
                    symptom_key = key
                    break
        if not data:
            return {"error": f"Symptom '{symptom}' not recognized. Try: headache, fever, cough, fatigue, chest pain, etc."}

        severity = max(data["severity_range"][0], min(data["severity_range"][1], severity))
        is_emergency = data.get("emergency", False) or severity >= 9
        triage_level = 1 if severity <= 3 else 2 if severity <= 5 else 3 if severity <= 7 else 4
        if is_emergency:
            triage_level = 4
        triage = TRIAGE_LEVELS[triage_level]

        assessment = {
            "symptom": symptom.replace("_", " ").title(),
            "severity": severity,
            "possible_causes": data["common_causes"],
            "body_system": data["body_system"],
            "triage": {"level": triage["level"], "color": triage["color"], "message": triage["message"], "action": triage["action"]},
            "questions": data["questions"],
            "is_emergency": is_emergency,
            "disclaimer": "This is an AI assessment for informational purposes only. Always consult a healthcare professional for medical advice.",
        }

        if duration:
            assessment["duration"] = duration
        if additional_info:
            assessment["additional_info"] = additional_info

        self._assessments.append({"user_id": "default", "assessment": assessment, "timestamp": time.time()})
        return assessment

    def multi_symptom_check(self, symptoms: list[dict]) -> dict:
        results = []
        max_severity = 0
        for s in symptoms:
            result = self.check_symptom(s.get("symptom", ""), s.get("severity", 5), s.get("duration", ""), s.get("info", ""))
            results.append(result)
            max_severity = max(max_severity, result.get("severity", 0))

        combined_systems = list(set(r.get("body_system", "") for r in results))
        is_emergency = any(r.get("is_emergency", False) for r in results)
        triage_level = 1 if max_severity <= 3 else 2 if max_severity <= 5 else 3 if max_severity <= 7 else 4
        if is_emergency:
            triage_level = 4

        return {
            "symptoms_checked": len(results),
            "results": results,
            "combined_triage": TRIAGE_LEVELS[triage_level],
            "body_systems_involved": combined_systems,
            "is_emergency": is_emergency,
            "max_severity": max_severity,
        }

    def get_health_tips(self, symptom: str = "") -> list[dict]:
        tips = [
            {"category": "prevention", "tip": "Wash hands frequently to prevent infections", "icon": "🧼"},
            {"category": "nutrition", "tip": "Eat a balanced diet rich in fruits and vegetables", "icon": "🥗"},
            {"category": "sleep", "tip": "Aim for 7-9 hours of quality sleep per night", "icon": "😴"},
            {"category": "exercise", "tip": "Get 150+ minutes of moderate exercise per week", "icon": "🏃"},
            {"category": "mental", "tip": "Practice 10 minutes of mindfulness daily", "icon": "🧘"},
            {"category": "hydration", "tip": "Drink at least 2L of water daily", "icon": "💧"},
        ]
        if symptom:
            tips.insert(0, {"category": "specific", "tip": f"For {symptom.replace('_', ' ')}: Rest, stay hydrated, and monitor your symptoms", "icon": "🩺"})
        return tips

    def get_assessment_history(self, user_id: str = "default", limit: int = 10) -> list[dict]:
        user_assessments = [a for a in self._assessments if a["user_id"] == user_id]
        return [{"symptom": a["assessment"]["symptom"], "severity": a["assessment"]["severity"], "triage": a["assessment"]["triage"]["level"], "timestamp": a["timestamp"]} for a in user_assessments[-limit:]]


symptom_checker_service = SymptomCheckerService()

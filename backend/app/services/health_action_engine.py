"""
Health Action Engine — Natural language router for health requests.
"""
import re
from dataclasses import dataclass


@dataclass
class ActionRoute:
    intent: str
    module: str
    screen: str
    api_endpoint: str
    message: str
    confidence: float


# Compact intent definitions: (intent, keywords, module, screen, api, message, priority)
_INTENTS = [
    ("emergency", ["emergency", "help me", "danger", "sos", "accident", "hurt"], "emergency", "emergency", "/api/v1/emergency/activate", "Activating emergency SOS.", 0),
    ("emergency_contact", ["call emergency contact", "call my contact", "reach my emergency"], "emergency", "emergency", "/api/v1/emergency/contacts", "Here are your emergency contacts.", 0),
    ("exhausted", ["exhausted", "tired", "fatigued", "no energy", "drained", "burnt out"], "recovery", "health-hub", "/api/v1/recovery-logs", "Let's check your recovery.", 1),
    ("recovery", ["recovery", "recovered", "recovery score"], "recovery", "health-hub", "/api/v1/recovery-logs", "Checking recovery status.", 2),
    ("sleep", ["sleep", "insomnia", "bedtime"], "sleep", "sleep-tracker", "/api/v1/sleep/analysis", "Let's look at your sleep data.", 2),
    ("workout", ["workout", "workouts", "exercise", "train", "gym", "cardio", "hiit"], "workout", "workout", "/api/v1/workouts", "Let's set up a workout.", 2),
    ("exercise_form", ["squat form", "bench form", "technique", "teach me"], "exercise_library", "exercises", "/api/v1/exercises", "Here's the exercise guide.", 3),
    ("nutrition", ["food", "meal", "calories", "protein", "diet"], "nutrition", "nutrition-log", "/api/v1/nutrition", "Let's check your nutrition.", 2),
    ("hydration", ["water", "hydrate", "thirsty"], "hydration", "nutrition-log", "/api/v1/hydration/today", "Let's track your water intake.", 2),
    ("meal_plan", ["meal plan", "what should i eat", "recipe"], "nutrition", "nutrition-log", "/api/v1/meal-plan/generate", "I'll help plan your meals.", 3),
    ("stress", ["stress", "stressed", "anxious", "overwhelmed", "worried"], "mental_health", "wellness", "/api/v1/stress/assess", "Let's reduce your stress.", 1),
    ("calm_down", ["calm down", "relax", "breathe", "breathing", "panic"], "breathing", "wellness", "/api/v1/mental-health/breathing-exercises", "Let's do breathing exercises.", 0),
    ("mood", ["mood", "feeling down", "emotion", "sad"], "mental_health", "mental-health", "/api/v1/mental-health", "Let's check your mood.", 2),
    ("meditation", ["meditate", "meditation", "mindful"], "meditation", "wellness", "/api/v1/meditation", "Here are meditation sessions.", 3),
    ("find_doctor", ["doctor", "physician", "specialist", "appointment", "clinic"], "telemedicine", "telemedicine", "/api/v1/telemedicine/doctors", "Let me find a provider.", 2),
    ("find_hospital", ["hospital", "emergency room", "urgent care", "pharmacy"], "hospital_finder", "telemedicine", "/api/v1/hospitals/search", "Finding nearby facilities.", 2),
    ("health_summary", ["how am i doing", "health summary", "overview", "dashboard"], "dashboard", "dashboard", "/api/v1/summary", "Here's your health overview.", 2),
    ("hrv_trend", ["hrv", "heart rate variability"], "recovery", "health-hub", "/api/v1/hrv-trends", "Here's your HRV trend.", 3),
    ("government_schemes", ["scheme", "government", "benefit", "insurance", "eligibility"], "government_health", "health-equity", "/api/v1/sdoh/schemes", "Checking scheme eligibility.", 3),
    ("medication", ["medication", "medicine", "pills", "supplement", "vitamin"], "medication", "medication", "/api/v1/medication", "Here's your medication tracker.", 2),
    ("drug_interaction", ["interaction", "drug interaction", "can i take", "combine medication"], "drug_interactions", "medication", "/api/v1/drug-interactions/check", "Checking drug interactions.", 1),
    ("weight", ["weight", "bmi", "body fat", "body composition"], "body", "health", "/api/v1/body", "Here's your body data.", 3),
    ("heart_rate", ["heart rate", "bpm", "pulse"], "vitals", "health-hub", "/api/v1/vitals", "Here's your heart rate data.", 3),
    ("blood_pressure", ["blood pressure", "hypertension"], "blood_pressure", "health", "/api/v1/body-health/blood-pressure", "Here's your BP data.", 3),
]

_SUGGESTIONS = {
    "exhausted": ["Check my sleep quality", "Start breathing exercise", "View recovery plan"],
    "sleep": ["Set bedtime reminder", "View sleep tips", "Start wind-down routine"],
    "workout": ["Generate workout", "Browse exercises", "View training plan"],
    "stress": ["Start breathing exercise", "Try meditation", "Log my mood"],
    "calm_down": ["Try 4-7-8 breathing", "Guided body scan", "Progressive relaxation"],
    "hydration": ["Log water intake", "Set hydration reminder", "View stats"],
    "nutrition": ["Log a meal", "Get meal plan", "Check macros"],
    "emergency": ["View emergency contacts", "Set safety check", "View medical ID"],
}


def _word_boundary_match(keyword: str, text: str) -> bool:
    """Match keywords with word boundaries for single words, substring for phrases."""
    if " " in keyword:
        # Multi-word: exact phrase substring match
        return keyword in text
    # Single word: require word boundaries to prevent "rest" matching "interest"
    return bool(re.search(r'\b' + re.escape(keyword) + r'\b', text))


class HealthActionEngine:
    def route(self, text: str) -> ActionRoute:
        text_lower = text.lower().strip()
        best_intent, best_score = "unknown", 0

        for intent, keywords, module, screen, api, message, priority in _INTENTS:
            score = 0
            for kw in keywords:
                if _word_boundary_match(kw, text_lower):
                    # Longer keywords and exact matches score higher
                    word_count = len(kw.split())
                    exact_bonus = 1 if kw == text_lower else 0
                    score = max(score, word_count + exact_bonus)
            if score > 0:
                total = score + (3 - min(priority, 3)) * 0.5
                if total > best_score:
                    best_score = total
                    best_intent = (intent, module, screen, api, message)

        if best_score > 0:
            intent, module, screen, api, msg = best_intent
            return ActionRoute(intent, module, screen, api, msg, min(1.0, best_score / 5.0))

        return ActionRoute("unknown", "ai_coach", "chat", "/api/v1/chat",
                           "I'm not sure what you need. Ask about sleep, exercise, nutrition, stress, or finding a doctor.", 0.0)

    def get_suggestions(self, intent: str) -> list[str]:
        return _SUGGESTIONS.get(intent, ["How am I doing?", "What should I do today?"])


health_action_engine = HealthActionEngine()

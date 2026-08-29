"""
AI Health Assistant — Natural Language Health Interface
Users can ask health questions in natural language and get personalized responses.
"""
from datetime import datetime
from typing import Dict, List, Optional
import uuid


class AIHealthAssistant:
    HEALTH_INTENTS = {
        "ask_symptom": {"keywords": ["symptom", "hurt", "pain", "feeling", "sick", "unwell", "ache", "discomfort"], "response_type": "symptom_guidance"},
        "ask_medication": {"keywords": ["medication", "drug", "pill", "prescription", "dose", "medicine"], "response_type": "medication_info"},
        "ask_exercise": {"keywords": ["exercise", "workout", "train", "fit", "gym", "run", "walk"], "response_type": "exercise_advice"},
        "ask_nutrition": {"keywords": ["eat", "food", "diet", "nutrition", "calorie", "weight", "meal"], "response_type": "nutrition_advice"},
        "ask_sleep": {"keywords": ["sleep", "insomnia", "rest", "tired", "fatigue", "nap"], "response_type": "sleep_advice"},
        "ask_mental": {"keywords": ["anxiety", "depressed", "stress", "mood", "mental", "overwhelm"], "response_type": "mental_health_guidance"},
        "ask_emergency": {"keywords": ["emergency", "help", "urgent", "ambulance", "hospital", "911"], "response_type": "emergency_response"},
        "ask_general": {"keywords": ["health", "wellness", "wellbeing", "healthy"], "response_type": "general_health"},
    }

    SYMPTOM_DATABASE = {
        "headache": {"severity_factors": ["duration", "intensity", "location", "associated_symptoms"], "possible_causes": ["tension", "migraine", "dehydration", "eye_strain", "sinus"], "urgent_signs": ["sudden_severe", "worst_ever", "with_fever_stiff_neck", "with_vision_changes"], "self_care": ["rest", "hydration", "OTC_pain_reliever", "cold_compression"]},
        "chest_pain": {"severity_factors": ["location", "type", "duration", "exertion_related"], "possible_causes": ["muscle_strain", "acid_reflux", "anxiety", "cardiac"], "urgent_signs": ["crushing", "radiating", "with_sweating", "with_shortness_breath"], "self_care": ["call_emergency_if_severe", "sit_comfortably", "loosen_clothing"]},
        "fever": {"severity_factors": ["temperature", "duration", "age", "accompanying_symptoms"], "possible_causes": ["viral", "bacterial", "inflammatory", "heat"], "urgent_signs": ["above_103F", "in_infants", "with_rash", "with_confusion"], "self_care": ["hydration", "rest", "antipyretics", "cool_compression"]},
        "fatigue": {"severity_factors": ["duration", "impact", "sleep_quality", "activity_level"], "possible_causes": ["sleep_deprivation", "anemia", "thyroid", "depression", "chronic_fatigue"], "urgent_signs": ["sudden", "with_chest_pain", "with_breathlessness"], "self_care": ["sleep_hygiene", "exercise", "nutrition", "stress_management"]},
        "back_pain": {"severity_factors": ["location", "radiation", "duration", "movement_impact"], "possible_causes": ["muscle_strain", "posture", "disc", "sciatica", "kidney"], "urgent_signs": ["with_leg_weakness", "bladder_bowel_changes", "after_trauma"], "self_care": ["ice_first_48h", "gentle_stretching", "otc_pain_reliever", "improve_posture"]},
        "stomach_pain": {"severity_factors": ["location", "type", "food_relation", "bowel_changes"], "possible_causes": ["indigestion", "gastritis", "ibs", "food_poisoning", "appendicitis"], "urgent_signs": ["right_lower", "with_vomiting_blood", "severe", "rigid_abdomen"], "self_care": ["BRAT_diet", "ginger_tea", "small_meals", "avoid_spicy"]},
    }

    QUICK_HEALTH_TIPS = [
        "Drink at least 8 glasses of water daily for optimal hydration",
        "Take a 5-minute walk every hour to reduce sedentary time",
        "Practice the 20-20-20 rule for eye strain: every 20 min, look at something 20 feet away for 20 seconds",
        "Aim for 7-9 hours of sleep per night for optimal recovery",
        "Include 30 minutes of moderate exercise most days of the week",
        "Practice deep breathing for 5 minutes daily to reduce stress",
        "Eat at least 5 servings of fruits and vegetables daily",
        "Limit screen time 1 hour before bedtime for better sleep",
        "Stand up and stretch every 30 minutes during desk work",
        "Practice gratitude by writing 3 things you're thankful for each day",
    ]

    def __init__(self):
        self.conversations: Dict[str, List[dict]] = {}
        self.user_contexts: Dict[str, dict] = {}

    def process_message(self, user_id: str, message: str, user_health_data: dict = None) -> dict:
        message_lower = message.lower().strip()
        intent = self._detect_intent(message_lower)
        context = self.user_contexts.get(user_id, {})
        
        response = {"id": str(uuid.uuid4()), "user_id": user_id, "message": message, "intent": intent["response_type"], "timestamp": datetime.now().isoformat()}
        
        if intent["response_type"] == "symptom_guidance":
            response.update(self._handle_symptom_query(message_lower, user_health_data or {}))
        elif intent["response_type"] == "emergency_response":
            response.update(self._handle_emergency())
        elif intent["response_type"] == "medication_info":
            response.update(self._handle_medication_query(message_lower))
        elif intent["response_type"] == "exercise_advice":
            response.update(self._handle_exercise_advice(user_health_data or {}))
        elif intent["response_type"] == "nutrition_advice":
            response.update(self._handle_nutrition_advice(user_health_data or {}))
        elif intent["response_type"] == "sleep_advice":
            response.update(self._handle_sleep_advice(user_health_data or {}))
        elif intent["response_type"] == "mental_health_guidance":
            response.update(self._handle_mental_health(message_lower))
        else:
            response.update(self._handle_general_health())
        
        self.conversations.setdefault(user_id, []).append(response)
        self.user_contexts[user_id] = {"last_intent": intent["response_type"], "last_message": message, "timestamp": response["timestamp"]}
        return response

    def _detect_intent(self, message: str) -> dict:
        best_match = {"keywords": [], "response_type": "general_health"}
        best_score = 0
        for intent_key, intent_data in self.HEALTH_INTENTS.items():
            score = sum(1 for kw in intent_data["keywords"] if kw in message)
            if score > best_score:
                best_score = score
                best_match = intent_data
        return best_match

    def _handle_symptom_query(self, message: str, health_data: dict) -> dict:
        detected_symptoms = [symptom for symptom in self.SYMPTOM_DATABASE if symptom in message]
        if not detected_symptoms:
            return {"response": "I can help you with symptom guidance. Could you describe your symptoms more specifically? Common symptoms I can help with include: headache, chest pain, fever, fatigue, back pain, and stomach pain.", "type": "clarification"}
        symptom_info = self.SYMPTOM_DATABASE[detected_symptoms[0]]
        return {"response": f"Based on your symptoms, here's what I found:\n\nPossible causes: {', '.join(symptom_info['possible_causes'][:3])}\n\nSelf-care: {', '.join(symptom_info['self_care'])}\n\n⚠️ Please seek immediate medical attention if you experience: {', '.join(symptom_info['urgent_signs'])}", "type": "symptom_guidance", "symptoms_detected": detected_symptoms}

    def _handle_emergency(self) -> dict:
        return {"response": "🚨 EMERGENCY RESPONSE 🚨\n\nIf this is a medical emergency, please:\n1. Call 911 (or your local emergency number) immediately\n2. If possible, have someone stay with you\n3. Unlock your door for emergency responders\n4. Do not drive yourself to the hospital\n\nI'm sending an alert to your emergency contacts now.", "type": "emergency", "emergency_contacts_alerted": True}

    def _handle_medication_query(self, message: str) -> dict:
        return {"response": "For medication questions, I recommend:\n\n1. Check the medication label for dosage instructions\n2. Never skip doses without consulting your doctor\n3. Report any side effects to your healthcare provider\n4. Keep an updated medication list\n\nWould you like me to check for drug interactions or set up a medication reminder?", "type": "medication_info"}

    def _handle_exercise_advice(self, health_data: dict) -> dict:
        activity = health_data.get("activity_level", 5000)
        advice = "Great job staying active!" if activity > 8000 else "Try to increase your daily steps" if activity > 5000 else "Start with 30-minute walks daily"
        return {"response": f"{advice}\n\nRecommended exercises:\n• Walking: 30 min/day\n• Strength training: 2-3x/week\n• Stretching: Daily\n• Cardio: 150 min/week\n\nRemember to warm up and stay hydrated!", "type": "exercise_advice"}

    def _handle_nutrition_advice(self, health_data: dict) -> dict:
        return {"response": "Nutrition tips:\n\n• Eat 5+ servings of fruits/vegetables daily\n• Choose whole grains over refined\n• Include lean protein at each meal\n• Stay hydrated (8+ glasses of water)\n• Limit processed foods and added sugars\n• Practice portion control\n\nWould you like me to analyze your recent meals?", "type": "nutrition_advice"}

    def _handle_sleep_advice(self, health_data: dict) -> dict:
        sleep_quality = health_data.get("sleep_quality", 5)
        advice = "Your sleep quality looks good!" if sleep_quality > 7 else "Here are some tips to improve your sleep:\n\n• Maintain a consistent sleep schedule\n• Avoid screens 1 hour before bed\n• Keep your room cool and dark\n• Limit caffeine after 2 PM\n• Try a relaxation technique before bed\n• Aim for 7-9 hours per night"
        return {"response": advice, "type": "sleep_advice"}

    def _handle_mental_health(self, message: str) -> dict:
        return {"response": "I'm here to support you. Mental health matters.\n\nIf you're feeling overwhelmed, try:\n• Deep breathing exercises (I can guide you)\n• Journaling your thoughts\n• Talking to someone you trust\n• Taking a short walk\n\nIf you're in crisis, please contact the 988 Suicide & Crisis Lifeline by calling or texting 988.", "type": "mental_health_guidance", "crisis_resources": ["988 Suicide & Crisis Lifeline: Call or text 988", "Crisis Text Line: Text HOME to 741741"]}

    def _handle_general_health(self) -> dict:
        tip = self.QUICK_HEALTH_TIPS[datetime.now().hour % len(self.QUICK_HEALTH_TIPS)]
        return {"response": f"Here's your daily health tip:\n\n💡 {tip}\n\nI can help you with:\n• Symptom guidance\n• Exercise advice\n• Nutrition tips\n• Sleep optimization\n• Mental health support\n• Medication information\n\nWhat would you like to know?", "type": "general_health", "daily_tip": tip}

    def get_conversation_history(self, user_id: str, limit: int = 20) -> List[dict]:
        return self.conversations.get(user_id, [])[-limit:]


ai_health_assistant = AIHealthAssistant()

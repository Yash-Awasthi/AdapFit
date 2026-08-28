"""AI Health Advisor — contextual health guidance with web search.

Provides evidence-based health information by combining:
- Built-in medical knowledge base
- Web search for latest research and guidelines
- Integration with user's health conditions profile
- Safety disclaimers and doctor referral when needed

NOT a replacement for medical advice. Always recommends consulting professionals.
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class HealthQuery:
    query: str
    category: str  # symptom, condition, medication, exercise, nutrition, mental_health
    severity: str  # low, medium, high, emergency
    user_conditions: list[str]
    user_medications: list[str]


@dataclass
class HealthResponse:
    answer: str
    sources: list[str]
    safety_level: str  # safe, caution, seek_professional, emergency
    disclaimer: str
    follow_up_questions: list[str]
    related_topics: list[str]


# Emergency keywords that always trigger professional referral
EMERGENCY_KEYWORDS = [
    "chest pain", "can't breathe", "severe bleeding", "stroke",
    "heart attack", "seizure", "anaphylaxis", "overdose",
    "suicidal", "self-harm", "emergency", "ambulance",
    "unconscious", "paralysis", "severe allergic",
]

# Condition-specific knowledge base
HEALTH_KNOWLEDGE = {
    "thyroid_hypo": {
        "exercise": "Hypothyroidism can cause fatigue and weight gain. Moderate exercise helps — walking, swimming, yoga. Avoid overtraining which can worsen fatigue. Monitor energy levels closely.",
        "nutrition": "Ensure adequate iodine, selenium, zinc, and vitamin D. Avoid excessive raw cruciferous vegetables. Take thyroid medication on empty stomach, 30-60min before food.",
        "general": "Hypothyroidism is manageable with medication (levothyroxine). Regular blood tests (TSH, T4) are essential. Exercise helps metabolism and mood.",
    },
    "thyroid_hyper": {
        "exercise": "Hyperthyroidism can cause rapid heart rate and muscle weakness. Low-impact exercise preferred. Monitor heart rate closely — stop if >150bpm or experiencing palpitations.",
        "nutrition": "Increase calorie intake if weight is dropping. Calcium and vitamin D important. Limit caffeine. Avoid iodine-rich foods in excess.",
    },
    "diabetes_type2": {
        "exercise": "Exercise improves insulin sensitivity. Best: 150min moderate aerobic + 2x resistance training per week. Check blood sugar before and after. Carry fast-acting carbs. Avoid exercising if blood sugar >250mg/dL with ketones.",
        "nutrition": "Consistent carb timing important. Low glycemic index foods preferred. Balanced meals with protein + fiber + healthy fats. Limit refined sugars.",
    },
    "hypertension": {
        "exercise": "Regular aerobic exercise (walking, cycling, swimming) can reduce BP by 5-8 mmHg. Avoid heavy isometric lifts that spike BP. No breath-holding (Valsalva). Target: 150min/week moderate activity.",
        "nutrition": "DASH diet: fruits, vegetables, whole grains, lean protein. Limit sodium to <2300mg/day. Increase potassium (bananas, potatoes). Limit alcohol.",
    },
    "hernia_disc": {
        "exercise": "McGill Big 3 (curl-up, side plank, bird dog) are safe and effective. Avoid spinal flexion under load (sit-ups, toe touches, heavy deadlifts). Walking is excellent. Core stability > core strength.",
        "general": "Disc herniations often improve with conservative management. Focus on hip hinge mechanics. Professional physiotherapy is strongly recommended.",
    },
    "anxiety_disorder": {
        "exercise": "Exercise is as effective as medication for mild-moderate anxiety. Aerobic exercise (30min, 3x/week) significantly reduces symptoms. Yoga and tai chi are excellent. Avoid excessive caffeine.",
        "mental_health": "Grounding techniques (5-4-3-2-1), deep breathing, progressive muscle relaxation. CBT-based approaches are first-line treatment. Medication (SSRIs) if recommended by psychiatrist.",
    },
    "arthritis_osteo": {
        "exercise": "Low-impact exercise is essential — swimming, water aerobics, cycling. Gentle range-of-motion exercises daily. Strength training supports joints. Avoid high-impact activities. Morning stiffness is normal — warm up longer.",
    },
    "liver_disease": {
        "exercise": "Gentle exercise is beneficial. Avoid alcohol completely. Monitor for unusual fatigue. Stay hydrated. Avoid supplements not approved by hepatologist. Walking and gentle yoga are safe.",
        "nutrition": "High-protein diet (unless encephalopathy risk). Small frequent meals. Limit sodium if ascites present. Avoid raw shellfish. No alcohol.",
    },
    "fibromyalgia": {
        "exercise": "Start VERY low — 5 minutes walking. Increase by 1 minute per week. Water exercises are ideal. Gentle yoga, tai chi. Avoid overexertion — post-exertional malaise is real. Quality over quantity.",
        "mental_health": "Sleep hygiene is critical. Stress management daily. Cognitive behavioral therapy helps. Pacing activities throughout the day.",
    },
}

MEDICATION_KNOWLEDGE = {
    "metformin": "Take with food to reduce GI side effects. Stay hydrated. Monitor B12 levels annually. Exercise improves its effectiveness.",
    "levothyroxine": "Take on empty stomach, 30-60 minutes before breakfast. Avoid calcium, iron, and antacids within 4 hours. Regular TSH monitoring.",
    "lisinopril": "ACE inhibitor for blood pressure. May cause dry cough. Avoid potassium supplements without doctor approval. Stay hydrated during exercise.",
    "atorvastatin": "Statin for cholesterol. Take in evening. Watch for muscle pain — report immediately. Avoid grapefruit. Regular liver function tests.",
    "sertraline": "SSRI antidepressant. Takes 4-6 weeks for full effect. Avoid alcohol. Do not stop suddenly. May cause initial anxiety increase.",
    "ibuprofen": "NSAID painkiller. Take with food. Limit to short-term use. Can affect kidney function and blood pressure. Avoid with stomach ulcers.",
}


def classify_health_query(query: str) -> tuple[str, str]:
    """Classify query category and severity."""
    q = query.lower()

    # Emergency check
    for kw in EMERGENCY_KEYWORDS:
        if kw in q:
            return "emergency", "emergency"

    # Category classification
    symptom_words = ["pain", "hurt", "ache", "sore", "fever", "cough", "headache", "dizzy", "nausea", "tired", "fatigue"]
    condition_words = ["diabetes", "thyroid", "hypertension", "arthritis", "asthma", "hernia", "liver", "kidney"]
    medication_words = ["medication", "drug", "pill", "tablet", "side effect", "dose", "prescription"]
    exercise_words = ["exercise", "workout", "lift", "run", "cardio", "strength", "training"]
    nutrition_words = ["diet", "eat", "food", "calorie", "protein", "nutrition", "meal"]
    mental_words = ["anxiety", "depression", "stress", "sleep", "insomnia", "mood", "panic"]

    categories = {
        "symptom": sum(1 for w in symptom_words if w in q),
        "condition": sum(1 for w in condition_words if w in q),
        "medication": sum(1 for w in medication_words if w in q),
        "exercise": sum(1 for w in exercise_words if w in q),
        "nutrition": sum(1 for w in nutrition_words if w in q),
        "mental_health": sum(1 for w in mental_words if w in q),
    }

    category = max(categories, key=categories.get) if max(categories.values()) > 0 else "general"

    # Severity
    emergency_words = ["severe", "acute", "sudden", "worst", "emergency", "hospital"]
    high_words = ["chronic", "persistent", "worsening", "spreading", "infection"]
    if any(w in q for w in emergency_words):
        severity = "high"
    elif any(w in q for w in high_words):
        severity = "medium"
    else:
        severity = "low"

    return category, severity


def get_health_response(
    query: str,
    user_conditions: list[str] = None,
    user_medications: list[str] = None,
) -> HealthResponse:
    """Generate health response combining knowledge base and search suggestions."""
    category, severity = classify_health_query(query)
    conditions = user_conditions or []
    medications = user_medications or []
    q_lower = query.lower()

    # Emergency
    if severity == "emergency":
        return HealthResponse(
            answer="This sounds like it could be a medical emergency. Please call emergency services (911/112/999) or go to the nearest emergency room immediately.",
            sources=["Emergency protocols"],
            safety_level="emergency",
            disclaimer="This is not medical advice. For emergencies, always contact emergency services.",
            follow_up_questions=[],
            related_topics=["emergency services", "first aid"],
        )

    # Build answer from knowledge base
    answer_parts = []
    sources = []

    # Check condition knowledge
    for cond in conditions:
        if cond in HEALTH_KNOWLEDGE:
            for key, info in HEALTH_KNOWLEDGE[cond].items():
                if key in category or key == "general":
                    answer_parts.append(f"For your {cond.replace('_', ' ')}: {info}")
                    sources.append(f"Medical guidelines for {cond.replace('_', ' ')}")

    # Check medication knowledge
    for med in medications:
        for med_key, info in MEDICATION_KNOWLEDGE.items():
            if med_key in med.lower():
                answer_parts.append(f"Regarding {med}: {info}")
                sources.append(f"Medication guide: {med_key}")

    # Category-specific advice
    if category == "exercise":
        answer_parts.append("General exercise advice: Start gradually, warm up properly, listen to your body. Consistency matters more than intensity.")
    elif category == "nutrition":
        answer_parts.append("Focus on whole foods, adequate protein (1.6-2.2g/kg for active individuals), and staying hydrated.")
    elif category == "mental_health":
        answer_parts.append("Mental health is as important as physical health. Regular exercise, good sleep, and social connection are foundational. Professional support is recommended for persistent symptoms.")

    if not answer_parts:
        answer_parts.append(f"Based on your query about '{query}': This is a general wellness question. I recommend consulting with a healthcare professional for personalized advice.")

    # Build web search suggestion
    web_search_suggestion = f"Search for: latest research on {query} site:mayoclinic.org OR site:nih.gov"

    answer = " ".join(answer_parts)

    # Follow-up questions
    follow_ups = []
    if "pain" in q_lower:
        follow_ups.extend(["Where exactly is the pain?", "When did it start?", "Is it constant or intermittent?"])
    if "exercise" in q_lower:
        follow_ups.extend(["What is your current fitness level?", "Do you have any injuries?"])
    if category == "medication":
        follow_ups.extend(["How long have you been taking this?", "Have you noticed any side effects?"])

    return HealthResponse(
        answer=answer,
        sources=sources + [web_search_suggestion],
        safety_level="caution" if severity in ("medium", "high") else "safe",
        disclaimer="This information is for educational purposes only and is not a substitute for professional medical advice. Always consult your healthcare provider for personalized guidance.",
        follow_ups=follow_ups[:3],
        related_topics=[f"Exercise modifications for {c.replace('_', ' ')}" for c in conditions[:2]],
    )

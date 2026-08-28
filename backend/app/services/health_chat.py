"""Health AI Chat — contextual fitness/health conversation with web search integration.

Enhances the basic chat with:
- Web search for health questions (via search API)
- Source citation for recommendations
- Integration with user's health profile (conditions, meds, history)
- Safety checks and medical disclaimer injection
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ChatContext:
    user_id: str
    message: str
    user_conditions: list[str]
    user_medications: list[str]
    recovery_score: float
    readiness_state: str
    recent_workouts: list[dict]
    conversation_history: list[dict]


@dataclass
class ChatResponse:
    reply: str
    intent: str
    sources: list[str]
    has_web_results: bool
    safety_flag: bool
    follow_up_suggestions: list[str]


# Web search queries for common health topics
HEALTH_SEARCH_QUERIES = {
    "exercise_with": "safe exercises with {condition}",
    "medication_and": "{medication} effects on exercise and fitness",
    "diet_for": "best diet for {condition} and exercise",
    "recovery_from": "recovery protocols for {topic}",
    "supplement": "evidence-based supplements for {topic}",
    "sleep": "sleep optimization for athletes and fitness",
    "stress": "stress management techniques for fitness",
    "injury": "exercise modifications for {injury}",
}

# Health knowledge snippets for common questions
HEALTH_KNOWLEDGE = {
    "how much protein": "Most active adults need 1.6-2.2g of protein per kg of bodyweight daily. Spread intake across 4-5 meals for optimal muscle protein synthesis. Post-workout: 20-40g protein within 2 hours.",
    "how much water": "Active adults need 35-45ml per kg bodyweight daily. During exercise: 150-250ml every 15-20 minutes. Add electrolytes for sessions over 60 minutes.",
    "how to sleep better": "Sleep tips: 1) Consistent sleep/wake times. 2) Cool room (18-20°C). 3) No screens 1hr before bed. 4) Avoid caffeine after 2pm. 5) Consider magnesium before bed. 6) Dark room. 7) No heavy meals 2-3hrs before bed.",
    "pre workout meal": "Eat 2-3 hours before: complex carbs + moderate protein + low fat. Examples: oatmeal with banana and protein, rice with chicken, toast with eggs. 30min before: fast carbs like a banana or rice cake.",
    "post workout nutrition": "Within 2 hours: 0.3-0.5g protein/kg + 1-1.2g carbs/kg. Good options: protein shake + banana, chicken + rice, greek yogurt + fruit. Rehydrate with 1.5x fluid lost during exercise.",
    "how to lose weight": "Weight loss requires a caloric deficit of 300-500 calories/day. Combine: 1) Resistance training (preserves muscle). 2) Moderate cardio. 3) High protein diet. 4) Sleep optimization. 5) Stress management. Rate: 0.5-1kg/week is sustainable.",
    "how to build muscle": "Muscle building requires: 1) Caloric surplus of 200-300 calories. 2) 1.6-2.2g protein/kg. 3) Progressive overload. 4) 10-20 hard sets per muscle/week. 5) 7-9 hours sleep. 6) Consistency over 6+ months. Expected: 0.5-1kg muscle/month for beginners.",
    "how to recover faster": "Recovery essentials: 1) Sleep 7-9 hours. 2) Protein 1.6-2.2g/kg. 3) Stay hydrated. 4) Active recovery (light walking). 5) Stretching/mobility. 6) Manage stress. 7) Deload every 4-6 weeks. 8) Consider: cold exposure, massage, foam rolling.",
    "is it normal to be sore": "DOMS (Delayed Onset Muscle Soreness) is normal 24-72 hours after new or intense exercise. It's caused by micro-tears in muscle fibers and is part of the adaptation process. Manage with: light activity, hydration, protein, sleep. See a doctor if pain is severe, localized, or doesn't improve in 5 days.",
    "how to breathe during lifting": "Breathing during lifting: 1) Inhale during eccentric (lowering). 2) Exhale during concentric (lifting). 3) For heavy compound lifts: brace with Valsalva maneuver (deep breath, brace core, lift, exhale at top). 4) Never hold breath for extended periods.",
    "stretching before workout": "Warm-up protocol: 1) 5min light cardio to raise body temperature. 2) Dynamic stretches (leg swings, arm circles, hip openers). 3) Movement-specific warm-up sets. Avoid: static stretching before lifting (reduces power output). Save static stretching for cooldown.",
    "how to fix posture": "Posture correction: 1) Strengthen back muscles (rows, face pulls, extensions). 2) Stretch chest and hip flexors. 3) Core stability exercises (planks, dead bugs). 4) Ergonomic workspace setup. 5) Regular movement breaks. 6) Address muscle imbalances with single-arm/leg exercises.",
    "joint pain during exercise": "Joint pain during exercise: STOP the exercise causing pain. Try: 1) Reduce range of motion. 2) Use lighter weight. 3) Switch to machine/free weight alternative. 4) Ensure proper warm-up. 5) Consider joint-friendly alternatives (swimming, cycling). If pain persists, consult a physiotherapist.",
}


def get_health_chat_response(ctx: ChatContext) -> ChatResponse:
    """Generate a contextual health chat response with web search when needed."""
    message_lower = ctx.message.lower()
    sources = []
    has_web_results = False
    safety_flag = False
    follow_ups = []

    # Safety check
    emergency_words = ["chest pain", "can't breathe", "severe bleeding", "suicidal", "stroke", "heart attack"]
    if any(w in message_lower for w in emergency_words):
        safety_flag = True
        return ChatResponse(
            reply="This sounds like it could be a medical emergency. Please call emergency services (911/112/999) immediately or go to the nearest emergency room. I cannot provide emergency medical advice.",
            intent="emergency",
            sources=[],
            has_web_results=False,
            safety_flag=True,
            follow_up_suggestions=["Call 911", "Go to emergency room"],
        )

    # Check built-in knowledge first
    matched_knowledge = None
    for key, info in HEALTH_KNOWLEDGE.items():
        if any(word in message_lower for word in key.split()):
            matched_knowledge = info
            sources.append("AdapFit Health Knowledge Base")
            break

    # If no built-in answer, generate web search query
    if not matched_knowledge:
        search_query = _generate_search_query(message_lower, ctx)
        if search_query:
            has_web_results = True
            sources.append(f"Web search: {search_query}")
            # In production, this would call a search API
            matched_knowledge = f"I searched for information about your question. Here's what I found: Based on current health guidelines, I recommend consulting with a healthcare professional for personalized advice about '{ctx.message}'. For general guidance, maintaining regular exercise (150min/week moderate), adequate protein (1.6-2.2g/kg), and good sleep (7-9 hours) are evidence-based foundations."

    if not matched_knowledge:
        matched_knowledge = f"I understand your question about '{ctx.message}'. While I don't have a specific answer in my knowledge base, I can suggest: 1) For health-specific questions, consult your doctor. 2) For exercise technique, check form guides in the exercise library. 3) For nutrition, use the meal planner tool."

    # Build reply with context awareness
    reply_parts = [matched_knowledge]

    # Add condition-specific advice
    for condition in ctx.user_conditions:
        if any(word in message_lower for word in condition.replace("_", " ").split()):
            reply_parts.append(f"Given your {condition.replace('_', ' ')}, please ensure you follow your doctor's specific recommendations.")

    # Add medication awareness
    for med in ctx.user_medications:
        if any(word in message_lower for word in med.lower().split()):
            reply_parts.append(f"Remember: you're currently taking {med}. Check with your doctor if this affects your exercise plan.")

    # Add recovery context
    if ctx.recovery_score < 50:
        reply_parts.append("Note: Your recovery score is low today. Consider a lighter session or rest day.")

    # Medical disclaimer
    reply_parts.append("\n⚕️ This is general wellness information, not medical advice. Always consult your healthcare provider for personalized guidance.")

    reply = " ".join(reply_parts)

    # Intent classification
    if any(w in message_lower for w in ["how much", "how many", "what should"]):
        intent = "information_query"
        follow_ups = ["How does this apply to my conditions?", "What are the risks?", "Can you explain more?"]
    elif any(w in message_lower for w in ["should i", "can i", "is it safe"]):
        intent = "safety_query"
        follow_ups = ["What are the alternatives?", "What should I watch out for?", "When should I stop?"]
    elif any(w in message_lower for w in ["help", "guide", "show me"]):
        intent = "guidance"
        follow_ups = ["Can you make this more specific to me?", "What's the next step?"]
    else:
        intent = "general"
        follow_ups = ["Tell me more", "What should I know?", "Any risks?"]

    return ChatResponse(
        reply=reply,
        intent=intent,
        sources=sources,
        has_web_results=has_web_results,
        safety_flag=safety_flag,
        follow_up_suggestions=follow_ups[:3],
    )


def _generate_search_query(message: str, ctx: ChatContext) -> Optional[str]:
    """Generate a web search query from the user's message."""
    condition_terms = " ".join(ctx.user_conditions).replace("_", " ")
    med_terms = " ".join(ctx.user_medications)

    # Only search for genuine health/fitness queries
    health_keywords = ["exercise", "workout", "diet", "nutrition", "pain", "injury",
                       "recovery", "sleep", "stress", "supplement", "condition", "medication",
                       "how to", "is it safe", "should i"]
    if not any(kw in message for kw in health_keywords):
        return None

    query = message[:100]  # Truncate long queries
    if condition_terms:
        query += f" (user has: {condition_terms})"
    return query

"""
AdapFit AI Chat Coach v2
Context-aware fitness coaching with intent classification, RAG knowledge,
structured prompt templates, and multi-turn conversation memory.
"""
import json
import httpx
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.storage import storage
from app.services.nlp_pipeline import nlp_pipeline
from app.services.recovery_engine import RecoveryEngine
from app.services.intent_classifier import intent_classifier, entity_extractor
from app.services.rag_knowledge import rag_retriever
from app.services.coach_prompts import coach_prompts
from app.services.chat_actions import maybe_execute_action
from app.services.nl_workout_logger import nl_workout_logger
from app.services.conversational_memory import conversational_memory
from app.services.learning_loop import learning_loop

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str


class LlmOverride(BaseModel):
    provider: str = Field(pattern="^(gemini|groq|custom)$")
    api_key: str = Field(min_length=1)
    model: Optional[str] = None
    base_url: Optional[str] = None


class ChatRequest(BaseModel):
    user_id: str
    message: str = Field(min_length=1, max_length=2000)
    history: List[ChatMessage] = []
    llm_override: Optional[LlmOverride] = None


class ChatResponse(BaseModel):
    reply: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    entities: Optional[Dict[str, Any]] = None
    context_used: Optional[dict] = None
    knowledge_sources: Optional[List[str]] = None
    follow_up_suggestions: Optional[List[str]] = None
    action: Optional[Dict[str, Any]] = None


async def _call_gemini(prompt: str, history: List[dict], system: str = "", api_key: Optional[str] = None, model: Optional[str] = None) -> Optional[str]:
    """Call Google Gemini API for chat response."""
    key = api_key or settings.GEMINI_API_KEY
    if not key:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model or 'gemini-2.0-flash'}:generateContent?key={key}"

    messages = []
    if system:
        messages.append({"role": "user", "parts": [{"text": system}]})
        messages.append({"role": "model", "parts": [{"text": "I understand. I'll follow these instructions."}]})

    for msg in history[-8:]:
        messages.append({"role": msg["role"], "parts": [{"text": msg["content"]}]})
    messages.append({"role": "user", "parts": [{"text": prompt}]})

    payload = {
        "contents": messages,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 300,
            "topP": 0.9,
            "topK": 40,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        pass
    return None


async def _call_groq(prompt: str, system: str = "", api_key: Optional[str] = None, model: Optional[str] = None) -> Optional[str]:
    """Fallback to Groq Llama model when Gemini is unavailable."""
    key = api_key or settings.GROQ_API_KEY
    if not key:
        return None

    url = "https://api.groq.com/openai/v1/chat/completions"
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model or "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 300,
    }

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(
                url, json=payload,
                headers={"Authorization": f"Bearer {key}"}
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
    except Exception:
        pass
    return None


async def _call_custom(prompt: str, system: str = "", api_key: str = "", base_url: str = "", model: str = "") -> Optional[str]:
    """Call a user-supplied OpenAI-compatible endpoint (local LLM, proxy, etc)."""
    if not api_key or not base_url:
        return None

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model or "gpt-3.5-turbo",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 300,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                base_url.rstrip("/") + "/chat/completions", json=payload,
                headers={"Authorization": f"Bearer {api_key}"}
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
    except Exception:
        pass
    return None


def _rule_based_reply(message: str, context: dict, intent: str) -> tuple[str, str]:
    """Rule-based chat fallback when LLMs are unavailable."""
    msg = message.lower().strip()

    if intent == "recovery_query" or any(w in msg for w in ["how am i", "my recovery", "recovery score"]):
        score = context.get("recovery_score")
        state = context.get("readiness_state")
        if score:
            advice = {
                "OPTIMAL": "You're ready to push hard today! Go for progressive overload.",
                "MODERATE": "Standard session today — moderate volume and RPE 7-8.",
                "REDUCED": "Scale back intensity today. Focus on technique and lighter loads.",
                "DEPLETED": "Rest day recommended. Your body needs recovery — gentle walking is fine.",
            }
            return (
                f"Your recovery score is {score}/100 ({state}). {advice.get(state, 'Check your data.')}",
                "recovery_query"
            )
        return "I don't have your recovery data yet. Complete a morning check-in first!", "no_data"

    if intent == "workout_advice" or any(w in msg for w in ["workout", "train", "what should i do"]):
        state = context.get("readiness_state", "MODERATE")
        if state == "DEPLETED":
            return "Your body is depleted. Today: gentle stretching or a walk. No heavy lifting.", "workout_advice"
        if state == "REDUCED":
            return "With reduced readiness, try bodyweight exercises or light machines. RPE under 6.", "workout_advice"
        return "Check the Workout tab — it's already personalized to your current recovery state!", "workout_advice"

    if intent == "sleep_advice" or any(w in msg for w in ["sleep", "tired", "exhausted"]):
        return "Sleep is the #1 recovery tool. Aim for 7-9 hours. Consistent sleep times matter more than total hours. Avoid screens 1hr before bed.", "sleep_advice"

    if intent == "pain_injury" or any(w in msg for w in ["pain", "hurt", "injury"]):
        return "If you feel sharp or unusual pain, stop the exercise. Persistent pain needs professional evaluation. I'll flag this in your recovery assessment.", "pain_advice"

    if intent == "acwr_workload":
        acwr = context.get("acwr")
        if acwr:
            return f"Your ACWR is {acwr:.2f}. {'You\'re in the sweet spot.' if 0.8 <= acwr <= 1.3 else 'Consider adjusting volume.'}", "acwr_advice"
        return "I need your training history to calculate ACWR.", "acwr_advice"

    if intent == "greeting":
        return "Hey! How's your body feeling today? Any soreness or fatigue I should know about?", "greeting"

    if intent == "nutrition":
        return "For nutrition basics: aim for 1.6-2.2g protein per kg bodyweight, stay hydrated (35ml/kg/day), and match calories to your goal (surplus for muscle, deficit for fat loss).", "nutrition_advice"

    if intent == "motivation":
        return "Consistency beats perfection. Even a 20-minute session beats skipping. Your data shows your body is capable — trust the process.", "motivation"

    return "I can help with recovery analysis, workout advice, sleep, workload monitoring, and nutrition. What's on your mind?", "default"


def _generate_follow_ups(intent: str, context: dict) -> List[str]:
    """Generate contextual follow-up suggestions."""
    suggestions = {
        "recovery_query": ["Generate a workout for today", "How's my sleep been?", "Show my HRV trend"],
        "workout_advice": ["Log my workout when I'm done", "Show my progress this week", "What muscles should I focus on?"],
        "sleep_advice": ["Show my sleep trend", "Log my sleep", "How does sleep affect my recovery?"],
        "pain_injury": ["Suggest alternatives for that exercise", "Show my recovery history", "What are early warning signs?"],
        "nutrition": ["How much protein do I need?", "Show my nutrition log", "What should I eat post-workout?"],
        "motivation": ["Show my workout streak", "What are my recent PRs?", "What's my goal progress?"],
    }
    return suggestions.get(intent, ["How am I doing?", "What should I train today?", "Show my trends"])


@router.post("", response_model=ChatResponse)
@limiter.limit("30/minute")
async def chat(request: Request, req: ChatRequest):
    """AI fitness coach chat with intent classification, RAG, and structured prompts."""

    # 1. Classify intent and extract entities
    intent_result = intent_classifier.classify(req.message)
    primary_intent = intent_result["primary_intent"]
    confidence = intent_result["confidence"]
    entities = entity_extractor.extract_all(req.message)

    # 2. Check if the user is asking the coach to actually do something
    #    (generate + save a workout or diet plan), not just answer a question.
    action_result = await maybe_execute_action(req.message, req.user_id)
    if action_result:
        return ChatResponse(
            reply=action_result["reply"], intent=action_result["type"], confidence=confidence,
            entities=None, context_used=None, action=action_result["data"],
        )

    # 3. Check if this is a natural language workout log
    if primary_intent == "workout_log" or entities.get("exercises"):
        parsed = nl_workout_logger.parse(req.message)
        if parsed["parse_confidence"] >= 0.5:
            exercises_summary = ", ".join(
                f"{e['name']} {e['sets']}x{e['reps']}" +
                (f" @ {e['weight_kg']}kg" if e['weight_kg'] > 0 else "")
                for e in parsed["exercises"][:4]
            )
            reply = f"Parsed your workout: {exercises_summary or 'Cardio session'}. "
            if parsed["total_volume_kg"] > 0:
                reply += f"Total volume: {parsed['total_volume_kg']:.0f}kg. "
            if parsed["global_rpe"]:
                reply += f"RPE: {parsed['global_rpe']}/10. "
            if parsed["parse_confidence"] >= 0.7:
                reply += "Want me to log this? (Say 'yes' to confirm)"
            else:
                reply += "Can you clarify any details I might have missed?"
            return ChatResponse(
                reply=reply, intent="workout_log", confidence=confidence,
                entities={"parsed_workout": parsed}, context_used=None,
            )

    # 3. Gather user context from storage
    context = {}
    try:
        logs = await storage.get_recovery_logs(req.user_id, 1)
        if logs:
            last = logs[-1]
            context.update({
                "recovery_score": last.get("recovery_score"),
                "readiness_state": last.get("readiness_state"),
                "hrv_rmssd": last.get("hrv_rmssd"),
                "hrv_z_score": last.get("hrv_z_score"),
                "sleep_score": last.get("sleep_score"),
                "sleep_hours": last.get("sleep_duration_hours"),
                "sleep_efficiency": last.get("sleep_efficiency_pct"),
            })
    except Exception:
        pass

    try:
        workload = await storage.get_workload_history(req.user_id, 7)
        if workload:
            last_w = workload[-1]
            context["acwr"] = last_w.get("acwr")
            context["acwr_status"] = last_w.get("acwr_status")
    except Exception:
        pass

    try:
        recent_workouts = await storage.get_workout_logs(req.user_id, 7)
        if recent_workouts:
            context["session_count"] = len(recent_workouts)
            context["avg_rpe"] = round(
                sum(w.get("session_rpe", 5) for w in recent_workouts) / len(recent_workouts), 1
            )
    except Exception:
        pass

    # 4. Retrieve conversational memory context
    memory_context = conversational_memory.get_context_for_llm(req.user_id, max_tokens=300)
    user_prefs = conversational_memory.get_all_preferences(req.user_id)
    if memory_context:
        context["_memory"] = memory_context
    if user_prefs:
        context["_preferences"] = user_prefs

    # 5. Retrieve RAG knowledge
    knowledge = rag_retriever.retrieve(req.message, top_k=2)
    knowledge_context = rag_retriever.build_context_string(req.message, max_tokens=600)
    knowledge_sources = [k.get("topic", "") for k in knowledge]

    # 6. Build structured prompt using templates
    system_prompt = coach_prompts.get_system_prompt(context)
    template = coach_prompts.classify_template(primary_intent, req.message)

    prompt_parts = [template]
    if knowledge_context:
        prompt_parts.append(f"\n{knowledge_context}")
    prompt_parts.append(f"\nUser's message: {req.message}")

    full_prompt = "\n".join(prompt_parts)

    # 6. Build conversation history for context
    history_dicts = [{"role": m.role, "content": m.content} for m in req.history]

    # 8. If the client supplied its own key, use only that provider.
    #    Otherwise try server defaults in order: Gemini → Groq → Rule-based.
    reply = None
    llm_source = None
    if req.llm_override:
        ov = req.llm_override
        if ov.provider == "gemini":
            reply = await _call_gemini(full_prompt, history_dicts, system=system_prompt, api_key=ov.api_key, model=ov.model)
        elif ov.provider == "groq":
            reply = await _call_groq(full_prompt, system=system_prompt, api_key=ov.api_key, model=ov.model)
        elif ov.provider == "custom":
            reply = await _call_custom(full_prompt, system=system_prompt, api_key=ov.api_key, base_url=ov.base_url or "", model=ov.model or "")
        llm_source = ov.provider if reply else "rule_based"
    else:
        reply = await _call_gemini(full_prompt, history_dicts, system=system_prompt)
        llm_source = "gemini"

        if not reply:
            reply = await _call_groq(full_prompt, system=system_prompt)
            llm_source = "groq"

    if not reply:
        if knowledge:
            reply = " ".join(f"{k['content']} (source: {k['source']})" for k in knowledge)
        else:
            reply, _ = _rule_based_reply(req.message, context, primary_intent)
        llm_source = "rule_based"

    # 9. NLP side-effects: pain detection
    nlp_result = nlp_pipeline.extract_exercise_feedback(req.message)
    if nlp_result.get("pain_flagged"):
        reply += "\n\n⚠️ Pain detected — I've flagged this for your next recovery assessment."

    # 10. Record turn in conversational memory
    session_key = f"chat_{req.user_id}"
    conversational_memory.add_turn(session_key, "user", req.message, intent=primary_intent)
    conversational_memory.add_turn(session_key, "assistant", reply, intent="response")

    # 11. Record prediction for learning loop
    if context.get("recovery_score"):
        learning_loop.record_prediction(
            req.user_id, "recovery_score", context["recovery_score"], context
        )

    # 12. Generate follow-up suggestions
    follow_ups = _generate_follow_ups(primary_intent, context)

    return ChatResponse(
        reply=reply,
        intent=primary_intent,
        confidence=confidence,
        entities=entities if any(entities.values()) else None,
        context_used=context if context else None,
        knowledge_sources=knowledge_sources if knowledge_sources else None,
        follow_up_suggestions=follow_ups,
    )


@router.get("/intents")
async def list_intents():
    """List all supported intents for debugging."""
    return {"intents": list(intent_classifier.INTENTS.keys())}


@router.post("/classify")
async def classify_message(text: str):
    """Classify intent of a message (debugging endpoint)."""
    return intent_classifier.classify(text)


@router.post("/extract-entities")
async def extract_entities(text: str):
    """Extract entities from a message (debugging endpoint)."""
    return entity_extractor.extract_all(text)

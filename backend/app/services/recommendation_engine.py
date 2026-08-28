import json
import uuid
import httpx
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.models.schemas import (
    WorkoutGenerateRequest,
    WorkoutGenerateResponse,
    ReadinessState,
    PrescribedExercise,
    WarmupCooldownItem
)
from app.services.exercise_service import exercise_service

class RecommendationEngine:
    """
    Synthesizes personalized adaptive workouts based on physiological recovery score,
    soreness maps, and equipment access using Google Gemini Free Tier / Groq or deterministic engine.
    """

    @classmethod
    async def generate_workout(
        cls,
        user_id: str,
        target_date: str,
        readiness_state: ReadinessState,
        recovery_score: int,
        sore_muscles: Optional[List[str]] = None,
        equipment_access: Optional[List[str]] = None,
        target_duration: int = 45,
        goal: str = "hypertrophy"
    ) -> WorkoutGenerateResponse:
        workout_id = str(uuid.uuid4())
        sore = sore_muscles or []
        eq = equipment_access or ["bodyweight", "dumbbells"]

        # 1. Attempt Gemini 2.0 Flash / Groq LLM Generation if API Key is configured
        if settings.GEMINI_API_KEY:
            try:
                llm_result = await cls._generate_via_gemini(
                    readiness_state=readiness_state,
                    recovery_score=recovery_score,
                    sore_muscles=sore,
                    equipment=eq,
                    duration=target_duration,
                    goal=goal
                )
                if llm_result:
                    return WorkoutGenerateResponse(
                        workout_id=workout_id,
                        title=llm_result.get("title", f"Adaptive Workout ({readiness_state.value})"),
                        readiness_state=readiness_state,
                        adaptation_rationale=llm_result.get("adaptation_rationale", f"Scaled for {readiness_state.value} recovery."),
                        target_duration_minutes=llm_result.get("target_duration_minutes", target_duration),
                        warmup=[WarmupCooldownItem(**w) for w in llm_result.get("warmup", [])],
                        exercises=[PrescribedExercise(**e) for e in llm_result.get("exercises", [])],
                        cooldown=[WarmupCooldownItem(**c) for c in llm_result.get("cooldown", [])]
                    )
            except Exception:
                pass # Fallback seamlessly on any LLM network/schema error

        # 2. Deterministic Scientific Rule-Based Fallback
        fallback_data = exercise_service.get_fallback_routine(
            readiness_state=readiness_state,
            sore_muscles=sore,
            equipment=eq
        )

        return WorkoutGenerateResponse(
            workout_id=workout_id,
            title=fallback_data["title"],
            readiness_state=readiness_state,
            adaptation_rationale=fallback_data["adaptation_rationale"],
            target_duration_minutes=fallback_data["target_duration_minutes"],
            warmup=fallback_data["warmup"],
            exercises=fallback_data["exercises"],
            cooldown=fallback_data["cooldown"]
        )

    @classmethod
    async def _generate_via_gemini(
        cls,
        readiness_state: ReadinessState,
        recovery_score: int,
        sore_muscles: List[str],
        equipment: List[str],
        duration: int,
        goal: str
    ) -> Optional[Dict[str, Any]]:
        """
        Calls Google Gemini 2.0 Flash / 1.5 Flash API via REST with Structured JSON mode.
        """
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        
        system_instruction = (
            "You are AdapFit's Biometric Exercise Physiologist. Generate an adaptive workout routine "
            "strictly customized to the user's recovery score and muscle soreness. "
            "Output valid JSON matching the exact schema."
        )

        prompt = f"""
        User Recovery Score: {recovery_score}/100 ({readiness_state.value})
        User Goal: {goal}
        Sore/Fatigued Muscles to Avoid: {', '.join(sore_muscles) if sore_muscles else 'None'}
        Available Equipment: {', '.join(equipment)}
        Target Duration: {duration} minutes

        Generate a JSON object with:
        - title: string
        - adaptation_rationale: string explaining why this volume/RPE was selected based on biometrics
        - target_duration_minutes: integer
        - warmup: list of objects with name, duration_sec, or reps
        - exercises: list of 3-5 objects with exercise_id, name, target_muscle, sets (integer), target_reps (string), target_rpe (float), rest_seconds (integer), notes (string)
        - cooldown: list of objects with name, duration_sec
        """

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.3
            }
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
        return None

recommendation_engine = RecommendationEngine()

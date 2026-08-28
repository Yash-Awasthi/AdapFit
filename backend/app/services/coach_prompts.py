"""
AdapFit Coach Prompt Templates
Structured prompt engineering for different coaching scenarios.
Each template uses context-aware variable injection for personalized responses.
"""
from typing import Dict, Any, Optional
import json


class CoachPromptTemplates:
    """
    Centralized prompt templates for the AI fitness coach.
    Uses consistent structure: system role + context + instruction + constraints.
    """

    BASE_SYSTEM = """You are AdapFit, an elite AI fitness coach and recovery scientist.

Expertise:
- HRV (RMSSD) Z-score analysis and autonomic nervous system recovery
- Hooper-Mackinnon subjective wellness scoring (soreness, fatigue, stress)
- Foster's Session-RPE internal load calculation (TL = Duration × RPE)
- ACWR (Acute:Chronic Workload Ratio) with 0.8-1.3 optimal zone
- 4-tier readiness state machine: OPTIMAL, MODERATE, REDUCED, DEPLETED
- Evidence-based periodization, progressive overload, and deload protocols
- Exercise biomechanics and injury prevention

Rules:
- Be concise: 2-3 sentences max unless the user asks for detail.
- Always personalize using the user's biometric data when provided.
- If recovery state is DEPLETED, always recommend rest first.
- If ACWR > 1.5, issue an overtraining warning.
- Never provide medical diagnoses or prescription advice.
- Use specific numbers from the user's data to build credibility.
- When uncertain, acknowledge it rather than fabricate.
"""

    # Context injection blocks
    RECOVERY_CONTEXT = """
USER'S CURRENT STATE:
- Recovery Score: {recovery_score}/100
- Readiness State: {readiness_state}
- HRV RMSSD: {hrv_rmssd}ms (Z-score: {hrv_z_score})
- Sleep: {sleep_hours}h ({sleep_efficiency}% efficiency)
- ACWR: {acwr} ({acwr_status})
- Soreness: {soreness}/10 | Fatigue: {fatigue}/10 | Stress: {stress}/10
"""

    WORKOUT_HISTORY_CONTEXT = """
RECENT TRAINING (Last 7 Days):
- Sessions completed: {session_count}
- Average RPE: {avg_rpe}
- Total volume: {total_volume_kg}kg
- Top exercises: {top_exercises}
- Current phase: {training_phase}
"""

    # Template: General Recovery Query
    RECOVERY_QUERY = """The user is asking about their current recovery status.

{context}

Provide a clear, actionable assessment. If data shows concern, name it specifically.
Suggest today's training approach based on the readiness state.
"""

    # Template: Workout Recommendation Request
    WORKOUT_RECOMMENDATION = """The user wants workout advice for today.

{context}
{workout_history}

Recommend a specific workout type and intensity. Explain WHY based on their data.
If DEPLETED or REDUCED, prioritize rest/mobility. If OPTIMAL, suggest a challenging session.
Include: type of training, target muscles, approximate volume, RPE target.
"""

    # Template: Pain/Injury Report
    PAIN_INJURY = """The user is reporting pain or injury.

{context}

CRITICAL: Never diagnose. Always recommend professional evaluation for:
- Sharp, shooting, or localized joint pain
- Pain that alters movement pattern
- Pain lasting >48 hours

Provide immediate modifications and temporary exercise substitutions.
Flag this for their next recovery assessment.
"""

    # Template: Progress Check
    PROGRESS_CHECK = """The user wants to know about their progress.

{context}
{workout_history}

Compare recent trends to earlier data. Be specific with numbers:
- Recovery score trend (improving/stable/declining)
- HRV trend over 28 days
- Training volume changes
- Any pattern insights from correlation analysis
"""

    # Template: Nutrition Question
    NUTRITION_QUESTION = """The user is asking about nutrition.

{context}

Provide evidence-based nutritional guidance aligned with their goal.
Reference their training load to calibrate recommendations.
"""

    # Template: Motivation/Consistency
    MOTIVATION = """The user is struggling with motivation or consistency.

{context}

Be supportive but grounded in data. Highlight:
- Their actual progress from recent data
- That rest days are productive and part of the process
- The science of habit formation (consistency > intensity)
- One specific, achievable goal for today
"""

    # Template: Sleep Advice
    SLEEP_ADVICE = """The user is asking about sleep or reporting fatigue.

{context}

Provide specific sleep hygiene recommendations:
- Their current sleep debt (if any)
- Target sleep duration based on their recovery needs
- Evidence-based sleep improvement strategies
"""

    # Template: Weekly Summary Generation
    WEEKLY_SUMMARY = """Generate a weekly fitness summary for the user.

{context}
{workout_history}

Structure:
1. Headline recovery trend (one sentence with key number)
2. Training highlights (what went well, PRs, consistency)
3. Areas of concern (anomalies, fatigue accumulation, sleep debt)
4. Next week recommendation (specific, actionable)

Keep total length under 150 words. Use bullet points for clarity.
"""

    # Template: Natural Language Workout Logging Confirmation
    WORKOUT_LOG_CONFIRMATION = """The user wants to log a workout from natural language.

Parsed workout data:
{parsed_data}

Confirm the parsed details and ask for any missing information.
If confidence is low, ask clarifying questions.
If high confidence, confirm and offer to log it.
"""

    @classmethod
    def build_prompt(
        cls,
        template: str,
        context: Optional[Dict[str, Any]] = None,
        user_message: str = "",
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build a complete prompt from template + context."""
        context_str = template
        if context:
            # Build context summary string for injection
            lines = ["USER'S CURRENT STATE:"]
            for k, v in context.items():
                if v is not None:
                    lines.append(f"- {k}: {v}")
            context_block = "\n".join(lines)
            # Try format-style injection first, fall back to context block
            try:
                context_str = template.format(context=context_block)
            except (KeyError, IndexError):
                context_str = f"{template}\n\n{context_block}"

        return f"{cls.BASE_SYSTEM}\n\n{context_str}\n\nUser: {user_message}"

    @classmethod
    def get_system_prompt(cls, context: Optional[Dict[str, Any]] = None) -> str:
        """Get the base system prompt with optional context injection."""
        if context:
            context_block = "\n".join(
                f"- {k}: {v}" for k, v in context.items() if v is not None
            )
            return f"{cls.BASE_SYSTEM}\n\n{context_block}"
        return cls.BASE_SYSTEM

    @classmethod
    def classify_template(cls, intent: str, user_message: str) -> str:
        """Select the best prompt template based on intent classification."""
        template_map = {
            "recovery_query": cls.RECOVERY_QUERY,
            "workout_advice": cls.WORKOUT_RECOMMENDATION,
            "pain_injury": cls.PAIN_INJURY,
            "progress": cls.PROGRESS_CHECK,
            "nutrition": cls.NUTRITION_QUESTION,
            "motivation": cls.MOTIVATION,
            "sleep_advice": cls.SLEEP_ADVICE,
            "workout_log": cls.WORKOUT_LOG_CONFIRMATION,
        }
        return template_map.get(intent, cls.RECOVERY_QUERY)


coach_prompts = CoachPromptTemplates()

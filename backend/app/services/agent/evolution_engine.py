"""
AdapFit Self-Evolving Agent Memory System
Learns user preferences, tracks adaptation success, and evolves recommendations over time.
"""
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from app.core.storage import storage


class EvolutionEngine:
    """Self-evolving memory system that learns from every interaction."""

    ACCEPT_BOOST = 0.1
    REJECT_PENALTY = 0.15
    PAIN_PENALTY = 0.3
    GREAT_BOOST = 0.2

    async def record_workout_accepted(self, user_id: str, workout_exercises: List[dict]):
        memory = await storage.get_agent_memory(user_id)
        memory["accepted_workouts"] = memory.get("accepted_workouts", 0) + 1
        prefs = memory.get("exercise_preferences", {})
        for ex in workout_exercises:
            eid = ex.get("exercise_id", "")
            if eid:
                prefs[eid] = min(1.0, prefs.get(eid, 0.5) + self.ACCEPT_BOOST)
        memory["exercise_preferences"] = prefs
        memory["adaptation_history"].append({
            "action": "workout_accepted",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "exercises": [ex.get("exercise_id") for ex in workout_exercises],
        })
        await storage.update_agent_memory(user_id, memory)

    async def record_workout_rejected(self, user_id: str, workout_exercises: List[dict], reason: Optional[str] = None):
        memory = await storage.get_agent_memory(user_id)
        memory["rejected_workouts"] = memory.get("rejected_workouts", 0) + 1
        prefs = memory.get("exercise_preferences", {})
        for ex in workout_exercises:
            eid = ex.get("exercise_id", "")
            if eid:
                prefs[eid] = max(0.0, prefs.get(eid, 0.5) - self.REJECT_PENALTY)
        memory["exercise_preferences"] = prefs
        memory["adaptation_history"].append({
            "action": "workout_rejected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
        })
        await storage.update_agent_memory(user_id, memory)

    async def record_exercise_feedback(self, user_id: str, exercise_id: str, feedback_type: str, notes: Optional[str] = None):
        memory = await storage.get_agent_memory(user_id)
        prefs = memory.get("exercise_preferences", {})
        current = prefs.get(exercise_id, 0.5)
        if feedback_type == "great":
            prefs[exercise_id] = min(1.0, current + self.GREAT_BOOST)
            great = memory.get("great_exercises", [])
            if exercise_id not in great:
                great.append(exercise_id)
                memory["great_exercises"] = great[-20:]
        elif feedback_type == "pain":
            prefs[exercise_id] = max(0.0, current - self.PAIN_PENALTY)
            flags = memory.get("pain_flags", [])
            if exercise_id not in flags:
                flags.append(exercise_id)
                memory["pain_flags"] = flags
        elif feedback_type == "disliked":
            prefs[exercise_id] = max(0.0, current - self.REJECT_PENALTY)
        memory["exercise_preferences"] = prefs
        memory["nlp_feedback_history"].append({
            "exercise_id": exercise_id,
            "feedback_type": feedback_type,
            "notes": notes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        await storage.update_agent_memory(user_id, memory)

    async def get_personalization_vector(self, user_id: str) -> Dict[str, float]:
        memory = await storage.get_agent_memory(user_id)
        prefs = memory.get("exercise_preferences", {})
        pain_flags = set(memory.get("pain_flags", []))
        return {eid: 0.0 if eid in pain_flags else score for eid, score in prefs.items()}

    async def detect_strategy_shifts(self, user_id: str) -> Dict[str, Any]:
        memory = await storage.get_agent_memory(user_id)
        history = memory.get("adaptation_history", [])
        if len(history) < 5:
            return {"shift_detected": False, "reason": "Insufficient history"}
        recent = history[-10:]
        accepted = sum(1 for h in recent if h.get("action") == "workout_accepted")
        rejected = sum(1 for h in recent if h.get("action") == "workout_rejected")
        total = accepted + rejected
        if total == 0:
            return {"shift_detected": False, "reason": "No recent activity"}
        rate = accepted / total
        if rate < 0.3:
            return {"shift_detected": True, "direction": "disengagement", "acceptance_rate": round(rate, 2)}
        elif rate > 0.9:
            return {"shift_detected": True, "direction": "high_engagement", "acceptance_rate": round(rate, 2)}
        return {"shift_detected": False, "acceptance_rate": round(rate, 2)}

    async def generate_personalization_report(self, user_id: str) -> Dict[str, Any]:
        memory = await storage.get_agent_memory(user_id)
        prefs = memory.get("exercise_preferences", {})
        sorted_prefs = sorted(prefs.items(), key=lambda x: x[1], reverse=True)
        return {
            "total_interactions": len(memory.get("adaptation_history", [])),
            "acceptance_rate": memory.get("accepted_workouts", 0) / max(memory.get("accepted_workouts", 0) + memory.get("rejected_workouts", 0), 1),
            "favorite_exercises": [{"id": eid, "preference_score": round(score, 2)} for eid, score in sorted_prefs[:5]],
            "least_favorite_exercises": [{"id": eid, "preference_score": round(score, 2)} for eid, score in sorted_prefs[-5:]],
            "pain_flagged_exercises": memory.get("pain_flags", []),
            "great_exercises": memory.get("great_exercises", []),
            "strategy_shift": await self.detect_strategy_shifts(user_id),
            "evolution_version": memory.get("evolution_version", 1),
        }

    def get_status(self) -> Dict[str, Any]:
        return {"engine_version": "2.0", "learning_rate_accept": self.ACCEPT_BOOST, "pain_penalty": self.PAIN_PENALTY}


evolution_engine = EvolutionEngine()

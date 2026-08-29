"""
AdapFit Multi-Agent Orchestrator
Node-shaped services for the LangGraph pipeline in app.services.agent.graph.
"""
from decimal import Decimal
from typing import Dict, List, Any, Optional, TypedDict
from core_engine import compute_acwr, compute_recovery_score, compute_hrv_zscore, compute_sleep_score, compute_subjective_score
from app.core.storage import storage
from app.services.ml_engine import ml_engine
from app.services.nlp_pipeline import nlp_pipeline
from app.services.agent.evolution_engine import evolution_engine


class FitnessAgentState(TypedDict, total=False):
    user_id: str
    biometrics: dict
    recovery_assessment: dict
    ml_predictions: dict
    acwr_status: dict
    nlp_insights: dict
    agent_memory: dict
    exercise_preferences: dict
    recommendations: dict
    timestamp: str
    checkin: Optional[dict]
    signals: Any
    decision: dict
    phrased_summary: str


def _floatify(records: List[dict]) -> List[dict]:
    """Postgres NUMERIC columns arrive as Decimal; ml_engine does float arithmetic on them."""
    return [
        {k: float(v) if isinstance(v, Decimal) else v for k, v in r.items()}
        for r in records
    ]


class AgentOrchestrator:
    """Node-shaped async methods wrapped by app.services.agent.graph's StateGraph."""

    async def execute_recovery_analysis(self, state):
        user_id = state["user_id"]
        biometrics = state.get("biometrics", {})
        baseline = await storage.get_baseline(user_id)
        
        hrv_val = biometrics.get("hrv_rmssd")
        if hrv_val and baseline:
            z_score, hrv_score = compute_hrv_zscore(hrv_val, baseline.get("hrv_mean_rmssd") or 50.0, baseline.get("hrv_std_rmssd") or 10.0)
            sleep_hours = biometrics.get("sleep_duration_hours") or 7.5
            sleep_eff = biometrics.get("sleep_efficiency_pct") or 85.0
            sleep_target = baseline.get("sleep_target_hours") or 8.0
            sleep_score = compute_sleep_score(sleep_hours, sleep_eff, sleep_target)
        else:
            z_score, hrv_score = None, 70.0
            sleep_score = 70.0
        
        subjective = biometrics.get("subjective_checkin", {})
        subj_score = compute_subjective_score(subjective.get("soreness", 5), subjective.get("fatigue", 5), subjective.get("stress", 5), len(subjective.get("sore_muscle_groups", [])))
        
        workload_history = await storage.get_workload_history(user_id, 28)
        chronic_load = biometrics.get("current_chronic_load")
        if not chronic_load:
            chronic_load = (baseline.get("chronic_load_28d") or 500.0) if baseline else 500.0
        acute_load = biometrics.get("current_acute_load")
        if not acute_load and workload_history:
            recent = [w.get("session_load", 0) for w in workload_history[-7:]]
            acute_load = sum(recent) * 7 / max(len(recent), 1) if recent else chronic_load * 0.9
        elif not acute_load:
            acute_load = chronic_load * 0.9
        
        acwr_val, acwr_status_str, acwr_penalty = compute_acwr(acute_load, chronic_load)
        recovery_score = compute_recovery_score(hrv_score, sleep_score, subj_score, acwr_penalty, hrv_val is not None)
        
        if recovery_score >= 85: state_val = "OPTIMAL"
        elif recovery_score >= 65: state_val = "MODERATE"
        elif recovery_score >= 45: state_val = "REDUCED"
        else: state_val = "DEPLETED"
        
        state["recovery_assessment"] = {"recovery_score": recovery_score, "readiness_state": state_val, "hrv_z_score": z_score, "hrv_score": hrv_score, "sleep_score": sleep_score, "subjective_score": subj_score, "acwr": acwr_val, "acwr_status": acwr_status_str}
        state["acwr_status"] = {"acute_load": acute_load, "chronic_load": chronic_load, "acwr": acwr_val, "acwr_status": acwr_status_str}
        return state

    async def execute_ml_analysis(self, state):
        user_id = state["user_id"]
        recovery_logs = _floatify(await storage.get_recovery_logs(user_id, 28))
        workout_logs = _floatify(await storage.get_workout_logs(user_id, 28))
        features = ml_engine.extract_features(recovery_logs, workout_logs)
        state["ml_predictions"] = ml_engine.predict_readiness(features)
        
        hrv_values = [r.get("hrv_rmssd", 50.0) for r in recovery_logs if r.get("hrv_rmssd")]
        state["ml_predictions"]["hrv_forecast"] = ml_engine.forecast_hrv(hrv_values) if hrv_values else {"trend": "no_data"}
        state["ml_predictions"]["anomalies"] = ml_engine.detect_anomalies([r.get("recovery_score", 70) for r in recovery_logs]) if len(recovery_logs) >= 3 else {"anomalies": []}
        state["ml_predictions"]["model_status"] = ml_engine.get_status()
        
        acwr_data = state.get("acwr_status", {})
        injury_risk = ml_engine.compute_injury_risk(acwr_data.get("acwr") or 1.0, state["ml_predictions"]["hrv_forecast"].get("slope") or 0.0, 0.0, 0)
        state["ml_predictions"]["injury_risk"] = injury_risk
        return state

    async def execute_nlp_analysis(self, state):
        user_id = state["user_id"]
        workout_logs = await storage.get_workout_logs(user_id, 7)
        feedback = [w.get("user_feedback_notes", "") for w in workout_logs if w.get("user_feedback_notes")]
        if feedback:
            sentiments = [nlp_pipeline.analyze_sentiment(f) for f in feedback]
            pos = sum(1 for s in sentiments if s.get("sentiment") == "positive")
            neg = sum(1 for s in sentiments if s.get("sentiment") == "negative")
            state["nlp_insights"] = {"sentiment": "negative" if neg > pos else ("positive" if pos > neg else "neutral"), "feedback_count": len(feedback)}
        else:
            state["nlp_insights"] = {"sentiment": "neutral", "feedback_count": 0}
        return state

    async def execute_preference_learning(self, state):
        user_id = state["user_id"]
        state["agent_memory"] = await storage.get_agent_memory(user_id)
        state["exercise_preferences"] = await evolution_engine.get_personalization_vector(user_id)
        return state

    def get_status(self):
        return {"orchestrator_version": "3.0", "nodes": ["recovery", "ml", "nlp", "preference", "signals", "decision", "recommendation", "phrasing"], "ml_status": ml_engine.get_status(), "nlp_status": nlp_pipeline.get_status()}


agent_orchestrator = AgentOrchestrator()

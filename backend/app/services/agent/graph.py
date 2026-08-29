"""
LangGraph pipeline for the fitness agent.

recovery -> ml -> nlp -> preference -> signals -> decision -> [conditional] -> recommendation -> phrasing

daily_decision.decide() is the only place today's training decision is made.
A safety override (pain or illness) skips straight to phrasing; nothing after
the decision node may change state["decision"].
"""
from datetime import datetime, timezone
from typing import Optional

import httpx
from langgraph.graph import END, StateGraph

from app.core.config import settings
from app.core.gemini import DEFAULT_MODEL, extract_text, gemini_endpoint
from app.core.storage import storage
from app.services.agent.orchestrator import FitnessAgentState, agent_orchestrator
from app.services.agent.supervisor import supervisor_agent
from app.services.daily_decision import decide, signals_from_logs

# daily_decision's bands (75/55/30) are authoritative. This only relabels the
# outcome into the vocabulary supervisor_agent's action text switches on.
_READINESS_BY_DECISION = {
    "TRAIN": "OPTIMAL",
    "REDUCE": "MODERATE",
    "RECOVER": "REDUCED",
    "REST": "DEPLETED",
}


async def _recovery_node(state: FitnessAgentState) -> FitnessAgentState:
    return await agent_orchestrator.execute_recovery_analysis(state)


async def _ml_node(state: FitnessAgentState) -> FitnessAgentState:
    return await agent_orchestrator.execute_ml_analysis(state)


async def _nlp_node(state: FitnessAgentState) -> FitnessAgentState:
    return await agent_orchestrator.execute_nlp_analysis(state)


async def _preference_node(state: FitnessAgentState) -> FitnessAgentState:
    return await agent_orchestrator.execute_preference_learning(state)


async def _latest(getter, *args) -> dict:
    try:
        items = await getter(*args)
    except Exception:
        return {}
    return items[-1] if items else {}


async def _signals_node(state: FitnessAgentState) -> FitnessAgentState:
    user_id = state["user_id"]
    recovery_log = await _latest(storage.get_recovery_logs, user_id, 1)
    workload = await _latest(storage.get_workload_history, user_id, 7)
    try:
        workout_logs = await storage.get_workout_logs(user_id, 7)
    except Exception:
        workout_logs = []
    state["signals"] = signals_from_logs(recovery_log, state.get("checkin"), workload, workout_logs)
    return state


async def _decision_node(state: FitnessAgentState) -> FitnessAgentState:
    state["decision"] = decide(state["signals"]).to_dict()
    return state


def _route_after_decision(state: FitnessAgentState) -> str:
    return "phrasing" if state["decision"].get("safety_override") else "recommendation"


async def _recommendation_node(state: FitnessAgentState) -> FitnessAgentState:
    recovery_assessment = dict(state.get("recovery_assessment", {}))
    recovery_assessment["readiness_state"] = _READINESS_BY_DECISION.get(
        state["decision"]["decision"], recovery_assessment.get("readiness_state")
    )
    state["recommendations"] = supervisor_agent.synthesize_recommendation(
        recovery_assessment=recovery_assessment,
        workout_plan={},
        acwr_status=state.get("acwr_status", {}),
        ml_predictions=state.get("ml_predictions", {}),
        nlp_insights=state.get("nlp_insights"),
        agent_memory=state.get("agent_memory"),
    )
    return state


async def _phrasing_node(state: FitnessAgentState) -> FitnessAgentState:
    """The only LLM node. Restates the decision; never allowed to pick one."""
    decision = state["decision"]
    key = settings.GEMINI_API_KEY
    if not key:
        state["phrased_summary"] = decision["headline"]
        return state

    prompt = (
        "Restate this training decision for the user in one short, encouraging sentence. "
        "Do not suggest a different decision or add new advice.\n"
        f"Decision: {decision['decision']}\n"
        f"Headline: {decision['headline']}\n"
        f"Reasons: {'; '.join(decision['reasons'])}"
    )
    url, headers = gemini_endpoint(key, DEFAULT_MODEL)
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 200},
    }
    text = None
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                text = extract_text(resp.json())
    except Exception:
        text = None
    state["phrased_summary"] = text or decision["headline"]
    return state


def build_graph():
    graph = StateGraph(FitnessAgentState)
    graph.add_node("recovery", _recovery_node)
    graph.add_node("ml", _ml_node)
    graph.add_node("nlp", _nlp_node)
    graph.add_node("preference", _preference_node)
    graph.add_node("signals", _signals_node)
    graph.add_node("decision", _decision_node)
    graph.add_node("recommendation", _recommendation_node)
    graph.add_node("phrasing", _phrasing_node)

    graph.set_entry_point("recovery")
    graph.add_edge("recovery", "ml")
    graph.add_edge("ml", "nlp")
    graph.add_edge("nlp", "preference")
    graph.add_edge("preference", "signals")
    graph.add_edge("signals", "decision")
    graph.add_conditional_edges(
        "decision", _route_after_decision, {"recommendation": "recommendation", "phrasing": "phrasing"}
    )
    graph.add_edge("recommendation", "phrasing")
    graph.add_edge("phrasing", END)
    return graph.compile()


fitness_graph = build_graph()


async def run(user_id: str, biometrics: Optional[dict] = None, checkin: Optional[dict] = None) -> FitnessAgentState:
    state: FitnessAgentState = {
        "user_id": user_id,
        "biometrics": biometrics or {},
        "checkin": checkin,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return await fitness_graph.ainvoke(state)

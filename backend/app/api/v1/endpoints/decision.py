"""Today's training decision — the single answer the home screen shows."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

from app.core.storage import storage
from app.core.workout_metrics import HISTORY_ENTRIES, acwr_ratio
from app.services.daily_decision import DecisionSignals, decide, signals_from_logs

router = APIRouter()


async def _latest(getter, *args) -> dict:
    try:
        items = await getter(*args)
    except Exception:
        return {}
    return items[-1] if items else {}


@router.get("/today")
async def decision_today(user_id: str = Query("default"),
                         day: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$",
                                                    description="The phone's local date; defaults to the server's")):
    """
    One decision, the reasons behind it, and how confident it is.

    Everything here is computed from stored signals; no field is invented when
    the data is missing, because a fabricated reading is indistinguishable
    from a real one once it reaches the screen.
    """
    recovery_log = await _latest(storage.get_recovery_logs, user_id, 1)
    # Yesterday's check-in says nothing about today; without today's there is no decision to make.
    if str(recovery_log.get("log_date", ""))[:10] != (day or date.today().isoformat()):
        return {"user_id": user_id, "decision": None, "headline": "Check in to see today's plan",
                "reasons": ["No check-in yet today."], "cautions": [], "confidence": None,
                "intensity_ceiling_pct": None, "safety_override": None}
    workload = await storage.get_workload_history(user_id, HISTORY_ENTRIES)

    try:
        workout_logs = await storage.get_workout_logs(user_id, 7)
    except Exception:
        workout_logs = []

    signals = signals_from_logs(recovery_log, None, acwr_ratio(workload), workout_logs)
    result = decide(signals)
    payload = result.to_dict()
    payload["user_id"] = user_id
    return payload


@router.post("/simulate")
async def decision_simulate(signals: dict):
    """Run the rules against supplied signals. Used for testing and tuning."""
    allowed = {f for f in DecisionSignals.__dataclass_fields__}
    return decide(DecisionSignals(**{k: v for k, v in signals.items() if k in allowed})).to_dict()

"""
The user's own normal.

A recovery score is only personal if "low HRV" means low *for this person*.
The population defaults are a starting point, not an answer, so the baseline
starts at them and moves toward the user's measured values as evidence
accumulates — rather than flipping to a personal mean on the first reading,
where one night's number would become the standard the next night is judged by.

Established here and refreshed on every recovery log, which is what
"establish an initial baseline and continuously refine it" requires.
"""
import math
from typing import Any, Dict, List, Optional

from app.core.config import settings

# Readings needed before a measured mean is trusted on its own. Below this the
# baseline is a weighted blend of the population default and what was measured,
# so a three-day-old account is not judged against three days of noise.
FULL_CONFIDENCE_SAMPLES = 14

# Window the baseline is computed over. 28 days is the standard HRV reference
# period: long enough to average out a bad week, short enough to track a
# genuine change in fitness.
WINDOW_DAYS = 28

# A standard deviation below this makes the HRV z-score explode, so it is the
# floor regardless of how consistent the readings look.
MIN_HRV_STD = 3.0

DEFAULTS: Dict[str, float] = {
    "hrv_mean_rmssd": settings.DEFAULT_BASELINE_HRV_RMSSD,
    "hrv_std_rmssd": settings.DEFAULT_BASELINE_HRV_STD,
    "rhr_baseline": 65.0,
    "sleep_target_hours": settings.DEFAULT_BASELINE_SLEEP_HOURS,
    "chronic_load_28d": 500.0,
}


def _values(logs: List[Dict[str, Any]], key: str) -> List[float]:
    out = []
    for log in logs[-WINDOW_DAYS:]:
        value = log.get(key)
        if value is None:
            continue
        try:
            out.append(float(value))
        except (TypeError, ValueError):
            continue
    return out


def _mean(values: List[float]) -> Optional[float]:
    return sum(values) / len(values) if values else None


def _std(values: List[float]) -> Optional[float]:
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    # Sample standard deviation: the readings are a sample of the user's
    # nights, not the whole population of them.
    return math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1))


def _blend(default: float, measured: Optional[float], samples: int) -> float:
    """Move from the population default toward the measured value with evidence."""
    if measured is None or samples <= 0:
        return default
    weight = min(1.0, samples / FULL_CONFIDENCE_SAMPLES)
    return default * (1 - weight) + measured * weight


def compute(recovery_logs: List[Dict[str, Any]], workload_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """The user's baseline from their history. Defaults where there is no history."""
    logs = recovery_logs or []
    hrvs = _values(logs, "hrv_rmssd")
    rhrs = _values(logs, "resting_heart_rate")
    sleeps = _values(logs, "sleep_duration_hours")

    hrv_std = _std(hrvs)
    baseline = {
        "hrv_mean_rmssd": round(_blend(DEFAULTS["hrv_mean_rmssd"], _mean(hrvs), len(hrvs)), 1),
        "hrv_std_rmssd": round(max(MIN_HRV_STD, _blend(DEFAULTS["hrv_std_rmssd"], hrv_std, len(hrvs))), 1),
        "rhr_baseline": round(_blend(DEFAULTS["rhr_baseline"], _mean(rhrs), len(rhrs)), 1),
        "sleep_target_hours": round(_blend(DEFAULTS["sleep_target_hours"], _mean(sleeps), len(sleeps)), 1),
        "chronic_load_28d": round(_chronic_load(workload_history or []), 1),
        "sample_counts": {"hrv": len(hrvs), "rhr": len(rhrs), "sleep": len(sleeps)},
        "confidence": round(min(1.0, max(len(hrvs), len(sleeps)) / FULL_CONFIDENCE_SAMPLES), 2),
    }
    return baseline


def _chronic_load(workload_history: List[Dict[str, Any]]) -> float:
    loads = _values(workload_history, "chronic_load")
    if loads:
        return loads[-1]
    sessions = _values(workload_history, "session_load")
    if sessions:
        # Chronic load is the 28-day average session load, scaled to a week.
        return sum(sessions) / len(sessions) * 7
    return DEFAULTS["chronic_load_28d"]


async def refresh(user_id: str) -> Dict[str, Any]:
    """Recompute and store the baseline from everything on record for this user."""
    from app.core.storage import storage

    recovery_logs = await storage.get_recovery_logs(user_id, WINDOW_DAYS)
    workload = await storage.get_workload_history(user_id, WINDOW_DAYS)
    baseline = compute(recovery_logs, workload)
    # sample_counts and confidence describe the baseline rather than being part
    # of it, and the stored shape is fixed by the user_baselines table.
    stored = {k: v for k, v in baseline.items() if k in DEFAULTS}
    await storage.set_baseline(user_id, stored)
    return baseline


async def load(user_id: str):
    """The stored baseline as a UserBaseline, computing one if none exists yet."""
    from app.core.storage import storage
    from app.models.schemas import UserBaseline

    record = await storage.get_baseline(user_id)
    if not record:
        record = {k: v for k, v in (await refresh(user_id)).items() if k in DEFAULTS}
    fields = {k: float(record.get(k, v)) for k, v in DEFAULTS.items()}
    return UserBaseline(user_id=user_id, **fields)

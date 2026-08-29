"""
AdapFit Workflow Engine — Background recovery assessment workflows.

Provides morning_recovery() for the daily readiness check-in flow.
"""
from typing import Dict, Any
from core_engine import compute_hrv_zscore, compute_sleep_score, compute_recovery_score


async def morning_recovery(user_id: str, biometrics: Dict[str, Any]) -> Dict[str, Any]:
    """Run morning recovery assessment from overnight biometrics.

    Computes a readiness state from sleep and HRV data, returning the
    same shape the ML pipeline uses: recovery_score + readiness_state.
    """
    hrv_val = biometrics.get("hrv_rmssd")
    sleep_hours = biometrics.get("sleep_duration_hours") or 7.5

    if hrv_val is not None:
        z_score, hrv_score = compute_hrv_zscore(hrv_val)
    else:
        z_score, hrv_score = None, 70.0

    sleep_score = compute_sleep_score(sleep_hours)
    subj_score = 70.0  # no subjective data in morning flow

    recovery_score = compute_recovery_score(hrv_score, sleep_score, subj_score, 0.0, hrv_val is not None)

    if recovery_score >= 85:
        state = "OPTIMAL"
    elif recovery_score >= 65:
        state = "MODERATE"
    elif recovery_score >= 45:
        state = "REDUCED"
    else:
        state = "DEPLETED"

    return {
        "user_id": user_id,
        "recovery_score": recovery_score,
        "readiness_state": state,
        "hrv_z_score": z_score,
        "hrv_score": hrv_score,
        "sleep_score": sleep_score,
        "subjective_score": subj_score,
    }

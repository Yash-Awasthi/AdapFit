"""
AdapFit Morning Recovery Workflow
Simple sequential pipeline: compute recovery → check anomaly → store → generate directive.
"""
from typing import Dict, Any
from datetime import datetime, timezone


async def morning_recovery(user_id: str, biometrics: Dict[str, Any]) -> Dict[str, Any]:
    """Run the morning recovery analysis pipeline."""
    from core_engine import compute_acwr, compute_recovery_score, compute_hrv_zscore, compute_sleep_score, compute_subjective_score
    from app.core.storage import storage

    # 1. Compute recovery
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

    subj = biometrics.get("subjective_checkin", {})
    subj_score = compute_subjective_score(subj.get("soreness", 5), subj.get("fatigue", 5), subj.get("stress", 5), len(subj.get("sore_muscle_groups", [])))

    chronic_load = biometrics.get("current_chronic_load")
    if not chronic_load:
        chronic_load = (baseline.get("chronic_load_28d") or 500.0) if baseline else 500.0
    acute_load = biometrics.get("current_acute_load") or chronic_load * 0.9

    acwr_val, acwr_status_str, acwr_penalty = compute_acwr(acute_load, chronic_load)
    recovery_score = compute_recovery_score(hrv_score, sleep_score, subj_score, acwr_penalty, hrv_val is not None)

    if recovery_score >= 85:
        state_val, directive = "OPTIMAL", "High readiness. Full intensity workout recommended."
    elif recovery_score >= 65:
        state_val, directive = "MODERATE", "Moderate readiness. Standard training permitted."
    elif recovery_score >= 45:
        state_val, directive = "REDUCED", "Low readiness. Scaled-back session or active recovery."
    else:
        state_val, directive = "DEPLETED", "Depleted. Rest or gentle mobility only."

    # 2. Check anomaly
    if z_score is not None and z_score < -2.0:
        directive += " [ANOMALY: Significant HRV deviation detected.]"

    # 3. Store
    await storage.add_recovery_log(user_id, {
        "recovery_score": recovery_score,
        "readiness_state": state_val,
        "hrv_rmssd": hrv_val,
        "sleep_duration_hours": biometrics.get("sleep_duration_hours"),
        "hrv_z_score": z_score,
        "log_date": biometrics.get("log_date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
    })

    return {
        "recovery_score": recovery_score,
        "readiness_state": state_val,
        "hrv_z_score": z_score,
        "sleep_score": sleep_score,
        "subjective_score": subj_score,
        "acwr": acwr_val,
        "acwr_status": acwr_status_str,
        "directive": directive,
    }

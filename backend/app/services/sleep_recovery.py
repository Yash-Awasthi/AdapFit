"""
Sleep recovery detection from sleep-recovery-detector patterns.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class SleepRecovery:
    recovery_score: float = 0.0
    deep_sleep_quality: float = 0.0
    rem_quality: float = 0.0
    hrv_recovery: float = 0.0
    restfulness: float = 0.0
    recommendation: str = ""


def assess_sleep_recovery(
    deep_minutes: float, rem_minutes: float, total_minutes: float,
    hrv_last_night: float, hrv_baseline: float, awake_minutes: float
) -> SleepRecovery:
    deep_pct = deep_minutes / max(1, total_minutes)
    rem_pct = rem_minutes / max(1, total_minutes)
    awake_pct = awake_minutes / max(1, total_minutes)
    deep_quality = min(1.0, deep_pct / 0.2)
    rem_quality = min(1.0, rem_pct / 0.22)
    hrv_recovery = min(1.0, hrv_last_night / hrv_baseline) if hrv_baseline > 0 else 0.5
    restfulness = max(0, 1 - awake_pct * 5)
    recovery_score = (deep_quality * 0.3 + rem_quality * 0.25 + hrv_recovery * 0.25 + restfulness * 0.2) * 100
    if recovery_score >= 80:
        rec = "Excellent recovery — ready for intense training"
    elif recovery_score >= 60:
        rec = "Good recovery — moderate training okay"
    elif recovery_score >= 40:
        rec = "Moderate recovery — light training recommended"
    else:
        rec = "Poor recovery — rest day recommended"
    return SleepRecovery(recovery_score=round(recovery_score, 1), deep_sleep_quality=round(deep_quality * 100, 1), rem_quality=round(rem_quality * 100, 1), hrv_recovery=round(hrv_recovery * 100, 1), restfulness=round(restfulness * 100, 1), recommendation=rec)


def detect_sleep_debt(sleep_history: List[float], target_hours: float = 8.0) -> float:
    if not sleep_history:
        return 0.0
    debt = sum(max(0, target_hours - h) for h in sleep_history)
    return round(debt, 1)


def suggest_recovery_activities(recovery_score: float) -> List[str]:
    activities = []
    if recovery_score < 40:
        activities.extend(["Complete rest day", "Light walking only", "Extra 30 min sleep tonight"])
    elif recovery_score < 60:
        activities.extend(["Light yoga or stretching", "Easy 20 min walk", "Hydration focus"])
    elif recovery_score < 80:
        activities.extend(["Moderate exercise okay", "Cool-down stretching", "Maintain hydration"])
    else:
        activities.extend(["High intensity training okay", "Push your limits", "Great day for PRs"])
    return activities

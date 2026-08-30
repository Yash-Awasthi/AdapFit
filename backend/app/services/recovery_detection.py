"""
Recovery & Training Readiness Detection

Multi-signal recovery assessment, sport-specific daily readiness scoring,
and ACWR (Acute:Chronic Workload Ratio) calculation.  Pure functions only.

References:
- Gabbett (2016) ACWR for injury prediction
- Plews et al. HRV-guided training
- Banister fitness-fatigue model (simplified)
"""
from dataclasses import dataclass
from typing import Optional
import statistics
import math


@dataclass
class DailyRecoveryData:
    """Relevant metrics for recovery assessment."""
    date: str                                  # "YYYY-MM-DD"
    hrv_rmssd: Optional[float] = None          # ms
    resting_hr: Optional[int] = None           # bpm
    sleep_quality: Optional[float] = None      # 0-100
    sleep_hours: Optional[float] = None
    subjective_readiness: Optional[int] = None # 1-10 self-reported
    steps: Optional[int] = None
    active_minutes: Optional[int] = None
    calories_burned: Optional[int] = None
    workout_strain: Optional[float] = None     # session RPE × duration, or TRIMP


# ── Helpers ────────────────────────────────────────────────────────────────

def _safe_mean(vals: list[float]) -> Optional[float]:
    clean = [v for v in vals if v is not None]
    return statistics.mean(clean) if clean else None


def _safe_stdev(vals: list[float]) -> Optional[float]:
    clean = [v for v in vals if v is not None]
    if len(clean) < 2:
        return None
    return statistics.stdev(clean)


# ── Recovery Score ─────────────────────────────────────────────────────────

# Signal weights (must sum to 1.0)
_RECOVERY_WEIGHTS = {
    "hrv_trend":        0.30,
    "sleep_quality":    0.20,
    "resting_hr_trend": 0.20,
    "sleep_duration":   0.10,
    "subjective":       0.20,
}


def compute_recovery_score(
    today: DailyRecoveryData,
    baseline_history: list[DailyRecoveryData],
    window_days: int = 7,
) -> dict:
    """
    Compute a weighted recovery score (0-100) from today's data versus baseline.

    Each signal is normalized to 0-100 based on how today compares to
    the recent baseline mean and standard deviation.
    """
    if not baseline_history:
        return {"error": "Need baseline history for recovery scoring."}

    recent = baseline_history[-window_days:]

    # ── HRV trend ──
    hrv_baseline = _safe_mean([d.hrv_rmssd for d in recent if d.hrv_rmssd is not None])
    hrv_std = _safe_stdev([d.hrv_rmssd for d in recent if d.hrv_rmssd is not None])
    if today.hrv_rmssd is not None and hrv_baseline is not None and hrv_std and hrv_std > 0:
        z = (today.hrv_rmssd - hrv_baseline) / hrv_std
        # z > 0 means better than baseline → higher score
        hrv_score = max(0, min(100, 50 + z * 25))
    else:
        hrv_score = 50.0  # neutral if no data

    # ── Sleep quality ──
    if today.sleep_quality is not None:
        sleep_q_score = min(100, max(0, today.sleep_quality))
    else:
        sleep_q_score = 50.0

    # ── Resting HR trend (lower is better recovery) ──
    rhr_baseline = _safe_mean([d.resting_hr for d in recent if d.resting_hr is not None])
    rhr_std = _safe_stdev([d.resting_hr for d in recent if d.resting_hr is not None])
    if today.resting_hr is not None and rhr_baseline is not None and rhr_std and rhr_std > 0:
        z = (rhr_baseline - today.resting_hr) / rhr_std  # inverted: lower HR = higher score
        rhr_score = max(0, min(100, 50 + z * 25))
    else:
        rhr_score = 50.0

    # ── Sleep duration ──
    if today.sleep_hours is not None:
        if today.sleep_hours >= 7.5:
            sd_score = 100.0
        elif today.sleep_hours >= 6.0:
            sd_score = (today.sleep_hours / 7.5) * 100
        else:
            sd_score = max(0, (today.sleep_hours / 6.0) * 60)
    else:
        sd_score = 50.0

    # ── Subjective readiness ──
    if today.subjective_readiness is not None:
        subj_score = max(0, min(100, today.subjective_readiness * 10))
    else:
        subj_score = 50.0

    # Weighted composite
    total = (
        hrv_score * _RECOVERY_WEIGHTS["hrv_trend"] +
        sleep_q_score * _RECOVERY_WEIGHTS["sleep_quality"] +
        rhr_score * _RECOVERY_WEIGHTS["resting_hr_trend"] +
        sd_score * _RECOVERY_WEIGHTS["sleep_duration"] +
        subj_score * _RECOVERY_WEIGHTS["subjective"]
    )

    # Phase detection
    if total >= 80:
        phase = "peaked"
        description = "Excellent recovery. You're ready for peak performance."
    elif total >= 60:
        phase = "recovered"
        description = "Good recovery. Normal training load is appropriate."
    elif total >= 40:
        phase = "recovering"
        description = "Partial recovery. Moderate training with easy options recommended."
    elif total >= 20:
        phase = "overreaching"
        description = "Accumulated fatigue detected. Reduce volume and intensity."
    else:
        phase = "detrained"
        description = "Significant fatigue or detraining. Rest day strongly recommended."

    return {
        "recovery_score": round(total, 1),
        "phase": phase,
        "description": description,
        "breakdown": {
            "hrv_trend": round(hrv_score, 1),
            "sleep_quality": round(sleep_q_score, 1),
            "resting_hr_trend": round(rhr_score, 1),
            "sleep_duration": round(sd_score, 1),
            "subjective": round(subj_score, 1),
        },
        "date": today.date,
    }


# ── Training Readiness (sport-specific) ───────────────────────────────────

_SPORT_PROFILES = {
    "cardio": {
        "hrv_weight": 0.35, "sleep_weight": 0.25, "rhr_weight": 0.25,
        "subjective_weight": 0.15, "min_score_for_high": 70,
    },
    "strength": {
        "hrv_weight": 0.20, "sleep_weight": 0.30, "rhr_weight": 0.15,
        "subjective_weight": 0.35, "min_score_for_high": 65,
    },
    "flexibility": {
        "hrv_weight": 0.15, "sleep_weight": 0.25, "rhr_weight": 0.10,
        "subjective_weight": 0.50, "min_score_for_high": 55,
    },
    "hiit": {
        "hrv_weight": 0.40, "sleep_weight": 0.25, "rhr_weight": 0.20,
        "subjective_weight": 0.15, "min_score_for_high": 75,
    },
    "general": {
        "hrv_weight": 0.25, "sleep_weight": 0.25, "rhr_weight": 0.20,
        "subjective_weight": 0.30, "min_score_for_high": 60,
    },
}


def training_readiness(
    recovery_data: DailyRecoveryData,
    baseline_history: list[DailyRecoveryData],
    sport: str = "general",
) -> dict:
    """
    Sport-specific daily training readiness score.

    Parameters
    ----------
    sport : str
        One of "cardio", "strength", "flexibility", "hiit", "general".
    """
    profile = _SPORT_PROFILES.get(sport, _SPORT_PROFILES["general"])
    recent = baseline_history[-7:]

    # Same signal normalization as recovery score
    hrv_baseline = _safe_mean([d.hrv_rmssd for d in recent if d.hrv_rmssd is not None])
    hrv_std = _safe_stdev([d.hrv_rmssd for d in recent if d.hrv_rmssd is not None])
    if recovery_data.hrv_rmssd is not None and hrv_baseline is not None and hrv_std and hrv_std > 0:
        z = (recovery_data.hrv_rmssd - hrv_baseline) / hrv_std
        hrv_s = max(0, min(100, 50 + z * 25))
    else:
        hrv_s = 50.0

    sleep_s = min(100, max(0, recovery_data.sleep_quality)) if recovery_data.sleep_quality is not None else 50.0

    rhr_baseline = _safe_mean([d.resting_hr for d in recent if d.resting_hr is not None])
    rhr_std = _safe_stdev([d.resting_hr for d in recent if d.resting_hr is not None])
    if recovery_data.resting_hr is not None and rhr_baseline is not None and rhr_std and rhr_std > 0:
        z = (rhr_baseline - recovery_data.resting_hr) / rhr_std
        rhr_s = max(0, min(100, 50 + z * 25))
    else:
        rhr_s = 50.0

    subj_s = max(0, min(100, recovery_data.subjective_readiness * 10)) if recovery_data.subjective_readiness is not None else 50.0

    score = (
        hrv_s * profile["hrv_weight"] +
        sleep_s * profile["sleep_weight"] +
        rhr_s * profile["rhr_weight"] +
        subj_s * profile["subjective_weight"]
    )

    if score >= profile["min_score_for_high"]:
        readiness = "high"
        recommendation = f"Go ahead with {sport} training at planned intensity."
    elif score >= profile["min_score_for_high"] - 20:
        readiness = "moderate"
        recommendation = f"Do {sport} at reduced intensity. Listen to your body."
    else:
        readiness = "low"
        recommendation = f"Skip {sport} today or switch to active recovery (walk, stretch)."

    return {
        "sport": sport,
        "readiness_score": round(score, 1),
        "readiness_level": readiness,
        "recommendation": recommendation,
        "breakdown": {
            "hrv": round(hrv_s, 1),
            "sleep": round(sleep_s, 1),
            "resting_hr": round(rhr_s, 1),
            "subjective": round(subj_s, 1),
        },
        "date": recovery_data.date,
    }


# ── ACWR (Acute:Chronic Workload Ratio) ──────────────────────────────────

def compute_acwr(
    daily_strain: list[dict],
    acute_window: int = 7,
    chronic_window: int = 28,
) -> dict:
    """
    Calculate Acute:Chronic Workload Ratio.

    Parameters
    ----------
    daily_strain : list of dicts
        Each dict has "date" (str) and "strain" (float, e.g. TRIMP or sRPE).
        Must be ordered oldest → newest.
    acute_window : int
        Days for acute workload (default 7).
    chronic_window : int
        Days for chronic workload (default 28).

    Returns
    -------
    dict with acwr value, classification, and injury risk assessment.
    """
    if len(daily_strain) < acute_window:
        return {
            "error": f"Need at least {acute_window} days of strain data.",
        }

    strains = [d["strain"] for d in daily_strain]

    acute = statistics.mean(strains[-acute_window:])
    chronic = statistics.mean(strains[-chronic_window:]) if len(strains) >= chronic_window else statistics.mean(strains)

    if chronic == 0:
        return {
            "acwr": None,
            "acute_load": round(acute, 2),
            "chronic_load": round(chronic, 2),
            "classification": "unmeasurable",
            "injury_risk": "unknown — no chronic workload established",
        }

    acwr = acute / chronic

    # Gabbett's sweet spot and risk zones
    if acwr < 0.8:
        zone = "detraining"
        risk = "low"
        description = "Undertraining zone. Fitness may decline. Consider increasing load gradually."
    elif acwr <= 1.3:
        zone = "sweet_spot"
        risk = "low"
        description = "Optimal training zone. Good balance of stimulus and recovery."
    elif acwr <= 1.5:
        zone = "caution"
        risk = "moderate"
        description = "Elevated load. Monitor fatigue closely. Avoid consecutive high-load days."
    else:
        zone = "danger"
        risk = "high"
        description = "Significantly elevated injury risk. Reduce acute load or insert recovery days."

    return {
        "acwr": round(acwr, 3),
        "acute_load": round(acute, 2),
        "chronic_load": round(chronic, 2),
        "acute_window_days": acute_window,
        "chronic_window_days": chronic_window,
        "zone": zone,
        "injury_risk": risk,
        "description": description,
        "data_points": len(strains),
    }


# ── Full recovery pipeline ────────────────────────────────────────────────

def full_recovery_assessment(
    today: DailyRecoveryData,
    history: list[DailyRecoveryData],
    sport: str = "general",
    daily_strain: Optional[list[dict]] = None,
) -> dict:
    """
    Complete recovery and readiness assessment.

    Returns recovery score, training readiness for the specified sport,
    ACWR if strain data is provided, and combined recommendations.
    """
    recovery = compute_recovery_score(today, history)
    readiness = training_readiness(today, history, sport)

    result = {
        "date": today.date,
        "recovery": recovery,
        "training_readiness": readiness,
    }

    if daily_strain:
        acwr = compute_acwr(daily_strain)
        result["acwr"] = acwr

        # Combined recommendation
        if recovery.get("phase") in ("overreaching", "detrained") or readiness.get("readiness_level") == "low":
            result["final_recommendation"] = (
                "Rest day recommended. Recovery metrics and training readiness are both low."
            )
        elif acwr.get("zone") == "danger":
            result["final_recommendation"] = (
                "Reduce training volume. ACWR is in the danger zone despite "
                f"{'acceptable' if readiness.get('readiness_level') != 'low' else 'poor'} readiness."
            )
        elif acwr.get("zone") == "sweet_spot" and readiness.get("readiness_level") == "high":
            result["final_recommendation"] = (
                "Excellent conditions for hard training. ACWR is optimal and readiness is high."
            )
        else:
            result["final_recommendation"] = readiness.get("recommendation", "Train as planned.")
    else:
        result["final_recommendation"] = readiness.get("recommendation", "Train as planned.")

    return result

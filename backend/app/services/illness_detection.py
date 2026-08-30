"""
Illness Early Warning Detection

Multi-signal system that detects likely illness onset 1-2 days before symptoms
by tracking deviations from personal baselines in:
- Heart rate variability (HRV / RMSSD)
- Resting heart rate (RHR)
- Body temperature
- Sleep quality and duration
- Respiratory rate
- Blood oxygen saturation (SpO2)

Uses rolling baselines and standard-deviation scoring.  Pure functions only,
no DB or async.
"""
from dataclasses import dataclass
from typing import Optional
import statistics
import math


@dataclass
class DailyHealthSnapshot:
    """Aggregated daily health metrics from a wearable."""
    date: str                           # "YYYY-MM-DD"
    hrv_rmssd: Optional[float] = None   # ms (higher = better)
    resting_hr: Optional[int] = None    # bpm
    body_temperature: Optional[float] = None  # °C
    sleep_quality_score: Optional[float] = None  # 0-100
    sleep_duration_hours: Optional[float] = None
    respiratory_rate: Optional[float] = None  # breaths/min
    spo2: Optional[float] = None        # percentage


# ── Baseline computation ──────────────────────────────────────────────────

def compute_baselines(
    history: list[DailyHealthSnapshot],
    window_days: int = 14,
) -> dict:
    """
    Compute rolling baselines (mean ± std) for each available metric.

    Uses the most recent `window_days` snapshots.  Only metrics with
    at least 3 non-None values are baselined.

    Returns
    -------
    dict mapping metric name → {"mean": float, "std": float, "count": int}
    """
    if not history:
        return {}

    recent = history[-window_days:]
    metrics = ["hrv_rmssd", "resting_hr", "body_temperature",
               "sleep_quality_score", "sleep_duration_hours",
               "respiratory_rate", "spo2"]

    baselines = {}
    for m in metrics:
        vals = [getattr(s, m) for s in recent if getattr(s, m) is not None]
        if len(vals) >= 3:
            mean = statistics.mean(vals)
            std = statistics.stdev(vals) if len(vals) > 1 else 0.0
            # Prevent zero std from producing infinite z-scores
            std = max(std, 0.01)
            baselines[m] = {"mean": round(mean, 3), "std": round(std, 3), "count": len(vals)}
    return baselines


# ── Deviation scoring ──────────────────────────────────────────────────────

# How many standard deviations from baseline triggers concern, per metric.
# Negative z = metric dropped below baseline; positive z = above.
# For HRV a drop is bad (illness suppresses HRV).
# For RHR a rise is bad.
# For temperature a rise is bad.
# For sleep quality a drop is bad.
# For respiratory rate a rise is bad.
# For SpO2 a drop is bad.
_Z_THRESHOLDS = {
    "hrv_rmssd":          {"drop": -1.5},   # HRV below baseline
    "resting_hr":         {"rise": 1.5},    # HR above baseline
    "body_temperature":   {"rise": 1.0},    # temp above baseline (>0.4°C absolute)
    "sleep_quality_score":{"drop": -1.5},   # sleep quality below baseline
    "sleep_duration_hours":{"drop": -1.5},  # short sleep
    "respiratory_rate":   {"rise": 1.5},    # breathing rate above baseline
    "spo2":               {"drop": -2.0},   # oxygen saturation drop
}


def score_deviations(
    snapshot: DailyHealthSnapshot,
    baselines: dict,
) -> list[dict]:
    """
    Compute z-scores and flag deviations for each metric in today's snapshot.

    Returns a list of deviation records, one per metric with data.
    """
    deviations = []
    for metric, thresholds in _Z_THRESHOLDS.items():
        current = getattr(snapshot, metric)
        if current is None or metric not in baselines:
            continue

        bl = baselines[metric]
        z_score = (current - bl["mean"]) / bl["std"]

        # Determine if this deviates in the concerning direction
        concerning = False
        if "drop" in thresholds and z_score < thresholds["drop"]:
            concerning = True
        if "rise" in thresholds and z_score > thresholds["rise"]:
            concerning = True

        # Absolute thresholds for temperature (clinical guard)
        if metric == "body_temperature" and current >= 37.8:
            concerning = True

        deviations.append({
            "metric": metric,
            "current": current,
            "baseline_mean": bl["mean"],
            "baseline_std": bl["std"],
            "z_score": round(z_score, 3),
            "concerning": concerning,
            "direction": "above" if z_score > 0 else "below",
        })
    return deviations


# ── Composite illness probability ─────────────────────────────────────────

# Weights for each signal in the composite score.  Higher = more predictive.
_SIGNAL_WEIGHTS = {
    "hrv_rmssd":           3.0,   # Strongest single predictor
    "resting_hr":          2.5,
    "body_temperature":    4.0,   # Fever is definitive
    "sleep_quality_score": 1.5,
    "sleep_duration_hours":1.0,
    "respiratory_rate":    2.0,
    "spo2":                3.5,
}


def compute_illness_probability(
    deviations: list[dict],
    baseline_count: int = 14,
) -> dict:
    """
    Combine deviation signals into a single illness probability estimate.

    Returns
    -------
    dict with:
        probability: float 0-1
        severity: str ("none", "low", "medium", "high", "critical")
        contributing_signals: list of the most concerning deviations
        confidence: str ("low", "moderate", "high") based on data availability
    """
    if not deviations:
        return {
            "probability": 0.0,
            "severity": "none",
            "contributing_signals": [],
            "confidence": "low",
            "message": "No deviation data available.",
        }

    weighted_sum = 0.0
    total_weight = 0.0
    concerning_signals = []

    for d in deviations:
        weight = _SIGNAL_WEIGHTS.get(d["metric"], 1.0)
        # Contribution: how many z-scores away in the concerning direction
        if d["concerning"]:
            contribution = abs(d["z_score"]) / 3.0  # normalize: 3σ → 1.0
            contribution = min(contribution, 1.0)
            weighted_sum += contribution * weight
            concerning_signals.append(d)
        total_weight += weight

    # Normalize to 0-1
    if total_weight > 0:
        raw_prob = weighted_sum / total_weight
    else:
        raw_prob = 0.0

    # Clamp
    probability = min(1.0, max(0.0, raw_prob))

    # Severity mapping
    if probability >= 0.75:
        severity = "critical"
    elif probability >= 0.50:
        severity = "high"
    elif probability >= 0.25:
        severity = "medium"
    elif probability > 0.05:
        severity = "low"
    else:
        severity = "none"

    # Confidence based on how many metrics we have data for
    available = len(deviations)
    if available >= 5:
        confidence = "high"
    elif available >= 3:
        confidence = "moderate"
    else:
        confidence = "low"

    # Sort contributing signals by magnitude
    concerning_signals.sort(key=lambda d: abs(d["z_score"]), reverse=True)

    messages = {
        "critical": "Multiple strong indicators suggest illness onset. Rest, hydrate, and consider seeking medical attention.",
        "high": "Several health metrics deviate from baseline. Monitor closely and prioritize rest.",
        "medium": "Some indicators suggest you may be fighting something. Reduce training intensity.",
        "low": "Minor deviations detected. Probably fine, but stay aware.",
        "none": "All metrics within normal baseline range.",
    }

    return {
        "probability": round(probability, 3),
        "severity": severity,
        "contributing_signals": [
            {"metric": s["metric"], "z_score": s["z_score"], "current": s["current"]}
            for s in concerning_signals[:5]
        ],
        "confidence": confidence,
        "message": messages[severity],
        "metrics_evaluated": available,
    }


# ── Full analysis pipeline ────────────────────────────────────────────────

def detect_illness(
    history: list[DailyHealthSnapshot],
    today: Optional[DailyHealthSnapshot] = None,
    baseline_window: int = 14,
) -> dict:
    """
    Complete illness detection pipeline.

    Parameters
    ----------
    history : list of DailyHealthSnapshot
        Past 14+ days of health data.
    today : DailyHealthSnapshot, optional
        Today's snapshot.  If None, uses the last entry in history.
    baseline_window : int
        Number of recent days for baseline calculation.

    Returns
    -------
    dict with baselines, deviations, illness probability, and recommendations.
    """
    if not history:
        return {"error": "No health history provided."}

    baselines = compute_baselines(history, baseline_window)
    if not baselines:
        return {"error": "Not enough data to compute baselines (need ≥3 days per metric)."}

    if today is None:
        today = history[-1]

    deviations = score_deviations(today, baselines)
    result = compute_illness_probability(deviations, baseline_window)

    result["baselines"] = baselines
    result["deviations"] = deviations
    result["baseline_window_days"] = baseline_window
    result["today_date"] = today.date

    # Temperature absolute guard
    if today.body_temperature is not None and today.body_temperature >= 38.5:
        result["fever_alert"] = True
        result["fever_temperature"] = today.body_temperature
        result["message"] = (
            f"Fever detected ({today.body_temperature}°C). "
            "Rest, hydrate, and monitor symptoms. Seek medical care if fever persists."
        )

    return result


# ── Trend detection for chronic illness monitoring ────────────────────────

def detect_illness_trend(
    history: list[DailyHealthSnapshot],
    window_days: int = 7,
) -> dict:
    """
    Detect whether illness risk is increasing, decreasing, or stable
    over the recent window.
    """
    if len(history) < window_days + 14:
        return {"error": "Need at least 21 days of data for trend analysis."}

    baselines = compute_baselines(history[:-window_days])
    if not baselines:
        return {"error": "Insufficient baseline data."}

    daily_probs = []
    for snapshot in history[-window_days:]:
        devs = score_deviations(snapshot, baselines)
        result = compute_illness_probability(devs)
        daily_probs.append(result["probability"])

    if len(daily_probs) < 3:
        return {"error": "Not enough daily scores for trend."}

    first_half = statistics.mean(daily_probs[:len(daily_probs) // 2])
    second_half = statistics.mean(daily_probs[len(daily_probs) // 2:])

    if second_half > first_half * 1.3:
        trend = "worsening"
        description = "Illness probability has been rising over recent days."
    elif second_half < first_half * 0.7:
        trend = "improving"
        description = "Illness probability has been declining — recovery looks likely."
    else:
        trend = "stable"
        description = "Illness risk has been stable."

    return {
        "trend": trend,
        "description": description,
        "recent_avg_probability": round(second_half, 3),
        "prior_avg_probability": round(first_half, 3),
        "daily_probabilities": [round(p, 3) for p in daily_probs],
    }

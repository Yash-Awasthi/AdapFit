"""
Health Predictions Engine

7-day forecasting for sleep, readiness, activity, and HRV using weighted
moving averages, trend extrapolation, and confidence intervals.  Includes
IQR and z-score anomaly detection.  Pure functions only.
"""
from dataclasses import dataclass
from typing import Optional
import statistics
import math


@dataclass
class DailyMetric:
    """Single day's health metrics for prediction input."""
    date: str
    sleep_score: Optional[float] = None       # 0-100
    sleep_hours: Optional[float] = None
    readiness_score: Optional[float] = None    # 0-100
    steps: Optional[int] = None
    hrv_rmssd: Optional[float] = None
    resting_hr: Optional[int] = None


# ── Helpers ────────────────────────────────────────────────────────────────

def _values(series: list[Optional[float]]) -> list[float]:
    """Extract non-None values."""
    return [v for v in series if v is not None]


def _linear_trend(values: list[float]) -> float:
    """Slope of linear regression (per-day change)."""
    n = len(values)
    if n < 2:
        return 0.0
    x = list(range(n))
    x_mean = statistics.mean(x)
    y_mean = statistics.mean(values)
    num = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, values))
    den = sum((xi - x_mean) ** 2 for xi in x)
    return num / den if den > 0 else 0.0


def _exponential_weights(n: int, alpha: float = 0.3) -> list[float]:
    """Exponential smoothing weights (most recent = highest weight)."""
    weights = [(1 - alpha) ** i for i in range(n)][::-1]
    total = sum(weights)
    return [w / total for w in weights]


def _confidence_interval(
    values: list[float], horizon: int, confidence: float = 0.95,
) -> tuple[float, float]:
    """Prediction interval using expanding standard deviation."""
    if len(values) < 2:
        mean = values[0] if values else 0.0
        return (mean, mean)
    std = statistics.stdev(values)
    # Z-score for confidence level (1.96 for 95%)
    z = 1.96 if confidence >= 0.95 else 1.645 if confidence >= 0.90 else 1.0
    # Uncertainty grows with sqrt(horizon)
    margin = z * std * math.sqrt(horizon) * 0.5
    return (std, margin)


# ── Sleep Score Prediction ─────────────────────────────────────────────────

def predict_sleep_score(
    history: list[DailyMetric],
    days: int = 7,
) -> dict:
    """
    Predict sleep score for the next `days` days using weighted moving average
    + linear trend extrapolation.

    Returns predictions with confidence intervals.
    """
    scores = _values([m.sleep_score for m in history])
    if not scores:
        return {"error": "No sleep score data available."}

    # Weighted moving average (recent days weighted more)
    weights = _exponential_weights(min(len(scores), 14))
    recent = scores[-len(weights):]
    wma = sum(s * w for s, w in zip(recent, weights))

    # Trend
    slope = _linear_trend(scores[-14:]) if len(scores) >= 2 else 0.0

    # Generate predictions
    predictions = []
    std, margin = _confidence_interval(scores, days)
    for d in range(1, days + 1):
        predicted = max(0, min(100, wma + slope * d))
        predictions.append({
            "day": d,
            "predicted_score": round(predicted, 1),
            "ci_lower": round(max(0, predicted - margin), 1),
            "ci_upper": round(min(100, predicted + margin), 1),
        })

    # Trend direction
    if slope > 1.0:
        trend = "improving"
    elif slope < -1.0:
        trend = "declining"
    else:
        trend = "stable"

    return {
        "predictions": predictions,
        "current_avg": round(statistics.mean(scores[-7:]), 1),
        "trend": trend,
        "trend_slope": round(slope, 3),
        "confidence_level": 0.95,
        "data_points": len(scores),
    }


# ── Readiness Prediction ──────────────────────────────────────────────────

def predict_readiness(
    history: list[DailyMetric],
    days: int = 7,
) -> dict:
    """
    Predict tomorrow's readiness from today's composite metrics.
    Uses a simple regression model: readiness = f(sleep, HRV, RHR).
    """
    # Build feature vectors for days with complete data
    features = []
    targets = []
    for i, m in enumerate(history):
        if m.readiness_score is None:
            continue
        feats = []
        if m.sleep_score is not None:
            feats.append(m.sleep_score / 100.0)
        if m.hrv_rmssd is not None:
            feats.append(min(1.0, m.hrv_rmssd / 100.0))
        if m.resting_hr is not None:
            feats.append(1.0 - min(1.0, m.resting_hr / 100.0))  # invert: lower is better
        if m.sleep_hours is not None:
            feats.append(min(1.0, m.sleep_hours / 9.0))
        if len(feats) >= 2:
            features.append(feats)
            targets.append(m.readiness_score)

    if len(features) < 3:
        # Fallback: weighted average
        scores = _values([m.readiness_score for m in history])
        if not scores:
            return {"error": "No readiness data available."}
        avg = statistics.mean(scores[-7:])
        std = statistics.stdev(scores[-7:]) if len(scores) >= 2 else 5.0
        return {
            "predictions": [{"day": d, "predicted": round(avg, 1),
                             "ci_lower": round(max(0, avg - std), 1),
                             "ci_upper": round(min(100, avg + std), 1)}
                            for d in range(1, days + 1)],
            "method": "weighted_average",
            "data_points": len(scores),
        }

    # Simple linear regression (OLS) with multiple features
    n = len(targets)
    n_feat = len(features[0])
    # Average coefficient: each feature's correlation with target
    coeffs = []
    for f_idx in range(n_feat):
        feat_vals = [f[f_idx] for f in features]
        if statistics.stdev(feat_vals) > 0 and statistics.stdev(targets) > 0:
            corr = statistics.correlation(feat_vals, targets) if hasattr(statistics, 'correlation') else (
                sum((fx - statistics.mean(feat_vals)) * (ty - statistics.mean(targets))
                    for fx, ty in zip(feat_vals, targets))
                / (n * statistics.stdev(feat_vals) * statistics.stdev(targets))
            )
        else:
            corr = 0.0
        coeffs.append(corr)

    # Predict using last known features
    last_feats = features[-1]
    base_pred = sum(f * c for f, c in zip(last_feats, coeffs))
    # Scale to 0-100
    base_pred = max(0, min(100, base_pred * 100 + statistics.mean(targets) * (1 - abs(sum(coeffs)))))

    # Trend
    readiness_scores = _values([m.readiness_score for m in history])
    slope = _linear_trend(readiness_scores[-14:]) if len(readiness_scores) >= 2 else 0.0
    std = statistics.stdev(readiness_scores[-7:]) if len(readiness_scores) >= 2 else 5.0

    predictions = []
    for d in range(1, days + 1):
        predicted = max(0, min(100, base_pred + slope * d))
        predictions.append({
            "day": d,
            "predicted": round(predicted, 1),
            "ci_lower": round(max(0, predicted - std * 1.5), 1),
            "ci_upper": round(min(100, predicted + std * 1.5), 1),
        })

    return {
        "predictions": predictions,
        "method": "feature_regression",
        "trend_slope": round(slope, 3),
        "data_points": n,
    }


# ── Activity Prediction ───────────────────────────────────────────────────

def predict_activity(
    history: list[DailyMetric],
    days: int = 7,
) -> dict:
    """
    Predict expected step count using day-of-week patterns + trend.
    """
    steps_data = [(m.date, m.steps) for m in history if m.steps is not None]
    if not steps_data:
        return {"error": "No step data available."}

    # Parse day of week from date strings
    from datetime import datetime
    dow_steps: dict[int, list[int]] = {}
    all_steps = []
    for date_str, steps in steps_data:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            dow = dt.weekday()
        except ValueError:
            dow = len(all_steps) % 7
        dow_steps.setdefault(dow, []).append(steps)
        all_steps.append(steps)

    # Day-of-week averages
    dow_avg = {dow: statistics.mean(vals) for dow, vals in dow_steps.items()}

    # Overall trend
    slope = _linear_trend([float(s) for s in all_steps[-28:]])
    overall_avg = statistics.mean(all_steps[-14:])

    # Predict for next N days
    last_date = datetime.strptime(steps_data[-1][0], "%Y-%m-%d")
    predictions = []
    std = statistics.stdev(all_steps[-14:]) if len(all_steps) >= 2 else overall_avg * 0.15

    for d in range(1, days + 1):
        future_date = last_date + __import__("datetime").timedelta(days=d)
        dow = future_date.weekday()
        base = dow_avg.get(dow, overall_avg)
        predicted = max(0, base + slope * d)
        predictions.append({
            "day": d,
            "date": future_date.strftime("%Y-%m-%d"),
            "day_of_week": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dow],
            "predicted_steps": round(predicted),
            "ci_lower": round(max(0, predicted - std)),
            "ci_upper": round(predicted + std),
        })

    return {
        "predictions": predictions,
        "daily_averages": {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][d]: round(v)
                          for d, v in sorted(dow_avg.items())},
        "overall_avg_steps": round(overall_avg),
        "trend_slope": round(slope, 1),
        "data_points": len(all_steps),
    }


# ── HRV Trend Prediction ──────────────────────────────────────────────────

def predict_hrv(
    history: list[DailyMetric],
    days: int = 7,
) -> dict:
    """
    Predict HRV recovery trajectory using exponential smoothing + trend.
    """
    hrv_values = _values([m.hrv_rmssd for m in history])
    if len(hrv_values) < 3:
        if not hrv_values:
            return {"error": "No HRV data available."}
        avg = statistics.mean(hrv_values)
        return {
            "predictions": [{"day": d, "predicted": round(avg, 1),
                             "ci_lower": round(avg * 0.8, 1), "ci_upper": round(avg * 1.2, 1)}
                            for d in range(1, days + 1)],
            "method": "mean_fallback",
            "data_points": len(hrv_values),
        }

    # Exponential weighted moving average
    weights = _exponential_weights(min(len(hrv_values), 14))
    recent = hrv_values[-len(weights):]
    ewma = sum(v * w for v, w in zip(recent, weights))

    # Trend
    slope = _linear_trend(hrv_values[-14:])
    std = statistics.stdev(hrv_values[-14:]) if len(hrv_values) >= 14 else statistics.stdev(hrv_values)

    predictions = []
    for d in range(1, days + 1):
        predicted = max(0, ewma + slope * d)
        predictions.append({
            "day": d,
            "predicted_hrv": round(predicted, 1),
            "ci_lower": round(max(0, predicted - std * 1.5), 1),
            "ci_upper": round(predicted + std * 1.5, 1),
        })

    # Recovery assessment
    if slope > 0.5:
        recovery = "improving"
    elif slope < -0.5:
        recovery = "declining"
    else:
        recovery = "stable"

    return {
        "predictions": predictions,
        "current_hrv": round(hrv_values[-1], 1),
        "avg_hrv": round(statistics.mean(hrv_values[-7:]), 1),
        "recovery_trajectory": recovery,
        "trend_slope": round(slope, 3),
        "data_points": len(hrv_values),
    }


# ── Anomaly Detection ─────────────────────────────────────────────────────

def detect_anomalies(
    history: list[DailyMetric],
    sensitivity: float = 1.5,
) -> dict:
    """
    Detect anomalous values using both IQR and z-score methods.

    Parameters
    ----------
    sensitivity : float
        IQR multiplier (lower = more sensitive). Default 1.5 = standard.
        Z-score threshold is sensitivity * 2 (so default = 3.0σ).

    Returns anomalies for each metric with method and severity.
    """
    metrics_to_check = {
        "sleep_score": [m.sleep_score for m in history if m.sleep_score is not None],
        "sleep_hours": [m.sleep_hours for m in history if m.sleep_hours is not None],
        "readiness_score": [m.readiness_score for m in history if m.readiness_score is not None],
        "steps": [float(m.steps) for m in history if m.steps is not None],
        "hrv_rmssd": [m.hrv_rmssd for m in history if m.hrv_rmssd is not None],
        "resting_hr": [float(m.resting_hr) for m in history if m.resting_hr is not None],
    }

    anomalies = []
    z_threshold = sensitivity * 2.0

    for metric_name, values in metrics_to_check.items():
        if len(values) < 5:
            continue

        sorted_vals = sorted(values)
        n = len(sorted_vals)

        # IQR method
        q1 = sorted_vals[n // 4]
        q3 = sorted_vals[3 * n // 4]
        iqr = q3 - q1
        lower_bound = q1 - sensitivity * iqr
        upper_bound = q3 + sensitivity * iqr

        # Z-score method
        mean = statistics.mean(values)
        std = statistics.stdev(values) if len(values) > 1 else 0.01

        # Check latest value
        latest = values[-1]
        z_score = (latest - mean) / std if std > 0 else 0.0

        iqr_anomaly = latest < lower_bound or latest > upper_bound
        z_anomaly = abs(z_score) > z_threshold

        if iqr_anomaly or z_anomaly:
            # Determine severity
            if abs(z_score) > z_threshold * 1.5 or latest < lower_bound * 0.5 or latest > upper_bound * 1.5:
                severity = "critical"
            elif abs(z_score) > z_threshold or latest < lower_bound or latest > upper_bound:
                severity = "warning"
            else:
                severity = "info"

            direction = "high" if latest > upper_bound else "low"
            anomalies.append({
                "metric": metric_name,
                "latest_value": round(latest, 2),
                "mean": round(mean, 2),
                "std": round(std, 2),
                "z_score": round(z_score, 3),
                "iqr_lower": round(lower_bound, 2),
                "iqr_upper": round(upper_bound, 2),
                "direction": direction,
                "severity": severity,
                "methods_triggered": (
                    ["iqr", "z_score"] if (iqr_anomaly and z_anomaly)
                    else ["iqr"] if iqr_anomaly else ["z_score"]
                ),
            })

    # Sort by severity then z-score magnitude
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    anomalies.sort(key=lambda a: (severity_order.get(a["severity"], 3), -abs(a["z_score"])))

    return {
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
        "metrics_evaluated": len(metrics_to_check),
        "sensitivity": sensitivity,
        "data_points": len(history),
    }

"""Trend analytics over a user's measured logs. Nothing here fills in a missing value."""
import math
from typing import Any, Dict, List
from app.core.workout_metrics import session_load

class TrendCorrelationAnalyzer:
    """Analyzes correlations between health metrics over time."""

    def __init__(self):
        self._correlation_cache: Dict[str, Dict] = {}

    def pearson_correlation(self, x: List[float], y: List[float]) -> Dict[str, Any]:
        """Compute Pearson correlation coefficient between two metric series."""
        n = min(len(x), len(y))
        if n < 3:
            return {"r": 0.0, "p_value_approx": 1.0, "significance": "insufficient_data", "n": n}

        x, y = x[:n], y[:n]
        mean_x = sum(x) / n
        mean_y = sum(y) / n

        cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        std_x = math.sqrt(sum((xi - mean_x)**2 for xi in x))
        std_y = math.sqrt(sum((yi - mean_y)**2 for yi in y))

        if std_x == 0 or std_y == 0:
            return {"r": 0.0, "p_value_approx": 1.0, "significance": "constant_series", "n": n}

        r = cov / (std_x * std_y)
        r = max(-1.0, min(1.0, r))

        # Approximate p-value using t-distribution (simplified)
        if abs(r) >= 1.0:
            p = 0.0
        else:
            t_stat = r * math.sqrt((n - 2) / (1 - r**2))
            # Rough approximation of p-value from t-statistic
            p = max(0.001, min(1.0, 2.0 * math.exp(-0.5 * abs(t_stat))))

        if p < 0.01:
            sig = "highly_significant"
        elif p < 0.05:
            sig = "significant"
        elif p < 0.10:
            sig = "marginally_significant"
        else:
            sig = "not_significant"

        return {
            "r": round(r, 4),
            "p_value_approx": round(p, 4),
            "significance": sig,
            "n": n,
            "interpretation": self._interpret_correlation(r),
        }

    def _interpret_correlation(self, r: float) -> str:
        abs_r = abs(r)
        direction = "positive" if r > 0 else "negative"
        if abs_r > 0.7:
            return f"Strong {direction} correlation"
        elif abs_r > 0.4:
            return f"Moderate {direction} correlation"
        elif abs_r > 0.2:
            return f"Weak {direction} correlation"
        else:
            return "Negligible correlation"

    def analyze_metric_correlations(
        self, recovery_logs: List[dict], workload_logs: List[dict]
    ) -> Dict[str, Any]:
        """Correlations between measured metrics, paired by calendar day; a missing value drops that day."""
        by_day: Dict[str, dict] = {str(r.get("log_date", ""))[:10]: dict(r) for r in recovery_logs if r.get("log_date")}
        for w in workload_logs:
            load, day = session_load(w), str(w.get("recorded_at") or w.get("completed_at") or "")[:10]
            if load is not None and day in by_day:
                by_day[day]["_load"] = by_day[day].get("_load", 0.0) + load
        days = sorted(by_day)
        rows = [by_day[d] for d in days]
        next_day = {days[i]: rows[i + 1] for i in range(len(days) - 1)}

        def series(xk, yk, lag=False):
            pairs = []
            for d, r in zip(days, rows):
                y_row = next_day.get(d) if lag else r
                if y_row is not None and r.get(xk) is not None and y_row.get(yk) is not None:
                    pairs.append((float(r[xk]), float(y_row[yk])))
            return [p[0] for p in pairs], [p[1] for p in pairs]

        specs = [
            ("hrv_vs_recovery", "hrv_rmssd", "recovery_score", False),
            ("sleep_vs_recovery", "sleep_duration_hours", "recovery_score", False),
            ("sleep_vs_hrv", "sleep_duration_hours", "hrv_rmssd", False),
            ("load_vs_next_day_recovery", "_load", "recovery_score", True),
        ]
        correlations, insights = {}, []
        for name, xk, yk, lag in specs:
            x, y = series(xk, yk, lag)
            if len(x) < 5:
                continue
            corr = self.pearson_correlation(x, y)
            correlations[name] = corr
            if corr["significance"] in ("significant", "highly_significant"):
                if name == "sleep_vs_recovery":
                    insights.append(f"On your nights with more sleep, your recovery score was "
                                    f"{'higher' if corr['r'] > 0 else 'lower'} (r={corr['r']:.2f}, {corr['n']} days).")
                elif name == "hrv_vs_recovery":
                    insights.append(f"Your HRV tracks your recovery score (r={corr['r']:.2f}, {corr['n']} days).")
                elif name == "load_vs_next_day_recovery":
                    insights.append(f"Harder training days were followed by {'better' if corr['r'] > 0 else 'lower'} "
                                    f"recovery the next morning (r={corr['r']:.2f}, {corr['n']} days).")
        if not correlations:
            insights.append("Need at least 5 days with both values logged to look for patterns.")
        elif not insights:
            insights.append("No clear pattern in your data yet. Keep logging.")
        return {"correlations": correlations, "insights": insights, "data_points": len(days)}


class WorkoutPerformancePredictor:
    """Today's volume capacity from measured recovery, sleep and training load."""

    def predict_volume_capacity(
        self, recovery_score: float, recent_avg_volume: float,
        acwr: float, sleep_hours: float
    ) -> Dict[str, Any]:
        """Estimate today's volume capacity compared to baseline."""
        # Base capacity from recovery score
        recovery_factor = recovery_score / 100.0

        # Sleep adjustment: < 6h reduces capacity
        sleep_factor = min(1.0, sleep_hours / 7.5) if sleep_hours > 0 else 0.85

        # ACWR adjustment: high ACWR reduces capacity
        if acwr > 1.5:
            acwr_factor = 0.6
        elif acwr > 1.3:
            acwr_factor = 0.8
        elif acwr < 0.7:
            acwr_factor = 0.9  # undertraining, slight boost
        else:
            acwr_factor = 1.0

        combined = recovery_factor * sleep_factor * acwr_factor
        capacity = recent_avg_volume * combined

        return {
            "estimated_volume": round(capacity, 0),
            "capacity_ratio": round(combined, 2),
            "recovery_factor": round(recovery_factor, 2),
            "sleep_factor": round(sleep_factor, 2),
            "acwr_factor": round(acwr_factor, 2),
            "recommendation": (
                "Push for PRs" if combined > 1.05
                else "Maintain current level" if combined > 0.85
                else "Reduce volume by " + str(int((1 - combined) * 100)) + "%"
            ),
        }


class AdvancedMLEngine:
    """Trend correlation, HRV trend line, anomaly flags and volume capacity over measured data."""

    def __init__(self):

        # New sub-systems
        self.correlation = TrendCorrelationAnalyzer()
        self.performance_predictor = WorkoutPerformancePredictor()

    def train_readiness_model(self, features_list: List[List[float]], labels: List[int]):
        # No trained model: a global net over every user's feedback is not personal, and it never ran.
        return {"status": "not_trained", "model_type": "rule_based"}

    def forecast_hrv(self, hrv_history: List[float], days_ahead: int = 7) -> Dict[str, Any]:
        if len(hrv_history) < 3:
            return {"forecast": [], "trend": "insufficient_data", "slope": 0.0}

        n = len(hrv_history)
        x_mean = (n - 1) / 2
        y_mean = sum(hrv_history) / n

        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(hrv_history))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator > 0 else 0
        intercept = y_mean - slope * x_mean

        # Compute R² for confidence
        ss_res = sum((v - (intercept + slope * i))**2 for i, v in enumerate(hrv_history))
        ss_tot = sum((v - y_mean)**2 for v in hrv_history)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        forecast = []
        for d in range(1, days_ahead + 1):
            pred = intercept + slope * (n + d - 1)
            forecast.append(round(max(0, pred), 1))

        trend = "improving" if slope > 0.5 else ("declining" if slope < -0.5 else "stable")

        return {
            "forecast": forecast,
            "trend": trend,
            "slope": round(slope, 3),
            "r_squared": round(max(0, r_squared), 3),
            "current_mean": round(y_mean, 1),
            "method": "linear_regression",
        }

    def detect_anomalies(self, values: List[float], threshold: float = 2.0) -> Dict[str, Any]:
        if len(values) < 3:
            return {"anomalies": [], "anomaly_count": 0}
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std = variance ** 0.5 if variance > 0 else 1.0
        anomalies = []
        for i, v in enumerate(values):
            z = abs((v - mean) / std) if std > 0.001 else 0
            if z > threshold:
                anomalies.append({"index": i, "value": v, "z_score": round(z, 2)})
        return {"anomalies": anomalies, "anomaly_count": len(anomalies), "mean": round(mean, 1), "std": round(std, 1)}

    def get_status(self):
        return {
            "model_trained": False,
            "correlation_engine": "active",
            "performance_predictor": "active",
        }


# Singleton — replace old ml_engine
ml_engine = AdvancedMLEngine()

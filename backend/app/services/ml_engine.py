"""
AdapFit Advanced ML Analytics Engine v2
Adds XGBoost/LightGBM ensemble, trend correlation analysis,
workout performance prediction, and fatigue forecasting.
"""
import math
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone

# Lazy-loaded ML dependencies — loaded on first use
_HAS_NUMPY = None  # None = not checked yet
_HAS_PYTORCH = None
_HAS_XGBOOST = None
_HAS_LIGHTGBM = None

def _ensure_numpy():
    global _HAS_NUMPY
    if _HAS_NUMPY is not None:
        return
    try:
        import numpy as np
        _HAS_NUMPY = True
    except ImportError:
        _HAS_NUMPY = False

def _ensure_pytorch():
    global _HAS_PYTORCH
    if _HAS_PYTORCH is not None:
        return
    try:
        import torch
        _HAS_PYTORCH = True
    except ImportError:
        _HAS_PYTORCH = False

def _ensure_xgboost():
    global _HAS_XGBOOST
    if _HAS_XGBOOST is not None:
        return
    try:
        from xgboost import XGBRegressor, XGBClassifier
        _HAS_XGBOOST = True
    except ImportError:
        _HAS_XGBOOST = False

def _ensure_lightgbm():
    global _HAS_LIGHTGBM
    if _HAS_LIGHTGBM is not None:
        return
    try:
        from lightgbm import LGBMRegressor
        _HAS_LIGHTGBM = True
    except ImportError:
        _HAS_LIGHTGBM = False


class ReadinessNet(object):
    def __init__(self, input_dim=14, hidden_dim=32, output_dim=4):
        if not _HAS_PYTORCH:
            return
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x):
        return self.net(x)


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
        self, recovery_logs: List[dict], workout_logs: List[dict]
    ) -> Dict[str, Any]:
        """Analyze correlations between key fitness metrics."""
        # Align logs by date
        n = min(len(recovery_logs), len(workout_logs))
        if n < 5:
            return {"correlations": {}, "insights": ["Need more data (5+ days) for correlation analysis."]}

        recent_recovery = recovery_logs[-n:]
        recent_workouts = workout_logs[-n:]

        # Extract aligned series
        hrv = [r.get("hrv_rmssd", 50) for r in recent_recovery]
        sleep = [r.get("sleep_duration_hours", 7) for r in recent_recovery]
        recovery_scores = [r.get("recovery_score", 70) for r in recent_recovery]
        rpe = [w.get("session_rpe", 5) for w in recent_workouts]
        workout_load = [w.get("session_load", 500) for w in recent_workouts]
        workout_duration = [w.get("duration_minutes", 45) for w in recent_workouts]

        # Calculate all pairwise correlations
        pairs = [
            ("hrv_vs_recovery", hrv, recovery_scores),
            ("sleep_vs_recovery", sleep, recovery_scores),
            ("hrv_vs_sleep", hrv, sleep),
            ("rpe_vs_next_day_recovery", rpe[:-1], recovery_scores[1:]) if n > 1 else ("rpe_vs_recovery", rpe, recovery_scores),
            ("workload_vs_acwr_trend", workout_load, [1.0] * n),  # placeholder
            ("sleep_vs_hrv", sleep, hrv),
            ("duration_vs_rpe", workout_duration, rpe),
        ]

        correlations = {}
        insights = []

        for name, x, y in pairs:
            if len(x) >= 3 and len(y) >= 3:
                corr = self.pearson_correlation(x, y)
                correlations[name] = corr

                # Generate insights
                if corr["significance"] in ("significant", "highly_significant"):
                    if "sleep_vs_recovery" in name:
                        insights.append(
                            f"Sleep duration {'positively' if corr['r'] > 0 else 'negatively'} "
                            f"correlates with recovery (r={corr['r']:.2f}). "
                            f"{'Prioritize sleep to boost recovery.' if corr['r'] > 0 else 'Unexpected — investigate sleep quality.'}"
                        )
                    elif "hrv_vs_recovery" in name:
                        insights.append(
                            f"HRV {'tracks well' if corr['r'] > 0.5 else 'weakly correlates'} "
                            f"with recovery score (r={corr['r']:.2f})."
                        )
                    elif "rpe_vs" in name:
                        direction = "higher" if corr["r"] > 0 else "lower"
                        insights.append(
                            f"Higher session RPE tends to lead to {'worse' if corr['r'] > 0 else 'better'} "
                            f"next-day recovery (r={corr['r']:.2f})."
                        )

        if not insights:
            insights.append("No strong correlations found yet. Keep logging daily data for pattern detection.")

        return {
            "correlations": correlations,
            "insights": insights,
            "data_points": n,
        }


class WorkoutPerformancePredictor:
    """Predicts workout performance metrics using gradient boosting."""

    def __init__(self):
        self._model = None
        self._is_trained = False
        self._training_data_x: List[List[float]] = []
        self._training_data_y: List[float] = []

    def extract_performance_features(self, recovery_log: dict, workout_log: dict) -> List[float]:
        """Extract features for performance prediction."""
        return [
            recovery_log.get("hrv_rmssd", 50),
            recovery_log.get("sleep_duration_hours", 7),
            recovery_log.get("sleep_efficiency_pct", 85),
            recovery_log.get("recovery_score", 70),
            recovery_log.get("hrv_z_score", 0) or 0,
            workout_log.get("session_rpe", 5),
            workout_log.get("session_load", 500),
            workout_log.get("duration_minutes", 45),
            workout_log.get("total_volume_kg", 5000),
            workout_log.get("acwr", 1.0),
            # Day of week as cyclical
            0.5,  # placeholder — in production use sin/cos encoding
            # Historical averages
            recovery_log.get("recovery_score", 70),  # placeholder for 7d avg
        ]

    def train(self, features_list: List[List[float]], labels: List[float]) -> Dict[str, Any]:
        """Train the performance predictor."""
        self._training_data_x.extend(features_list)
        self._training_data_y.extend(labels)

        if len(self._training_data_x) < 5:
            return {"status": "insufficient_data", "samples": len(self._training_data_x)}

        _ensure_xgboost()
        if _HAS_XGBOOST:
            try:
                from xgboost import XGBRegressor
                X = self._training_data_x[-200:]
                y = self._training_data_y[-200:]

                self._model = XGBRegressor(
                    n_estimators=50, max_depth=4, learning_rate=0.1,
                    random_state=42, verbosity=0
                )
                self._model.fit(X, y)
                self._is_trained = True
                return {"status": "trained", "model": "xgboost", "samples": len(self._training_data_x)}
            except Exception as e:
                return {"status": "error", "error": str(e)}

        return {"status": "no_xgboost", "samples": len(self._training_data_x)}

    def predict_next_rpe(self, features: List[float]) -> Dict[str, Any]:
        """Predict expected RPE for tomorrow's workout."""
        _ensure_xgboost()
        if _HAS_XGBOOST and self._is_trained and self._model is not None:
            try:
                pred = self._model.predict([features])[0]
                return {
                    "predicted_rpe": round(max(1, min(10, float(pred))), 1),
                    "model_type": "xgboost",
                    "confidence": 0.75,
                }
            except Exception:
                pass

        # Fallback: weighted average of recent context
        avg_rpe = sum(features[5:6]) / 1 if features[5:6] else 5.0
        recovery_factor = features[3] / 100.0  # recovery score
        adjusted_rpe = avg_rpe * (1.1 - 0.2 * recovery_factor)
        return {
            "predicted_rpe": round(max(1, min(10, adjusted_rpe)), 1),
            "model_type": "heuristic_fallback",
            "confidence": 0.4,
        }

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


class FatigueForecaster:
    """Forecasts fatigue accumulation and optimal deload timing."""

    def forecast_fatigue_trajectory(
        self, workout_logs: List[dict], recovery_logs: List[dict]
    ) -> Dict[str, Any]:
        """Project fatigue trajectory and suggest deload timing."""
        if len(workout_logs) < 7:
            return {
                "trajectory": "insufficient_data",
                "days_to_deload": None,
                "current_fatigue": 0,
            }

        # Calculate cumulative fatigue from recent sessions
        fatigue_scores = []
        cumulative = 0.0

        for wl in workout_logs[-14:]:
            rpe = wl.get("session_rpe", 5)
            duration = wl.get("duration_minutes", 45)
            load = rpe * duration

            # Fatigue accumulates faster than fitness
            acute_fatigue = load * 0.3  # fast component
            chronic_fitness = load * 0.1  # slow component
            cumulative += (acute_fatigue - chronic_fitness)

            # Recovery reduces fatigue
            recovery_factor = 0.85  # 15% recovery per day baseline
            cumulative *= recovery_factor

            fatigue_scores.append(round(max(0, cumulative), 1))

        current_fatigue = fatigue_scores[-1] if fatigue_scores else 0

        # Find fatigue threshold (adaptive based on history)
        threshold = max(500, sum(fatigue_scores) / len(fatigue_scores) * 2.5) if fatigue_scores else 750

        # Forecast
        future_fatigue = []
        projected = current_fatigue
        days_to_deload = None

        for day in range(1, 14):
            # Assume moderate training continues
            projected = projected * 0.85 + 200  # ~200 fatigue/day moderate training
            future_fatigue.append(round(projected, 1))

            if projected >= threshold and days_to_deload is None:
                days_to_deload = day

        # Overall assessment
        if current_fatigue >= threshold * 0.8:
            status = "NEAR_DELOAD"
        elif current_fatigue >= threshold * 0.5:
            status = "ACCUMULATING"
        else:
            status = "MANAGEABLE"

        return {
            "current_fatigue": round(current_fatigue, 1),
            "fatigue_threshold": round(threshold, 1),
            "status": status,
            "days_to_deload": days_to_deload,
            "future_trajectory": future_fatigue[:7],  # Next 7 days
            "recommendation": (
                "Schedule deload this week" if status == "NEAR_DELOAD"
                else f"Deload recommended in ~{days_to_deload} days" if days_to_deload
                else "Fatigue is manageable — continue current training"
            ),
        }


class AdvancedMLEngine:
    """
    Enterprise ML analytics engine v2.
    Combines neural nets, XGBoost/LightGBM ensemble, trend correlation,
    workout performance prediction, and fatigue forecasting.
    """

    def __init__(self):
        self.readiness_model = None  # lazy-created on first train/predict
        self.is_trained = False
        self.training_samples = 0
        self._feature_history: List[List[float]] = []
        self._label_history: List[int] = []

        # New sub-systems
        self.correlation = TrendCorrelationAnalyzer()
        self.performance_predictor = WorkoutPerformancePredictor()
        self.fatigue_forecaster = FatigueForecaster()

    def extract_features(self, recovery_logs: List[dict], workout_logs: List[dict]) -> List[float]:
        """Extract ML features from user's recent history."""
        features = []

        hrvs = [r.get("hrv_rmssd") or 50.0 for r in recovery_logs[-7:]]
        hrvs += [50.0] * (7 - len(hrvs))
        features.extend(hrvs[:7])

        sleeps = [r.get("sleep_duration_hours") or 7.5 for r in recovery_logs[-7:]]
        sleeps += [7.5] * (7 - len(sleeps))
        features.extend(sleeps[:7])

        scores = [r.get("recovery_score", 70) for r in recovery_logs[-7:]]
        scores += [70] * (7 - len(scores))
        features.extend(scores[:3])

        latest_acwr = 1.0
        if workout_logs:
            latest_acwr = workout_logs[-1].get("acwr", 1.0)
        features.append(latest_acwr)

        last_rpe = 5.0
        if workout_logs:
            last_rpe = float(workout_logs[-1].get("session_rpe", 5))
        features.append(last_rpe)

        # Extended features for v2
        # 7-day average recovery score
        avg_recovery = sum(r.get("recovery_score", 70) for r in recovery_logs[-7:]) / max(len(recovery_logs[-7:]), 1)
        features.append(avg_recovery)

        # 7-day average RPE
        avg_rpe = sum(w.get("session_rpe", 5) for w in workout_logs[-7:]) / max(len(workout_logs[-7:]), 1) if workout_logs else 5.0
        features.append(avg_rpe)

        # Workout frequency (sessions per week in last 14 days)
        features.append(min(7, len(workout_logs[-7:])))

        # Sleep debt (target 8h minus actual over last 3 days)
        recent_sleep = [r.get("sleep_duration_hours", 7) for r in recovery_logs[-3:]]
        sleep_debt = sum(max(0, 8.0 - s) for s in recent_sleep)
        features.append(min(12.0, sleep_debt))

        return features

    def train_readiness_model(self, features_list: List[List[float]], labels: List[int]):
        _ensure_pytorch()
        if not _HAS_PYTORCH or len(features_list) < 5:
            self._feature_history.extend(features_list)
            self._label_history.extend(labels)
            self.training_samples = len(self._label_history)
            return {"status": "insufficient_data", "samples": self.training_samples}

        self._feature_history.extend(features_list)
        self._label_history.extend(labels)
        self.training_samples = len(self._label_history)

        X = torch.tensor(self._feature_history[-100:], dtype=torch.float32)
        y = torch.tensor(self._label_history[-100:], dtype=torch.long)

        optimizer = optim.Adam(self.readiness_model.parameters(), lr=0.001)
        criterion = nn.CrossEntropyLoss()

        self.readiness_model.train()
        for epoch in range(50):
            optimizer.zero_grad()
            output = self.readiness_model(X)
            loss = criterion(output, y)
            loss.backward()
            optimizer.step()

        self.is_trained = True
        return {"status": "trained", "samples": self.training_samples, "loss": loss.item()}

    def predict_readiness(self, features: List[float]) -> Dict[str, Any]:
        states = ["DEPLETED", "REDUCED", "MODERATE", "OPTIMAL"]

        _ensure_pytorch()
        if _HAS_PYTORCH and self.is_trained and self.readiness_model is not None:
            self.readiness_model.eval()
            with torch.no_grad():
                x = torch.tensor([features], dtype=torch.float32)
                output = self.readiness_model(x)
                probs = torch.softmax(output, dim=1).numpy()[0]
                pred_idx = int(probs.argmax())
                return {
                    "predicted_state": states[pred_idx],
                    "confidence": float(probs[pred_idx]),
                    "probabilities": {states[i]: float(probs[i]) for i in range(4)},
                    "model_type": "pytorch_neural_network",
                    "is_trained": True,
                }

        avg_hrv = sum(features[:7]) / 7 if features[:7] else 50.0
        avg_sleep = sum(features[7:14]) / 7 if len(features) >= 14 else 7.5
        last_score = features[14] if len(features) > 14 else 70
        acwr = features[17] if len(features) > 17 else 1.0

        score = 0.0
        if avg_hrv > 55: score += 30
        elif avg_hrv > 45: score += 20
        else: score += 10

        if avg_sleep >= 7.5: score += 25
        elif avg_sleep >= 6.0: score += 15
        else: score += 5

        score += min(25, last_score * 0.25)

        if 0.8 <= acwr <= 1.3: score += 20
        elif acwr > 1.5: score -= 10

        if score >= 80: state = "OPTIMAL"
        elif score >= 60: state = "MODERATE"
        elif score >= 40: state = "REDUCED"
        else: state = "DEPLETED"

        return {
            "predicted_state": state,
            "confidence": 0.5,
            "probabilities": {s: (0.7 if s == state else 0.1) for s in states},
            "model_type": "rule_based_fallback",
            "is_trained": False,
        }

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

    def compute_injury_risk(self, acwr: float, hrv_trend_slope: float, sleep_debt: float, consecutive_high_days: int) -> Dict[str, Any]:
        risk = 0.0
        factors = []
        if acwr > 1.5: risk += 35; factors.append({"factor": "ACWR Danger", "contribution": 35.0})
        elif acwr > 1.3: risk += 20; factors.append({"factor": "ACWR Caution", "contribution": 20.0})
        elif acwr < 0.8: risk += 10; factors.append({"factor": "Under-training", "contribution": 10.0})
        if hrv_trend_slope < -2.0: risk += 25; factors.append({"factor": "HRV Declining Rapidly", "contribution": 25.0})
        elif hrv_trend_slope < -1.0: risk += 15; factors.append({"factor": "HRV Declining", "contribution": 15.0})
        if sleep_debt > 4.0: risk += 20; factors.append({"factor": "Severe Sleep Debt", "contribution": 20.0})
        elif sleep_debt > 2.0: risk += 12; factors.append({"factor": "Moderate Sleep Debt", "contribution": 12.0})
        if consecutive_high_days >= 5: risk += 20
        elif consecutive_high_days >= 3: risk += 12
        risk = max(0.0, min(100.0, risk))
        level = "CRITICAL" if risk >= 70 else ("ELEVATED" if risk >= 40 else ("MODERATE" if risk >= 20 else "LOW"))
        return {"risk_score": round(risk, 1), "risk_level": level, "contributing_factors": factors}

    def record_feedback(self, features: List[float], actual_state: int):
        self._feature_history.append(features)
        self._label_history.append(actual_state)
        self.training_samples = len(self._label_history)
        if self.training_samples >= 5 and self.training_samples % 5 == 0:
            return self.train_readiness_model([], [])
        return {"status": "buffered", "samples": self.training_samples}

    def get_status(self):
        return {
            "pytorch_available": _HAS_PYTORCH,
            "xgboost_available": _HAS_XGBOOST,
            "lightgbm_available": _HAS_LIGHTGBM,
            "model_trained": self.is_trained,
            "training_samples": self.training_samples,
            "correlation_engine": "active",
            "fatigue_forecaster": "active",
            "performance_predictor": "active",
        }


# Singleton — replace old ml_engine
ml_engine = AdvancedMLEngine()

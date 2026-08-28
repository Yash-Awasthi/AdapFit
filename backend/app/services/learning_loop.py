"""
AdapFit Continuous Learning Feedback Loop
Collects user feedback on predictions and recommendations,
tracks accuracy over time, and triggers model retraining.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field, asdict
import math


@dataclass
class PredictionRecord:
    prediction_id: str
    user_id: str
    prediction_type: str  # "readiness", "workout_rpe", "volume_capacity", "recovery_score"
    predicted_value: Any
    context_features: Dict[str, Any]
    timestamp: str
    actual_value: Optional[Any] = None
    user_feedback: Optional[str] = None  # "accurate", "too_high", "too_low", "way_off"
    feedback_timestamp: Optional[str] = None


@dataclass
class RecommendationRecord:
    rec_id: str
    user_id: str
    recommendation_type: str  # "workout", "rest", "deload", "nutrition"
    recommendation: str
    context: Dict[str, Any]
    timestamp: str
    user_action: Optional[str] = None  # "followed", "modified", "ignored"
    outcome_rating: Optional[int] = None  # 1-5
    feedback_timestamp: Optional[str] = None


class ContinuousLearningLoop:
    """
    Tracks prediction accuracy and recommendation effectiveness.
    Feeds corrections back into ML models for continuous improvement.
    """

    def __init__(self):
        self._predictions: Dict[str, List[PredictionRecord]] = {}  # user_id -> records
        self._recommendations: Dict[str, List[RecommendationRecord]] = {}
        self._accuracy_stats: Dict[str, Dict] = {}  # prediction_type -> stats
        self._feedback_queue: List[Dict] = []  # pending retrain triggers

        # Retrain thresholds
        self.RETRAIN_BATCH_SIZE = 10  # retrain after N new feedbacks
        self.ACCURACY_WINDOW = 50  # compute accuracy over last N predictions

    def record_prediction(
        self, user_id: str, prediction_type: str,
        predicted_value: Any, context_features: Dict[str, Any]
    ) -> str:
        """Record a prediction for later comparison."""
        pred_id = f"pred_{user_id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:16]}"
        record = PredictionRecord(
            prediction_id=pred_id,
            user_id=user_id,
            prediction_type=prediction_type,
            predicted_value=predicted_value,
            context_features=context_features,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        if user_id not in self._predictions:
            self._predictions[user_id] = []
        self._predictions[user_id].append(record)

        return pred_id

    def record_feedback(
        self, prediction_id: str, actual_value: Any, user_feedback: str = "accurate"
    ) -> Dict[str, Any]:
        """Record feedback on a prediction."""
        # Find the prediction
        record = None
        for user_records in self._predictions.values():
            for r in user_records:
                if r.prediction_id == prediction_id:
                    record = r
                    break
            if record:
                break

        if not record:
            return {"status": "not_found"}

        record.actual_value = actual_value
        record.user_feedback = user_feedback
        record.feedback_timestamp = datetime.now(timezone.utc).isoformat()

        # Update accuracy stats
        self._update_accuracy_stats(record)

        # Queue for retrain if needed
        self._feedback_queue.append({
            "type": "prediction_correction",
            "prediction_type": record.prediction_type,
            "predicted": record.predicted_value,
            "actual": actual_value,
            "feedback": user_feedback,
        })

        # Check if retrain is needed
        needs_retrain = len(self._feedback_queue) >= self.RETRAIN_BATCH_SIZE

        return {
            "status": "recorded",
            "prediction_id": prediction_id,
            "accuracy_delta": self._compute_accuracy_delta(record),
            "needs_retrain": needs_retrain,
        }

    def record_recommendation_feedback(
        self, rec_id: str, user_action: str, outcome_rating: Optional[int] = None
    ) -> Dict[str, Any]:
        """Record feedback on a coaching recommendation."""
        record = None
        for user_records in self._recommendations.values():
            for r in user_records:
                if r.rec_id == rec_id:
                    record = r
                    break
            if record:
                break

        if not record:
            return {"status": "not_found"}

        record.user_action = user_action
        record.outcome_rating = outcome_rating
        record.feedback_timestamp = datetime.now(timezone.utc).isoformat()

        return {"status": "recorded", "rec_id": rec_id}

    def get_accuracy_report(self, prediction_type: Optional[str] = None) -> Dict[str, Any]:
        """Get accuracy statistics for predictions."""
        if prediction_type:
            stats = self._accuracy_stats.get(prediction_type, {})
            return {
                "prediction_type": prediction_type,
                "stats": stats,
                "total_feedback": stats.get("total_feedback", 0),
            }

        return {
            "all_types": self._accuracy_stats,
            "total_predictions": sum(
                len(records) for records in self._predictions.values()
            ),
            "total_feedback": sum(
                sum(1 for r in records if r.user_feedback is not None)
                for records in self._predictions.values()
            ),
        }

    def get_calibration_data(self, prediction_type: str) -> Dict[str, Any]:
        """
        Get calibration data: how well do confidence scores
        match actual accuracy?
        """
        all_records = []
        for records in self._predictions.values():
            for r in records:
                if (r.prediction_type == prediction_type
                        and r.user_feedback is not None):
                    all_records.append(r)

        if not all_records:
            return {"buckets": [], "message": "No feedback data yet"}

        # Bucket by predicted value ranges
        buckets = {}
        for r in all_records:
            pred = float(r.predicted_value) if r.predicted_value is not None else 0
            actual = float(r.actual_value) if r.actual_value is not None else 0
            bucket_key = int(pred // 10) * 10  # 0-9, 10-19, etc.

            if bucket_key not in buckets:
                buckets[bucket_key] = {"predicted_sum": 0, "actual_sum": 0, "count": 0}
            buckets[bucket_key]["predicted_sum"] += pred
            buckets[bucket_key]["actual_sum"] += actual
            buckets[bucket_key]["count"] += 1

        calibrated = []
        for bucket_key in sorted(buckets.keys()):
            b = buckets[bucket_key]
            avg_pred = b["predicted_sum"] / b["count"]
            avg_actual = b["actual_sum"] / b["count"]
            calibrated.append({
                "bucket": f"{bucket_key}-{bucket_key+9}",
                "avg_predicted": round(avg_pred, 1),
                "avg_actual": round(avg_actual, 1),
                "count": b["count"],
                "calibration_error": round(abs(avg_pred - avg_actual), 1),
            })

        return {
            "prediction_type": prediction_type,
            "buckets": calibrated,
            "total_samples": len(all_records),
            "mean_calibration_error": round(
                sum(b["calibration_error"] for b in calibrated) / max(len(calibrated), 1), 1
            ),
        }

    def get_retrain_data(self) -> Dict[str, Any]:
        """Get accumulated feedback data ready for model retraining."""
        features = []
        labels = []

        for records in self._predictions.values():
            for r in records:
                if r.actual_value is not None and r.context_features:
                    # Convert context features to feature vector
                    feat_vector = self._features_to_vector(r.context_features)
                    if feat_vector:
                        features.append(feat_vector)
                        labels.append(self._normalize_label(r.prediction_type, r.actual_value))

        return {
            "features": features[-200:],  # Last 200 samples
            "labels": labels[-200:],
            "total_samples": len(features),
            "feedback_queue_size": len(self._feedback_queue),
        }

    def pop_retrain_batch(self) -> List[Dict]:
        """Pop accumulated feedback for retraining. Clears the queue."""
        batch = self._feedback_queue[:self.RETRAIN_BATCH_SIZE]
        self._feedback_queue = self._feedback_queue[self.RETRAIN_BATCH_SIZE:]
        return batch

    def get_user_feedback_summary(self, user_id: str) -> Dict[str, Any]:
        """Get feedback summary for a specific user."""
        records = self._predictions.get(user_id, [])
        total = len(records)
        with_feedback = [r for r in records if r.user_feedback is not None]

        if not with_feedback:
            return {"total_predictions": total, "feedback_count": 0}

        feedback_dist = {}
        for r in with_feedback:
            fb = r.user_feedback or "unknown"
            feedback_dist[fb] = feedback_dist.get(fb, 0) + 1

        accurate_pct = feedback_dist.get("accurate", 0) / max(len(with_feedback), 1) * 100

        return {
            "total_predictions": total,
            "feedback_count": len(with_feedback),
            "feedback_distribution": feedback_dist,
            "accuracy_rate": round(accurate_pct, 1),
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "total_predictions": sum(len(r) for r in self._predictions.values()),
            "total_recommendations": sum(len(r) for r in self._recommendations.values()),
            "feedback_queue_size": len(self._feedback_queue),
            "accuracy_types": list(self._accuracy_stats.keys()),
            "users_tracked": len(self._predictions),
        }

    # --- Internal methods ---

    def _update_accuracy_stats(self, record: PredictionRecord):
        """Update running accuracy statistics."""
        ptype = record.prediction_type
        if ptype not in self._accuracy_stats:
            self._accuracy_stats[ptype] = {
                "total_feedback": 0,
                "accurate": 0,
                "too_high": 0,
                "too_low": 0,
                "way_off": 0,
                "mse_sum": 0.0,
            }

        stats = self._accuracy_stats[ptype]
        stats["total_feedback"] += 1

        fb = record.user_feedback or "accurate"
        if fb in stats:
            stats[fb] += 1

        # Mean squared error
        if record.predicted_value is not None and record.actual_value is not None:
            try:
                diff = float(record.predicted_value) - float(record.actual_value)
                stats["mse_sum"] += diff ** 2
            except (ValueError, TypeError):
                pass

    def _compute_accuracy_delta(self, record: PredictionRecord) -> float:
        """Compute how far off the prediction was."""
        if record.predicted_value is None or record.actual_value is None:
            return 0.0
        try:
            pred = float(record.predicted_value)
            actual = float(record.actual_value)
            return round(pred - actual, 2)
        except (ValueError, TypeError):
            return 0.0

    def _features_to_vector(self, features: Dict[str, Any]) -> Optional[List[float]]:
        """Convert feature dict to numeric vector for ML training."""
        vector = []
        key_order = [
            "recovery_score", "hrv_rmssd", "sleep_hours", "acwr",
            "session_rpe", "session_load", "duration_minutes",
        ]
        for key in key_order:
            val = features.get(key)
            if val is not None:
                try:
                    vector.append(float(val))
                except (ValueError, TypeError):
                    vector.append(0.0)
            else:
                vector.append(0.0)
        return vector if any(v != 0 for v in vector) else None

    def _normalize_label(self, prediction_type: str, actual_value: Any) -> int:
        """Normalize actual values to integer labels for classification."""
        try:
            val = float(actual_value)
        except (ValueError, TypeError):
            return 2  # neutral

        if prediction_type == "readiness":
            # Map to 0-3: DEPLETED, REDUCED, MODERATE, OPTIMAL
            if val >= 85: return 3
            elif val >= 65: return 2
            elif val >= 45: return 1
            else: return 0
        elif prediction_type == "workout_rpe":
            # Map to 0-4: very_low, low, moderate, high, very_high
            if val <= 3: return 0
            elif val <= 5: return 1
            elif val <= 7: return 2
            elif val <= 9: return 3
            else: return 4
        else:
            return int(min(10, max(0, val / 10)))


# Singleton
learning_loop = ContinuousLearningLoop()

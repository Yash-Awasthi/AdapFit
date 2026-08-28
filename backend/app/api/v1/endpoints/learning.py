"""
Continuous Learning Feedback Loop API endpoints.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.services.learning_loop import learning_loop
from app.services.ml_engine import ml_engine

router = APIRouter()


class PredictionRequest(BaseModel):
    user_id: str
    prediction_type: str
    predicted_value: Any
    context_features: Dict[str, Any] = {}


class FeedbackRequest(BaseModel):
    prediction_id: str
    actual_value: Any
    user_feedback: str = Field(default="accurate", pattern="^(accurate|too_high|too_low|way_off)$")


class RecFeedbackRequest(BaseModel):
    rec_id: str
    user_action: str = Field(pattern="^(followed|modified|ignored)$")
    outcome_rating: Optional[int] = Field(default=None, ge=1, le=5)


@router.post("/prediction")
async def record_prediction(req: PredictionRequest):
    pred_id = learning_loop.record_prediction(
        req.user_id, req.prediction_type, req.predicted_value, req.context_features
    )
    return {"prediction_id": pred_id, "status": "recorded"}


@router.post("/feedback")
async def record_feedback(req: FeedbackRequest):
    result = learning_loop.record_feedback(req.prediction_id, req.actual_value, req.user_feedback)
    if result["status"] == "not_found":
        return {"status": "not_found", "message": "Prediction not found"}
    return result


@router.post("/recommendation-feedback")
async def record_rec_feedback(req: RecFeedbackRequest):
    return learning_loop.record_recommendation_feedback(req.rec_id, req.user_action, req.outcome_rating)


@router.get("/accuracy")
async def get_accuracy(prediction_type: Optional[str] = None):
    return learning_loop.get_accuracy_report(prediction_type)


@router.get("/calibration/{prediction_type}")
async def get_calibration(prediction_type: str):
    return learning_loop.get_calibration_data(prediction_type)


@router.get("/retrain-data")
async def get_retrain_data():
    return learning_loop.get_retrain_data()


@router.post("/trigger-retrain")
async def trigger_retrain():
    """Trigger model retraining with accumulated feedback."""
    batch = learning_loop.pop_retrain_batch()
    if not batch:
        return {"status": "no_data", "message": "No feedback data to retrain with"}

    # Extract features and labels from batch
    features = []
    labels = []
    for item in batch:
        feat = learning_loop._features_to_vector(item.get("context_features", {}))
        if feat:
            features.append(feat)
            label = learning_loop._normalize_label(
                item.get("prediction_type", ""),
                item.get("actual", 50)
            )
            labels.append(label)

    if features:
        result = ml_engine.train_readiness_model(features, labels)
        return {"status": "retrained", "batch_size": len(batch), "model_result": result}

    return {"status": "insufficient_features", "batch_size": len(batch)}


@router.get("/user/{user_id}")
async def get_user_feedback_summary(user_id: str):
    return learning_loop.get_user_feedback_summary(user_id)


@router.get("/status")
async def get_learning_status():
    return learning_loop.get_status()

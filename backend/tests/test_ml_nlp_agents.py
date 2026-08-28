"""ML, NLP, vector store, agent, workflow behavior contract."""
import asyncio
import pytest
from app.services.ml_engine import ml_engine
from app.services.nlp_pipeline import nlp_pipeline
from app.services.vector_store import VectorStore
from app.services.agent.supervisor import supervisor_agent
from app.services.agent.evolution_engine import evolution_engine
from app.services.workflow_engine import morning_recovery
from app.services.spark_processor import spark_analytics
from core_engine import (
    compute_hrv_zscore, compute_ewma, compute_acwr,
    detect_anomalies, detect_injury_risk,
)


# --- Core engine math ---

def test_hrv_zscore():
    z, s = compute_hrv_zscore(55.0, 50.0, 10.0)
    assert z == 0.5 and s == 62.5


def test_ewma_bounds():
    r = compute_ewma([100, 200, 150, 180, 160], 5)
    assert len(r) == 5 and 100 <= r[-1] <= 200


def test_anomaly_detection():
    a = detect_anomalies([50, 50, 50, 50, 50, 200, 50], 2.0)
    assert a[5] is True and a[0] is False


def test_injury_risk_extremes():
    assert detect_injury_risk(1.6, -3.0, 5.0, 6) >= 70.0
    assert detect_injury_risk(1.0, 0.0, 0.0, 0) < 20.0


# --- ML engine ---

def test_readiness_prediction():
    f = [50.0] * 7 + [7.5] * 7 + [70, 70, 70] + [1.0, 7.0]
    r = ml_engine.predict_readiness(f)
    assert r["predicted_state"] in ("OPTIMAL", "MODERATE", "REDUCED", "DEPLETED")
    assert 0 <= r["confidence"] <= 1.0


def test_hrv_forecast_trend():
    r = ml_engine.forecast_hrv([45, 48, 50, 52, 55, 58, 60], 7)
    assert r["trend"] == "improving" and len(r["forecast"]) == 7


def test_anomaly_detection_values():
    r = ml_engine.detect_anomalies([70, 72, 68, 71, 69, 30, 73])
    assert r["anomaly_count"] >= 1


def test_injury_risk_score():
    r = ml_engine.compute_injury_risk(1.6, -2.5, 4.0, 5)
    assert r["risk_level"] in ("LOW", "MODERATE", "ELEVATED", "CRITICAL")


def test_online_learning_feedback():
    f = [50.0] * 7 + [7.5] * 7 + [70, 70, 70] + [1.0, 7.0]
    state_before = ml_engine.training_samples
    result = ml_engine.record_feedback(f, 2)  # 2 = MODERATE
    assert "status" in result
    assert ml_engine.training_samples == state_before + 1


# --- NLP pipeline ---

@pytest.mark.parametrize("text,expected", [
    ("Great session, felt amazing!", "positive"),
    ("Terrible workout, pain in shoulder", "negative"),
    ("", "neutral"),
])
def test_sentiment(text, expected):
    assert nlp_pipeline.analyze_sentiment(text)["sentiment"] == expected


def test_pain_detection():
    assert nlp_pipeline.extract_exercise_feedback("Felt pain in my knee")["pain_flagged"] is True


def test_muscle_extraction():
    m = nlp_pipeline.extract_mentioned_muscles("My chest and shoulders are sore")
    assert "chest" in m and "shoulders" in m


def test_goal_parsing():
    r = asyncio.run(nlp_pipeline.parse_goals_from_text("I want to build muscle"))
    assert r["primary_goal"] == "hypertrophy"


# --- Vector store ---

def test_semantic_search():
    store = VectorStore()
    store.initialize([
        {"id": "bench", "name": "Bench Press", "primary_muscles": ["chest"],
         "equipment": "barbell", "category": "strength", "mechanic": "compound",
         "gif_url": "", "axial_loading_rating": 2},
        {"id": "curl", "name": "Bicep Curl", "primary_muscles": ["biceps"],
         "equipment": "dumbbells", "category": "strength", "mechanic": "isolation",
         "gif_url": "", "axial_loading_rating": 1},
    ])
    r = store.semantic_search("chest press", top_k=1)
    assert r[0]["id"] == "bench"


# --- Agent ---

def test_supervisor_optimal():
    r = supervisor_agent.synthesize_recommendation(
        recovery_assessment={"recovery_score": 90, "readiness_state": "OPTIMAL"},
        workout_plan={}, acwr_status={"acwr_status": "SWEET_SPOT"},
        ml_predictions={"is_trained": False})
    assert r["readiness_state"] == "OPTIMAL" and len(r["actions"]) > 0


def test_supervisor_safety_override():
    r = supervisor_agent.resolve_conflict(
        workout_suggestion={}, acwr_warning=True,
        injury_risk={"risk_level": "CRITICAL"})
    assert r["resolution"] == "safety_override"


# --- Evolution engine ---

def test_evolution_record_and_report():
    uid = "test-evo-" + str(id(evolution_engine))
    asyncio.run(evolution_engine.record_workout_accepted(uid, [{"exercise_id": "bench"}]))
    asyncio.run(evolution_engine.record_workout_rejected(uid, [{"exercise_id": "curl"}]))
    report = asyncio.run(evolution_engine.generate_personalization_report(uid))
    assert report["total_interactions"] == 2
    assert report["acceptance_rate"] == 0.5


# --- Workflow ---

def test_morning_recovery():
    r = asyncio.run(morning_recovery("test-wf", {"sleep_duration_hours": 7.5, "hrv_rmssd": 50}))
    assert r["readiness_state"] in ("OPTIMAL", "MODERATE", "REDUCED", "DEPLETED")


# --- Spark baselines ---

def test_rolling_baselines():
    logs = [{"hrv_rmssd": 50 + i, "resting_heart_rate": 65 - i,
             "sleep_duration_hours": 7.5, "recovery_score": 70 + i} for i in range(14)]
    b = spark_analytics.compute_rolling_baselines(logs)
    assert b["hrv_mean_rmssd"] > 0 and b["hrv_std_rmssd"] > 0

"""Check-in to decision to workout: the rules agree with each other and with the app's scales."""
import asyncio
from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.core import workout_metrics
from app.core.repository import RecoveryLogRepository
from app.core.storage import storage
from app.main import app
from app.models.schemas import ReadinessState, SubjectiveCheckin, WearableBiometrics
from app.services import personal_baseline
from app.services.adaptive_workouts import Exercise, UserFitnessProfile, WorkoutPerformance, \
    select_adaptive_workout, suggest_progression
from app.services.daily_decision import Decision, decide, signals_from_logs
from app.services.exercise_service import exercise_service
from app.services.recovery_engine import RecoveryEngine

c = TestClient(app)


def _decision_for(soreness, fatigue, stress, sleep=8.0, hrv=50.0):
    sc = SubjectiveCheckin(soreness=soreness, fatigue=fatigue, stress=stress)
    r = RecoveryEngine.compute_daily_recovery(WearableBiometrics(sleep_duration_hours=sleep, hrv_rmssd=hrv), sc)
    log = {"recovery_score": r.recovery_score, "hrv_z_score": r.metrics_breakdown.hrv_z_score,
           "sleep_duration_hours": sleep, "soreness_score": sc.soreness, "fatigue_score": sc.fatigue}
    return r, decide(signals_from_logs(log, None, None))


def test_a_fresh_user_trains_and_a_wrecked_one_does_not():
    _, fresh = _decision_for(10, 10, 1)
    _, wrecked = _decision_for(1, 1, 10)
    assert fresh.decision == Decision.TRAIN, fresh.reasons
    assert wrecked.decision != Decision.TRAIN
    assert any("soreness" in r.lower() for r in wrecked.reasons)


def test_signals_already_in_the_score_downgrade_at_most_once():
    r, d = _decision_for(5, 5, 5, sleep=5.5, hrv=38)
    assert 30 <= r.recovery_score < 55
    assert d.decision != Decision.REST, d.reasons


def test_readiness_state_uses_the_decision_bands():
    for score, state in ((90, ReadinessState.OPTIMAL), (80, ReadinessState.MODERATE),
                         (70, ReadinessState.REDUCED), (60, ReadinessState.REDUCED),
                         (40, ReadinessState.DEPLETED)):
        assert RecoveryEngine.readiness_for(score) == state


def _checkin(uid, day, **sc):
    return c.post("/api/v1/recovery-logs", json={
        "user_id": uid, "log_date": day,
        "wearable_data": {"hrv_rmssd": 60, "sleep_duration_hours": 8.5, "sleep_efficiency_pct": 92},
        "subjective_checkin": {"soreness": 10, "fatigue": 10, "stress": 1, **sc},
    })


def test_pain_reaches_the_decision_and_the_workout():
    day = "2026-06-01"
    assert _checkin("core-pain", day, pain_flagged=True).status_code == 201
    d = c.get(f"/api/v1/decision/today?user_id=core-pain&day={day}").json()
    assert d["decision"] == "REST" and d["safety_override"] == "pain"
    w = c.post("/api/v1/workouts", json={"user_id": "core-pain", "target_date": day}).json()
    assert w["readiness_state"] == "DEPLETED"


def test_the_workout_follows_the_decision_not_a_second_band():
    day = "2026-06-02"
    _checkin("core-bands", day, soreness=6, fatigue=6, stress=5)
    d = c.get(f"/api/v1/decision/today?user_id=core-bands&day={day}").json()
    w = c.post("/api/v1/workouts", json={"user_id": "core-bands", "target_date": day}).json()
    expected = {"TRAIN": ("OPTIMAL", "MODERATE"), "REDUCE": ("REDUCED",),
                "RECOVER": ("DEPLETED",), "REST": ("DEPLETED",)}[d["decision"]]
    assert w["readiness_state"] in expected


def test_postgres_keeps_the_fields_the_decision_reads():
    for col in ("pain_flagged", "illness_flagged", "resting_hr_delta"):
        assert col in RecoveryLogRepository._COLUMNS


def test_a_second_checkin_the_same_day_replaces_the_first():
    _checkin("core-dup", "2026-06-03")
    _checkin("core-dup", "2026-06-03", soreness=2)
    logs = c.get("/api/v1/recovery-logs?user_id=core-dup").json()["items"]
    assert len(logs) == 1 and logs[0]["soreness_score"] == 2


def test_fallback_routine_is_varied_and_sized():
    short = exercise_service.get_fallback_routine(ReadinessState.MODERATE, target_duration=30, seed="2026-06-01")
    long = exercise_service.get_fallback_routine(ReadinessState.MODERATE, target_duration=75, seed="2026-06-01")
    muscles = [e.target_muscle for e in long["exercises"]]
    assert len(set(muscles)) == len(muscles), muscles
    assert len(long["exercises"]) > len(short["exercises"])
    assert long["target_duration_minutes"] == 75
    other_day = exercise_service.get_fallback_routine(ReadinessState.MODERATE, target_duration=75, seed="2026-06-02")
    assert [e.exercise_id for e in other_day["exercises"]] != [e.exercise_id for e in long["exercises"]]


def test_adaptive_selection_spreads_muscle_groups():
    exs = [Exercise(id=f"c{i}", name=f"Chest {i}", muscle_group="chest", difficulty=5, equipment=[], accessibility=["standing"])
           for i in range(6)] + [Exercise(id=m, name=m, muscle_group=m, difficulty=5, equipment=[], accessibility=[])
                           for m in ("legs", "back")]
    out = select_adaptive_workout(exs, UserFitnessProfile("intermediate", []), [], target_exercises=3)
    assert {e["muscle_group"] for e in out["exercises"]} == {"chest", "legs", "back"}


def test_a_short_sleeper_is_not_measured_against_their_own_deficit():
    logs = [{"sleep_duration_hours": 5.0} for _ in range(28)]
    assert personal_baseline.compute(logs)["sleep_target_hours"] >= 7.0


def test_hrv_domain_matches_the_engine_mapping():
    for day in range(1, 4):
        c.post("/api/v1/recovery-logs", json={"user_id": "core-hrv", "log_date": f"2026-06-0{day}",
                                              "wearable_data": {"hrv_rmssd": 40 + day * 5}})
    today = c.get("/api/v1/recovery-logs/today?user_id=core-hrv&day=2026-06-03").json()
    z = c.get("/api/v1/recovery-logs?user_id=core-hrv").json()["items"][-1]["hrv_z_score"]
    hrv = next(d for d in today["domains"] if d["name"] == "hrv")
    assert hrv["score"] == round(RecoveryEngine.hrv_score_from_z(z))


def test_steady_training_reads_as_steady_from_day_28():
    today = date(2026, 6, 28)
    logs = [{"session_load": 300, "recorded_at": (today - timedelta(days=d)).isoformat()} for d in range(28)]
    assert 0.95 <= workout_metrics.acwr_ratio(logs, today) <= 1.05


def test_progression_follows_its_documented_rules():
    easy = [WorkoutPerformance("x", 3, [10, 10, 10], rpe=5) for _ in range(3)]
    assert suggest_progression(easy, UserFitnessProfile("beginner", []))["recommendation"] == "increase_difficulty"
    hard = [WorkoutPerformance("x", 3, [5, 5, 5], rpe=6)] * 3 + [WorkoutPerformance("x", 3, [5, 5], rpe=9)] * 2
    assert suggest_progression(hard, UserFitnessProfile("beginner", []))["recommendation"] == "decrease_difficulty"
    limited = suggest_progression(easy, UserFitnessProfile("beginner", ["knee"]))
    assert "knee" in limited["suggested_change"]


def test_completing_the_same_workout_twice_logs_its_load_once():
    w = c.post("/api/v1/workouts", json={"user_id": "core-done", "target_date": "2026-06-05"}).json()
    body = {"user_id": "core-done", "actual_duration_minutes": 40, "session_rpe": 7, "logged_exercises": []}
    c.patch(f"/api/v1/workouts/{w['workout_id']}", json=body)
    c.patch(f"/api/v1/workouts/{w['workout_id']}", json=body)
    history = asyncio.run(storage.get_workload_history("core-done", 400))
    assert len(history) == 1


def test_a_sore_body_area_excludes_its_muscles():
    r = exercise_service.get_fallback_routine(ReadinessState.MODERATE, sore_muscles=["legs"], target_duration=75, seed="x")
    legs = {"Quadriceps", "Quads", "Hamstrings", "Glutes", "Calves", "Inner_thighs"}
    assert not legs & {e.target_muscle for e in r["exercises"]}


def test_logged_symptoms_and_vision_strain_are_clamped_and_scored():
    from app.services.chronic_disease_manager import chronic_disease_service
    from app.services.vision_health import vision_health_service as v
    assert chronic_disease_service.log_symptoms("core-cd", "type2_diabetes", ["fatigue"], 14)["severity"] == 10
    v.log_screen_time("core-v", 5, 3, 6)
    v.log_strain("core-v", ["dry eyes"], 0, 2.0)
    assert 0 <= v.get_vision_health_score("core-v")["score"] <= 100


def test_a_session_synced_later_keeps_the_day_it_was_done():
    w = c.post("/api/v1/workouts", json={"user_id": "core-sync", "target_date": "2026-06-01"}).json()
    done_at = "2026-06-01T18:30:00+00:00"
    body = {"user_id": "core-sync", "actual_duration_minutes": 40, "session_rpe": 7, "logged_exercises": [],
            "completed_at": done_at}
    c.patch(f"/api/v1/workouts/{w['workout_id']}", json=body)
    entry = asyncio.run(storage.get_workload_history("core-sync", 400))[-1]
    assert str(entry["recorded_at"])[:10] == "2026-06-01"


def test_a_completion_time_in_the_future_is_not_trusted():
    w = c.post("/api/v1/workouts", json={"user_id": "core-future", "target_date": "2026-06-01"}).json()
    body = {"user_id": "core-future", "actual_duration_minutes": 40, "session_rpe": 7, "logged_exercises": [],
            "completed_at": "2999-01-01T00:00:00+00:00"}
    c.patch(f"/api/v1/workouts/{w['workout_id']}", json=body)
    entry = asyncio.run(storage.get_workload_history("core-future", 400))[-1]
    assert str(entry["recorded_at"])[:4] != "2999"


def _llm_plan(n):
    ex = {"exercise_id": "pushups", "name": "Push-Up", "target_muscle": "Chest", "sets": 4,
          "target_reps": "10", "target_rpe": 7.0, "rest_seconds": 90}
    return {"title": "LLM plan", "adaptation_rationale": "ok", "target_duration_minutes": 120,
            "warmup": [], "exercises": [dict(ex, exercise_id=f"e{i}") for i in range(n)], "cooldown": []}


def test_an_llm_plan_is_fitted_to_the_requested_time(monkeypatch):
    from app.services import recommendation_engine as re_mod
    monkeypatch.setattr(re_mod.settings, "GEMINI_API_KEY", "test")
    monkeypatch.setattr(re_mod, "ai_call_allowed", lambda *a, **k: True)

    async def fake(cls, **kw):
        return _llm_plan(12)
    monkeypatch.setattr(re_mod.RecommendationEngine, "_generate_via_gemini", classmethod(fake))
    w = asyncio.run(re_mod.recommendation_engine.generate_workout(
        "core-llm", "2026-06-01", ReadinessState.MODERATE, 80, target_duration=30))
    assert w.target_duration_minutes == 30
    assert 1 <= len(w.exercises) < 12


def test_a_depleted_day_never_asks_the_llm(monkeypatch):
    from app.services import recommendation_engine as re_mod
    monkeypatch.setattr(re_mod.settings, "GEMINI_API_KEY", "test")
    monkeypatch.setattr(re_mod, "ai_call_allowed", lambda *a, **k: True)

    calls = []

    async def fake(cls, **kw):
        calls.append(kw)
        return _llm_plan(6)
    monkeypatch.setattr(re_mod.RecommendationEngine, "_generate_via_gemini", classmethod(fake))
    w = asyncio.run(re_mod.recommendation_engine.generate_workout(
        "core-llm2", "2026-06-01", ReadinessState.DEPLETED, 20, target_duration=45))
    assert not calls and w.exercises[0].exercise_id == "world-greatest-stretch"


def test_an_offline_completion_replayed_by_sync_keeps_its_day():
    from app.core.per_user import CURRENT_USER
    w = c.post("/api/v1/workouts", json={"user_id": "core-replay", "target_date": "2026-06-02"}).json()
    token = CURRENT_USER.set("core-replay")
    try:
        from app.api.v1.endpoints.tasks import BatchSyncRequest, batch_sync
        asyncio.run(batch_sync(BatchSyncRequest(mutations=[{
            "id": "q1", "table_name": "workouts", "record_id": w["workout_id"], "operation": "update",
            "payload": {"actual_duration_minutes": 30, "session_rpe": 6, "logged_exercises": [],
                        "completed_at": "2026-06-02T07:00:00Z"}}])))
    finally:
        CURRENT_USER.reset(token)
    entry = asyncio.run(storage.get_workload_history("core-replay", 400))[-1]
    assert str(entry["recorded_at"])[:10] == "2026-06-02"


def test_natural_language_log_reads_weight_then_reps():
    from app.services.nl_workout_logger import nl_workout_logger
    one = nl_workout_logger.parse("did bench press 80kg for 12 reps")["exercises"]
    assert [(e["sets"], e["reps"], e["weight_kg"]) for e in one] == [(1, 12, 80.0)]
    two = nl_workout_logger.parse("squats 100 kg 8 reps then deadlift 140kg 5 reps")["exercises"]
    assert sorted((e["reps"], e["weight_kg"]) for e in two) == [(5, 140.0), (8, 100.0)]
    assert not any(e["name"].lower().startswith("then") for e in two)


def test_condition_summary_reports_what_it_measures():
    from app.services.chronic_disease_manager import chronic_disease_service as cd
    cd.register_condition("core-sum", "hypertension", "2020-01-01")
    cd.log_symptoms("core-sum", "hypertension", ["fatigue"], 6)
    cd.log_symptoms("core-sum", "hypertension", ["thirst"], 4)
    s = cd.get_condition_summary("core-sum", "hypertension")
    assert s["avg_recent_symptom_severity"] == 5.0 and "medication_adherence" in s


def test_meal_plan_scales_portions_to_the_calorie_target():
    from app.services.recipe_generator import recipe_generator_service as rg
    plan = rg.generate_meal_plan(target_calories=2400, days=3)
    assert abs(plan["avg_daily_calories"] - 2400) <= 2400 * 0.2

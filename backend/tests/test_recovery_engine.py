"""Recovery engine behavior contract."""
from app.services.recovery_engine import RecoveryEngine
from app.models.schemas import WearableBiometrics, SubjectiveCheckin, ReadinessState, ACWRStatus


def test_hrv_zscore():
    z, s = RecoveryEngine.calculate_hrv_z_score(60.0, 50.0, 10.0)
    assert z == 1.0 and s == 75.0
    z, s = RecoveryEngine.calculate_hrv_z_score(None)
    assert z is None and s == 70.0


def test_sleep_score():
    assert RecoveryEngine.calculate_sleep_score(8.0, 90.0, 8.0) == 97.0
    assert RecoveryEngine.calculate_sleep_score(4.0, target_hours=8.0) == 50.0


def test_subjective_score():
    good = RecoveryEngine.calculate_subjective_score(
        SubjectiveCheckin(soreness=10, fatigue=10, stress=1))
    bad = RecoveryEngine.calculate_subjective_score(
        SubjectiveCheckin(soreness=2, fatigue=2, stress=9, sore_muscle_groups=["chest", "quads", "back"]))
    assert good == 100.0 and bad < 40.0


def test_acwr():
    v, s, p = RecoveryEngine.evaluate_acwr(500.0, 500.0)
    assert v == 1.0 and s == ACWRStatus.SWEET_SPOT and p == 0.0
    v, s, p = RecoveryEngine.evaluate_acwr(800.0, 500.0)
    assert s == ACWRStatus.DANGER_ZONE and p == -15.0


def test_composite_optimal():
    r = RecoveryEngine.compute_daily_recovery(
        WearableBiometrics(sleep_duration_hours=8.5, sleep_efficiency_pct=92, hrv_rmssd=65),
        SubjectiveCheckin(soreness=9, fatigue=9, stress=2),
        acute_load=450, chronic_load=500)
    assert r.recovery_score >= 85 and r.readiness_state == ReadinessState.OPTIMAL


def test_composite_depleted():
    r = RecoveryEngine.compute_daily_recovery(
        WearableBiometrics(sleep_duration_hours=4, sleep_efficiency_pct=60, hrv_rmssd=25),
        SubjectiveCheckin(soreness=2, fatigue=2, stress=9, sore_muscle_groups=["chest", "quads"]),
        acute_load=850, chronic_load=500)
    assert r.recovery_score < 45 and r.readiness_state == ReadinessState.DEPLETED
    assert "ALERT" in r.recommendation_directive

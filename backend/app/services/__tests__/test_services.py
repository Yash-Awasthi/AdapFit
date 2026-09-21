"""Unit tests for the workout plan generator, HRV recovery scorer and nutrition analyzer."""

from datetime import datetime, timedelta


def _profile(goal, *, experience=5, sessions=4, minutes=60):
    from app.services.workout_plan_generator import Equipment, UserProfile

    return UserProfile(
        experience_level=experience,
        age=30,
        weight_kg=80.0,
        height_cm=180.0,
        injuries=[],
        available_equipment=[Equipment.BARBELL, Equipment.DUMBBELLS, Equipment.BODYWEIGHT],
        max_sessions_per_week=sessions,
        max_minutes_per_session=minutes,
        training_goal=goal,
        current_1rm={},
    )


class TestWorkoutPlanGenerator:
    def test_import(self):
        from app.services.workout_plan_generator import WorkoutPlanGenerator

        assert WorkoutPlanGenerator is not None

    def test_every_muscle_group_in_the_exercise_db_is_a_real_enum_member(self):
        from app.services.workout_plan_generator import EXERCISE_DB, MuscleGroup

        known = {m.value for m in MuscleGroup}
        assert set(EXERCISE_DB) <= known

    def test_generate_plan_returns_a_plan(self):
        from app.services.workout_plan_generator import TrainingGoal, TrainingPlan, WorkoutPlanGenerator

        plan = WorkoutPlanGenerator().generate_plan(_profile(TrainingGoal.STRENGTH))
        assert isinstance(plan, TrainingPlan)
        assert plan.goal is TrainingGoal.STRENGTH
        assert plan.duration_weeks > 0

    def test_plan_has_one_week_entry_per_week(self):
        from app.services.workout_plan_generator import TrainingGoal, WorkoutPlanGenerator

        plan = WorkoutPlanGenerator().generate_plan(
            _profile(TrainingGoal.ENDURANCE, experience=2, sessions=3, minutes=45), weeks=8
        )
        assert plan.duration_weeks == 8
        assert len(plan.weeks) == 8

    def test_deload_weeks_are_scheduled(self):
        from app.services.workout_plan_generator import TrainingGoal, WorkoutPlanGenerator

        plan = WorkoutPlanGenerator().generate_plan(
            _profile(TrainingGoal.HYPERTROPHY, experience=9, sessions=5, minutes=75), weeks=12
        )
        assert any(week.phase == "deload" for week in plan.weeks)

    def test_sessions_respect_the_session_cap(self):
        from app.services.workout_plan_generator import TrainingGoal, WorkoutPlanGenerator

        plan = WorkoutPlanGenerator().generate_plan(_profile(TrainingGoal.STRENGTH, sessions=3), weeks=4)
        assert all(len(week.sessions) <= 3 for week in plan.weeks)


def _hrv(scorer, days_ago: int, rmssd: float, resting_hr: float):
    from app.services.hrv_recovery_scorer import HRVMetrics

    scorer.add_hrv(
        HRVMetrics(
            timestamp=datetime.now() - timedelta(days=days_ago),
            duration_seconds=300,
            rmssd=rmssd,
            sdnn=rmssd * 1.2,
            lf_power=800.0,
            hf_power=700.0,
            lf_hf_ratio=1.14,
            resting_hr=resting_hr,
            hrv_score=50.0,
        )
    )


def _sleep(scorer, date: str, hours: float, score: float):
    from app.services.hrv_recovery_scorer import SleepData

    total = int(hours * 60)
    scorer.add_sleep(
        SleepData(
            date=date,
            total_minutes=total,
            deep_minutes=int(total * 0.2),
            rem_minutes=int(total * 0.22),
            light_minutes=int(total * 0.5),
            awake_minutes=int(total * 0.08),
            sleep_score=score,
            interruptions=1,
        )
    )


def _loaded_scorer(rmssd: float, resting_hr: float, sleep_hours: float, sleep_score: float):
    """A scorer with 14 days of history, so baselines and trends are populated."""
    from app.services.hrv_recovery_scorer import HRVRecoveryScorer

    scorer = HRVRecoveryScorer()
    today = datetime.now()
    for day in range(14, 0, -1):
        _hrv(scorer, day, rmssd, resting_hr)
        _sleep(scorer, (today - timedelta(days=day)).strftime("%Y-%m-%d"), sleep_hours, sleep_score)
    _hrv(scorer, 0, rmssd, resting_hr)
    _sleep(scorer, today.strftime("%Y-%m-%d"), sleep_hours, sleep_score)
    return scorer, today.strftime("%Y-%m-%d")


class TestHRVRecoveryScorer:
    def test_import(self):
        from app.services.hrv_recovery_scorer import HRVRecoveryScorer

        assert HRVRecoveryScorer is not None

    def test_calculate_recovery_is_in_range(self):
        scorer, today = _loaded_scorer(rmssd=50, resting_hr=60, sleep_hours=7.5, sleep_score=75)
        report = scorer.calculate_recovery(today)
        assert 0 <= report.recovery_score <= 100

    def test_good_signals_score_above_poor_signals(self):
        good, today = _loaded_scorer(rmssd=80, resting_hr=55, sleep_hours=8, sleep_score=90)
        poor, _ = _loaded_scorer(rmssd=20, resting_hr=75, sleep_hours=5, sleep_score=35)
        assert good.calculate_recovery(today).recovery_score > poor.calculate_recovery(today).recovery_score

    def test_readiness_matches_the_score_band(self):
        from app.services.hrv_recovery_scorer import ReadinessLevel

        scorer, today = _loaded_scorer(rmssd=65, resting_hr=58, sleep_hours=7, sleep_score=80)
        report = scorer.calculate_recovery(today)
        bands = [(75, ReadinessLevel.EXCELLENT), (50, ReadinessLevel.GOOD), (30, ReadinessLevel.FAIR)]
        expected = next((level for cut, level in bands if report.recovery_score >= cut), ReadinessLevel.POOR)
        assert report.readiness is expected

    def test_empty_history_still_produces_a_report(self):
        from app.services.hrv_recovery_scorer import HRVRecoveryScorer

        report = HRVRecoveryScorer().calculate_recovery(datetime.now().strftime("%Y-%m-%d"))
        assert 0 <= report.recovery_score <= 100


class TestNutritionAnalyzer:
    def test_import(self):
        from app.services.nutrition_analyzer import NutritionAnalyzer

        assert NutritionAnalyzer is not None

    def test_targets_return_positive_macros(self):
        from app.services.nutrition_analyzer import DietaryGoal, NutritionAnalyzer

        targets = NutritionAnalyzer().calculate_targets(
            weight_kg=80, height_cm=180, age=30, sex="male", goal=DietaryGoal.MUSCLE_GAIN
        )
        assert targets.calories > 0
        assert targets.protein_g > 0
        assert targets.carbs_g > 0
        assert targets.fat_g > 0

    def test_muscle_gain_targets_more_calories_than_fat_loss(self):
        from app.services.nutrition_analyzer import DietaryGoal, NutritionAnalyzer

        analyzer = NutritionAnalyzer()
        common = dict(weight_kg=80, height_cm=180, age=30, sex="male")
        gain = analyzer.calculate_targets(goal=DietaryGoal.MUSCLE_GAIN, **common)
        cut = analyzer.calculate_targets(goal=DietaryGoal.FAT_LOSS, **common)
        assert gain.calories > cut.calories

    def test_macro_calories_reconcile_with_the_target(self):
        from app.services.nutrition_analyzer import DietaryGoal, NutritionAnalyzer

        targets = NutritionAnalyzer().calculate_targets(
            weight_kg=70, height_cm=170, age=28, sex="female", goal=DietaryGoal.MAINTENANCE
        )
        from_macros = targets.protein_g * 4 + targets.carbs_g * 4 + targets.fat_g * 9
        assert abs(from_macros - targets.calories) / targets.calories < 0.05

"""Exercise service behavior contract."""
from app.services.exercise_service import exercise_service
from app.models.schemas import ReadinessState


def test_catalog_loads():
    assert len(exercise_service.get_all()) >= 20
    assert exercise_service.get_by_id("barbell-bench-press") is not None


def test_equipment_and_muscle_filter():
    results = exercise_service.filter_exercises(equipment_list=["dumbbells"], exclude_muscles=["chest"])
    for ex in results:
        assert "dumbbells" in ex.equipment or "bodyweight" in ex.equipment
        assert "chest" not in [m.lower() for m in ex.primary_muscles]


def test_axial_load_filter():
    for ex in exercise_service.filter_exercises(max_axial_load=1):
        assert ex.axial_loading_rating <= 1


def test_fallback_depleted():
    r = exercise_service.get_fallback_routine(ReadinessState.DEPLETED)
    assert "Recovery" in r["title"]
    assert len(r["exercises"]) > 0


def test_fallback_optimal():
    r = exercise_service.get_fallback_routine(ReadinessState.OPTIMAL)
    assert "Optimal" in r["title"]
    assert r["target_duration_minutes"] == 45

"""Tests for nutrition validator service."""

import pytest
from app.services.nutrition_validator import (
    IngredientData,
    ValidationResult,
    validate_ingredient,
    compute_energy_from_macros,
    calculate_macro_breakdown,
    calculate_nutrition_score,
    calculate_completeness,
    scale_to_serving,
)


@pytest.fixture
def apple():
    return IngredientData(
        name="Apple",
        energy=52,
        protein=0.3,
        carbohydrates=14,
        carbohydrates_sugar=10,
        fat=0.2,
        fat_saturated=0.1,
        fiber=2.4,
        sodium=0.001,
    )


class TestValidation:
    def test_valid_ingredient(self, apple):
        result = validate_ingredient(apple)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_empty_name(self):
        ing = IngredientData(name="", energy=100, protein=10, carbohydrates=20, fat=5)
        result = validate_ingredient(ing)
        assert not result.is_valid
        assert any("Name is empty" in e for e in result.errors)

    def test_negative_energy(self):
        ing = IngredientData(name="Test", energy=-10, protein=10, carbohydrates=20, fat=5)
        result = validate_ingredient(ing)
        assert not result.is_valid

    def test_macro_over_100(self):
        ing = IngredientData(name="Test", energy=100, protein=110, carbohydrates=20, fat=5)
        result = validate_ingredient(ing)
        assert not result.is_valid
        assert any("exceeds 100g" in e for e in result.errors)

    def test_saturated_fat_exceeds_total(self):
        ing = IngredientData(name="Test", energy=100, protein=10, carbohydrates=20, fat=5, fat_saturated=10)
        result = validate_ingredient(ing)
        assert not result.is_valid

    def test_sugar_exceeds_carbs(self):
        ing = IngredientData(name="Test", energy=100, protein=10, carbohydrates=5, fat=5, carbohydrates_sugar=10)
        result = validate_ingredient(ing)
        assert not result.is_valid

    def test_invalid_nutriscore(self):
        ing = IngredientData(name="Test", energy=100, protein=10, carbohydrates=20, fat=5, nutriscore="x")
        result = validate_ingredient(ing)
        assert not result.is_valid

    def test_total_macros_exceed_105(self):
        ing = IngredientData(name="Test", energy=100, protein=40, carbohydrates=40, fat=30)
        result = validate_ingredient(ing)
        assert not result.is_valid


class TestEnergyCalculation:
    def test_compute_energy(self, apple):
        energy = compute_energy_from_macros(apple)
        assert energy > 0

    def test_energy_formula(self):
        ing = IngredientData(name="Test", energy=100, protein=10, carbohydrates=20, fat=10)
        energy = compute_energy_from_macros(ing)
        expected = 10 * 4 + 20 * 4 + 10 * 9  # 40 + 80 + 90 = 210
        assert energy == pytest.approx(expected, abs=1)


class TestMacroBreakdown:
    def test_breakdown(self, apple):
        breakdown = calculate_macro_breakdown(apple)
        assert breakdown.protein_pct + breakdown.carbohydrate_pct + breakdown.fat_pct == pytest.approx(100, abs=1)
        assert breakdown.total_kcal > 0


class TestScoring:
    def test_nutrition_score(self, apple):
        score = calculate_nutrition_score(apple)
        assert 0 <= score <= 100

    def test_completeness(self, apple):
        completeness = calculate_completeness(apple)
        assert 0 <= completeness <= 1


class TestServingScale:
    def test_scale(self, apple):
        scaled = scale_to_serving(apple, 150)
        assert scaled["serving_grams"] == 150
        assert scaled["energy"] == pytest.approx(apple.energy * 1.5, abs=1)
        assert scaled["protein"] == pytest.approx(apple.protein * 1.5, abs=0.1)

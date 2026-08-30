"""Tests for protein recommender service."""

import pytest
from app.services.protein_recommender import (
    calculate_protein_needs,
    calculate_protein_from_lbs,
    distribute_protein_timing,
    adjust_for_goal,
    validate_activity_level,
    validate_body_weight,
)


class TestProteinCalculation:
    def test_moderate_activity(self):
        rec = calculate_protein_needs(70, "moderate")
        assert rec.daily_grams == pytest.approx(84, abs=1)
        assert rec.per_kg_bodyweight == 1.2

    def test_strength_training(self):
        rec = calculate_protein_needs(80, "resistance/strength training")
        assert rec.daily_grams == pytest.approx(128, abs=1)

    def test_endurance(self):
        rec = calculate_protein_needs(75, "endurance training")
        assert rec.daily_grams == pytest.approx(105, abs=1)

    def test_from_lbs(self):
        rec = calculate_protein_from_lbs(154, "moderate")
        assert rec.daily_grams > 0


class TestTiming:
    def test_distribute(self):
        timings = distribute_protein_timing(120, 4)
        assert len(timings) == 4
        total = sum(t.grams for t in timings)
        assert total == pytest.approx(120, abs=1)


class TestGoalAdjustment:
    def test_muscle_gain(self):
        base = calculate_protein_needs(70, "moderate")
        adjusted = adjust_for_goal(base, "muscle_gain")
        assert adjusted.daily_grams > base.daily_grams

    def test_fat_loss(self):
        base = calculate_protein_needs(70, "moderate")
        adjusted = adjust_for_goal(base, "fat_loss")
        assert adjusted.daily_grams > base.daily_grams

    def test_maintenance(self):
        base = calculate_protein_needs(70, "moderate")
        adjusted = adjust_for_goal(base, "maintenance")
        assert adjusted.daily_grams == base.daily_grams


class TestValidation:
    def test_valid_activity(self):
        valid, msg = validate_activity_level("moderate")
        assert valid

    def test_invalid_activity(self):
        valid, msg = validate_activity_level("xyz")
        assert not valid
        assert "Invalid" in msg

    def test_valid_weight(self):
        valid, msg = validate_body_weight(70)
        assert valid

    def test_invalid_weight(self):
        valid, msg = validate_body_weight(-10)
        assert not valid

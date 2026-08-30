"""Tests for Cycling Analysis."""
import pytest
from app.services.cycling_analysis import (
    categorise_climb,
    detect_climbs,
    compute_elevation_profile,
    estimate_power_required,
    estimate_vam,
    classify_ride_type,
    estimate_calories_climbing,
    ClimbSegment,
)


class TestCategoriseClimb:
    def test_hc(self):
        cat, pts, idx = categorise_climb(10.0, 8.5)
        assert cat == "HC"
        assert pts == 20

    def test_cat1(self):
        cat, pts, idx = categorise_climb(8.0, 6.0)
        assert cat == "Cat 1"
        assert pts == 10

    def test_cat2(self):
        cat, pts, idx = categorise_climb(5.0, 4.0)
        assert cat == "Cat 2"
        assert pts == 5

    def test_cat3(self):
        cat, pts, idx = categorise_climb(3.0, 3.0)
        assert cat == "Cat 3"
        assert pts == 2

    def test_cat4(self):
        cat, pts, idx = categorise_climb(1.0, 3.0)
        assert cat == "Cat 4"
        assert pts == 1

    def test_uncategorised(self):
        cat, pts, idx = categorise_climb(0.5, 1.0)
        assert cat == "uncategorised"
        assert pts == 0

    def test_benchmark(self):
        # 1.45km at 9% = index 13.05 → Cat 3
        cat, pts, idx = categorise_climb(1.45, 9.0)
        assert cat == "Cat 3"
        assert idx == pytest.approx(13.05)


class TestDetectClimbs:
    def test_simple_climb(self):
        # Create data with a climb
        d = [i * 0.1 for i in range(100)]  # 0-10 km
        # Flat then climb then flat
        e = [100.0] * 30 + [100 + i * 10 for i in range(40)] + [500.0] * 30
        climbs = detect_climbs(d, e, min_gradient_pct=3.0, min_length_m=200)
        assert len(climbs) >= 1
        assert climbs[0].elevation_gain_m > 0

    def test_no_climbs(self):
        d = [i * 0.1 for i in range(100)]
        e = [100.0] * 100  # flat
        climbs = detect_climbs(d, e)
        assert len(climbs) == 0

    def test_empty_data(self):
        assert detect_climbs([], []) == []


class TestElevationProfile:
    def test_basic(self):
        d = [0.0, 1.0, 2.0, 3.0]
        e = [100.0, 200.0, 300.0, 400.0]
        profile = compute_elevation_profile(d, e)
        assert profile.total_distance_km == 3.0
        assert profile.total_elevation_gain_m == 300.0
        assert profile.max_elevation_m == 400.0
        assert profile.min_elevation_m == 100.0

    def test_empty(self):
        profile = compute_elevation_profile([], [])
        assert profile.total_distance_km == 0.0


class TestPowerRequired:
    def test_flat_ride(self):
        power = estimate_power_required(75.0, 8.0, 0.0, 30.0)
        assert power > 0
        assert power < 200  # flat at 30km/h

    def test_uphill(self):
        power_flat = estimate_power_required(75.0, 8.0, 0.0, 20.0)
        power_hill = estimate_power_required(75.0, 8.0, 8.0, 10.0)
        assert power_hill > power_flat  # uphill needs more power

    def test_zero_speed(self):
        assert estimate_power_required(75.0, 8.0, 5.0, 0.0) == 0.0


class TestVAM:
    def test_basic(self):
        vam = estimate_vam(1000.0, 1.0)
        assert vam == 1000.0

    def test_zero_time(self):
        assert estimate_vam(1000.0, 0.0) == 0.0


class TestRideClassification:
    def test_mountain(self):
        result = classify_ride_type(80.0, 8000.0, 15.0)
        assert result["type"] == "mountain"

    def test_flat(self):
        result = classify_ride_type(30.0, 50.0, 3.0)
        assert result["type"] == "flat"

    def test_endurance(self):
        result = classify_ride_type(120.0, 500.0, 5.0)
        assert result["type"] == "endurance"

    def test_hilly(self):
        result = classify_ride_type(50.0, 3000.0, 8.0)
        assert result["type"] == "hilly"


class TestCalories:
    def test_basic(self):
        cal = estimate_calories_climbing(83.0, 1000.0, 50.0, 2.0)
        assert cal > 0

    def test_zero_duration(self):
        assert estimate_calories_climbing(83.0, 1000.0, 50.0, 0.0) == 0.0

"""Tests for Biomarker Tracker."""
import pytest
from app.services.biomarker_tracker import (
    parse_reference_range,
    classify_value,
    compute_deviation_pct,
    detect_trend,
    analyze_biomarker,
    analyze_panel,
    track_longitudinal_changes,
    generate_clinical_summary,
    Biomarker,
    REFERENCE_RANGES,
)


class TestParseReferenceRange:
    def test_normal_range(self):
        low, high = parse_reference_range("70-100")
        assert low == 70.0
        assert high == 100.0

    def test_with_spaces(self):
        low, high = parse_reference_range("  70 - 100  ")
        assert low == 70.0
        assert high == 100.0

    def test_greater_than(self):
        low, high = parse_reference_range(">60")
        assert low == 60.0
        assert high is None

    def test_less_than(self):
        low, high = parse_reference_range("<4.0")
        assert low is None
        assert high == 4.0

    def test_empty(self):
        low, high = parse_reference_range("")
        assert low is None
        assert high is None

    def test_en_dash(self):
        low, high = parse_reference_range("70–100")
        assert low == 70.0
        assert high == 100.0


class TestClassifyValue:
    def test_normal(self):
        assert classify_value(85, 70, 100) == "normal"

    def test_low(self):
        assert classify_value(65, 70, 100) == "low"

    def test_high(self):
        assert classify_value(105, 70, 100) == "high"

    def test_critical_low(self):
        assert classify_value(40, 70, 100) == "critical_low"

    def test_critical_high(self):
        assert classify_value(150, 70, 100) == "critical_high"

    def test_no_range(self):
        assert classify_value(50) == "unknown"

    def test_min_only(self):
        assert classify_value(50, ref_min=60) == "low"
        assert classify_value(70, ref_min=60) == "normal"

    def test_max_only(self):
        assert classify_value(50, ref_max=60) == "normal"
        assert classify_value(70, ref_max=60) == "high"


class TestDeviationPct:
    def test_at_midpoint(self):
        assert compute_deviation_pct(85, 70, 100) == 0.0

    def test_above(self):
        dev = compute_deviation_pct(95, 70, 100)
        assert dev > 0

    def test_below(self):
        dev = compute_deviation_pct(75, 70, 100)
        assert dev < 0

    def test_no_range(self):
        assert compute_deviation_pct(50) == 0.0


class TestDetectTrend:
    def test_rising(self):
        values = [10, 12, 14, 16, 18, 20]
        direction, slope = detect_trend(values)
        assert direction == "rising"
        assert slope > 0

    def test_falling(self):
        values = [20, 18, 16, 14, 12, 10]
        direction, slope = detect_trend(values)
        assert direction == "falling"
        assert slope < 0

    def test_stable(self):
        values = [10, 10, 10, 10, 10]
        direction, slope = detect_trend(values)
        assert direction == "stable"

    def test_insufficient(self):
        direction, slope = detect_trend([10])
        assert direction == "insufficient_data"


class TestAnalyzeBiomarker:
    def test_normal(self):
        marker = Biomarker(
            name="Glucose",
            ref_range_min=70,
            ref_range_max=100,
            history=[("2024-01-01", 85), ("2024-02-01", 88), ("2024-03-01", 90)],
        )
        analysis = analyze_biomarker(marker)
        assert analysis.name == "Glucose"
        assert analysis.latest_value == 90
        assert analysis.status == "normal"
        assert analysis.data_points == 3

    def test_empty_history(self):
        marker = Biomarker(name="Glucose")
        analysis = analyze_biomarker(marker)
        assert analysis.latest_value is None

    def test_abnormal(self):
        marker = Biomarker(
            name="Glucose",
            ref_range_min=70,
            ref_range_max=100,
            history=[("2024-01-01", 110)],
        )
        analysis = analyze_biomarker(marker)
        assert analysis.status == "high"


class TestAnalyzePanel:
    def test_basic(self):
        markers = [
            Biomarker("Glucose", ref_range_min=70, ref_range_max=100, history=[("2024-01", 85)]),
            Biomarker("Cholesterol", ref_range_min=0, ref_range_max=200, history=[("2024-01", 180)]),
        ]
        result = analyze_panel(markers)
        assert result["total_markers"] == 2
        assert result["normal_count"] == 2
        assert result["health_score"] == 100.0

    def test_with_abnormal(self):
        markers = [
            Biomarker("Glucose", ref_range_min=70, ref_range_max=100, history=[("2024-01", 110)]),
            Biomarker("Cholesterol", ref_range_min=0, ref_range_max=200, history=[("2024-01", 85)]),
        ]
        result = analyze_panel(markers)
        assert result["abnormal_count"] == 1
        assert result["health_score"] < 100.0


class TestLongitudinalChanges:
    def test_significant_change(self):
        markers = [
            Biomarker("Glucose", history=[
                ("2024-01", 80), ("2024-02", 85), ("2024-03", 95),
                ("2024-04", 110), ("2024-05", 120),
            ]),
        ]
        changes = track_longitudinal_changes(markers)
        assert len(changes) >= 1
        assert changes[0]["name"] == "Glucose"
        assert abs(changes[0]["pct_change"]) > 10

    def test_no_significant(self):
        markers = [
            Biomarker("Glucose", history=[
                ("2024-01", 85), ("2024-02", 86), ("2024-03", 85),
            ]),
        ]
        changes = track_longitudinal_changes(markers)
        assert len(changes) == 0


class TestClinicalSummary:
    def test_all_normal(self):
        analyses = [
            type("A", (), {"status": "normal", "name": "Glucose", "latest_value": 85, "trend": "stable", "trend_slope": 0})(),
        ]
        summary = generate_clinical_summary(analyses)
        assert "normal" in summary.lower()

    def test_with_critical(self):
        analyses = [
            type("A", (), {"status": "critical_high", "name": "Glucose", "latest_value": 150, "trend": "rising", "trend_slope": 2.0})(),
        ]
        summary = generate_clinical_summary(analyses)
        assert "CRITICAL" in summary

    def test_empty(self):
        assert generate_clinical_summary([]) == "No biomarker data available."


class TestReferenceRanges:
    def test_all_have_ranges(self):
        for name, (low, high, unit) in REFERENCE_RANGES.items():
            assert low < high
            assert len(unit) > 0

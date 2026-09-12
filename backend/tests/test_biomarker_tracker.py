"""Tests for Biomarker Tracker — matches actual service API."""
import pytest
from datetime import datetime
from app.services.biomarker_tracker import (
    BiomarkerStatus,
    ReferenceRange,
    BiomarkerReading,
    BiomarkerTrend,
    classify_biomarker,
    status_severity,
    analyze_trend,
    convert_unit,
    generate_biomarker_dashboard,
    COMMON_REFERENCE_RANGES,
)


class TestClassifyBiomarker:
    def test_normal(self):
        ref = ReferenceRange(low=70, high=100, unit="mg/dL")
        assert classify_biomarker(85, ref) == BiomarkerStatus.NORMAL

    def test_low(self):
        ref = ReferenceRange(low=70, high=100, unit="mg/dL")
        assert classify_biomarker(60, ref) == BiomarkerStatus.LOW

    def test_high(self):
        ref = ReferenceRange(low=70, high=100, unit="mg/dL")
        assert classify_biomarker(110, ref) == BiomarkerStatus.HIGH

    def test_critical_low(self):
        ref = ReferenceRange(low=70, high=100, unit="mg/dL", critical_low=50)
        assert classify_biomarker(45, ref) == BiomarkerStatus.CRITICAL_LOW

    def test_critical_high(self):
        ref = ReferenceRange(low=70, high=100, unit="mg/dL", critical_high=150)
        assert classify_biomarker(160, ref) == BiomarkerStatus.CRITICAL_HIGH

    def test_boundary_low(self):
        ref = ReferenceRange(low=70, high=100, unit="mg/dL")
        assert classify_biomarker(70, ref) == BiomarkerStatus.NORMAL

    def test_boundary_high(self):
        ref = ReferenceRange(low=70, high=100, unit="mg/dL")
        assert classify_biomarker(100, ref) == BiomarkerStatus.NORMAL


class TestStatusSeverity:
    def test_normal(self):
        assert status_severity(BiomarkerStatus.NORMAL) == 0

    def test_low(self):
        assert status_severity(BiomarkerStatus.LOW) == 1

    def test_high(self):
        assert status_severity(BiomarkerStatus.HIGH) == 1

    def test_critical_low(self):
        assert status_severity(BiomarkerStatus.CRITICAL_LOW) == 4

    def test_critical_high(self):
        assert status_severity(BiomarkerStatus.CRITICAL_HIGH) == 4


class TestAnalyzeTrend:
    def _make_reading(self, name, value, day):
        return BiomarkerReading(name=name, value=value, unit="mg/dL",
                                timestamp=datetime(2024, 1, day))

    def test_rising_trend(self):
        readings = [self._make_reading("glucose", v, d)
                    for d, v in enumerate([80, 85, 95, 110, 120], 1)]
        ref = ReferenceRange(low=70, high=100, unit="mg/dL")
        trend = analyze_trend(readings, ref)
        assert trend.trend_direction == "rising"
        assert trend.change_rate > 0

    def test_falling_trend(self):
        readings = [self._make_reading("glucose", v, d)
                    for d, v in enumerate([120, 110, 95, 85, 80], 1)]
        ref = ReferenceRange(low=70, high=100, unit="mg/dL")
        trend = analyze_trend(readings, ref)
        assert trend.trend_direction == "falling"

    def test_stable_trend(self):
        readings = [self._make_reading("glucose", v, d)
                    for d, v in enumerate([85, 86, 85, 84, 85], 1)]
        ref = ReferenceRange(low=70, high=100, unit="mg/dL")
        trend = analyze_trend(readings, ref)
        assert trend.trend_direction == "stable"

    def test_single_reading(self):
        readings = [self._make_reading("glucose", 85, 1)]
        ref = ReferenceRange(low=70, high=100, unit="mg/dL")
        trend = analyze_trend(readings, ref)
        assert trend.status == BiomarkerStatus.NORMAL
        assert trend.trend_direction == "stable"

    def test_empty_raises(self):
        ref = ReferenceRange(low=70, high=100, unit="mg/dL")
        with pytest.raises(ValueError):
            analyze_trend([], ref)

    def test_anomaly_on_critical(self):
        readings = [self._make_reading("glucose", v, d)
                    for d, v in enumerate([85, 85, 85, 85, 160], 1)]
        ref = ReferenceRange(low=70, high=100, unit="mg/dL", critical_high=150)
        trend = analyze_trend(readings, ref)
        assert trend.anomaly_detected


class TestConvertUnit:
    def test_same_unit(self):
        assert convert_unit(100, "mg/dL", "mg/dL") == 100

    def test_mg_to_mmol(self):
        result = convert_unit(180, "mg/dL", "mmol/L")
        assert abs(result - 10.0) < 0.01

    def test_mmol_to_mg(self):
        result = convert_unit(10, "mmol/L", "mg/dL")
        assert abs(result - 180.18) < 0.1

    def test_unknown_conversion(self):
        assert convert_unit(100, "mg/dL", "unknown") is None

    def test_ng_to_nmol(self):
        result = convert_unit(40, "ng/mL", "nmol/L")
        assert abs(result - 99.84) < 0.1


class TestGenerateDashboard:
    def _make_reading(self, name, value, day):
        return BiomarkerReading(name=name, value=value, unit="mg/dL",
                                timestamp=datetime(2024, 1, day))

    def test_empty_readings(self):
        dashboard = generate_biomarker_dashboard([])
        assert dashboard["summary"]["total"] == 0

    def test_basic_dashboard(self):
        readings = [
            self._make_reading("hemoglobin", 14.0, 1),
            self._make_reading("glucose_fasting", 85, 1),
        ]
        dashboard = generate_biomarker_dashboard(readings)
        assert dashboard["summary"]["total"] == 2
        assert dashboard["summary"]["normal"] == 2

    def test_critical_alert(self):
        readings = [
            self._make_reading("glucose_fasting", 400, 1),
        ]
        dashboard = generate_biomarker_dashboard(readings)
        assert dashboard["summary"]["critical"] == 1
        assert len(dashboard["alerts"]) == 1

    def test_abnormal_marker(self):
        readings = [
            self._make_reading("glucose_fasting", 120, 1),
        ]
        dashboard = generate_biomarker_dashboard(readings)
        assert dashboard["summary"]["abnormal"] == 1


class TestCommonReferenceRanges:
    def test_all_have_valid_ranges(self):
        for name, ref in COMMON_REFERENCE_RANGES.items():
            assert ref.low < ref.high
            assert len(ref.unit) > 0

    def test_key_markers_present(self):
        expected = ["hemoglobin", "glucose_fasting", "creatinine", "tsh"]
        for marker in expected:
            assert marker in COMMON_REFERENCE_RANGES

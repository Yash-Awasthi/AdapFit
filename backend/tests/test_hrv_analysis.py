"""Tests for hrv_analysis.py — comprehensive HRV analysis service."""

import math
import pytest
from app.services.hrv_analysis import (
    HRVAnalyzer, TimeDomainFeatures, FrequencyDomainFeatures,
    NonlinearFeatures, HRVReport,
)


@pytest.fixture
def normal_rr():
    """Normal healthy RR intervals (~75 bpm with variability)."""
    import random
    random.seed(42)
    base = 800
    return [base + random.gauss(0, 30) for _ in range(300)]


@pytest.fixture
def short_rr():
    return [800, 810, 790, 820, 780]


@pytest.fixture
def low_hrv_rr():
    """Low HRV — monotonous rhythm."""
    return [800] * 100


class TestRRIProcessing:
    def test_compute_rri(self):
        rr = [200, 400, 800, 1200, 2500]
        filtered = HRVAnalyzer.compute_rri(rr)
        assert 200 not in filtered
        assert 2500 not in filtered
        assert 800 in filtered

    def test_detect_outliers(self):
        rr = [800, 810, 1500, 820, 800]  # 1500 is outlier
        outliers = HRVAnalyzer.detect_outliers(rr, threshold=200)
        assert outliers[2] == True

    def test_interpolate_outliers(self):
        rr = [800, 810, 1500, 820, 800]
        outliers = [False, False, True, False, False]
        result = HRVAnalyzer.interpolate_outliers(rr, outliers)
        assert result[2] == 815  # (810 + 820) / 2

    def test_detrend_linear(self):
        rr = [100 + i * 2 for i in range(100)]
        detrended, slope = HRVAnalyzer.detrend_linear(rr)
        assert abs(slope - 2.0) < 0.01
        assert abs(sum(detrended) / len(detrended)) < 1.0


class TestTimeDomain:
    def test_basic_features(self, normal_rr):
        td = HRVAnalyzer.time_domain(normal_rr)
        assert td.hr_mean > 50
        assert td.rr_mean > 500
        assert td.rmssd > 0
        assert td.sdnn > 0

    def test_nn50(self, normal_rr):
        td = HRVAnalyzer.time_domain(normal_rr)
        assert td.nn50 >= 0
        assert 0 <= td.pnn50 <= 100

    def test_short_input(self, short_rr):
        td = HRVAnalyzer.time_domain(short_rr)
        assert td.rmssd >= 0

    def test_constant_rr(self, low_hrv_rr):
        td = HRVAnalyzer.time_domain(low_hrv_rr)
        assert td.rmssd == 0.0
        assert td.sdnn == 0.0


class TestFrequencyDomain:
    def test_basic_fd(self, normal_rr):
        fd = HRVAnalyzer.frequency_domain(normal_rr)
        assert fd.total_power >= 0
        assert fd.lf_power >= 0
        assert fd.hf_power >= 0

    def test_lf_hf_ratio(self, normal_rr):
        fd = HRVAnalyzer.frequency_domain(normal_rr)
        assert fd.lf_hf_ratio >= 0

    def test_short_input(self, short_rr):
        fd = HRVAnalyzer.frequency_domain(short_rr)
        assert fd.total_power == 0  # Too short


class TestNonlinear:
    def test_poincare(self, normal_rr):
        sd1, sd2 = HRVAnalyzer.poincare(normal_rr)
        assert sd1 > 0
        assert sd2 > 0

    def test_poincare_short(self):
        sd1, sd2 = HRVAnalyzer.poincare([800])
        assert sd1 == 0.0

    def test_sample_entropy(self, normal_rr):
        se = HRVAnalyzer.sample_entropy(normal_rr)
        assert not math.isnan(se)
        assert se > 0

    def test_approximate_entropy(self, normal_rr):
        ae = HRVAnalyzer.approximate_entropy(normal_rr)
        assert not math.isnan(ae)


class TestQuality:
    def test_good_quality(self, normal_rr):
        q = HRVAnalyzer.signal_quality(normal_rr)
        assert q > 50

    def test_empty(self):
        q = HRVAnalyzer.signal_quality([])
        assert q == 0.0


class TestAnalyze:
    def test_full_analysis(self, normal_rr):
        report = HRVAnalyzer.analyze(normal_rr)
        assert report is not None
        assert report.duration_seconds > 0
        assert report.sample_count > 0
        assert report.time_domain.rmssd > 0
        assert report.quality_score > 0
        assert len(report.interpretation) > 0

    def test_with_frequency_domain(self, normal_rr):
        report = HRVAnalyzer.analyze(normal_rr)
        assert report.frequency_domain is not None

    def test_with_nonlinear(self, normal_rr):
        report = HRVAnalyzer.analyze(normal_rr)
        assert report.nonlinear is not None

    def test_too_short(self, short_rr):
        report = HRVAnalyzer.analyze(short_rr)
        assert report is None

    def test_reference(self):
        ref = HRVAnalyzer.get_hrv_reference()
        assert "time_domain" in ref
        assert "frequency_domain" in ref

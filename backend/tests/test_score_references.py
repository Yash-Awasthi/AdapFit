"""Scores checked against hand-computed values from their published definitions."""
import math

from app.services.endurance_coaching import DailyTrainingLoad, calculate_ctl_atl
from app.services.hrv_analysis import HRVAnalyzer
from app.services.hrv_biofeedback import HRVBiofeedbackAnalyzer
from app.services.recovery_engine import RecoveryEngine

RR = [800, 810, 790, 820, 780]  # ms; successive differences 10, -20, 30, -40


def test_rmssd_task_force_1996():
    # sqrt(mean(100, 400, 900, 1600)) = sqrt(750)
    expected = math.sqrt(750)
    assert HRVBiofeedbackAnalyzer.calculate_rmssd(RR) == expected
    assert abs(HRVAnalyzer.time_domain(RR).rmssd - expected) < 0.01


def test_sdnn_and_pnn50():
    td = HRVAnalyzer.time_domain(RR)
    # deviations from 800: 0, 10, -10, 20, -20; population SD sqrt(1000 / 5), as short-term HRV tools report
    assert abs(td.sdnn - math.sqrt(200)) < 0.01
    assert td.pnn50 == 0


def test_hrv_z_score_against_personal_baseline():
    z, score = RecoveryEngine.calculate_hrv_z_score(60, baseline_mean=50, baseline_std=5)
    assert z == 2.0 and score == 100.0
    assert RecoveryEngine.calculate_hrv_z_score(None)[0] is None


def test_banister_one_session():
    # Exponential impulse response with time constants 42 and 7 days (Banister 1975).
    m = calculate_ctl_atl([DailyTrainingLoad(date="2026-01-01", tss=100, duration_min=0)])[-1]
    assert abs(m.ctl - 100 * (1 - math.exp(-1 / 42))) < 0.05
    assert abs(m.atl - 100 * (1 - math.exp(-1 / 7))) < 0.05
    assert abs(m.tsb - (m.ctl - m.atl)) <= 0.1  # each figure is rounded to 0.1

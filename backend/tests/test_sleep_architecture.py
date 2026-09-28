"""Tests for Sleep Architecture Analysis."""
import pytest
from app.services.sleep_architecture import (
    calculate_sol,
    calculate_waso,
    calculate_tst,
    calculate_sleep_efficiency,
    calculate_rem_latency,
    count_wake_episodes,
    get_stage_durations,
    get_stage_percentages,
    count_sleep_cycles,
    calculate_continuity_index,
    calculate_sleep_score,
    analyze_sleep_architecture,
    classify_sleep_quality,
    detect_sleep_patterns,
    WAKE, N1, N2, N3, REM,
)


# Helper to create a typical sleep hypnogram (8 hours, 960 epochs at 30s)
def make_normal_sleep():
    """Create a typical night of sleep (960 epochs = 8 hours)."""
    stages = []

    # Wake at start (30 min = 60 epochs)
    stages.extend([WAKE] * 60)

    # Cycle 1: N1→N2→N3→N2→REM
    stages.extend([N1] * 10)  # 5 min
    stages.extend([N2] * 40)  # 20 min
    stages.extend([N3] * 80)  # 40 min
    stages.extend([N2] * 20)  # 10 min
    stages.extend([REM] * 30)  # 15 min

    # Brief wake
    stages.extend([WAKE] * 5)

    # Cycle 2: N1→N2→N3→N2→REM
    stages.extend([N1] * 8)
    stages.extend([N2] * 30)
    stages.extend([N3] * 60)
    stages.extend([N2] * 15)
    stages.extend([REM] * 40)

    # Brief wake
    stages.extend([WAKE] * 5)

    # Cycle 3: N1→N2→REM (less deep sleep later)
    stages.extend([N1] * 8)
    stages.extend([N2] * 40)
    stages.extend([REM] * 60)

    # Brief wake
    stages.extend([WAKE] * 5)

    # Cycle 4: N2→REM
    stages.extend([N2] * 30)
    stages.extend([REM] * 80)

    # Morning wake
    stages.extend([WAKE] * 40)

    # Fill to 960
    remaining = 960 - len(stages)
    if remaining > 0:
        stages.extend([WAKE] * remaining)
    elif remaining < 0:
        stages = stages[:960]

    return stages


class TestSOL:
    def test_normal(self):
        stages = [WAKE] * 30 + [N1] * 10 + [N2] * 100
        sol = calculate_sol(stages)
        assert sol == pytest.approx(15.0, abs=1.0)

    def test_no_wake(self):
        stages = [N2] * 100
        sol = calculate_sol(stages)
        assert sol == 0.0

    def test_long_solidation(self):
        stages = [WAKE] * 60 + [N1] * 10 + [N2] * 100
        sol = calculate_sol(stages)
        assert sol == pytest.approx(30.0, abs=1.0)


class TestWASO:
    def test_no_wake_after_onset(self):
        stages = [WAKE] * 10 + [N2] * 100
        waso = calculate_waso(stages)
        assert waso == 0.0

    def test_with_wake_episodes(self):
        stages = [WAKE] * 10 + [N2] * 40 + [WAKE] * 10 + [N2] * 40
        waso = calculate_waso(stages)
        assert waso == pytest.approx(5.0, abs=1.0)


class TestTST:
    def test_all_sleep(self):
        stages = [N2] * 100
        assert calculate_tst(stages) == pytest.approx(50.0)

    def test_mixed(self):
        stages = [WAKE] * 20 + [N2] * 80
        assert calculate_tst(stages) == pytest.approx(40.0)

    def test_empty(self):
        assert calculate_tst([]) == 0.0


class TestSleepEfficiency:
    def test_perfect(self):
        stages = [N2] * 100
        assert calculate_sleep_efficiency(stages) == pytest.approx(100.0)

    def test_half(self):
        stages = [WAKE] * 50 + [N2] * 50
        assert calculate_sleep_efficiency(stages) == pytest.approx(50.0)


class TestREMLatency:
    def test_no_rem(self):
        stages = [WAKE] * 10 + [N1] * 10 + [N2] * 100
        assert calculate_rem_latency(stages) == -1.0

    def test_with_rem(self):
        stages = [WAKE] * 10 + [N1] * 10 + [N2] * 20 + [REM] * 20
        latency = calculate_rem_latency(stages)
        assert latency > 0


class TestWakeEpisodes:
    def test_no_wake(self):
        stages = [N2] * 100
        assert count_wake_episodes(stages) == 0

    def test_multiple_episodes(self):
        stages = [WAKE] * 10 + [N2] * 20 + [WAKE] * 5 + [N2] * 20 + [WAKE] * 5 + [N2] * 20
        assert count_wake_episodes(stages) == 2  # 2 after sleep onset


class TestStageDurations:
    def test_basic(self):
        stages = [WAKE] * 10 + [N1] * 5 + [N2] * 20 + [N3] * 10 + [REM] * 5
        durations = get_stage_durations(stages)
        assert durations["Wake"] == 5.0  # 10 * 0.5 min
        assert durations["N1 (Light)"] == 2.5
        assert durations["N2 (Intermediate)"] == 10.0
        assert durations["N3 (Deep/SWS)"] == 5.0
        assert durations["REM"] == 2.5


class TestStagePercentages:
    def test_basic(self):
        # 50 epochs sleep: 10 N1, 20 N2, 10 N3, 10 REM
        stages = [N1] * 10 + [N2] * 20 + [N3] * 10 + [REM] * 10
        pct = get_stage_percentages(stages)
        assert pct["N1 (Light)"] == pytest.approx(20.0)
        assert pct["N2 (Intermediate)"] == pytest.approx(40.0)
        assert pct["N3 (Deep/SWS)"] == pytest.approx(20.0)
        assert pct["REM"] == pytest.approx(20.0)


class TestSleepCycles:
    def test_normal(self):
        stages = [N1] * 10 + [N2] * 20 + [REM] * 10 + [N2] * 20 + [REM] * 10
        assert count_sleep_cycles(stages) == 2

    def test_no_rem(self):
        stages = [N1] * 10 + [N2] * 20 + [N3] * 20
        assert count_sleep_cycles(stages) == 0


class TestContinuityIndex:
    def test_continuous(self):
        stages = [N2] * 100
        assert calculate_continuity_index(stages) == 1.0

    def test_fragmented(self):
        stages = [N2] * 10 + [WAKE] * 5 + [N2] * 10
        ci = calculate_continuity_index(stages)
        assert ci < 1.0


class TestSleepScore:
    def test_normal_sleep(self):
        stages = make_normal_sleep()
        score = calculate_sleep_score(stages)
        assert 0 <= score <= 100
        assert score > 50  # Normal sleep should score decently

    def test_perfect_sleep(self):
        stages = [N2] * 480 + [N3] * 120 + [REM] * 120  # 6h sleep
        score = calculate_sleep_score(stages)
        assert score > 70

    def test_terrible_sleep(self):
        stages = [WAKE] * 480 + [N1] * 20  # mostly awake
        score = calculate_sleep_score(stages)
        assert score < 30


class TestAnalyzeArchitecture:
    def test_normal(self):
        stages = make_normal_sleep()
        arch = analyze_sleep_architecture(stages)
        assert arch.total_sleep_time_min > 0
        assert arch.sleep_efficiency_pct > 0
        assert arch.sleep_score > 0
        assert arch.sleep_cycles >= 1

    def test_empty(self):
        arch = analyze_sleep_architecture([])
        assert arch.total_sleep_time_min == 0.0


class TestQualityClassification:
    def test_excellent(self):
        result = classify_sleep_quality(90)
        assert result["label"] == "Excellent"

    def test_good(self):
        result = classify_sleep_quality(75)
        assert result["label"] == "Good"

    def test_poor(self):
        result = classify_sleep_quality(45)
        assert result["label"] == "Poor"


class TestSleepPatterns:
    def test_ordinary_night_has_no_long_onset(self):
        stages = [WAKE] * 10 + [N2] * 100 + [N3] * 40 + [REM] * 40 + [WAKE] * 10
        keys = [p["pattern"] for p in detect_sleep_patterns(stages)]
        assert "long_time_to_fall_asleep" not in keys

    def test_long_onset_is_described_not_diagnosed(self):
        stages = [WAKE] * 100 + [N2] * 50
        patterns = detect_sleep_patterns(stages)
        assert "long_time_to_fall_asleep" in [p["pattern"] for p in patterns]
        text = " ".join(p["observed"] + p["next_step"] for p in patterns).lower()
        assert "insomnia" not in text

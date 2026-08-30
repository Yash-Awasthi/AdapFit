"""Sleep Architecture Analysis.

Extracted from asleep (inspiration).
Computes sleep statistics from stage sequences: SOL, WASO, TST, SE,
REM latency, stage durations, sleep continuity, and quality scoring.

All pure functions — no DB, no async.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


# Sleep stage constants (following standard PSG scoring)
WAKE = 0
N1 = 1
N2 = 2
N3 = 3  # Slow-wave / deep sleep
REM = 4

STAGE_NAMES = {
    WAKE: "Wake",
    N1: "N1 (Light)",
    N2: "N2 (Intermediate)",
    N3: "N3 (Deep/SWS)",
    REM: "REM",
}

EPOCH_DURATION_SEC = 30.0  # Standard PSG epoch


@dataclass
class SleepArchitecture:
    """Complete sleep architecture metrics."""
    total_sleep_time_min: float = 0.0
    time_in_bed_min: float = 0.0
    sleep_onset_latency_min: float = 0.0
    wake_after_sleep_onset_min: float = 0.0
    sleep_efficiency_pct: float = 0.0
    rem_latency_min: float = 0.0
    wake_count: int = 0
    stage_durations_min: dict = field(default_factory=dict)
    stage_percentages: dict = field(default_factory=dict)
    sleep_cycles: int = 0
    sleep_score: float = 0.0
    continuity_index: float = 0.0


def get_sleep_onset_index(
    stages: list[int],
    threshold_epochs: int = 3,
) -> int:
    """Find the index of sleep onset.

    Sleep onset is defined as the first epoch of 3+ consecutive non-wake epochs.

    Args:
        stages: List of sleep stage codes
        threshold_epochs: Consecutive non-wake epochs needed (default 3)

    Returns:
        Index of sleep onset, or len(stages) if no onset found
    """
    k = 0
    for i, stage in enumerate(stages):
        if stage != WAKE:
            k += 1
            if k >= threshold_epochs:
                return i - (threshold_epochs - 1)
        else:
            k = 0
    return len(stages)


def calculate_sol(stages: list[int]) -> float:
    """Calculate Sleep Onset Latency (SOL).

    Time from lights out to first sustained sleep (3+ non-wake epochs).

    Args:
        stages: List of sleep stage codes (30s epochs)

    Returns:
        SOL in minutes
    """
    onset_idx = get_sleep_onset_index(stages)
    return onset_idx * (EPOCH_DURATION_SEC / 60.0)


def calculate_waso(stages: list[int]) -> float:
    """Calculate Wake After Sleep Onset (WASO).

    Total wake time occurring after sleep onset.

    Args:
        stages: List of sleep stage codes (30s epochs)

    Returns:
        WASO in minutes
    """
    onset_idx = get_sleep_onset_index(stages)
    stages_after_onset = stages[onset_idx:]
    wake_epochs = sum(1 for s in stages_after_onset if s == WAKE)
    return wake_epochs * (EPOCH_DURATION_SEC / 60.0)


def calculate_tst(stages: list[int]) -> float:
    """Calculate Total Sleep Time (TST).

    Total time spent in any sleep stage.

    Args:
        stages: List of sleep stage codes (30s epochs)

    Returns:
        TST in minutes
    """
    sleep_epochs = sum(1 for s in stages if s != WAKE)
    return sleep_epochs * (EPOCH_DURATION_SEC / 60.0)


def calculate_sleep_efficiency(stages: list[int]) -> float:
    """Calculate Sleep Efficiency (SE).

    SE = TST / Time in Bed * 100

    Args:
        stages: List of sleep stage codes (30s epochs)

    Returns:
        Sleep efficiency as percentage
    """
    tst = calculate_tst(stages)
    tib = len(stages) * (EPOCH_DURATION_SEC / 60.0)
    return (tst / tib * 100.0) if tib > 0 else 0.0


def calculate_rem_latency(stages: list[int]) -> float:
    """Calculate REM latency.

    Time from sleep onset to first REM epoch.

    Args:
        stages: List of sleep stage codes (30s epochs)

    Returns:
        REM latency in minutes, or -1 if no REM
    """
    onset_idx = get_sleep_onset_index(stages)
    for i in range(onset_idx, len(stages)):
        if stages[i] == REM:
            return (i - onset_idx) * (EPOCH_DURATION_SEC / 60.0)
    return -1.0


def count_wake_episodes(stages: list[int]) -> int:
    """Count the number of wake episodes after sleep onset.

    Args:
        stages: List of sleep stage codes (30s epochs)

    Returns:
        Number of wake episodes
    """
    onset_idx = get_sleep_onset_index(stages)
    stages_after = stages[onset_idx:]

    count = 0
    in_wake = False
    for stage in stages_after:
        if stage == WAKE and not in_wake:
            count += 1
            in_wake = True
        elif stage != WAKE:
            in_wake = False

    return count


def get_stage_durations(stages: list[int]) -> dict:
    """Calculate duration of each sleep stage.

    Args:
        stages: List of sleep stage codes (30s epochs)

    Returns:
        Dictionary mapping stage name to duration in minutes
    """
    durations = {}
    for stage_code, name in STAGE_NAMES.items():
        count = sum(1 for s in stages if s == stage_code)
        durations[name] = count * (EPOCH_DURATION_SEC / 60.0)
    return durations


def get_stage_percentages(stages: list[int]) -> dict:
    """Calculate percentage of total sleep time for each stage.

    Args:
        stages: List of sleep stage codes (30s epochs)

    Returns:
        Dictionary mapping stage name to percentage
    """
    tst = calculate_tst(stages)
    if tst == 0:
        return {name: 0.0 for name in STAGE_NAMES.values()}

    percentages = {}
    for stage_code, name in STAGE_NAMES.items():
        if stage_code == WAKE:
            continue  # Wake is not part of sleep %
        count = sum(1 for s in stages if s == stage_code)
        percentages[name] = round(count * (EPOCH_DURATION_SEC / 60.0) / tst * 100.0, 1)

    return percentages


def count_sleep_cycles(stages: list[int]) -> int:
    """Count complete sleep cycles.

    A typical cycle is NREM (N1→N2→N3) followed by REM.
    Simplified: count transitions from any NREM to REM.

    Args:
        stages: List of sleep stage codes (30s epochs)

    Returns:
        Estimated number of sleep cycles
    """
    cycles = 0
    in_nrem = False

    for stage in stages:
        if stage in (N1, N2, N3):
            in_nrem = True
        elif stage == REM and in_nrem:
            cycles += 1
            in_nrem = False

    return cycles


def calculate_continuity_index(stages: list[int]) -> float:
    """Calculate sleep continuity index.

    Ratio of longest uninterrupted sleep bout to total sleep time.

    Args:
        stages: List of sleep stage codes (30s epochs)

    Returns:
        Continuity index (0-1, higher = more continuous)
    """
    # Find longest uninterrupted sleep bout
    max_bout = 0
    current_bout = 0

    for stage in stages:
        if stage != WAKE:
            current_bout += 1
            max_bout = max(max_bout, current_bout)
        else:
            current_bout = 0

    tst_epochs = sum(1 for s in stages if s != WAKE)
    return round(max_bout / tst_epochs, 3) if tst_epochs > 0 else 0.0


def calculate_sleep_score(stages: list[int]) -> float:
    """Calculate a composite sleep quality score (0-100).

    Factors: efficiency, TST, SOL, WASO, deep sleep %, REM %, continuity.

    Args:
        stages: List of sleep stage codes (30s epochs)

    Returns:
        Sleep quality score (0-100)
    """
    if not stages:
        return 0.0

    # Individual scores (0-100)
    se = calculate_sleep_efficiency(stages)
    se_score = min(100.0, se * 1.1)  # 90% SE = 99 points

    tst = calculate_tst(stages)
    # Optimal TST is 7-9 hours (420-540 min)
    if 420 <= tst <= 540:
        tst_score = 100.0
    elif tst < 420:
        tst_score = max(0, tst / 420 * 100)
    else:
        tst_score = max(0, 100 - (tst - 540) / 120 * 50)

    sol = calculate_sol(stages)
    # SOL < 15 min is ideal
    sol_score = max(0, 100 - max(0, sol - 15) * 5)

    waso = calculate_waso(stages)
    # WASO < 30 min is ideal
    waso_score = max(0, 100 - max(0, waso - 30) * 3)

    # Deep sleep percentage (target: 15-25%)
    percentages = get_stage_percentages(stages)
    deep_pct = percentages.get("N3 (Deep/SWS)", 0.0)
    if 15 <= deep_pct <= 25:
        deep_score = 100.0
    elif deep_pct < 15:
        deep_score = max(0, deep_pct / 15 * 100)
    else:
        deep_score = max(0, 100 - (deep_pct - 25) * 5)

    # REM percentage (target: 20-25%)
    rem_pct = percentages.get("REM", 0.0)
    if 20 <= rem_pct <= 25:
        rem_score = 100.0
    elif rem_pct < 20:
        rem_score = max(0, rem_pct / 20 * 100)
    else:
        rem_score = max(0, 100 - (rem_pct - 25) * 5)

    continuity = calculate_continuity_index(stages)
    continuity_score = continuity * 100.0

    # Weighted composite
    weights = {
        "efficiency": 0.25,
        "tst": 0.15,
        "sol": 0.10,
        "waso": 0.10,
        "deep": 0.15,
        "rem": 0.15,
        "continuity": 0.10,
    }

    score = (
        se_score * weights["efficiency"]
        + tst_score * weights["tst"]
        + sol_score * weights["sol"]
        + waso_score * weights["waso"]
        + deep_score * weights["deep"]
        + rem_score * weights["rem"]
        + continuity_score * weights["continuity"]
    )

    return round(score, 1)


def analyze_sleep_architecture(stages: list[int]) -> SleepArchitecture:
    """Perform complete sleep architecture analysis.

    Args:
        stages: List of sleep stage codes (30s epochs)

    Returns:
        SleepArchitecture with all computed metrics
    """
    if not stages:
        return SleepArchitecture()

    durations = get_stage_durations(stages)
    percentages = get_stage_percentages(stages)

    return SleepArchitecture(
        total_sleep_time_min=round(calculate_tst(stages), 1),
        time_in_bed_min=round(len(stages) * (EPOCH_DURATION_SEC / 60.0), 1),
        sleep_onset_latency_min=round(calculate_sol(stages), 1),
        wake_after_sleep_onset_min=round(calculate_waso(stages), 1),
        sleep_efficiency_pct=round(calculate_sleep_efficiency(stages), 1),
        rem_latency_min=round(calculate_rem_latency(stages), 1),
        wake_count=count_wake_episodes(stages),
        stage_durations_min=durations,
        stage_percentages=percentages,
        sleep_cycles=count_sleep_cycles(stages),
        sleep_score=calculate_sleep_score(stages),
        continuity_index=calculate_continuity_index(stages),
    )


def classify_sleep_quality(score: float) -> dict:
    """Classify sleep quality from composite score.

    Args:
        score: Sleep score (0-100)

    Returns:
        Quality classification with label and recommendations
    """
    if score >= 85:
        return {
            "label": "Excellent",
            "color": "green",
            "recommendation": "Outstanding sleep quality. Maintain your current habits.",
        }
    elif score >= 70:
        return {
            "label": "Good",
            "color": "blue",
            "recommendation": "Good sleep quality. Minor improvements possible in consistency.",
        }
    elif score >= 55:
        return {
            "label": "Fair",
            "color": "yellow",
            "recommendation": "Fair sleep quality. Consider optimizing sleep schedule and environment.",
        }
    elif score >= 40:
        return {
            "label": "Poor",
            "color": "orange",
            "recommendation": "Poor sleep quality. Review sleep hygiene and consider professional consultation.",
        }
    else:
        return {
            "label": "Very Poor",
            "color": "red",
            "recommendation": "Very poor sleep quality. Strongly consider consulting a sleep specialist.",
        }


def detect_sleep_disorders_indicators(stages: list[int]) -> list[dict]:
    """Detect potential sleep disorder indicators.

    NOTE: This is informational only, not a medical diagnosis.

    Args:
        stages: List of sleep stage codes (30s epochs)

    Returns:
        List of potential indicators with severity
    """
    indicators = []

    if not stages:
        return indicators

    sol = calculate_sol(stages)
    se = calculate_sleep_efficiency(stages)
    waso = calculate_waso(stages)
    tst = calculate_tst(stages)
    percentages = get_stage_percentages(stages)

    # Insomnia indicators
    if sol > 30:
        indicators.append({
            "condition": "Sleep Onset Insomnia",
            "indicator": f"SOL of {sol:.0f} min (>30 min threshold)",
            "severity": "moderate" if sol <= 60 else "severe",
        })

    if waso > 60:
        indicators.append({
            "condition": "Sleep Maintenance Insomnia",
            "indicator": f"WASO of {waso:.0f} min (>60 min threshold)",
            "severity": "moderate" if waso <= 90 else "severe",
        })

    if se < 85:
        indicators.append({
            "condition": "Reduced Sleep Efficiency",
            "indicator": f"SE of {se:.0f}% (<85% threshold)",
            "severity": "mild" if se >= 75 else "moderate",
        })

    # Short sleep
    if tst < 360:
        indicators.append({
            "condition": "Short Sleep Duration",
            "indicator": f"TST of {tst:.0f} min (<6 hours)",
            "severity": "moderate",
        })

    # Excessive sleep
    if tst > 600:
        indicators.append({
            "condition": "Long Sleep Duration",
            "indicator": f"TST of {tst:.0f} min (>10 hours)",
            "severity": "mild",
        })

    # REM abnormalities
    rem_pct = percentages.get("REM", 0.0)
    if rem_pct < 15:
        indicators.append({
            "condition": "Reduced REM Sleep",
            "indicator": f"REM at {rem_pct:.0f}% (<15% of TST)",
            "severity": "mild",
        })
    elif rem_pct > 35:
        indicators.append({
            "condition": "Elevated REM Sleep",
            "indicator": f"REM at {rem_pct:.0f}% (>35% of TST)",
            "severity": "mild",
        })

    # SWS abnormalities
    deep_pct = percentages.get("N3 (Deep/SWS)", 0.0)
    if deep_pct < 5:
        indicators.append({
            "condition": "Reduced Deep Sleep",
            "indicator": f"N3 at {deep_pct:.0f}% (<5% of TST)",
            "severity": "moderate",
        })

    # Fragmentation
    wake_count = count_wake_episodes(stages)
    if wake_count > 10:
        indicators.append({
            "condition": "Sleep Fragmentation",
            "indicator": f"{wake_count} wake episodes after onset",
            "severity": "moderate" if wake_count <= 15 else "severe",
        })

    return indicators

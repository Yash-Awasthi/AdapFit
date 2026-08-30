"""HRV artifact correction — Lipponen et al. 2019 algorithm.

Extracted from inspiration/ZFIT/hrv-correction.
Pattern: time-varying thresholds from distribution of successive RR-interval
discrepancies, paired with beat categorization methodology.
Corrects extra, missing, or misaligned beat detections.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class Artifact:
    """A detected artifact in the RR interval series."""
    index: int
    artifact_type: str  # "extra", "missing", "misaligned"
    severity: float  # 0-1
    corrected: bool = False


@dataclass
class CorrectionResult:
    """Result of artifact correction."""
    corrected_rr: list[float]  # corrected RR intervals
    artifacts: list[Artifact]
    quality_score: float  # 0-1, higher = better quality
    removed_beats: int
    added_beats: int


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    if n % 2 == 0:
        return (s[n//2-1] + s[n//2]) / 2
    return s[n//2]


def _mad(values: list[float], med: float) -> float:
    """Median Absolute Deviation."""
    return _median([abs(v - med) for v in values])


def _quartile(values: list[float], q: float) -> float:
    """Get the q-th quartile (0-1)."""
    if not values:
        return 0.0
    s = sorted(values)
    idx = q * (len(s) - 1)
    lower = int(math.floor(idx))
    upper = int(math.ceil(idx))
    if lower == upper:
        return s[lower]
    return s[lower] * (1 - (idx - lower)) + s[upper] * (idx - lower)


def _successive_differences(rr: list[float]) -> list[float]:
    """Calculate successive differences (ΔRR)."""
    return [rr[i+1] - rr[i] for i in range(len(rr) - 1)]


def _time_varying_threshold(
    differences: list[float],
    window: int = 41,
) -> list[float]:
    """Calculate time-varying threshold using a sliding window.

    The threshold adapts to the local variability of the signal.
    """
    n = len(differences)
    thresholds = []

    half_w = window // 2
    for i in range(n):
        start = max(0, i - half_w)
        end = min(n, i + half_w + 1)
        window_vals = differences[start:end]

        med = _median([abs(d) for d in window_vals])
        # Use 2.5× the MAD-based threshold (Lipponen et al.)
        mad = _mad([abs(d) for d in window_vals], med) if window_vals else 0
        threshold = med + 2.5 * 1.4826 * mad  # 1.4826 = MAD to SD conversion
        thresholds.append(max(threshold, 50))  # minimum 50ms

    return thresholds


def categorize_beat(
    rr: list[float],
    i: int,
    diff: float,
    threshold: float,
) -> str | None:
    """Categorize a beat as normal, extra, missing, or misaligned.

    Returns None for normal beats, or the artifact type string.
    """
    abs_diff = abs(diff)

    if abs_diff <= threshold:
        return None  # Normal

    if i == 0 or i >= len(rr) - 1:
        return None  # Can't categorize at edges

    prev_rr = rr[i-1]
    curr_rr = rr[i]
    next_rr = rr[i+1] if i+1 < len(rr) else curr_rr

    # Missing beat: RR interval ~2× normal → insert a beat
    if curr_rr > 1.8 * prev_rr and curr_rr > 1.8 * _median(rr[max(0, i-5):i+5]):
        return "missing"

    # Extra beat: very short RR followed by compensatory pause
    if curr_rr < 0.5 * prev_rr and next_rr < 0.5 * _median(rr[max(0, i-5):i+5]):
        return "extra"

    # Misaligned: RR is abnormal but not clearly extra or missing
    return "misaligned"


def correct_artifacts(rr_intervals: list[float]) -> CorrectionResult:
    """Correct artifacts in an RR interval series.

    Based on Lipponen et al. (2019) algorithm:
    1. Calculate successive differences
    2. Compute time-varying thresholds using sliding window
    3. Categorize each abnormal beat
    4. Apply corrections: remove extra beats, interpolate missing beats
    """
    if len(rr_intervals) < 3:
        return CorrectionResult(
            corrected_rr=rr_intervals[:],
            artifacts=[],
            quality_score=1.0,
            removed_beats=0,
            added_beats=0,
        )

    corrected = rr_intervals[:]
    artifacts: list[Artifact] = []
    removed = 0
    added = 0

    # Step 1: successive differences
    diffs = _successive_differences(corrected)

    # Step 2: time-varying thresholds
    thresholds = _time_varying_threshold(diffs)

    # Step 3: detect and categorize artifacts
    i = 0
    while i < len(corrected) - 1:
        diff = corrected[i+1] - corrected[i] if i+1 < len(corrected) else 0
        threshold = thresholds[i] if i < len(thresholds) else 500

        artifact_type = categorize_beat(corrected, i, diff, threshold)

        if artifact_type == "extra":
            # Remove the extra beat: merge two intervals into one
            merged = corrected[i] + corrected[i+1]
            corrected[i] = merged
            del corrected[i+1]
            artifacts.append(Artifact(i, "extra", min(abs(diff) / threshold, 1.0), True))
            removed += 1
            # Don't advance i — re-check merged interval
            continue

        elif artifact_type == "missing":
            # Insert a beat: split the interval
            half = corrected[i] / 2
            corrected[i] = half
            corrected.insert(i+1, half)
            artifacts.append(Artifact(i, "missing", min(abs(diff) / threshold, 1.0), True))
            added += 1
            i += 2  # Skip the inserted beat
            continue

        elif artifact_type == "misaligned":
            # Replace with local median
            local = corrected[max(0, i-5):min(len(corrected), i+5)]
            local_median = _median(local)
            if 0.5 * local_median < corrected[i] < 2.0 * local_median:
                # Interpolate between neighbors
                if i > 0 and i < len(corrected) - 1:
                    corrected[i] = (corrected[i-1] + corrected[i+1]) / 2
                artifacts.append(Artifact(i, "misaligned", min(abs(diff) / threshold, 1.0), True))

        i += 1

    # Calculate quality score: fraction of non-artifact beats
    quality = 1.0 - (len(artifacts) / max(len(rr_intervals), 1))
    quality = max(0, min(1, quality))

    return CorrectionResult(
        corrected_rr=corrected,
        artifacts=artifacts,
        quality_score=quality,
        removed_beats=removed,
        added_beats=added,
    )

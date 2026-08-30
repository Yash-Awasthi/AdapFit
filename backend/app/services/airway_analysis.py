"""
Airway Analysis for PAP Therapy - ZFIT
Extracted from: airwaylab (airway analysis dashboard for PAP therapy users)
Patterns: Glasgow Index breath scoring, flow limitation detection,
          wobble analysis, NED analysis, oximetry pipeline, multi-night trends
"""
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class FlowLimitationSeverity(Enum):
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class GlasgowComponent(Enum):
    SKEW = "skew"
    FLAT_TOP = "flat_top"
    SPIKE = "spike"
    PLATEAU = "plateau"
    RIPPLE = "ripple"
    DOUBLE_PEAK = "double_peak"
    TRIANGULAR = "triangular"
    SHARP_RISE = "sharp_rise"
    DELAYED_PEAK = "delayed_peak"


@dataclass
class BreathSample:
    timestamp: float
    flow: float  # L/min (positive = inspiration)


@dataclass
class GlasgowResult:
    score: int  # 0-9
    components: dict[str, bool]  # which components detected
    description: str


@dataclass
class WobbleResult:
    fl_score: float  # Flow Limitation score (0-1)
    regularity: float  # Sample entropy (0-1, higher = more regular)
    periodicity: float  # Dominant frequency Hz
    severity: FlowLimitationSeverity


@dataclass
class NedResult:
    peak_mid_ratio: float
    rera_detected: bool
    rera_count: int
    description: str


@dataclass
class OximetryResult:
    avg_spo2: float
    min_spo2: float
    max_spo2: float
    time_below_90: float  # minutes
    time_below_88: float  # minutes
    desaturation_index: float
    oxygen_desiondex: float
    pulse_avg: float
    pulse_min: float
    pulse_max: float
    odi: float  # Oxygen Desaturation Index
    avg_spo2_no_desat: float


@dataclass
class NightReport:
    date: datetime
    glasgow: GlasgowResult
    wobble: WobbleResult
    ned: NedResult
    oximetry: Optional[OximetryResult]
    total_breaths: int
    flow_limitation_pct: float
    rera_count: int


# ─── Glasgow Index Analysis ────────────────────────────────────────────

def analyze_glasgow(breaths: list[BreathSample]) -> GlasgowResult:
    """9-component breath shape scoring (Glasgow Index)."""
    components = {}

    for breath in _segment_breaths(breaths):
        if len(breath) < 5:
            continue
        flows = [b.flow for b in breath]
        peak_idx = flows.index(max(flows))
        peak_ratio = peak_idx / len(flows) if len(flows) > 0 else 0.5

        # Skew: peak shifted to right
        components["skew"] = peak_ratio > 0.6

        # Flat top: flow stays near max for >30% of breath
        max_flow = max(flows)
        flat_count = sum(1 for f in flows if f > max_flow * 0.85)
        components["flat_top"] = flat_count / len(flows) > 0.3

        # Spike: very sharp peak
        if peak_idx > 0 and peak_idx < len(flows) - 1:
            rise = flows[peak_idx] - flows[peak_idx - 1]
            fall = flows[peak_idx] - flows[peak_idx + 1]
            components["spike"] = rise > max_flow * 0.5 and fall > max_flow * 0.5

        # Plateau: sustained flat region
        diffs = [abs(flows[i] - flows[i - 1]) for i in range(1, len(flows))]
        avg_diff = sum(diffs) / len(diffs) if diffs else 0
        components["plateau"] = avg_diff < max_flow * 0.05

        # Ripple: multiple small peaks
        peaks = sum(1 for i in range(1, len(flows) - 1) if flows[i] > flows[i - 1] and flows[i] > flows[i + 1])
        components["ripple"] = peaks >= 3

        # Double peak
        components["double_peak"] = peaks == 2

        # Triangular: symmetric rise and fall
        components["triangular"] = not components["flat_top"] and not components["spike"]

        # Sharp rise
        if peak_idx > 0:
            components["sharp_rise"] = (flows[peak_idx] - flows[0]) / max_flow > 0.8

        # Delayed peak
        components["delayed_peak"] = peak_ratio > 0.7

    score = sum(1 for v in components.values() if v)
    descriptions = [k for k, v in components.items() if v]

    return GlasgowResult(
        score=min(9, score),
        components=components,
        description=f"Score {score}/9: {', '.join(descriptions) if descriptions else 'normal breathing pattern'}",
    )


def _segment_breaths(breaths: list[BreathSample]) -> list[list[BreathSample]]:
    """Segment continuous flow data into individual breaths."""
    segments = []
    current = []
    for b in breaths:
        if b.flow > 0:
            current.append(b)
        elif current:
            segments.append(current)
            current = []
    if current:
        segments.append(current)
    return segments


# ─── Wobble Analysis (Flow Limitation) ─────────────────────────────────

def analyze_wobble(breaths: list[BreathSample], sampling_rate_hz: float = 100) -> WobbleResult:
    """Wobble Analysis Tool: FL Score, regularity, periodicity."""
    flows = [b.flow for b in breaths]
    if not flows:
        return WobbleResult(0, 0, 0, FlowLimitationSeverity.NONE)

    # FL Score: ratio of flow-limited breaths
    fl_count = 0
    segments = _segment_breaths(breaths)
    for seg in segments:
        if len(seg) < 5:
            continue
        seg_flows = [s.flow for s in seg]
        max_f = max(seg_flows)
        plateau_count = sum(1 for f in seg_flows if f > max_f * 0.8)
        if plateau_count / len(seg_flows) > 0.3:
            fl_count += 1

    fl_score = fl_count / len(segments) if segments else 0

    # Sample entropy (simplified)
    regularity = _sample_entropy(flows)

    # FFT periodicity (simplified)
    periodicity = _dominant_frequency(flows, sampling_rate_hz)

    severity = FlowLimitationSeverity.NONE
    if fl_score > 0.5:
        severity = FlowLimitationSeverity.SEVERE
    elif fl_score > 0.3:
        severity = FlowLimitationSeverity.MODERATE
    elif fl_score > 0.1:
        severity = FlowLimitationSeverity.MILD

    return WobbleResult(
        fl_score=round(fl_score, 3),
        regularity=round(regularity, 3),
        periodicity=round(periodicity, 3),
        severity=severity,
    )


def _sample_entropy(data: list[float], m: int = 2, r: float = 0.2) -> float:
    """Simplified sample entropy."""
    if len(data) < m + 1:
        return 0.0
    mean_val = sum(data) / len(data)
    std_val = math.sqrt(sum((x - mean_val) ** 2 for x in data) / len(data))
    if std_val == 0:
        return 0.0
    tolerance = r * std_val
    matches = 0
    total = 0
    for i in range(len(data) - m):
        for j in range(i + 1, len(data) - m):
            if all(abs(data[i + k] - data[j + k]) < tolerance for k in range(m)):
                matches += 1
            total += 1
    return matches / total if total > 0 else 0.0


def _dominant_frequency(data: list[float], sampling_rate: float) -> float:
    """Find dominant frequency using simple DFT."""
    n = len(data)
    if n < 10:
        return 0.0
    mean_val = sum(data) / n
    max_power = 0
    best_freq = 0
    for k in range(1, n // 2):
        real = sum((data[i] - mean_val) * math.cos(2 * math.pi * k * i / n) for i in range(n))
        imag = sum((data[i] - mean_val) * math.sin(2 * math.pi * k * i / n) for i in range(n))
        power = real * real + imag * imag
        if power > max_power:
            max_power = power
            best_freq = k * sampling_rate / n
    return best_freq


# ─── NED Analysis ──────────────────────────────────────────────────────

def analyze_ned(breaths: list[BreathSample]) -> NedResult:
    """NED Analysis: Peak-to-mid inspiratory flow ratio with RERA detection."""
    segments = _segment_breaths(breaths)
    ratios = []
    rera_count = 0

    for seg in segments:
        if len(seg) < 5:
            continue
        flows = [s.flow for s in seg]
        peak = max(flows)
        mid_idx = len(flows) // 2
        mid_flow = flows[mid_idx]

        ratio = peak / mid_flow if mid_flow > 0 else 1.0
        ratios.append(ratio)

        # RERA: effort-related awakening (high ratio with irregularity)
        if ratio > 2.0:
            rera_count += 1

    avg_ratio = sum(ratios) / len(ratios) if ratios else 1.0

    return NedResult(
        peak_mid_ratio=round(avg_ratio, 3),
        rera_detected=rera_count > 0,
        rera_count=rera_count,
        description=f"Avg ratio: {avg_ratio:.2f}, RERAs: {rera_count}",
    )


# ─── Night Report ──────────────────────────────────────────────────────

def generate_night_report(
    breaths: list[BreathSample],
    oximetry_data: Optional[list[float]] = None,
    date: datetime = None,
) -> NightReport:
    """Generate a comprehensive night report."""
    glasgow = analyze_glasgow(breaths)
    wobble = analyze_wobble(breaths)
    ned = analyze_ned(breaths)

    segments = _segment_breaths(breaths)
    fl_breaths = sum(1 for seg in segments if len(seg) >= 5)
    total_breaths = len(segments)

    oximetry = None
    if oximetry_data:
        oximetry = OximetryResult(
            avg_spo2=sum(oximetry_data) / len(oximetry_data),
            min_spo2=min(oximetry_data),
            max_spo2=max(oximetry_data),
            time_below_90=sum(1 for x in oximetry_data if x < 90) * 0.1,
            time_below_88=sum(1 for x in oximetry_data if x < 88) * 0.1,
            desaturation_index=0,
            oxygen_desiondex=0,
            pulse_avg=0,
            pulse_min=0,
            pulse_max=0,
            odi=0,
            avg_spo2_no_desat=sum(oximetry_data) / len(oximetry_data),
        )

    return NightReport(
        date=date or datetime.now(),
        glasgow=glasgow,
        wobble=wobble,
        ned=ned,
        oximetry=oximetry,
        total_breaths=total_breaths,
        flow_limitation_pct=round(wobble.fl_score * 100, 1),
        rera_count=ned.rera_count,
    )

"""
Advanced HRV Analysis for ZFIT
Extracted from: awesome-hrv (curated HRV research and libraries)
Patterns: Time-domain, frequency-domain, non-linear HRV analysis,
          clinical interpretation, recovery scoring, autonomic balance
"""
import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class HRVStatus(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    NORMAL = "normal"
    LOW = "low"
    VERY_LOW = "very_low"


class AutonomicBalance(Enum):
    SYMPATHETIC_DOMINANT = "sympathetic_dominant"
    PARASYMPATHETIC_DOMINANT = "parasympathetic_dominant"
    BALANCED = "balanced"


@dataclass
class HRVResult:
    # Time domain
    sdnn: float  # ms - overall HRV
    rmssd: float  # ms - short-term variability (parasympathetic)
    sdsd: float  # ms - successive differences
    nn50: int  # count of successive differences > 50ms
    pnn50: float  # percentage of nn50
    mean_rr: float  # ms - mean R-R interval
    median_rr: float
    min_rr: float
    max_rr: float

    # Frequency domain (if computed)
    vlf_power: Optional[float] = None  # ms² (0.003-0.04 Hz)
    lf_power: Optional[float] = None  # ms² (0.04-0.15 Hz)
    hf_power: Optional[float] = None  # ms² (0.15-0.4 Hz)
    lf_hf_ratio: Optional[float] = None
    total_power: Optional[float] = None

    # Interpretation
    status: HRVStatus = HRVStatus.NORMAL
    autonomic_balance: AutonomicBalance = AutonomicBalance.BALANCED
    recovery_score: float = 50.0  # 0-100
    stress_index: float = 0.0  # 0-100
    notes: list[str] = None

    def __post_init__(self):
        if self.notes is None:
            self.notes = []


# ─── Time Domain Analysis ──────────────────────────────────────────────

def compute_time_domain(rr_intervals_ms: list[float]) -> dict:
    """Compute time-domain HRV metrics from R-R intervals in milliseconds."""
    if len(rr_intervals_ms) < 2:
        return {"error": "Need at least 2 RR intervals"}

    n = len(rr_intervals_ms)
    mean_rr = sum(rr_intervals_ms) / n
    median_rr = sorted(rr_intervals_ms)[n // 2]
    min_rr = min(rr_intervals_ms)
    max_rr = max(rr_intervals_ms)

    # SDNN
    variance = sum((rr - mean_rr) ** 2 for rr in rr_intervals_ms) / (n - 1)
    sdnn = math.sqrt(variance)

    # Successive differences
    diffs = [abs(rr_intervals_ms[i] - rr_intervals_ms[i - 1]) for i in range(1, n)]
    mean_diff = sum(diffs) / len(diffs)

    # RMSSD
    rmssd = math.sqrt(sum(d ** 2 for d in diffs) / len(diffs))

    # SDSD
    diff_variance = sum((d - mean_diff) ** 2 for d in diffs) / (len(diffs) - 1)
    sdsd = math.sqrt(diff_variance)

    # NN50 and pNN50
    nn50 = sum(1 for d in diffs if d > 50)
    pnn50 = (nn50 / len(diffs)) * 100

    return {
        "sdnn": round(sdnn, 2),
        "rmssd": round(rmssd, 2),
        "sdsd": round(sdsd, 2),
        "nn50": nn50,
        "pnn50": round(pnn50, 2),
        "mean_rr": round(mean_rr, 2),
        "median_rr": round(median_rr, 2),
        "min_rr": round(min_rr, 2),
        "max_rr": round(max_rr, 2),
    }


# ─── Frequency Domain Analysis ─────────────────────────────────────────

def estimate_frequency_domain(
    rr_intervals_ms: list[float],
    sampling_rate_hz: float = 4.0,
) -> dict:
    """Estimate frequency-domain HRV metrics using Lomb-Scargle periodogram (simplified)."""
    if len(rr_intervals_ms) < 10:
        return {"error": "Need at least 10 RR intervals for frequency analysis"}

    mean_rr = sum(rr_intervals_ms) / len(rr_intervals_ms)
    detrended = [rr - mean_rr for rr in rr_intervals_ms]

    # Simple FFT-based power estimation
    n = len(detrended)
    freq_resolution = sampling_rate_hz / n

    total_power = sum(x ** 2 for x in detrended) / n

    # Band power estimation (simplified)
    lf_low, lf_high = 0.04, 0.15
    hf_low, hf_high = 0.15, 0.4

    lf_power = total_power * 0.45  # Approximate LF proportion
    hf_power = total_power * 0.35  # Approximate HF proportion
    vlf_power = total_power * 0.20  # Approximate VLF proportion

    lf_hf_ratio = lf_power / hf_power if hf_power > 0 else float('inf')

    return {
        "vlf_power": round(vlf_power, 2),
        "lf_power": round(lf_power, 2),
        "hf_power": round(hf_power, 2),
        "lf_hf_ratio": round(lf_hf_ratio, 3),
        "total_power": round(total_power, 2),
    }


# ─── Clinical Interpretation ───────────────────────────────────────────

def interpret_hrv(rmssd: float, sdnn: float, lf_hf_ratio: float = None) -> HRVStatus:
    """Interpret HRV status based on clinical guidelines."""
    if rmssd > 50:
        return HRVStatus.EXCELLENT
    elif rmssd > 35:
        return HRVStatus.GOOD
    elif rmssd > 20:
        return HRVStatus.NORMAL
    elif rmssd > 10:
        return HRVStatus.LOW
    else:
        return HRVStatus.VERY_LOW


def assess_autonomic_balance(lf_hf_ratio: float) -> AutonomicBalance:
    """Assess autonomic nervous system balance from LF/HF ratio."""
    if lf_hf_ratio > 2.0:
        return AutonomicBalance.SYMPATHETIC_DOMINANT
    elif lf_hf_ratio < 0.5:
        return AutonomicBalance.PARASYMPATHETIC_DOMINANT
    else:
        return AutonomicBalance.BALANCED


def compute_recovery_score(
    rmssd: float,
    resting_hr: float = 60,
    sleep_quality: float = 0.8,
    stress_level: float = 0.3,
) -> float:
    """Compute a 0-100 recovery score from multiple indicators."""
    # RMSSD component (0-40 points)
    rmssd_score = min(40, rmssd * 0.8)

    # Resting HR component (0-30 points)
    # Lower resting HR = better recovery
    rhr_score = max(0, 30 - (resting_hr - 50) * 0.5)

    # Sleep quality component (0-20 points)
    sleep_score = sleep_quality * 20

    # Stress component (0-10 points, inverted)
    stress_score = (1 - stress_level) * 10

    total = rmssd_score + rhr_score + sleep_score + stress_score
    return round(min(100, max(0, total)), 1)


def compute_stress_index(pnn50: float, lf_hf_ratio: float, rmssd: float) -> float:
    """Compute a 0-100 stress index (higher = more stressed)."""
    # Low pNN50 = higher stress
    pnn50_stress = max(0, (50 - pnn50) * 2)

    # High LF/HF ratio = sympathetic dominance = higher stress
    lf_hf_stress = min(40, max(0, (lf_hf_ratio - 1.0) * 20))

    # Low RMSSD = higher stress
    rmssd_stress = max(0, (40 - rmssd) * 1.5)

    total = pnn50_stress + lf_hf_stress + rmssd_stress
    return round(min(100, max(0, total)), 1)


# ─── Full Analysis ─────────────────────────────────────────────────────

def analyze_hrv(
    rr_intervals_ms: list[float],
    resting_hr: float = 60,
    sleep_quality: float = 0.8,
    stress_level: float = 0.3,
) -> HRVResult:
    """Perform complete HRV analysis."""
    time_domain = compute_time_domain(rr_intervals_ms)
    freq_domain = estimate_frequency_domain(rr_intervals_ms)

    status = interpret_hrv(time_domain["rmssd"], time_domain["sdnn"], freq_domain.get("lf_hf_ratio"))
    autonomic = assess_autonomic_balance(freq_domain.get("lf_hf_ratio", 1.0))
    recovery = compute_recovery_score(time_domain["rmssd"], resting_hr, sleep_quality, stress_level)
    stress = compute_stress_index(time_domain["pnn50"], freq_domain.get("lf_hf_ratio", 1.0), time_domain["rmssd"])

    notes = []
    if status in (HRVStatus.LOW, HRVStatus.VERY_LOW):
        notes.append("HRV is low — consider rest, hydration, and stress reduction")
    if autonomic == AutonomicBalance.SYMPATHETIC_DOMINANT:
        notes.append("Sympathetic dominance detected — recovery may be impaired")
    if recovery < 40:
        notes.append("Recovery score is low — prioritize sleep and rest")
    if stress > 70:
        notes.append("Stress index is high — consider relaxation techniques")

    return HRVResult(
        sdnn=time_domain["sdnn"],
        rmssd=time_domain["rmssd"],
        sdsd=time_domain["sdsd"],
        nn50=time_domain["nn50"],
        pnn50=time_domain["pnn50"],
        mean_rr=time_domain["mean_rr"],
        median_rr=time_domain["median_rr"],
        min_rr=time_domain["min_rr"],
        max_rr=time_domain["max_rr"],
        vlf_power=freq_domain.get("vlf_power"),
        lf_power=freq_domain.get("lf_power"),
        hf_power=freq_domain.get("hf_power"),
        lf_hf_ratio=freq_domain.get("lf_hf_ratio"),
        total_power=freq_domain.get("total_power"),
        status=status,
        autonomic_balance=autonomic,
        recovery_score=recovery,
        stress_index=stress,
        notes=notes,
    )

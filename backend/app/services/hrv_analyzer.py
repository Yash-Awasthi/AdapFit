"""
HRV analysis with frequency domain metrics.

Extracted from hrv-analysis — power spectral density and autonomic balance.
"""
from dataclasses import dataclass
from typing import List
import math


@dataclass
class HRVMetrics:
    mean_rr: float = 0.0
    sdnn: float = 0.0
    rmssd: float = 0.0
    pnn50: float = 0.0
    lf_power: float = 0.0
    hf_power: float = 0.0
    lf_hf_ratio: float = 0.0
    total_power: float = 0.0
    vlf_power: float = 0.0
    sd1: float = 0.0
    sd2: float = 0.0
    sample_entropy: float = 0.0


def compute_time_domain(rr_intervals: List[float]) -> dict:
    if len(rr_intervals) < 2:
        return {"mean_rr": 0, "sdnn": 0, "rmssd": 0, "pnn50": 0}

    mean_rr = sum(rr_intervals) / len(rr_intervals)
    sdnn = math.sqrt(sum((r - mean_rr) ** 2 for r in rr_intervals) / len(rr_intervals))

    diffs = [rr_intervals[i + 1] - rr_intervals[i] for i in range(len(rr_intervals) - 1)]
    rmssd = math.sqrt(sum(d ** 2 for d in diffs) / len(diffs))
    pnn50 = sum(1 for d in diffs if abs(d) > 50) / len(diffs) * 100

    return {"mean_rr": mean_rr, "sdnn": sdnn, "rmssd": rmssd, "pnn50": pnn50}


def compute_frequency_domain(rr_intervals: List[float], fs: float = 4.0) -> dict:
    n = len(rr_intervals)
    if n < 16:
        return {"lf_power": 0, "hf_power": 0, "lf_hf_ratio": 0, "total_power": 0}

    mean_rr = sum(rr_intervals) / n
    centered = [r - mean_rr for r in rr_intervals]

    lf_power = 0.0
    hf_power = 0.0
    vlf_power = 0.0

    for k in range(n // 2):
        freq = k * fs / n
        real = sum(centered[i] * math.cos(2 * math.pi * k * i / n) for i in range(n))
        imag = sum(centered[i] * math.sin(2 * math.pi * k * i / n) for i in range(n))
        psd = (real ** 2 + imag ** 2) / (n * fs)

        if 0.003 <= freq < 0.04:
            vlf_power += psd
        elif 0.04 <= freq < 0.15:
            lf_power += psd
        elif 0.15 <= freq < 0.4:
            hf_power += psd

    total_power = lf_power + hf_power + vlf_power
    lf_hf_ratio = lf_power / hf_power if hf_power > 0 else 0

    return {"lf_power": lf_power, "hf_power": hf_power, "lf_hf_ratio": lf_hf_ratio, "total_power": total_power, "vlf_power": vlf_power}


def compute_poincare(rr_intervals: List[float]) -> dict:
    if len(rr_intervals) < 3:
        return {"sd1": 0, "sd2": 0}

    diffs = [rr_intervals[i + 1] - rr_intervals[i] for i in range(len(rr_intervals) - 1)]
    sums = [rr_intervals[i] + rr_intervals[i + 1] for i in range(len(rr_intervals) - 1)]

    sd1 = math.sqrt(sum(d ** 2 for d in diffs) / (2 * len(diffs)))
    sd2 = math.sqrt(sum(s ** 2 for s in sums) / (2 * len(sums)))

    return {"sd1": sd1, "sd2": sd2}


def analyze_hrv(rr_intervals: List[float]) -> HRVMetrics:
    time = compute_time_domain(rr_intervals)
    freq = compute_frequency_domain(rr_intervals)
    poincare = compute_poincare(rr_intervals)

    return HRVMetrics(
        mean_rr=time["mean_rr"],
        sdnn=time["sdnn"],
        rmssd=time["rmssd"],
        pnn50=time["pnn50"],
        lf_power=freq["lf_power"],
        hf_power=freq["hf_power"],
        lf_hf_ratio=freq["lf_hf_ratio"],
        total_power=freq["total_power"],
        vlf_power=freq.get("vlf_power", 0),
        sd1=poincare["sd1"],
        sd2=poincare["sd2"],
    )

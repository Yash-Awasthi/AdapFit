"""
Advanced HRV analysis from pyhrv — frequency domain and nonlinear analysis.
"""
from dataclasses import dataclass
from typing import List
import math


@dataclass
class AdvancedHRV:
    # Time domain
    mean_rr: float = 0.0
    sdnn: float = 0.0
    rmssd: float = 0.0
    sdsd: float = 0.0
    pnn50: float = 0.0
    pnn20: float = 0.0
    # Frequency domain
    vlf_power: float = 0.0
    lf_power: float = 0.0
    hf_power: float = 0.0
    total_power: float = 0.0
    lf_nu: float = 0.0
    hf_nu: float = 0.0
    lf_hf_ratio: float = 0.0
    # Nonlinear
    sd1: float = 0.0
    sd2: float = 0.0
    sample_entropy: float = 0.0
    detrended_fluctuation: float = 0.0


def analyze_advanced_hrv(rr_intervals: List[float], fs: float = 4.0) -> AdvancedHRV:
    if len(rr_intervals) < 10:
        return AdvancedHRV()

    mean_rr = sum(rr_intervals) / len(rr_intervals)
    sdnn = math.sqrt(sum((r - mean_rr) ** 2 for r in rr_intervals) / len(rr_intervals))

    diffs = [rr_intervals[i + 1] - rr_intervals[i] for i in range(len(rr_intervals) - 1)]
    sdsd = math.sqrt(sum(d ** 2 for d in diffs) / len(diffs))
    rmssd = math.sqrt(sum(d ** 2 for d in diffs) / len(diffs))
    pnn50 = sum(1 for d in diffs if abs(d) > 50) / len(diffs) * 100
    pnn20 = sum(1 for d in diffs if abs(d) > 20) / len(diffs) * 100

    n = len(rr_intervals)
    centered = [r - mean_rr for r in rr_intervals]
    vlf = lf = hf = 0.0
    for k in range(n // 2):
        freq = k * fs / n
        real = sum(centered[i] * math.cos(2 * math.pi * k * i / n) for i in range(n))
        imag = sum(centered[i] * math.sin(2 * math.pi * k * i / n) for i in range(n))
        psd = (real ** 2 + imag ** 2) / (n * fs)
        if 0.003 <= freq < 0.04: vlf += psd
        elif 0.04 <= freq < 0.15: lf += psd
        elif 0.15 <= freq < 0.4: hf += psd

    total = lf + hf + vlf
    lf_nu = lf / (lf + hf) * 100 if (lf + hf) > 0 else 0
    hf_nu = hf / (lf + hf) * 100 if (lf + hf) > 0 else 0
    lf_hf = lf / hf if hf > 0 else 0

    sd1 = math.sqrt(sum(d ** 2 for d in diffs) / (2 * len(diffs)))
    sd2_x = [rr_intervals[i] + rr_intervals[i + 1] for i in range(len(rr_intervals) - 1)]
    sd2 = math.sqrt(sum(s ** 2 for s in sd2_x) / (2 * len(sd2_x)))

    return AdvancedHRV(
        mean_rr=round(mean_rr, 2), sdnn=round(sdnn, 2), rmssd=round(rmssd, 2),
        sdsd=round(sdsd, 2), pnn50=round(pnn50, 2), pnn20=round(pnn20, 2),
        vlf_power=round(vlf, 4), lf_power=round(lf, 4), hf_power=round(hf, 4),
        total_power=round(total, 4), lf_nu=round(lf_nu, 2), hf_nu=round(hf_nu, 2),
        lf_hf_ratio=round(lf_hf, 4), sd1=round(sd1, 2), sd2=round(sd2, 2),
    )

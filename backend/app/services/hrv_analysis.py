"""
Comprehensive HRV Analysis Service — Time domain, frequency domain, nonlinear features
Inspired by biosppy: full HRV feature extraction with detrending, outlier handling, entropy

Patterns extracted:
- Time domain: RMSSD, SDNN, NN50, pNN50, HR stats, HTI, TINN
- Frequency domain: ULF/VLF/LF/HF/VHF bands, spectral power
- Nonlinear: Poincare (SD1, SD2), sample entropy, approximate entropy
- RRI processing: outlier detection, interpolation, detrending
- HRV triangular index (geometrical)
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


@dataclass
class TimeDomainFeatures:
    hr_mean: float
    hr_min: float
    hr_max: float
    hr_std: float
    rr_mean: float
    rr_min: float
    rr_max: float
    rr_std: float
    rmssd: float
    sdnn: float
    nn50: int
    pnn50: float
    sdsd: float
    hrv_triangular_index: float
    tinn: float


@dataclass
class FrequencyDomainFeatures:
    total_power: float
    ulf_power: float
    vlf_power: float
    lf_power: float
    hf_power: float
    vhf_power: float
    lf_hf_ratio: float
    lf_norm: float
    hf_norm: float
    peak_lf: float
    peak_hf: float


@dataclass
class NonlinearFeatures:
    sd1: float
    sd2: float
    sd_ratio: float
    sample_entropy: float
    approximate_entropy: float
    detrended_fluctuation: float


@dataclass
class HRVReport:
    duration_seconds: float
    sample_count: int
    time_domain: TimeDomainFeatures
    frequency_domain: Optional[FrequencyDomainFeatures]
    nonlinear: Optional[NonlinearFeatures]
    quality_score: float  # 0-100 based on signal quality
    interpretation: str


# ── Frequency Bands (Hz) ─────────────────────────────────────────────────

FREQ_BANDS = {
    "ulf": (0.0, 0.003),
    "vlf": (0.003, 0.04),
    "lf": (0.04, 0.15),
    "hf": (0.15, 0.4),
    "vhf": (0.4, 0.5),
}


class HRVAnalyzer:
    """Pure function comprehensive HRV analysis."""

    # ── RRI Processing ────────────────────────────────────────────────────

    @staticmethod
    def compute_rri(rr_intervals_ms: List[float], min_ms: float = 300,
                    max_ms: float = 2000) -> List[float]:
        """Filter RR intervals to plausible range."""
        return [rr for rr in rr_intervals_ms if min_ms <= rr <= max_ms]

    @staticmethod
    def detect_outliers(rr_ms: List[float], threshold: float = 250) -> List[bool]:
        """Detect outlier RR intervals (diff > threshold from neighbors)."""
        if len(rr_ms) < 3:
            return [False] * len(rr_ms)
        outliers = [False] * len(rr_ms)
        for i in range(1, len(rr_ms) - 1):
            if abs(rr_ms[i] - rr_ms[i - 1]) > threshold and abs(rr_ms[i] - rr_ms[i + 1]) > threshold:
                outliers[i] = True
        return outliers

    @staticmethod
    def interpolate_outliers(rr_ms: List[float], outliers: List[bool]) -> List[float]:
        """Replace outliers with linear interpolation from neighbors."""
        result = rr_ms[:]
        for i in range(len(rr_ms)):
            if outliers[i]:
                left = right = None
                for j in range(i - 1, -1, -1):
                    if not outliers[j]:
                        left = rr_ms[j]
                        break
                for j in range(i + 1, len(rr_ms)):
                    if not outliers[j]:
                        right = rr_ms[j]
                        break
                if left is not None and right is not None:
                    result[i] = (left + right) / 2
                elif left is not None:
                    result[i] = left
                elif right is not None:
                    result[i] = right
        return result

    @staticmethod
    def detrend_linear(rr_ms: List[float]) -> Tuple[List[float], float]:
        """Remove linear trend from RR intervals."""
        n = len(rr_ms)
        if n < 2:
            return rr_ms[:], 0.0
        x_mean = (n - 1) / 2
        y_mean = sum(rr_ms) / n
        numerator = sum((i - x_mean) * (rr_ms[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator > 0 else 0.0
        detrended = [rr_ms[i] - (slope * i + (y_mean - slope * x_mean)) for i in range(n)]
        return detrended, slope

    # ── Time Domain Features ──────────────────────────────────────────────

    @classmethod
    def time_domain(cls, rr_ms: List[float]) -> TimeDomainFeatures:
        """Compute all time-domain HRV features."""
        if len(rr_ms) < 2:
            return TimeDomainFeatures(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0)

        hr = [60000.0 / rr for rr in rr_ms if rr > 0]
        diffs = [rr_ms[i + 1] - rr_ms[i] for i in range(len(rr_ms) - 1)]
        abs_diffs = [abs(d) for d in diffs]

        # RMSSD
        rmssd = math.sqrt(sum(d ** 2 for d in diffs) / len(diffs))

        # SDNN
        mean_rr = sum(rr_ms) / len(rr_ms)
        sdnn = math.sqrt(sum((rr - mean_rr) ** 2 for rr in rr_ms) / len(rr_ms))

        # NN50, pNN50
        nn50 = sum(1 for d in abs_diffs if d > 50)
        pnn50 = (nn50 / len(abs_diffs) * 100) if abs_diffs else 0.0

        # SDSD
        sdsd = math.sqrt(sum(d ** 2 for d in diffs) / len(diffs)) if diffs else 0.0

        # HTI (triangular index) — simplified
        binsize = int(round(1000 / 7.8125))  # 7.8125 ms bin width
        if binsize > 0:
            min_rr = int(min(rr_ms))
            max_rr = int(max(rr_ms))
            hist = [0] * max(1, (max_rr - min_rr) // binsize + 1)
            for rr in rr_ms:
                idx = min(len(hist) - 1, max(0, (int(rr) - min_rr) // binsize))
                hist[idx] += 1
            max_bin = max(hist) if hist else 1
            hrv_tri = len(rr_ms) / max_bin if max_bin > 0 else 0
        else:
            hrv_tri = 0

        # TINN (simplified)
        tinn = max_rr - min_rr if len(rr_ms) > 1 else 0

        return TimeDomainFeatures(
            hr_mean=round(sum(hr) / len(hr), 1) if hr else 0,
            hr_min=round(min(hr), 1) if hr else 0,
            hr_max=round(max(hr), 1) if hr else 0,
            hr_std=round(math.sqrt(sum((h - sum(hr) / len(hr)) ** 2 for h in hr) / len(hr)), 2) if hr else 0,
            rr_mean=round(mean_rr, 2),
            rr_min=round(min(rr_ms), 2),
            rr_max=round(max(rr_ms), 2),
            rr_std=round(sdnn, 2),
            rmssd=round(rmssd, 2),
            sdnn=round(sdnn, 2),
            nn50=nn50,
            pnn50=round(pnn50, 2),
            sdsd=round(sdsd, 2),
            hrv_triangular_index=round(hrv_tri, 2),
            tinn=round(tinn, 2),
        )

    # ── Frequency Domain Features ─────────────────────────────────────────

    @staticmethod
    def frequency_domain(rr_ms: List[float], sampling_rate: float = 4.0) -> FrequencyDomainFeatures:
        """Compute frequency-domain HRV features using periodogram."""
        if len(rr_ms) < 16:
            return FrequencyDomainFeatures(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

        # Interpolate to uniform sampling
        n = len(rr_ms)
        t = [sum(rr_ms[:i]) / 1000.0 for i in range(n)]  # cumulative time in seconds
        uniform_t = [t[0] + i / sampling_rate for i in range(int((t[-1] - t[0]) * sampling_rate))]
        if len(uniform_t) < 16:
            return FrequencyDomainFeatures(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

        # Simple linear interpolation
        uniform_rr = []
        for ut in uniform_t:
            # Find bracketing indices
            idx = 0
            for i in range(len(t) - 1):
                if t[i] <= ut <= t[i + 1]:
                    idx = i
                    break
            if t[idx + 1] - t[idx] > 0:
                frac = (ut - t[idx]) / (t[idx + 1] - t[idx])
                val = rr_ms[idx] + frac * (rr_ms[idx + 1] - rr_ms[idx])
            else:
                val = rr_ms[idx]
            uniform_rr.append(val)

        # Detrend
        mean_val = sum(uniform_rr) / len(uniform_rr)
        detrended = [rr - mean_val for rr in uniform_rr]

        # Compute periodogram (simplified FFT)
        ns = len(detrended)
        freqs = [i * sampling_rate / ns for i in range(ns // 2)]
        powers = []
        for k in range(ns // 2):
            re = sum(detrended[n] * math.cos(2 * math.pi * k * n / ns) for n in range(ns))
            im = sum(detrended[n] * math.sin(2 * math.pi * k * n / ns) for n in range(ns))
            powers.append((re ** 2 + im ** 2) / ns)

        # Band powers
        band_powers = {}
        for band_name, (low, high) in FREQ_BANDS.items():
            power = sum(powers[i] for i in range(len(freqs))
                       if low <= freqs[i] <= high)
            band_powers[band_name] = power

        total_power = sum(band_powers.values())
        lf = band_powers.get("lf", 0)
        hf = band_powers.get("hf", 0)
        lf_hf = lf / hf if hf > 0 else 0
        lf_norm = (lf / (lf + hf) * 100) if (lf + hf) > 0 else 0
        hf_norm = (hf / (lf + hf) * 100) if (lf + hf) > 0 else 0

        # Peak frequencies
        peak_lf = 0
        peak_hf = 0
        max_lf = 0
        max_hf = 0
        for i, f in enumerate(freqs):
            if 0.04 <= f <= 0.15 and powers[i] > max_lf:
                max_lf = powers[i]
                peak_lf = f
            if 0.15 < f <= 0.4 and powers[i] > max_hf:
                max_hf = powers[i]
                peak_hf = f

        return FrequencyDomainFeatures(
            total_power=round(total_power, 2),
            ulf_power=round(band_powers.get("ulf", 0), 2),
            vlf_power=round(band_powers.get("vlf", 0), 2),
            lf_power=round(lf, 2),
            hf_power=round(hf, 2),
            vhf_power=round(band_powers.get("vhf", 0), 2),
            lf_hf_ratio=round(lf_hf, 3),
            lf_norm=round(lf_norm, 2),
            hf_norm=round(hf_norm, 2),
            peak_lf=round(peak_lf, 4),
            peak_hf=round(peak_hf, 4),
        )

    # ── Nonlinear Features ────────────────────────────────────────────────

    @staticmethod
    def poincare(rr_ms: List[float]) -> Tuple[float, float]:
        """Compute Poincare plot features (SD1, SD2)."""
        if len(rr_ms) < 3:
            return 0.0, 0.0
        diffs = [rr_ms[i + 1] - rr_ms[i] for i in range(len(rr_ms) - 1)]
        sd1 = math.sqrt(sum(d ** 2 for d in diffs) / (2 * len(diffs)))
        sd2 = math.sqrt(2 * sum(rr_ms[i] ** 2 + rr_ms[i + 1] ** 2
                               for i in range(len(rr_ms) - 1)) / (2 * len(diffs)) - sd1 ** 2)
        return round(sd1, 2), round(abs(sd2), 2)

    @staticmethod
    def sample_entropy(rr_ms: List[float], m: int = 2, r: float = 0.2) -> float:
        """Approximate sample entropy (SampEn)."""
        if len(rr_ms) < 30:
            return float('nan')
        mean_rr = sum(rr_ms) / len(rr_ms)
        std_rr = math.sqrt(sum((rr - mean_rr) ** 2 for rr in rr_ms) / len(rr_ms))
        if std_rr == 0:
            return float('nan')
        threshold = r * std_rr

        def count_matches(seq, m_val, thresh):
            count = 0
            n = len(seq)
            for i in range(n - m_val):
                for j in range(i + 1, n - m_val):
                    if all(abs(seq[i + k] - seq[j + k]) < thresh for k in range(m_val)):
                        count += 1
            return count

        a = count_matches(rr_ms, m + 1, threshold)
        b = count_matches(rr_ms, m, threshold)
        if a == 0 or b == 0:
            return float('nan')
        return round(-math.log(a / b), 4)

    @staticmethod
    def approximate_entropy(rr_ms: List[float], m: int = 2, r: float = 0.2) -> float:
        """Approximate entropy (ApEn)."""
        if len(rr_ms) < 30:
            return float('nan')
        mean_rr = sum(rr_ms) / len(rr_ms)
        std_rr = math.sqrt(sum((rr - mean_rr) ** 2 for rr in rr_ms) / len(rr_ms))
        if std_rr == 0:
            return float('nan')
        threshold = r * std_rr
        n = len(rr_ms)

        def phi(m_val):
            count = 0
            for i in range(n - m_val + 1):
                template = rr_ms[i:i + m_val]
                for j in range(n - m_val + 1):
                    other = rr_ms[j:j + m_val]
                    if all(abs(template[k] - other[k]) < threshold for k in range(m_val)):
                        count += 1
            if count == 0:
                return 0
            return math.log(count / (n - m_val + 1))

        return round(phi(m) - phi(m + 1), 4)

    @classmethod
    def nonlinear(cls, rr_ms: List[float]) -> NonlinearFeatures:
        """Compute nonlinear HRV features."""
        sd1, sd2 = cls.poincare(rr_ms)
        sd_ratio = sd1 / sd2 if sd2 > 0 else 0
        samp_en = cls.sample_entropy(rr_ms)
        apen = cls.approximate_entropy(rr_ms)
        # Simplified DFA
        dfa = 0.0
        if len(rr_ms) >= 20:
            mean_rr = sum(rr_ms) / len(rr_ms)
            cumsum = [0]
            for rr in rr_ms:
                cumsum.append(cumsum[-1] + rr - mean_rr)
            # Simple fluctuation at scale 10
            scale = min(10, len(cumsum) // 2)
            if scale > 1:
                fluct = math.sqrt(sum((cumsum[i] - cumsum[i - scale]) ** 2
                                     for i in range(scale, len(cumsum))) / (len(cumsum) - scale))
                dfa = round(fluct / max(std_rr, 0.001), 4) if (std_rr := math.sqrt(sum((rr - mean_rr) ** 2 for rr in rr_ms) / len(rr_ms))) > 0 else 0

        return NonlinearFeatures(
            sd1=sd1, sd2=sd2, sd_ratio=round(sd_ratio, 3),
            sample_entropy=samp_en, approximate_entropy=apen,
            detrended_fluctuation=dfa,
        )

    # ── Quality Assessment ────────────────────────────────────────────────

    @staticmethod
    def signal_quality(rr_ms: List[float]) -> float:
        """Assess signal quality (0-100) based on outlier ratio and duration."""
        if not rr_ms:
            return 0.0
        valid = [rr for rr in rr_ms if 300 <= rr <= 2000]
        outlier_ratio = 1 - len(valid) / len(rr_ms)
        duration_score = min(1.0, len(rr_ms) / 300)  # 5 minutes = full score
        quality = (1 - outlier_ratio) * 70 + duration_score * 30
        return round(max(0, min(100, quality)), 1)

    # ── Main Analysis ─────────────────────────────────────────────────────

    @classmethod
    def analyze(cls, rr_intervals_ms: List[float]) -> Optional[HRVReport]:
        """Full HRV analysis from RR intervals."""
        if not rr_intervals_ms or len(rr_intervals_ms) < 10:
            return None

        # Process RRI
        rr = cls.compute_rri(rr_intervals_ms)
        if len(rr) < 10:
            return None

        # Duration
        duration = sum(rr) / 1000.0

        # Time domain
        td = cls.time_domain(rr)

        # Frequency domain (need >= 2.5 min for reliable LF/HF)
        fd = cls.frequency_domain(rr) if duration >= 60 else None

        # Nonlinear (need >= 30 samples)
        nl = cls.nonlinear(rr) if len(rr) >= 30 else None

        # Quality
        quality = cls.signal_quality(rr)

        # Interpretation
        interp = cls._interpret(td, fd, nl, quality)

        return HRVReport(
            duration_seconds=round(duration, 1),
            sample_count=len(rr),
            time_domain=td,
            frequency_domain=fd,
            nonlinear=nl,
            quality_score=quality,
            interpretation=interp,
        )

    @staticmethod
    def _interpret(td, fd, nl, quality) -> str:
        parts = []
        if quality < 50:
            parts.append("⚠️ Low signal quality — results may be unreliable")
        if td.rmssd > 50:
            parts.append("High parasympathetic activity (relaxed)")
        elif td.rmssd < 20:
            parts.append("Low parasympathetic activity (stressed/fatigued)")
        if fd:
            if fd.lf_hf_ratio > 2.0:
                parts.append("Sympathetic dominance (stress/alertness)")
            elif fd.lf_hf_ratio < 0.5:
                parts.append("Parasympathetic dominance (recovery/rest)")
        if td.sdnn < 20:
            parts.append("Low overall HRV — possible overtraining or illness")
        if not parts:
            parts.append("HRV within normal range")
        return "; ".join(parts)

    @staticmethod
    def get_hrv_reference() -> Dict:
        return {
            "time_domain": {
                "rmssd_normal": {"young": "27-45 ms", "adult": "19-35 ms", "elderly": "10-25 ms"},
                "sdnn_normal": {"healthy": "30-100 ms"},
                "pnn50_normal": {"healthy": "> 5%"},
            },
            "frequency_domain": {
                "lf_range": "0.04-0.15 Hz (baroreflex, mixed sympatho-parasympathetic)",
                "hf_range": "0.15-0.4 Hz (parasympathetic / respiratory sinus arrhythmia)",
                "lf_hf_ratio_interpretation": {
                    "< 0.5": "Parasympathetic dominance",
                    "0.5-2.0": "Balanced",
                    "> 2.0": "Sympathetic dominance",
                },
            },
            "nonlinear": {
                "sd1": "Short-term variability (similar to RMSSD)",
                "sd2": "Long-term variability (overall HRV)",
                "sample_entropy": "Complexity of heart rhythm (higher = healthier)",
            },
        }

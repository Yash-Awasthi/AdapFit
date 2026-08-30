"""
Drowsiness & Fatigue Detection Service — Multi-signal alertness recognition
Inspired by alertness-recognition: HRV stress staging, EDA arousal, calibration

Patterns extracted:
- HRV-based stress staging from RMSSD thresholds (inverted: high RMSSD = low stress)
- EDA arousal detection from skin conductance (relative to personal baseline)
- Multi-signal alertness scoring combining HRV, blink, head pose, EDA
- Calibration baseline management
- Plausible RR interval filtering for HRV accuracy
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class AlertnessLevel(Enum):
    ALERT = "alert"
    SLIGHTLY_DROWSY = "slightly_drowsy"
    DROWSY = "drowsy"
    VERY_DROWSY = "very_drowsy"
    ASLEEP = "asleep"


class StressLevel(Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class BioSignal:
    timestamp: float
    heart_rate: float
    rr_intervals_ms: List[float]
    eda_signal: float = 0.0  # skin conductance (microsiemens)
    blink_rate: float = 0.0  # blinks per minute
    head_pitch: float = 0.0  # degrees from vertical (positive = nodding)
    eye_aspect_ratio: float = 0.3  # EAR (lower = more closed)


@dataclass
class CalibrationBaseline:
    resting_rmssd: float = 40.0
    resting_eda: float = 2.0
    resting_blink_rate: float = 15.0
    resting_ear: float = 0.3
    resting_hr: float = 65.0
    samples_collected: int = 0


@dataclass
class AlertnessResult:
    timestamp: float
    alertness_level: AlertnessLevel
    alertness_score: float  # 0-100 (100 = fully alert)
    stress_level: StressLevel
    stress_score: float  # 0-100 (100 = max stress)
    rmssd: float
    eda_arousal: float
    blink_score: float
    head_pose_score: float
    eye_closing_score: float
    recommendations: List[str]


# ── HRV Constants ─────────────────────────────────────────────────────────

LEVELS = ["none", "low", "medium", "high"]

# Default RMSSD thresholds (ms) — descending order (high RMSSD = low stress)
DEFAULT_RMSSD_THRESHOLDS = [50.0, 35.0, 20.0]

# Physiological RR interval bounds
MIN_RR_MS = 300.0
MAX_RR_MS = 2000.0
MAX_RR_DEVIATION = 0.25


class DrowsinessDetector:
    """Pure function drowsiness and fatigue detection from bio signals."""

    # ── HRV Processing ────────────────────────────────────────────────────

    @staticmethod
    def rr_intervals_from_peaks(peak_times_s: List[float]) -> List[float]:
        """Convert peak times (seconds) to RR intervals (milliseconds)."""
        if len(peak_times_s) < 2:
            return []
        sorted_times = sorted(peak_times_s)
        return [(sorted_times[i + 1] - sorted_times[i]) * 1000.0
                for i in range(len(sorted_times) - 1)]

    @staticmethod
    def filter_plausible_rr(rr_ms: List[float]) -> List[bool]:
        """Filter RR intervals for physiological plausibility."""
        if not rr_ms:
            return []
        in_range = [MIN_RR_MS <= rr <= MAX_RR_MS for rr in rr_ms]
        if not any(in_range):
            return in_range
        in_range_vals = [rr for rr, ok in zip(rr_ms, in_range) if ok]
        if not in_range_vals:
            return in_range
        median = sorted(in_range_vals)[len(in_range_vals) // 2]
        if median <= 0:
            return in_range
        return [ok and abs(rr - median) <= MAX_RR_DEVIATION * median
                for rr, ok in zip(rr_ms, in_range)]

    @staticmethod
    def calculate_rmssd(rr_ms: List[float], valid: Optional[List[bool]] = None) -> float:
        """Calculate RMSSD (Root Mean Square of Successive Differences) in ms."""
        if len(rr_ms) < 2:
            return float('nan')
        diffs = [rr_ms[i + 1] - rr_ms[i] for i in range(len(rr_ms) - 1)]
        if valid is not None:
            usable = [i for i in range(len(diffs))
                     if valid[i] and valid[i + 1]]
            if not usable:
                return float('nan')
            diffs = [diffs[i] for i in usable]
        if not diffs:
            return float('nan')
        mean_sq = sum(d ** 2 for d in diffs) / len(diffs)
        return math.sqrt(mean_sq)

    @staticmethod
    def calculate_sdnn(rr_ms: List[float]) -> float:
        """Calculate SDNN (Standard Deviation of NN intervals) in ms."""
        if len(rr_ms) < 2:
            return float('nan')
        mean = sum(rr_ms) / len(rr_ms)
        variance = sum((rr - mean) ** 2 for rr in rr_ms) / (len(rr_ms) - 1)
        return math.sqrt(variance)

    @staticmethod
    def calculate_pnn50(rr_ms: List[float]) -> float:
        """Calculate pNN50 — percentage of successive RR diffs > 50ms."""
        if len(rr_ms) < 2:
            return float('nan')
        diffs = [abs(rr_ms[i + 1] - rr_ms[i]) for i in range(len(rr_ms) - 1)]
        return sum(1 for d in diffs if d > 50) / len(diffs)

    @staticmethod
    def mean_hr(rr_ms: List[float]) -> float:
        """Calculate mean heart rate in bpm."""
        if not rr_ms:
            return float('nan')
        mean_rr = sum(rr_ms) / len(rr_ms)
        if mean_rr <= 0:
            return float('nan')
        return 60000.0 / mean_rr

    # ── Stress Staging ────────────────────────────────────────────────────

    @staticmethod
    def stage_from_rmssd(rmssd_ms: float,
                        thresholds: List[float] = None,
                        levels: List[str] = None) -> str:
        """RMSSD → stress stage. High RMSSD = low stress (inverted mapping)."""
        thresholds = thresholds or DEFAULT_RMSSD_THRESHOLDS
        levels = levels or LEVELS
        if len(thresholds) != len(levels) - 1:
            raise ValueError("thresholds must have len(levels) - 1 entries")
        if math.isnan(rmssd_ms):
            return ""
        for level, t in zip(levels, thresholds):
            if rmssd_ms >= t:
                return level
        return levels[-1]

    @staticmethod
    def rmssd_to_stress_score(rmssd_ms: float, baseline_rmssd: float = 40.0) -> float:
        """Convert RMSSD to 0-100 stress score (lower RMSSD = higher stress)."""
        if math.isnan(rmssd_ms) or baseline_rmssd <= 0:
            return 50.0
        ratio = rmssd_ms / baseline_rmssd
        score = max(0, min(100, (1 - ratio) * 100 + 50))
        return round(score, 1)

    # ── EDA Arousal ───────────────────────────────────────────────────────

    @staticmethod
    def eda_relative_arousal(current_eda: float, baseline_eda: float,
                            spread: float = 1.0) -> float:
        """EDA arousal relative to personal baseline (0=rest, 1=highly aroused)."""
        if spread <= 0:
            return 0.0
        return max(0.0, min(1.0, (current_eda - baseline_eda) / spread))

    @staticmethod
    def eda_to_stress_score(arousal: float) -> float:
        """Convert EDA arousal (0-1) to stress score (0-100)."""
        return round(arousal * 100, 1)

    # ── Blink Analysis ────────────────────────────────────────────────────

    @staticmethod
    def blink_rate_score(blink_rate: float, baseline: float = 15.0) -> float:
        """Score blink rate for drowsiness (0-100, higher = more drowsy).
        
        Drowsy: increased blink rate or prolonged eye closure.
        Very drowsy: reduced blink rate (fighting sleep).
        """
        if baseline <= 0:
            return 50.0
        ratio = blink_rate / baseline
        if ratio > 1.5:
            # Very high blink rate = fighting drowsiness
            return min(100, (ratio - 1) * 80)
        elif ratio < 0.5:
            # Very low blink rate = eyes closing / microsleeps
            return min(100, (1 - ratio) * 120)
        elif ratio > 1.2:
            return min(100, (ratio - 1) * 60)
        return 0.0

    # ── Eye Aspect Ratio (EAR) ────────────────────────────────────────────

    @staticmethod
    def ear_drowsiness_score(ear: float, baseline: float = 0.3) -> float:
        """EAR-based drowsiness score (0-100, lower EAR = more drowsy)."""
        if baseline <= 0:
            return 50.0
        ratio = ear / baseline
        if ratio < 0.5:
            return 100.0  # Eyes nearly closed
        elif ratio < 0.7:
            return 80.0
        elif ratio < 0.85:
            return 50.0
        elif ratio < 1.0:
            return 20.0
        return 0.0

    # ── Head Pose ─────────────────────────────────────────────────────────

    @staticmethod
    def head_pose_drowsiness_score(pitch: float) -> float:
        """Head nodding score (0-100, higher pitch = more drowsy)."""
        abs_pitch = abs(pitch)
        if abs_pitch > 30:
            return 100.0  # Head dropped
        elif abs_pitch > 20:
            return 80.0
        elif abs_pitch > 10:
            return 50.0
        elif abs_pitch > 5:
            return 20.0
        return 0.0

    # ── Calibration ───────────────────────────────────────────────────────

    @staticmethod
    def calibrate(baseline_signals: List[BioSignal]) -> CalibrationBaseline:
        """Create calibration baseline from resting-state signals."""
        if not baseline_signals:
            return CalibrationBaseline()
        rmsds = []
        edas = []
        blink_rates = []
        ears = []
        hrs = []
        for sig in baseline_signals:
            if sig.rr_intervals_ms and len(sig.rr_intervals_ms) >= 2:
                valid = DrowsinessDetector.filter_plausible_rr(sig.rr_intervals_ms)
                rmssd = DrowsinessDetector.calculate_rmssd(sig.rr_intervals_ms, valid)
                if not math.isnan(rmssd):
                    rmsds.append(rmssd)
            edas.append(sig.eda_signal)
            blink_rates.append(sig.blink_rate)
            ears.append(sig.eye_aspect_ratio)
            hrs.append(sig.heart_rate)
        return CalibrationBaseline(
            resting_rmssd=sum(rmsds) / len(rmsds) if rmsds else 40.0,
            resting_eda=sum(edas) / len(edas) if edas else 2.0,
            resting_blink_rate=sum(blink_rates) / len(blink_rates) if blink_rates else 15.0,
            resting_ear=sum(ears) / len(ears) if ears else 0.3,
            resting_hr=sum(hrs) / len(hrs) if hrs else 65.0,
            samples_collected=len(baseline_signals),
        )

    # ── Main Analysis ─────────────────────────────────────────────────────

    @classmethod
    def analyze(cls, signal: BioSignal,
                baseline: Optional[CalibrationBaseline] = None) -> AlertnessResult:
        """Full alertness analysis from a single bio signal snapshot."""
        baseline = baseline or CalibrationBaseline()

        # HRV analysis
        valid_rr = cls.filter_plausible_rr(signal.rr_intervals_ms) if signal.rr_intervals_ms else []
        rmssd = cls.calculate_rmssd(signal.rr_intervals_ms, valid_rr) if signal.rr_intervals_ms else float('nan')
        stress_stage = cls.stage_from_rmssd(rmssd) if not math.isnan(rmssd) else "medium"
        hrv_stress = cls.rmssd_to_stress_score(rmssd, baseline.resting_rmssd)

        # EDA arousal
        eda_baseline_spread = max(1.0, baseline.resting_eda * 0.5)
        eda_arousal = cls.eda_relative_arousal(signal.eda_signal, baseline.resting_eda, eda_baseline_spread)
        eda_stress = cls.eda_to_stress_score(eda_arousal)

        # Blink analysis
        blink_score = cls.blink_rate_score(signal.blink_rate, baseline.resting_blink_rate)

        # EAR analysis
        ear_score = cls.ear_drowsiness_score(signal.eye_aspect_ratio, baseline.resting_ear)

        # Head pose
        head_score = cls.head_pose_drowsiness_score(signal.head_pitch)

        # Composite drowsiness score (0=alert, 100=asleep)
        drowsiness = (
            blink_score * 0.25 +
            ear_score * 0.30 +
            head_score * 0.25 +
            (100 - hrv_stress) * 0.10 +  # Low HRV = drowsy, not stressed
            eda_stress * 0.10  # Low EDA = drowsy
        )
        drowsiness = max(0, min(100, drowsiness))

        # Alertness is inverse of drowsiness
        alertness_score = round(100 - drowsiness, 1)

        # Alertness level
        if alertness_score >= 80:
            alertness_level = AlertnessLevel.ALERT
        elif alertness_score >= 60:
            alertness_level = AlertnessLevel.SLIGHTLY_DROWSY
        elif alertness_score >= 40:
            alertness_level = AlertnessLevel.DROWSY
        elif alertness_score >= 20:
            alertness_level = AlertnessLevel.VERY_DROWSY
        else:
            alertness_level = AlertnessLevel.ASLEEP

        # Stress level from HRV + EDA
        combined_stress = (hrv_stress * 0.6 + eda_stress * 0.4)
        if combined_stress >= 70:
            stress_level = StressLevel.HIGH
        elif combined_stress >= 45:
            stress_level = StressLevel.MEDIUM
        elif combined_stress >= 20:
            stress_level = StressLevel.LOW
        else:
            stress_level = StressLevel.NONE

        # Recommendations
        recs = []
        if alertness_score < 40:
            recs.append("⚠️ DROWSINESS DETECTED — Consider taking a break")
        if alertness_score < 20:
            recs.append("🚨 CRITICAL: Pull over or stop driving immediately")
        if head_score > 50:
            recs.append("Head nodding detected — signs of microsleep")
        if ear_score > 60:
            recs.append("Eyes closing frequently — severe drowsiness")
        if blink_score > 40:
            recs.append("Abnormal blink pattern — fatigue detected")
        if not recs:
            recs.append("✅ Alertness level normal")

        return AlertnessResult(
            timestamp=signal.timestamp,
            alertness_level=alertness_level,
            alertness_score=alertness_score,
            stress_level=stress_level,
            stress_score=round(combined_stress, 1),
            rmssd=round(rmssd, 2) if not math.isnan(rmssd) else 0.0,
            eda_arousal=round(eda_arousal, 3),
            blink_score=round(blink_score, 1),
            head_pose_score=round(head_score, 1),
            eye_closing_score=round(ear_score, 1),
            recommendations=recs,
        )

    @classmethod
    def analyze_series(cls, signals: List[BioSignal],
                      baseline: Optional[CalibrationBaseline] = None) -> List[AlertnessResult]:
        """Analyze a time series of bio signals."""
        baseline = baseline or CalibrationBaseline()
        return [cls.analyze(sig, baseline) for sig in signals]

    @staticmethod
    def get_alertness_info() -> Dict:
        """Return alertness level descriptions."""
        return {
            "levels": {
                "alert": {"score_range": "80-100", "meaning": "Fully awake and attentive"},
                "slightly_drowsy": {"score_range": "60-79", "meaning": "Mild fatigue, should monitor"},
                "drowsy": {"score_range": "40-59", "meaning": "Significant drowsiness, take break"},
                "very_drowsy": {"score_range": "20-39", "meaning": "Severe drowsiness, stop activity"},
                "asleep": {"score_range": "0-19", "meaning": "Falling asleep or microsleep"},
            },
            "hrv_thresholds": {
                "high_rmssd": "Low stress (relaxed)",
                "low_rmssd": "High stress (sympathetic activation)",
            },
        }

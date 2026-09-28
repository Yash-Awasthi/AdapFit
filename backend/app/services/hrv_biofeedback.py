"""
HRV Biofeedback Service — Inspired by OpenHRV
Real-time HRV biofeedback training with guided breathing and coherence scoring
"""

import math
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class BreathingPhase(Enum):
    INHALE = "inhale"
    EXHALE = "exhale"
    HOLD = "hold"


class CoherenceLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class BreathingPattern:
    name: str
    inhale_seconds: float
    exhale_seconds: float
    hold_in_seconds: float = 0.0
    hold_out_seconds: float = 0.0
    description: str = ""

    @property
    def cycle_length(self) -> float:
        return (self.inhale_seconds + self.exhale_seconds +
                self.hold_in_seconds + self.hold_out_seconds)

    @property
    def breaths_per_minute(self) -> float:
        if self.cycle_length > 0:
            return 60.0 / self.cycle_length
        return 0.0


@dataclass
class HRVSample:
    timestamp: float
    rr_interval_ms: float
    heart_rate: float


@dataclass
class CoherenceResult:
    score: float
    level: CoherenceLevel
    lf_power: float
    hf_power: float
    lf_hf_ratio: float
    rmssd: float
    breathing_rate: float


@dataclass
class BiofeedbackSession:
    session_id: str
    start_time: float
    pattern: BreathingPattern
    samples: List[HRVSample] = field(default_factory=list)
    coherence_scores: List[CoherenceResult] = field(default_factory=list)
    end_time: Optional[float] = None


class HRVBiofeedbackAnalyzer:
    """Pure function analyzer for HRV biofeedback training."""

    # Standard breathing patterns
    PATTERNS = {
        "calm": BreathingPattern(
            name="calm",
            inhale_seconds=4.0,
            exhale_seconds=6.0,
            description="Relaxing 6 BPM pattern"
        ),
        "coherence": BreathingPattern(
            name="coherence",
            inhale_seconds=5.5,
            exhale_seconds=5.5,
            description="5.5 BPM coherence breathing"
        ),
        "energize": BreathingPattern(
            name="energize",
            inhale_seconds=3.0,
            exhale_seconds=3.0,
            description="10 BPM energizing pattern"
        ),
        "sleep": BreathingPattern(
            name="sleep",
            inhale_seconds=4.0,
            exhale_seconds=8.0,
            hold_in_seconds=7.0,
            description="4-7-8 sleep pattern"
        ),
        "box": BreathingPattern(
            name="box",
            inhale_seconds=4.0,
            exhale_seconds=4.0,
            hold_in_seconds=4.0,
            hold_out_seconds=4.0,
            description="Box breathing for focus"
        ),
    }

    @staticmethod
    def calculate_rmssd(rr_intervals_ms: List[float]) -> float:
        if len(rr_intervals_ms) < 2:
            return 0.0
        squared_diffs = []
        for i in range(1, len(rr_intervals_ms)):
            diff = rr_intervals_ms[i] - rr_intervals_ms[i - 1]
            squared_diffs.append(diff ** 2)
        mean_squared = sum(squared_diffs) / len(squared_diffs)
        return math.sqrt(mean_squared)

    @staticmethod
    def calculate_sdnn(rr_intervals_ms: List[float]) -> float:
        if len(rr_intervals_ms) < 2:
            return 0.0
        mean_rr = sum(rr_intervals_ms) / len(rr_intervals_ms)
        squared_diffs = [(rr - mean_rr) ** 2 for rr in rr_intervals_ms]
        return math.sqrt(sum(squared_diffs) / len(squared_diffs))

    @staticmethod
    def calculate_lf_hf_ratio(rr_intervals_ms: List[float], sampling_rate: float = 4.0) -> Tuple[float, float, float]:
        if len(rr_intervals_ms) < 8:
            return 0.0, 0.0, 0.0
        n = len(rr_intervals_ms)
        mean_rr = sum(rr_intervals_ms) / n
        detrended = [rr - mean_rr for rr in rr_intervals_ms]
        low_freq_power = 0.0
        high_freq_power = 0.0
        for i in range(n):
            freq = (i * sampling_rate) / n
            re = sum(detrended[j] * math.cos(2 * math.pi * freq * j / sampling_rate)
                     for j in range(n))
            im = sum(detrended[j] * math.sin(2 * math.pi * freq * j / sampling_rate)
                     for j in range(n))
            power = (re ** 2 + im ** 2) / n
            if 0.04 <= freq <= 0.15:
                low_freq_power += power
            elif 0.15 < freq <= 0.4:
                high_freq_power += power
        hf = max(high_freq_power, 0.001)
        lf_hf = low_freq_power / hf
        return low_freq_power, high_freq_power, lf_hf

    @staticmethod
    def estimate_breathing_rate(rr_intervals_ms: List[float], window_seconds: float = 60.0) -> float:
        if len(rr_intervals_ms) < 4:
            return 0.0
        total_time = sum(rr_intervals_ms) / 1000.0
        if total_time <= 0:
            return 0.0
        mean_rr = sum(rr_intervals_ms) / len(rr_intervals_ms)
        crossings = 0
        for i in range(1, len(rr_intervals_ms)):
            if ((rr_intervals_ms[i] > mean_rr) != (rr_intervals_ms[i - 1] > mean_rr)):
                crossings += 1
        breathing_cycles = crossings / 2.0
        duration = total_time
        return (breathing_cycles / duration) * 60.0

    @staticmethod
    def score_coherence(rmssd: float, lf_hf_ratio: float, breathing_rate: float,
                       target_bpm: float = 5.5) -> CoherenceResult:
        rmssd_score = min(1.0, rmssd / 50.0)
        lf_hf_score = 1.0 - min(1.0, abs(lf_hf_ratio - 1.5) / 3.0)
        target_diff = abs(breathing_rate - target_bpm)
        breath_score = max(0.0, 1.0 - target_diff / 5.0)
        coherence_score = (rmssd_score * 0.4 + lf_hf_score * 0.3 + breath_score * 0.3)
        coherence_score = max(0.0, min(1.0, coherence_score))
        if coherence_score >= 0.7:
            level = CoherenceLevel.HIGH
        elif coherence_score >= 0.4:
            level = CoherenceLevel.MEDIUM
        else:
            level = CoherenceLevel.LOW
        return CoherenceResult(
            score=coherence_score,
            level=level,
            lf_power=lf_hf_ratio * 100,
            hf_power=100.0,
            lf_hf_ratio=lf_hf_ratio,
            rmssd=rmssd,
            breathing_rate=breathing_rate
        )

    @classmethod
    def analyze_breathing_session(cls, samples: List[HRVSample],
                                  pattern: BreathingPattern) -> Dict:
        if not samples:
            return {"error": "No samples provided"}
        rr_intervals = [s.rr_interval_ms for s in samples]
        rmssd = cls.calculate_rmssd(rr_intervals)
        sdnn = cls.calculate_sdnn(rr_intervals)
        lf, hf, lf_hf = cls.calculate_lf_hf_ratio(rr_intervals)
        breathing_rate = cls.estimate_breathing_rate(rr_intervals)
        coherence = cls.score_coherence(rmssd, lf_hf, breathing_rate, pattern.breaths_per_minute)
        total_time = (samples[-1].timestamp - samples[0].timestamp) / 1000.0
        hr_values = [s.heart_rate for s in samples]
        avg_hr = sum(hr_values) / len(hr_values)
        min_hr = min(hr_values)
        max_hr = max(hr_values)
        coherence_scores = [c.score for c in [coherence]]
        avg_coherence = sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0.0
        return {
            "duration_seconds": total_time,
            "sample_count": len(samples),
            "rmssd": round(rmssd, 2),
            "sdnn": round(sdnn, 2),
            "lf_power": round(lf, 2),
            "hf_power": round(hf, 2),
            "lf_hf_ratio": round(lf_hf, 2),
            "breathing_rate_bpm": round(breathing_rate, 1),
            "coherence_score": round(coherence.score, 3),
            "coherence_level": coherence.level.value,
            "heart_rate": {
                "average": round(avg_hr, 1),
                "min": round(min_hr, 1),
                "max": round(max_hr, 1)
            },
            "pattern": pattern.name,
            "target_bpm": pattern.breaths_per_minute
        }

    @classmethod
    def get_recommended_pattern(cls, stress_level: float, goal: str = "relax") -> BreathingPattern:
        if goal == "sleep":
            return cls.PATTERNS["sleep"]
        elif goal == "focus":
            return cls.PATTERNS["box"]
        elif goal == "energize":
            return cls.PATTERNS["energize"]
        elif stress_level > 0.7:
            return cls.PATTERNS["calm"]
        elif stress_level > 0.4:
            return cls.PATTERNS["coherence"]
        else:
            return cls.PATTERNS["energize"]

    @staticmethod
    def calculate_coherence_trend(scores: List[float], window: int = 5) -> Dict:
        if len(scores) < 2:
            return {"trend": "insufficient_data", "slope": 0.0}
        if len(scores) < window:
            window = max(2, len(scores))
        recent = scores[-window:]
        older = scores[:window] if len(scores) > window else scores[:1]
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        x_vals = list(range(len(recent)))
        x_mean = sum(x_vals) / len(x_vals)
        y_mean = sum(recent) / len(recent)
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, recent))
        denominator = sum((x - x_mean) ** 2 for x in x_vals)
        slope = numerator / denominator if denominator > 0 else 0.0
        if slope > 0.01:
            trend = "improving"
        elif slope < -0.01:
            trend = "declining"
        else:
            trend = "stable"
        return {
            "trend": trend,
            "slope": round(slope, 4),
            "recent_average": round(recent_avg, 3),
            "older_average": round(older_avg, 3),
            "change": round(recent_avg - older_avg, 3)
        }

    @staticmethod
    def generate_session_summary(session: BiofeedbackSession) -> Dict:
        if not session.samples:
            return {"error": "Empty session"}
        durations = []
        for i in range(1, len(session.samples)):
            durations.append(session.samples[i].timestamp - session.samples[i - 1].timestamp)
        avg_ibi = sum(durations) / len(durations) if durations else 0
        coherence_scores = [c.score for c in session.coherence_scores]
        avg_coherence = sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0.0
        high_coherence_pct = (
            sum(1 for s in coherence_scores if s >= 0.7) / len(coherence_scores) * 100
            if coherence_scores else 0.0
        )
        return {
            "session_id": session.session_id,
            "pattern": session.pattern.name,
            "duration_seconds": (session.end_time or time.time()) - session.start_time,
            "sample_count": len(session.samples),
            "average_inter_beat_interval_ms": round(avg_ibi, 2),
            "average_coherence": round(avg_coherence, 3),
            "high_coherence_percentage": round(high_coherence_pct, 1),
            "coherence_trend": HRVBiofeedbackAnalyzer.calculate_coherence_trend(coherence_scores)
        }

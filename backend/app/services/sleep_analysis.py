"""
Sleep Analysis Service — Sleep stage detection, quality scoring, circadian rhythm
Inspired by autosleepscorer, awesome-sleep-tracking, attnsleep
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class SleepStage(Enum):
    AWAKE = "awake"
    LIGHT = "light"
    DEEP = "deep"
    REM = "rem"


@dataclass
class SleepSample:
    timestamp: float
    heart_rate: float
    movement: float
    hrv: float = 0.0
    blood_oxygen: float = 98.0
    skin_temp: float = 36.5


@dataclass
class SleepSegment:
    stage: SleepStage
    start_time: float
    end_time: float
    duration_minutes: float


@dataclass
class SleepSession:
    start_time: float
    end_time: float
    samples: List[SleepSample]
    segments: List[SleepSegment] = None


@dataclass
class SleepAnalysis:
    total_sleep_minutes: float
    sleep_efficiency: float
    sleep_onset_minutes: float
    wake_after_sleep_onset: float
    deep_sleep_minutes: float
    light_sleep_minutes: float
    rem_sleep_minutes: float
    awake_minutes: float
    sleep_score: float
    sleep_stages: Dict[str, float]
    quality_rating: str


class SleepAnalyzer:
    """Pure function sleep analysis from sensor data."""

    @staticmethod
    def classify_sleep_stage(sample: SleepSample, prev_sample: Optional[SleepSample] = None) -> SleepStage:
        hr = sample.heart_rate
        movement = sample.movement
        hrv = sample.hrv
        if movement > 0.7 or hr > 85:
            return SleepStage.AWAKE
        if hrv > 50 and hr < 65 and movement < 0.3:
            return SleepStage.REM
        if hr < 55 and movement < 0.2 and hrv > 40:
            return SleepStage.DEEP
        if movement < 0.5 and hr < 75:
            return SleepStage.LIGHT
        return SleepStage.LIGHT

    @staticmethod
    def detect_sleep_segments(samples: List[SleepSample], min_segment_minutes: float = 5.0) -> List[SleepSegment]:
        if not samples:
            return []
        segments = []
        current_stage = SleepAnalyzer.classify_sleep_stage(samples[0])
        segment_start = samples[0].timestamp
        for i in range(1, len(samples)):
            stage = SleepAnalyzer.classify_sleep_stage(samples[i], samples[i - 1])
            if stage != current_stage:
                duration = (samples[i].timestamp - segment_start) / 60.0
                if duration >= min_segment_minutes:
                    segments.append(SleepSegment(
                        stage=current_stage,
                        start_time=segment_start,
                        end_time=samples[i].timestamp,
                        duration_minutes=round(duration, 1)
                    ))
                current_stage = stage
                segment_start = samples[i].timestamp
        duration = (samples[-1].timestamp - segment_start) / 60.0
        if duration >= min_segment_minutes:
            segments.append(SleepSegment(
                stage=current_stage,
                start_time=segment_start,
                end_time=samples[-1].timestamp,
                duration_minutes=round(duration, 1)
            ))
        return segments

    @staticmethod
    def calculate_sleep_efficiency(total_sleep_minutes: float, time_in_bed_minutes: float) -> float:
        if time_in_bed_minutes <= 0:
            return 0.0
        return min(100.0, round(total_sleep_minutes / time_in_bed_minutes * 100, 1))

    @staticmethod
    def calculate_sleep_score(segments: List[SleepSegment], total_time_minutes: float) -> float:
        if not segments or total_time_minutes <= 0:
            return 0.0
        deep = sum(s.duration_minutes for s in segments if s.stage == SleepStage.DEEP)
        rem = sum(s.duration_minutes for s in segments if s.stage == SleepStage.REM)
        light = sum(s.duration_minutes for s in segments if s.stage == SleepStage.LIGHT)
        awake = sum(s.duration_minutes for s in segments if s.stage == SleepStage.AWAKE)
        deep_pct = deep / total_time_minutes * 100 if total_time_minutes > 0 else 0
        rem_pct = rem / total_time_minutes * 100 if total_time_minutes > 0 else 0
        awake_pct = awake / total_time_minutes * 100 if total_time_minutes > 0 else 0
        deep_score = min(25, deep_pct * 0.8)
        rem_score = min(25, rem_pct * 0.7)
        duration_score = min(25, total_time_minutes / 480 * 25)
        awake_penalty = max(0, awake_pct - 5) * 0.5
        score = deep_score + rem_score + duration_score - awake_penalty
        return round(max(0, min(100, score)), 1)

    @staticmethod
    def detect_circadian_phase(samples: List[SleepSample]) -> str:
        if not samples:
            return "unknown"
        hr_values = [s.heart_rate for s in samples]
        avg_hr = sum(hr_values) / len(hr_values)
        if avg_hr < 55:
            return "deep_sleep_phase"
        elif avg_hr < 65:
            return "light_sleep_phase"
        elif avg_hr < 75:
            return "rem_phase"
        else:
            return "awake_phase"

    @staticmethod
    def calculate_sleep_debt(sleep_history: List[float], target_hours: float = 8.0) -> float:
        if not sleep_history:
            return 0.0
        debt = 0.0
        for actual_hours in sleep_history:
            debt += target_hours - actual_hours
        return round(max(0, debt), 1)

    @classmethod
    def analyze_session(cls, session: SleepSession) -> SleepAnalysis:
        total_time = (session.end_time - session.start_time) / 60.0
        segments = session.segments or cls.detect_sleep_segments(session.samples)
        deep = sum(s.duration_minutes for s in segments if s.stage == SleepStage.DEEP)
        light = sum(s.duration_minutes for s in segments if s.stage == SleepStage.LIGHT)
        rem = sum(s.duration_minutes for s in segments if s.stage == SleepStage.REM)
        awake = sum(s.duration_minutes for s in segments if s.stage == SleepStage.AWAKE)
        total_sleep = deep + light + rem
        efficiency = cls.calculate_sleep_efficiency(total_sleep, total_time)
        score = cls.calculate_sleep_score(segments, total_time)
        if score >= 85:
            rating = "excellent"
        elif score >= 70:
            rating = "good"
        elif score >= 50:
            rating = "fair"
        else:
            rating = "poor"
        return SleepAnalysis(
            total_sleep_minutes=round(total_sleep, 1),
            sleep_efficiency=efficiency,
            sleep_onset_minutes=round(segments[0].duration_minutes if segments else 0, 1),
            wake_after_sleep_onset=round(awake, 1),
            deep_sleep_minutes=round(deep, 1),
            light_sleep_minutes=round(light, 1),
            rem_sleep_minutes=round(rem, 1),
            awake_minutes=round(awake, 1),
            sleep_score=score,
            sleep_stages={
                "deep": round(deep, 1),
                "light": round(light, 1),
                "rem": round(rem, 1),
                "awake": round(awake, 1),
            },
            quality_rating=rating,
        )

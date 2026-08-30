"""
Sleep kit analysis from sleepkit — sleep staging and scoring.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class SleepStageResult:
    stage: str  # wake, light, deep, rem
    confidence: float
    duration_seconds: float
    index: int


@dataclass
class SleepKitReport:
    total_sleep_time: float = 0.0
    sleep_efficiency: float = 0.0
    sleep_onset_latency: float = 0.0
    wake_after_sleep_onset: float = 0.0
    stages: List[SleepStageResult] = None
    deep_pct: float = 0.0
    rem_pct: float = 0.0
    light_pct: float = 0.0
    wake_pct: float = 0.0

    def __post_init__(self):
        if self.stages is None:
            self.stages = []


def analyze_sleep_stages(stages: List[str], durations: List[float]) -> SleepKitReport:
    if not stages or not durations:
        return SleepKitReport()
    total = sum(durations)
    counts = {}
    for stage, dur in zip(stages, durations):
        counts[stage] = counts.get(stage, 0) + dur
    sleep_stages = [SleepStageResult(stage=s, confidence=0.8, duration_seconds=d, index=i) for i, (s, d) in enumerate(zip(stages, durations))]
    sleep_time = total - counts.get("wake", 0)
    efficiency = sleep_time / total if total > 0 else 0
    return SleepKitReport(
        total_sleep_time=sleep_time, sleep_efficiency=efficiency,
        stages=sleep_stages,
        deep_pct=counts.get("deep", 0) / total * 100 if total > 0 else 0,
        rem_pct=counts.get("rem", 0) / total * 100 if total > 0 else 0,
        light_pct=counts.get("light", 0) / total * 100 if total > 0 else 0,
        wake_pct=counts.get("wake", 0) / total * 100 if total > 0 else 0,
    )

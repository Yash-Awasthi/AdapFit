"""
Breathing Pattern Analyzer — analyzes respiratory data for sleep and fitness.
Detects breathing irregularities, apnea events, and recovery patterns.

Inspired by: airwaylab (PAP therapy airway analysis)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class BreathingEvent(Enum):
    NORMAL = "normal"
    APNEA = "apnea"
    HYPOPNEA = "hypopnea"
    RERA = "rera"  # Respiratory Effort-Related Arousal
    SNORING = "snoring"
    FLOW_LIMITATION = "flow_limitation"


class BreathingQuality(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class BreathSample:
    """A single respiratory sample."""
    timestamp: datetime
    flow_rate: float  # Normalized airflow (-1 to 1, negative = inspiration)
    pressure_cmh2o: float = 0.0
    spo2: float | None = None


@dataclass
class BreathingEventLog:
    """A detected breathing event."""
    event_type: BreathingEvent
    start_time: datetime
    end_time: datetime
    severity: float  # 0-1
    details: str = ""

    @property
    def duration_seconds(self) -> float:
        return (self.end_time - self.start_time).total_seconds()


@dataclass
class BreathingAnalysis:
    """Analysis results for a breathing recording."""
    total_breaths: int
    avg_breath_rate: float  # breaths per minute
    avg_inspiratory_time: float  # seconds
    avg_expiratory_time: float  # seconds
    ie_ratio: float  # inspiratory:expiratory ratio
    breath_regularity: float  # 0-1 (coefficient of variation, inverted)
    events: list[BreathingEventLog]
    quality: BreathingQuality
    ahi: float  # Apnea-Hypopnea Index (events per hour)
    summary: dict[str, Any] = field(default_factory=dict)


class BreathingAnalyzer:
    """Analyzes respiratory waveforms for sleep quality and health insights."""

    def __init__(
        self,
        sample_rate_hz: float = 25.0,
        min_breath_duration: float = 1.5,  # seconds
        max_breath_duration: float = 12.0,
    ) -> None:
        self.sample_rate_hz = sample_rate_hz
        self.min_breath_duration = min_breath_duration
        self.max_breath_duration = max_breath_duration

        # Thresholds
        self._apnea_threshold = -0.1  # flow below this = apnea
        self._hypopnea_threshold = 0.5  # 50% reduction = hypopnea

    def _detect_breath_cycles(self, samples: list[BreathSample]) -> list[dict[str, Any]]:
        """Detect individual breath cycles from flow data."""
        if len(samples) < 10:
            return []

        # Zero-crossing detection for breath cycle identification
        cycles: list[dict[str, Any]] = []
        in_inspiration = False
        cycle_start = 0

        for i in range(1, len(samples)):
            prev_flow = samples[i - 1].flow_rate
            curr_flow = samples[i].flow_rate

            # Detect zero crossing (transition from expiration to inspiration)
            if prev_flow <= 0 and curr_flow > 0 and not in_inspiration:
                if in_inspiration or cycle_start > 0:
                    duration = (samples[i].timestamp - samples[cycle_start].timestamp).total_seconds()
                    if self.min_breath_duration <= duration <= self.max_breath_duration:
                        cycles.append({
                            "start_idx": cycle_start,
                            "end_idx": i,
                            "duration": duration,
                            "start_time": samples[cycle_start].timestamp,
                            "end_time": samples[i].timestamp,
                        })
                cycle_start = i
                in_inspiration = True

            elif prev_flow > 0 and curr_flow <= 0 and in_inspiration:
                in_inspiration = False

        return cycles

    def _detect_events(
        self, samples: list[BreathSample], cycles: list[dict[str, Any]]
    ) -> list[BreathingEventLog]:
        """Detect breathing events (apnea, hypopnea, etc.)."""
        events: list[BreathingEventLog] = []
        total_recording_seconds = (
            (samples[-1].timestamp - samples[0].timestamp).total_seconds()
            if len(samples) > 1
            else 1
        )

        for cycle in cycles:
            start_idx = cycle["start_idx"]
            end_idx = cycle["end_idx"]
            duration = cycle["duration"]

            # Check for apnea (no or minimal flow for >10 seconds)
            if duration >= 10.0:
                min_flow = min(
                    abs(samples[j].flow_rate)
                    for j in range(start_idx, min(end_idx, len(samples)))
                )
                if min_flow < abs(self._apnea_threshold):
                    events.append(BreathingEventLog(
                        event_type=BreathingEvent.APNEA,
                        start_time=cycle["start_time"],
                        end_time=cycle["end_time"],
                        severity=min(1.0, duration / 30.0),
                        details=f"Apnea detected: {duration:.1f}s",
                    ))
                    continue

            # Check for hypopnea (reduced flow for >10 seconds)
            if duration >= 10.0:
                avg_flow = sum(
                    abs(samples[j].flow_rate)
                    for j in range(start_idx, min(end_idx, len(samples)))
                ) / max(end_idx - start_idx, 1)

                if avg_flow < self._hypopnea_threshold:
                    events.append(BreathingEventLog(
                        event_type=BreathingEvent.HYPOPNEA,
                        start_time=cycle["start_time"],
                        end_time=cycle["end_time"],
                        severity=min(1.0, (1.0 - avg_flow) * 2),
                        details=f"Hypopnea detected: {duration:.1f}s, avg flow: {avg_flow:.2f}",
                    ))

            # Check for flow limitation (plateau in inspiratory flow)
            if duration >= 3.0:
                inspiratory_flows = [
                    samples[j].flow_rate
                    for j in range(start_idx, min(start_idx + (end_idx - start_idx) // 2, len(samples)))
                    if samples[j].flow_rate > 0
                ]
                if len(inspiratory_flows) > 5:
                    max_flow = max(inspiratory_flows)
                    plateau_ratio = sum(
                        1 for f in inspiratory_flows if abs(f - max_flow) < 0.1 * max_flow
                    ) / len(inspiratory_flows)

                    if plateau_ratio > 0.6:
                        events.append(BreathingEventLog(
                            event_type=BreathingEvent.FLOW_LIMITATION,
                            start_time=cycle["start_time"],
                            end_time=cycle["end_time"],
                            severity=min(1.0, plateau_ratio),
                            details=f"Flow limitation: {plateau_ratio:.0%} plateau",
                        ))

        return events

    def _calculate_quality(self, ahi: float, breath_regularity: float) -> BreathingQuality:
        """Calculate overall breathing quality score."""
        if ahi >= 30 or breath_regularity < 0.3:
            return BreathingQuality.CRITICAL
        elif ahi >= 15 or breath_regularity < 0.5:
            return BreathingQuality.POOR
        elif ahi >= 5 or breath_regularity < 0.7:
            return BreathingQuality.FAIR
        elif ahi < 5 and breath_regularity >= 0.85:
            return BreathingQuality.EXCELLENT
        else:
            return BreathingQuality.GOOD

    def analyze(self, samples: list[BreathSample]) -> BreathingAnalysis:
        """Perform full breathing analysis on a sample set."""
        if len(samples) < 10:
            return BreathingAnalysis(
                total_breaths=0,
                avg_breath_rate=0,
                avg_inspiratory_time=0,
                avg_expiratory_time=0,
                ie_ratio=0,
                breath_regularity=0,
                events=[],
                quality=BreathingQuality.FAIR,
                ahi=0,
            )

        # Detect breath cycles
        cycles = self._detect_breath_cycles(samples)
        events = self._detect_events(samples, cycles)

        total_breaths = len(cycles)
        durations = [c["duration"] for c in cycles]

        # Breathing rate
        total_time = (samples[-1].timestamp - samples[0].timestamp).total_seconds()
        avg_breath_rate = (total_breaths / max(total_time, 1)) * 60 if total_time > 0 else 0

        # I:E ratio estimation (simplified: assume 40% inspiration)
        avg_ie_ratio = 0.4 / 0.6  # Typical 2:3

        # Breath regularity (coefficient of variation, inverted)
        if durations:
            mean_dur = sum(durations) / len(durations)
            var_dur = sum((d - mean_dur) ** 2 for d in durations) / len(durations)
            cv = math.sqrt(var_dur) / max(mean_dur, 0.001)
            breath_regularity = max(0, 1.0 - cv)
        else:
            breath_regularity = 0

        # AHI (events per hour)
        hours = max(total_time / 3600, 0.001)
        apnea_events = sum(1 for e in events if e.event_type in (BreathingEvent.APNEA, BreathingEvent.HYPOPNEA))
        ahi = apnea_events / hours

        quality = self._calculate_quality(ahi, breath_regularity)

        return BreathingAnalysis(
            total_breaths=total_breaths,
            avg_breath_rate=round(avg_breath_rate, 1),
            avg_inspiratory_time=round(total_time / total_breaths * 0.4, 2) if total_breaths else 0,
            avg_expiratory_time=round(total_time / total_breaths * 0.6, 2) if total_breaths else 0,
            ie_ratio=round(avg_ie_ratio, 2),
            breath_regularity=round(breath_regularity, 3),
            events=events,
            quality=quality,
            ahi=round(ahi, 1),
            summary={
                "total_recording_minutes": round(total_time / 60, 1),
                "total_events": len(events),
                "apnea_count": sum(1 for e in events if e.event_type == BreathingEvent.APNEA),
                "hypopnea_count": sum(1 for e in events if e.event_type == BreathingEvent.HYPOPNEA),
                "flow_limitation_count": sum(1 for e in events if e.event_type == BreathingEvent.FLOW_LIMITATION),
            },
        )

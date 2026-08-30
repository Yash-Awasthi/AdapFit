"""
Breathing Pacer Service — Inspired by OpenHRV
Visual breathing guide with multiple patterns and real-time feedback
"""

import math
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class PacerStyle(Enum):
    CIRCLE = "circle"
    BAR = "bar"
    BOX = "box"
    WAVE = "wave"


@dataclass
class PacerConfig:
    style: PacerStyle
    pattern_name: str
    inhale_seconds: float
    exhale_seconds: float
    hold_in_seconds: float = 0.0
    hold_out_seconds: float = 0.0
    color: str = "#4CAF50"
    bg_color: str = "#1a1a2e"
    size: int = 200

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
class PacerState:
    phase: str
    progress: float
    scale: float
    opacity: float
    time_in_phase: float
    total_cycle_time: float


class BreathingPacer:
    """Pure function breathing pacer with visual feedback generation."""

    PRESETS = {
        "4-7-8": PacerConfig(
            style=PacerStyle.CIRCLE,
            pattern_name="4-7-8",
            inhale_seconds=4.0,
            exhale_seconds=8.0,
            hold_in_seconds=7.0,
            color="#6C63FF"
        ),
        "box": PacerConfig(
            style=PacerStyle.BOX,
            pattern_name="box",
            inhale_seconds=4.0,
            exhale_seconds=4.0,
            hold_in_seconds=4.0,
            hold_out_seconds=4.0,
            color="#FF6B6B"
        ),
        "calm": PacerConfig(
            style=PacerStyle.CIRCLE,
            pattern_name="calm",
            inhale_seconds=4.0,
            exhale_seconds=6.0,
            color="#4ECDC4"
        ),
        "energize": PacerConfig(
            style=PacerStyle.BAR,
            pattern_name="energize",
            inhale_seconds=2.0,
            exhale_seconds=2.0,
            color="#FFE66D"
        ),
        "sleep": PacerConfig(
            style=PacerStyle.WAVE,
            pattern_name="sleep",
            inhale_seconds=4.0,
            exhale_seconds=7.0,
            hold_in_seconds=1.0,
            color="#95E1D3"
        ),
    }

    @staticmethod
    def get_phase_at_time(elapsed_seconds: float, config: PacerConfig) -> PacerState:
        cycle_pos = elapsed_seconds % config.cycle_length if config.cycle_length > 0 else 0
        phases = []
        current_time = 0.0
        if config.inhale_seconds > 0:
            phases.append(("inhale", config.inhale_seconds, current_time))
            current_time += config.inhale_seconds
        if config.hold_in_seconds > 0:
            phases.append(("hold_in", config.hold_in_seconds, current_time))
            current_time += config.hold_in_seconds
        if config.exhale_seconds > 0:
            phases.append(("exhale", config.exhale_seconds, current_time))
            current_time += config.exhale_seconds
        if config.hold_out_seconds > 0:
            phases.append(("hold_out", config.hold_out_seconds, current_time))
            current_time += config.hold_out_seconds
        if not phases:
            return PacerState("idle", 0.0, 0.5, 1.0, 0.0, 0.0)
        active_phase = phases[0]
        for phase_name, duration, start_time in phases:
            if cycle_pos < start_time + duration:
                active_phase = (phase_name, duration, start_time)
                break
        phase_name, duration, start_time = active_phase
        time_in_phase = cycle_pos - start_time
        progress = time_in_phase / duration if duration > 0 else 0.0
        if phase_name == "inhale":
            scale = 0.5 + 0.5 * progress
            opacity = 1.0
        elif phase_name == "hold_in":
            scale = 1.0
            opacity = 0.9
        elif phase_name == "exhale":
            scale = 1.0 - 0.5 * progress
            opacity = 0.7 + 0.3 * (1.0 - progress)
        elif phase_name == "hold_out":
            scale = 0.5
            opacity = 0.6
        else:
            scale = 0.5
            opacity = 1.0
        return PacerState(
            phase=phase_name,
            progress=round(progress, 3),
            scale=round(scale, 3),
            opacity=round(opacity, 3),
            time_in_phase=round(time_in_phase, 3),
            total_cycle_time=round(config.cycle_length, 3)
        )

    @staticmethod
    def generate_circle_animation(state: PacerState, config: PacerConfig) -> Dict:
        radius = (config.size / 2) * state.scale
        return {
            "type": "circle",
            "cx": config.size / 2,
            "cy": config.size / 2,
            "radius": round(radius, 1),
            "fill": config.color,
            "opacity": state.opacity,
            "phase": state.phase,
            "progress": state.progress
        }

    @staticmethod
    def generate_bar_animation(state: PacerState, config: PacerConfig) -> Dict:
        bar_height = config.size * state.scale
        return {
            "type": "bar",
            "x": config.size * 0.2,
            "y": config.size - bar_height,
            "width": config.size * 0.6,
            "height": round(bar_height, 1),
            "fill": config.color,
            "opacity": state.opacity,
            "phase": state.phase,
            "progress": state.progress
        }

    @staticmethod
    def generate_wave_animation(state: PacerState, config: PacerConfig) -> Dict:
        points = []
        for i in range(100):
            x = (i / 99) * config.size
            wave_progress = state.progress * math.pi * 2
            amplitude = config.size * 0.2 * state.scale
            y = config.size / 2 + amplitude * math.sin(wave_progress + (i / 99) * math.pi * 4)
            points.append({"x": round(x, 1), "y": round(y, 1)})
        return {
            "type": "wave",
            "points": points,
            "stroke": config.color,
            "stroke_width": 3,
            "opacity": state.opacity,
            "phase": state.phase,
            "progress": state.progress
        }

    @staticmethod
    def generate_box_animation(state: PacerState, config: PacerConfig) -> Dict:
        size = config.size * state.scale
        x = (config.size - size) / 2
        return {
            "type": "box",
            "x": round(x, 1),
            "y": round(x, 1),
            "width": round(size, 1),
            "height": round(size, 1),
            "fill": "none",
            "stroke": config.color,
            "stroke_width": 3,
            "opacity": state.opacity,
            "phase": state.phase,
            "progress": state.progress
        }

    @classmethod
    def generate_frame(cls, elapsed_seconds: float, config: PacerConfig) -> Dict:
        state = cls.get_phase_at_time(elapsed_seconds, config)
        if config.style == PacerStyle.CIRCLE:
            animation = cls.generate_circle_animation(state, config)
        elif config.style == PacerStyle.BAR:
            animation = cls.generate_bar_animation(state, config)
        elif config.style == PacerStyle.BOX:
            animation = cls.generate_box_animation(state, config)
        elif config.style == PacerStyle.WAVE:
            animation = cls.generate_wave_animation(state, config)
        else:
            animation = cls.generate_circle_animation(state, config)
        return {
            "animation": animation,
            "phase": state.phase,
            "progress": state.progress,
            "scale": state.scale,
            "breaths_per_minute": config.breaths_per_minute,
            "cycle_time": config.cycle_length,
            "time_in_phase": state.time_in_phase
        }

    @staticmethod
    def calculate_session_stats(session_duration_seconds: float,
                                config: PacerConfig) -> Dict:
        if config.cycle_length <= 0:
            return {"error": "Invalid pattern"}
        total_breaths = session_duration_seconds / config.cycle_length
        return {
            "total_breaths": round(total_breaths, 1),
            "average_bpm": round(config.breaths_per_minute, 1),
            "cycle_length": round(config.cycle_length, 1),
            "pattern": config.pattern_name,
            "duration_seconds": session_duration_seconds,
            "inhale_time": round(total_breaths * config.inhale_seconds, 1),
            "exhale_time": round(total_breaths * config.exhale_seconds, 1),
            "hold_time": round(total_breaths * (config.hold_in_seconds + config.hold_out_seconds), 1)
        }

    @classmethod
    def get_adaptive_pattern(cls, current_hr: float, resting_hr: float,
                             stress_level: float = 0.5) -> PacerConfig:
        hr_ratio = current_hr / resting_hr if resting_hr > 0 else 1.0
        if stress_level > 0.7 or hr_ratio > 1.3:
            return cls.PRESETS["4-7-8"]
        elif stress_level > 0.4 or hr_ratio > 1.1:
            return cls.PRESETS["calm"]
        elif hr_ratio < 0.9:
            return cls.PRESETS["energize"]
        else:
            return cls.PRESETS["calm"]

    @staticmethod
    def generate_haptic_pattern(state: PacerState) -> Dict:
        if state.phase == "inhale":
            return {"type": "ramp_up", "duration_ms": int(state.time_in_phase * 1000)}
        elif state.phase == "exhale":
            return {"type": "ramp_down", "duration_ms": int(state.time_in_phase * 1000)}
        elif state.phase in ("hold_in", "hold_out"):
            return {"type": "steady", "intensity": 0.3}
        return {"type": "none"}

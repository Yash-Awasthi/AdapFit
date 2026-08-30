"""
Training Plan Periodization
Extracted from garmin-ai-coach's training plan patterns

Features:
- Periodization models (linear, undulating, block)
- Phase management (base, build, peak, taper)
- Load management (ACWR, TSS)
- Recovery integration
- Race preparation
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import math
import time


class TrainingPhase(Enum):
    BASE = "base"
    BUILD = "build"
    PEAK = "peak"
    TAPER = "taper"
    RECOVERY = "recovery"


class PeriodizationModel(Enum):
    LINEAR = "linear"
    UNDULATING = "undulating"
    BLOCK = "block"


@dataclass
class TrainingZone:
    """Training intensity zone"""
    name: str
    min_intensity: float  # 0-1
    max_intensity: float
    description: str
    target_duration: float  # minutes


@dataclass
class Workout:
    """Single workout definition"""
    day: int
    phase: TrainingPhase
    zone: TrainingZone
    duration: float  # minutes
    intensity: float  # 0-1
    description: str
    tss: float  # Training Stress Score
    notes: str


@dataclass
class TrainingWeek:
    """Weekly training plan"""
    week_number: int
    phase: TrainingPhase
    workouts: List[Workout]
    total_tss: float
    intensity_distribution: Dict[str, float]  # zone -> percentage
    recovery_score: float


@dataclass
class TrainingPlan:
    """Complete training plan"""
    name: str
    start_date: float
    end_date: float
    goal: str
    model: PeriodizationModel
    weeks: List[TrainingWeek]
    total_tss: float
    peak_tss: float
    taper_ratio: float


# Standard training zones (based on garmin-ai-coach patterns)
DEFAULT_ZONES = [
    TrainingZone(
        name="Recovery",
        min_intensity=0.0,
        max_intensity=0.5,
        description="Easy recovery pace",
        target_duration=30
    ),
    TrainingZone(
        name="Endurance",
        min_intensity=0.5,
        max_intensity=0.65,
        description="Aerobic base building",
        target_duration=60
    ),
    TrainingZone(
        name="Tempo",
        min_intensity=0.65,
        max_intensity=0.75,
        description="Sustained effort",
        target_duration=45
    ),
    TrainingZone(
        name="Threshold",
        min_intensity=0.75,
        max_intensity=0.85,
        description="Lactate threshold",
        target_duration=30
    ),
    TrainingZone(
        name="VO2max",
        min_intensity=0.85,
        max_intensity=0.95,
        description="Maximal aerobic capacity",
        target_duration=20
    ),
    TrainingZone(
        name="Anaerobic",
        min_intensity=0.95,
        max_intensity=1.0,
        description="Anaerobic capacity",
        target_duration=10
    )
]


def calculate_acwr(
    acute_load: float,
    chronic_load: float
) -> float:
    """
    Calculate Acute:Chronic Workload Ratio
    
    Args:
        acute_load: 7-day training load
        chronic_load: 28-day training load
    
    Returns:
        ACWR ratio (optimal: 0.8-1.3)
    """
    if chronic_load <= 0:
        return 0.0
    return acute_load / chronic_load


def calculate_tss(
    duration_minutes: float,
    intensity: float,
    heart_rate: Optional[float] = None,
    max_heart_rate: float = 190.0
) -> float:
    """
    Calculate Training Stress Score
    
    Args:
        duration_minutes: Workout duration
        intensity: Intensity factor (0-1)
        heart_rate: Average heart rate (optional)
        max_heart_rate: Maximum heart rate
    
    Returns:
        TSS score
    """
    # Basic TSS calculation
    duration_hours = duration_minutes / 60.0
    tss = duration_hours * intensity * 100
    
    # Adjust for heart rate if available
    if heart_rate and max_heart_rate > 0:
        hr_intensity = heart_rate / max_heart_rate
        tss = tss * (0.8 + 0.2 * hr_intensity)
    
    return tss


def generate_linear_periodization(
    weeks: int,
    peak_week: int,
    goal_tss: float,
    start_date: float
) -> TrainingPlan:
    """
    Generate linear periodization plan
    
    Args:
        weeks: Total weeks
        peak_week: Week of peak load
        goal_tss: Target TSS for peak week
        start_date: Start timestamp
    
    Returns:
        TrainingPlan
    """
    training_weeks = []
    
    for week in range(1, weeks + 1):
        # Calculate phase
        if week <= weeks * 0.3:
            phase = TrainingPhase.BASE
        elif week <= weeks * 0.6:
            phase = TrainingPhase.BUILD
        elif week <= peak_week:
            phase = TrainingPhase.PEAK
        elif week <= peak_week + 2:
            phase = TrainingPhase.TAPER
        else:
            phase = TrainingPhase.RECOVERY
        
        # Calculate TSS for this week
        if phase == TrainingPhase.BASE:
            week_tss = goal_tss * 0.5 * (week / (weeks * 0.3))
        elif phase == TrainingPhase.BUILD:
            week_tss = goal_tss * 0.75 * (week / (weeks * 0.6))
        elif phase == TrainingPhase.PEAK:
            week_tss = goal_tss
        elif phase == TrainingPhase.TAPER:
            taper_week = week - peak_week
            week_tss = goal_tss * (1 - taper_week * 0.3)
        else:
            week_tss = goal_tss * 0.3
        
        # Generate workouts
        workouts = _generate_weekly_workouts(phase, week_tss)
        
        # Calculate intensity distribution
        intensity_dist = _calculate_intensity_distribution(workouts)
        
        training_weeks.append(TrainingWeek(
            week_number=week,
            phase=phase,
            workouts=workouts,
            total_tss=sum(w.tss for w in workouts),
            intensity_distribution=intensity_dist,
            recovery_score=1.0 - (week_tss / goal_tss) * 0.5
        ))
    
    return TrainingPlan(
        name="Linear Periodization Plan",
        start_date=start_date,
        end_date=start_date + (weeks * 7 * 24 * 3600),
        goal="Progressive overload with linear increase",
        model=PeriodizationModel.LINEAR,
        weeks=training_weeks,
        total_tss=sum(w.total_tss for w in training_weeks),
        peak_tss=goal_tss,
        taper_ratio=0.3
    )


def generate_undulating_periodization(
    weeks: int,
    base_tss: float,
    variation: float,
    start_date: float
) -> TrainingPlan:
    """
    Generate undulating periodization plan
    
    Args:
        weeks: Total weeks
        base_tss: Base TSS for each week
        variation: Variation factor (0-1)
        start_date: Start timestamp
    
    Returns:
        TrainingPlan
    """
    training_weeks = []
    
    for week in range(1, weeks + 1):
        # Calculate phase
        if week <= weeks * 0.25:
            phase = TrainingPhase.BASE
        elif week <= weeks * 0.5:
            phase = TrainingPhase.BUILD
        elif week <= weeks * 0.75:
            phase = TrainingPhase.PEAK
        else:
            phase = TrainingPhase.TAPER
        
        # Undulating TSS (wave pattern)
        wave = math.sin(week * math.pi / 4) * variation
        week_tss = base_tss * (1 + wave)
        
        # Generate workouts
        workouts = _generate_weekly_workouts(phase, week_tss)
        
        # Calculate intensity distribution
        intensity_dist = _calculate_intensity_distribution(workouts)
        
        training_weeks.append(TrainingWeek(
            week_number=week,
            phase=phase,
            workouts=workouts,
            total_tss=sum(w.tss for w in workouts),
            intensity_distribution=intensity_dist,
            recovery_score=1.0 - abs(wave) * 0.5
        ))
    
    return TrainingPlan(
        name="Undulating Periodization Plan",
        start_date=start_date,
        end_date=start_date + (weeks * 7 * 24 * 3600),
        goal="Varied intensity with wave pattern",
        model=PeriodizationModel.UNDULATING,
        weeks=training_weeks,
        total_tss=sum(w.total_tss for w in training_weeks),
        peak_tss=max(w.total_tss for w in training_weeks),
        taper_ratio=0.25
    )


def _generate_weekly_workouts(
    phase: TrainingPhase,
    target_tss: float
) -> List[Workout]:
    """Generate workouts for a week"""
    workouts = []
    
    if phase == TrainingPhase.BASE:
        # Base: mostly easy, some tempo
        workouts = [
            Workout(1, phase, DEFAULT_ZONES[1], 60, 0.55, "Easy run", 50, "Build aerobic base"),
            Workout(2, phase, DEFAULT_ZONES[1], 45, 0.5, "Recovery run", 35, "Active recovery"),
            Workout(3, phase, DEFAULT_ZONES[2], 50, 0.7, "Tempo run", 60, "Sustained effort"),
            Workout(4, phase, DEFAULT_ZONES[1], 60, 0.55, "Easy run", 50, "Build aerobic base"),
            Workout(5, phase, DEFAULT_ZONES[1], 45, 0.5, "Recovery run", 35, "Active recovery"),
            Workout(6, phase, DEFAULT_ZONES[1], 90, 0.55, "Long run", 80, "Build endurance"),
            Workout(7, phase, DEFAULT_ZONES[0], 0, 0, "Rest day", 0, "Full recovery"),
        ]
    elif phase == TrainingPhase.BUILD:
        # Build: more intensity, threshold work
        workouts = [
            Workout(1, phase, DEFAULT_ZONES[1], 60, 0.6, "Easy run", 55, "Aerobic maintenance"),
            Workout(2, phase, DEFAULT_ZONES[3], 40, 0.8, "Threshold intervals", 70, "Lactate threshold"),
            Workout(3, phase, DEFAULT_ZONES[1], 50, 0.55, "Recovery run", 40, "Active recovery"),
            Workout(4, phase, DEFAULT_ZONES[4], 35, 0.9, "VO2max intervals", 65, "Maximal aerobic"),
            Workout(5, phase, DEFAULT_ZONES[1], 60, 0.55, "Easy run", 50, "Aerobic base"),
            Workout(6, phase, DEFAULT_ZONES[2], 100, 0.65, "Long run with tempo", 90, "Endurance + tempo"),
            Workout(7, phase, DEFAULT_ZONES[0], 0, 0, "Rest day", 0, "Full recovery"),
        ]
    elif phase == TrainingPhase.PEAK:
        # Peak: highest intensity
        workouts = [
            Workout(1, phase, DEFAULT_ZONES[1], 60, 0.6, "Easy run", 55, "Aerobic maintenance"),
            Workout(2, phase, DEFAULT_ZONES[4], 40, 0.9, "VO2max intervals", 75, "Maximal effort"),
            Workout(3, phase, DEFAULT_ZONES[1], 50, 0.55, "Recovery run", 40, "Active recovery"),
            Workout(4, phase, DEFAULT_ZONES[3], 45, 0.85, "Threshold workout", 80, "Race pace"),
            Workout(5, phase, DEFAULT_ZONES[1], 60, 0.55, "Easy run", 50, "Aerobic base"),
            Workout(6, phase, DEFAULT_ZONES[2], 110, 0.65, "Long run", 100, "Peak endurance"),
            Workout(7, phase, DEFAULT_ZONES[0], 0, 0, "Rest day", 0, "Full recovery"),
        ]
    elif phase == TrainingPhase.TAPER:
        # Taper: reduced volume, maintained intensity
        workouts = [
            Workout(1, phase, DEFAULT_ZONES[1], 45, 0.55, "Easy run", 40, "Maintain fitness"),
            Workout(2, phase, DEFAULT_ZONES[3], 30, 0.8, "Short threshold", 45, "Maintain intensity"),
            Workout(3, phase, DEFAULT_ZONES[1], 40, 0.5, "Recovery run", 30, "Active recovery"),
            Workout(4, phase, DEFAULT_ZONES[1], 45, 0.55, "Easy run", 40, "Maintain fitness"),
            Workout(5, phase, DEFAULT_ZONES[0], 0, 0, "Rest day", 0, "Full recovery"),
            Workout(6, phase, DEFAULT_ZONES[1], 30, 0.5, "Shakeout run", 20, "Pre-race"),
            Workout(7, phase, DEFAULT_ZONES[0], 0, 0, "Rest day", 0, "Race day preparation"),
        ]
    else:  # RECOVERY
        workouts = [
            Workout(1, phase, DEFAULT_ZONES[0], 30, 0.4, "Very easy run", 20, "Recovery"),
            Workout(2, phase, DEFAULT_ZONES[0], 30, 0.4, "Very easy run", 20, "Recovery"),
            Workout(3, phase, DEFAULT_ZONES[0], 0, 0, "Rest day", 0, "Full recovery"),
            Workout(4, phase, DEFAULT_ZONES[0], 30, 0.4, "Very easy run", 20, "Recovery"),
            Workout(5, phase, DEFAULT_ZONES[0], 30, 0.4, "Very easy run", 20, "Recovery"),
            Workout(6, phase, DEFAULT_ZONES[0], 45, 0.45, "Easy run", 25, "Recovery"),
            Workout(7, phase, DEFAULT_ZONES[0], 0, 0, "Rest day", 0, "Full recovery"),
        ]
    
    return workouts


def _calculate_intensity_distribution(workouts: List[Workout]) -> Dict[str, float]:
    """Calculate intensity zone distribution"""
    total_duration = sum(w.duration for w in workouts)
    if total_duration == 0:
        return {}
    
    zone_durations = {}
    for workout in workouts:
        zone = workout.zone.name
        zone_durations[zone] = zone_durations.get(zone, 0) + workout.duration
    
    return {zone: duration / total_duration for zone, duration in zone_durations.items()}


def calculate_race_readiness(
    current_tss: float,
    target_tss: float,
    days_to_race: int,
    acwr: float
) -> float:
    """
    Calculate race readiness score
    
    Args:
        current_tss: Recent training load
        target_tss: Target training load
        days_to_race: Days until race
        acwr: Acute:Chronic workload ratio
    
    Returns:
        Readiness score (0-1)
    """
    # Training load readiness
    load_readiness = min(1.0, current_tss / target_tss) if target_tss > 0 else 0
    
    # Taper readiness (optimal taper is 7-14 days)
    if days_to_race <= 14:
        taper_readiness = 1.0 - (14 - days_to_race) / 14
    else:
        taper_readiness = 0.5
    
    # ACWR readiness (optimal is 0.8-1.3)
    if 0.8 <= acwr <= 1.3:
        acwr_readiness = 1.0
    elif acwr < 0.8:
        acwr_readiness = acwr / 0.8
    else:
        acwr_readiness = max(0.5, 1.0 - (acwr - 1.3) / 2)
    
    # Combined readiness
    readiness = (
        load_readiness * 0.4 +
        taper_readiness * 0.3 +
        acwr_readiness * 0.3
    )
    
    return min(1.0, readiness)
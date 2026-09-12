"""
Activity Recognition Service — Automatic workout detection from sensor data
Inspired by ai-fitness-planner, athlete-training-load-prediction
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field


class ActivityType(Enum):
    WALKING = "walking"
    RUNNING = "running"
    CYCLING = "cycling"
    SWIMMING = "swimming"
    STRENGTH = "strength"
    YOGA = "yoga"
    HIIT = "hiit"
    REST = "rest"
    UNKNOWN = "unknown"


@dataclass
class SensorSample:
    timestamp: float
    accelerometer: Tuple[float, float, float]  # x, y, z
    gyroscope: Tuple[float, float, float]  # x, y, z
    heart_rate: Optional[float] = None
    step_count: Optional[int] = None


@dataclass
class ActivityDetection:
    activity: ActivityType
    confidence: float
    start_time: float
    end_time: float
    duration_seconds: float
    calories_burned: float
    steps: int
    distance_meters: float
    avg_heart_rate: float
    max_heart_rate: float


@dataclass
class DailyActivitySummary:
    date: str
    total_steps: int
    total_distance_km: float
    total_calories: float
    active_minutes: int
    sedentary_minutes: int
    activities: List[ActivityDetection]
    intensity_distribution: Dict[str, int]


class ActivityRecognizer:
    """Pure function activity recognition from sensor data."""

    # Metabolic equivalents (METs) for each activity
    METS = {
        ActivityType.WALKING: 3.5,
        ActivityType.RUNNING: 8.0,
        ActivityType.CYCLING: 6.0,
        ActivityType.SWIMMING: 7.0,
        ActivityType.STRENGTH: 5.0,
        ActivityType.YOGA: 2.5,
        ActivityType.HIIT: 9.0,
        ActivityType.REST: 1.0,
        ActivityType.UNKNOWN: 2.0,
    }

    # Step length estimates (meters)
    STEP_LENGTHS = {
        ActivityType.WALKING: 0.75,
        ActivityType.RUNNING: 1.0,
    }

    @staticmethod
    def calculate_magnitude(acceleration: Tuple[float, float, float]) -> float:
        return math.sqrt(sum(a ** 2 for a in acceleration))

    @staticmethod
    def calculate_jerk(accelerations: List[Tuple[float, float, float]]) -> List[float]:
        if len(accelerations) < 2:
            return [0.0]
        jerks = []
        for i in range(1, len(accelerations)):
            dx = accelerations[i][0] - accelerations[i - 1][0]
            dy = accelerations[i][1] - accelerations[i - 1][1]
            dz = accelerations[i][2] - accelerations[i - 1][2]
            jerks.append(math.sqrt(dx ** 2 + dy ** 2 + dz ** 2))
        return jerks

    @staticmethod
    def detect_step_peaks(accelerations: List[float], threshold: float = 1.2) -> int:
        if len(accelerations) < 3:
            return 0
        peaks = 0
        for i in range(1, len(accelerations) - 1):
            if (accelerations[i] > accelerations[i - 1] and
                accelerations[i] > accelerations[i + 1] and
                accelerations[i] > threshold):
                peaks += 1
        return peaks

    @staticmethod
    def estimate_stride_frequency(samples: List[SensorSample], window_seconds: float = 5.0) -> float:
        if not samples:
            return 0.0
        window_samples = [s for s in samples
                         if s.timestamp <= samples[0].timestamp + window_seconds]
        accelerations = [s.accelerometer for s in window_samples]
        magnitudes = [ActivityRecognizer.calculate_magnitude(a) for a in accelerations]
        peaks = ActivityRecognizer.detect_step_peaks(magnitudes)
        return peaks / window_seconds if window_seconds > 0 else 0.0

    @staticmethod
    def classify_activity(samples: List[SensorSample]) -> Tuple[ActivityType, float]:
        if not samples:
            return ActivityType.UNKNOWN, 0.0
        accelerations = [s.accelerometer for s in samples]
        magnitudes = [ActivityRecognizer.calculate_magnitude(a) for a in accelerations]
        avg_magnitude = sum(magnitudes) / len(magnitudes)
        max_magnitude = max(magnitudes)
        variance = sum((m - avg_magnitude) ** 2 for m in magnitudes) / len(magnitudes)
        stride_freq = ActivityRecognizer.estimate_stride_frequency(samples)
        hr_values = [s.heart_rate for s in samples if s.heart_rate is not None]
        avg_hr = sum(hr_values) / len(hr_values) if hr_values else 0
        scores = {}
        scores[ActivityType.WALKING] = 0.0
        scores[ActivityType.RUNNING] = 0.0
        scores[ActivityType.CYCLING] = 0.0
        scores[ActivityType.STRENGTH] = 0.0
        scores[ActivityType.YOGA] = 0.0
        scores[ActivityType.HIIT] = 0.0
        scores[ActivityType.REST] = 0.0
        if 0.1 < stride_freq < 2.5:
            if avg_magnitude < 15:
                scores[ActivityType.WALKING] += 0.4
            elif avg_magnitude > 20:
                scores[ActivityType.RUNNING] += 0.5
            else:
                scores[ActivityType.WALKING] += 0.3
                scores[ActivityType.RUNNING] += 0.2
        if variance > 50 and avg_magnitude > 15:
            scores[ActivityType.HIIT] += 0.4
        if variance < 10 and avg_magnitude < 12:
            scores[ActivityType.YOGA] += 0.5
        if avg_magnitude < 10.5:
            scores[ActivityType.REST] += 0.6
        if avg_hr > 120:
            scores[ActivityType.RUNNING] += 0.2
            scores[ActivityType.HIIT] += 0.2
        best_activity = max(scores, key=scores.get)
        confidence = scores[best_activity]
        if confidence < 0.2:
            return ActivityType.UNKNOWN, confidence
        return best_activity, min(1.0, confidence)

    @staticmethod
    def calculate_calories(activity: ActivityType, duration_seconds: float,
                          weight_kg: float = 70.0) -> float:
        met = ActivityRecognizer.METS.get(activity, 2.0)
        hours = duration_seconds / 3600.0
        return met * weight_kg * hours

    @staticmethod
    def calculate_distance(steps: int, activity: ActivityType,
                          height_cm: float = 170.0) -> float:
        if activity == ActivityType.WALKING:
            step_length = height_cm * 0.415 / 100
        elif activity == ActivityType.RUNNING:
            step_length = height_cm * 0.5 / 100
        else:
            step_length = 0.75
        return steps * step_length

    @classmethod
    def detect_activities(cls, samples: List[SensorSample],
                         min_duration_seconds: float = 30.0) -> List[ActivityDetection]:
        if not samples:
            return []
        activities = []
        window_size = 60
        i = 0
        while i < len(samples):
            window = samples[i:i + window_size]
            if len(window) < 10:
                i += window_size // 2
                continue
            activity, confidence = cls.classify_activity(window)
            start_time = window[0].timestamp
            end_time = window[-1].timestamp
            duration = end_time - start_time
            if duration >= min_duration_seconds:
                hr_values = [s.heart_rate for s in window if s.heart_rate]
                step_count = window[-1].step_count - window[0].step_count if window[0].step_count and window[-1].step_count else 0
                detection = ActivityDetection(
                    activity=activity,
                    confidence=confidence,
                    start_time=start_time,
                    end_time=end_time,
                    duration_seconds=duration,
                    calories_burned=cls.calculate_calories(activity, duration),
                    steps=max(0, step_count),
                    distance_meters=cls.calculate_distance(max(0, step_count), activity),
                    avg_heart_rate=sum(hr_values) / len(hr_values) if hr_values else 0,
                    max_heart_rate=max(hr_values) if hr_values else 0,
                )
                activities.append(detection)
            i += window_size // 2
        return cls._merge_activities(activities)

    @staticmethod
    def _merge_activities(activities: List[ActivityDetection]) -> List[ActivityDetection]:
        if not activities:
            return []
        merged = [activities[0]]
        for act in activities[1:]:
            if (act.activity == merged[-1].activity and
                act.start_time - merged[-1].end_time < 60):
                merged[-1] = ActivityDetection(
                    activity=merged[-1].activity,
                    confidence=(merged[-1].confidence + act.confidence) / 2,
                    start_time=merged[-1].start_time,
                    end_time=act.end_time,
                    duration_seconds=act.end_time - merged[-1].start_time,
                    calories_burned=merged[-1].calories_burned + act.calories_burned,
                    steps=merged[-1].steps + act.steps,
                    distance_meters=merged[-1].distance_meters + act.distance_meters,
                    avg_heart_rate=(merged[-1].avg_heart_rate + act.avg_heart_rate) / 2,
                    max_heart_rate=max(merged[-1].max_heart_rate, act.max_heart_rate),
                )
            else:
                merged.append(act)
        return merged

    @classmethod
    def create_daily_summary(cls, date: str, activities: List[ActivityDetection]) -> DailyActivitySummary:
        total_steps = sum(a.steps for a in activities)
        total_distance = sum(a.distance_meters for a in activities) / 1000
        total_calories = sum(a.calories_burned for a in activities)
        active_minutes = sum(int(a.duration_seconds / 60) for a in activities
                           if a.activity not in (ActivityType.REST, ActivityType.UNKNOWN))
        intensity = {"low": 0, "moderate": 0, "high": 0, "very_high": 0}
        for a in activities:
            if a.activity in (ActivityType.WALKING, ActivityType.YOGA):
                intensity["low"] += int(a.duration_seconds / 60)
            elif a.activity in (ActivityType.CYCLING, ActivityType.STRENGTH):
                intensity["moderate"] += int(a.duration_seconds / 60)
            elif a.activity in (ActivityType.RUNNING, ActivityType.SWIMMING):
                intensity["high"] += int(a.duration_seconds / 60)
            elif a.activity == ActivityType.HIIT:
                intensity["very_high"] += int(a.duration_seconds / 60)
        total_day = 24 * 60
        sedentary = total_day - active_minutes
        return DailyActivitySummary(
            date=date,
            total_steps=total_steps,
            total_distance_km=round(total_distance, 2),
            total_calories=round(total_calories, 1),
            active_minutes=active_minutes,
            sedentary_minutes=max(0, sedentary),
            activities=activities,
            intensity_distribution=intensity
        )


# ── Endpoint-facing API ─────────────────────────────────────────────────────
# The recogniser works on SensorSample tuples. Phone and watch clients post
# flat sensor frames, so these models are the wire format and the functions
# below convert a request into samples and return JSON-ready dicts.

class SensorReading(BaseModel):
    """One flat sensor frame as posted by a device."""
    timestamp: float
    accel_x: float
    accel_y: float
    accel_z: float
    gyro_x: float = 0.0
    gyro_y: float = 0.0
    gyro_z: float = 0.0
    heart_rate: Optional[float] = None

    def to_sample(self) -> SensorSample:
        return SensorSample(
            timestamp=self.timestamp,
            accelerometer=(self.accel_x, self.accel_y, self.accel_z),
            gyroscope=(self.gyro_x, self.gyro_y, self.gyro_z),
            heart_rate=self.heart_rate,
        )


class UserProfile(BaseModel):
    """Body metrics needed to turn sensor data into energy and distance."""
    weight_kg: float = Field(default=70.0, ge=20, le=300)
    height_cm: float = Field(default=170.0, ge=100, le=250)
    age: int = Field(default=30, ge=10, le=120)
    sex: str = "unspecified"


def _activity_from(value: str) -> ActivityType:
    try:
        return ActivityType(value.strip().lower())
    except ValueError:
        return ActivityType.UNKNOWN


def detect_activity(readings: List[SensorReading], window_seconds: float = 5.0) -> Dict:
    """Detect the dominant activity in a run of sensor frames."""
    samples = [r.to_sample() for r in readings]
    detections = ActivityRecognizer.detect_activities(samples)

    if not detections:
        single = ActivityRecognizer.classify_activity(samples) if samples else (ActivityType.UNKNOWN, 0.0)
        return {
            "activity": single[0].value,
            "confidence": round(single[1], 3),
            "windows": 0,
            "detail": "Not enough data to segment the session into activities.",
        }

    dominant = max(detections, key=lambda d: d.duration_seconds)
    return {
        "activity": dominant.activity.value,
        "confidence": round(dominant.confidence, 3),
        "duration_seconds": round(sum(d.duration_seconds for d in detections), 1),
        "calories_burned": round(sum(d.calories_burned for d in detections), 1),
        "steps": sum(d.steps for d in detections),
        "distance_meters": round(sum(d.distance_meters for d in detections), 1),
        "windows": len(detections),
        "segments": [
            {
                "activity": d.activity.value,
                "confidence": round(d.confidence, 3),
                "start_time": d.start_time,
                "end_time": d.end_time,
                "duration_seconds": round(d.duration_seconds, 1),
                "calories_burned": round(d.calories_burned, 1),
                "steps": d.steps,
            }
            for d in detections
        ],
    }


def count_steps(readings: List[SensorReading], sensitivity: float = 1.2) -> Dict:
    """Count steps in a run of sensor frames from acceleration peaks."""
    magnitudes = [
        ActivityRecognizer.calculate_magnitude((r.accel_x, r.accel_y, r.accel_z))
        for r in readings
    ]
    steps = ActivityRecognizer.detect_step_peaks(magnitudes, sensitivity)

    duration = ((readings[-1].timestamp - readings[0].timestamp)
                if len(readings) > 1 else 0.0)
    cadence = round(steps / duration * 60, 1) if duration > 0 else 0.0

    return {
        "steps": steps,
        "sensitivity": sensitivity,
        "duration_seconds": round(duration, 1),
        "cadence_steps_per_minute": cadence,
        "samples": len(readings),
    }


def estimate_distance(steps: int, height_cm: float, sex: str) -> Dict:
    """Estimate walking distance from a step count and body height."""
    # Stride-to-height ratio: 0.415 for men, 0.413 for women, averaged when the
    # sex is not given. Matches the walking ratio the recogniser uses.
    ratio = {"male": 0.415, "female": 0.413}.get(sex.strip().lower(), 0.414)
    stride_m = height_cm * ratio / 100
    distance_m = steps * stride_m

    return {
        "steps": steps,
        "stride_length_m": round(stride_m, 3),
        "distance_meters": round(distance_m, 1),
        "distance_km": round(distance_m / 1000, 3),
    }


def calculate_calories(
    activity: str,
    duration_minutes: float,
    user: UserProfile,
    heart_rate: Optional[int] = None,
) -> Dict:
    """Calorie burn for an activity, weighted by the person's body mass."""
    activity_type = _activity_from(activity)
    duration_seconds = duration_minutes * 60
    calories = ActivityRecognizer.calculate_calories(
        activity_type, duration_seconds, user.weight_kg
    )

    max_hr = 220 - user.age
    intensity = None
    note = None
    if heart_rate is not None:
        # The heart-rate response is a real measurement of effort, so a session
        # that ran harder than its activity class implies is scaled up to match.
        intensity = classify_intensity(heart_rate, user.age)
        if intensity["zone"] in ("vigorous", "maximum"):
            calories *= 1.1
            note = "Adjusted upward for a heart-rate response above the activity's typical effort."

    return {
        "activity": activity_type.value,
        "duration_minutes": duration_minutes,
        "met": ActivityRecognizer.METS.get(activity_type, 2.0),
        "calories": round(calories, 1),
        "weight_kg": user.weight_kg,
        "max_heart_rate": max_hr,
        "heart_rate_intensity": intensity,
        "note": note,
    }


def classify_intensity(heart_rate: int, age: int) -> Dict:
    """Classify exercise intensity from heart rate as a percentage of HRmax."""
    max_hr = 220 - age
    if max_hr <= 0:
        return {"zone": "unknown", "percent_max": 0.0, "heart_rate": heart_rate, "max_heart_rate": max_hr}

    percent = max(0.0, min(1.5, heart_rate / max_hr))

    if percent < 0.57:
        zone, label = "very_light", "Very light — recovery pace"
    elif percent < 0.64:
        zone, label = "light", "Light — fat-burning base"
    elif percent < 0.76:
        zone, label = "moderate", "Moderate — aerobic base"
    elif percent < 0.89:
        zone, label = "vigorous", "Vigorous — threshold work"
    else:
        zone, label = "maximum", "Maximum — VO2max and sprint work"

    return {
        "heart_rate": heart_rate,
        "max_heart_rate": max_hr,
        "percent_max": round(percent * 100, 1),
        "zone": zone,
        "label": label,
    }

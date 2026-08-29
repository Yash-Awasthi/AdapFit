"""
Activity Recognition Engine

Automatic workout detection from accelerometer/gyroscope patterns,
step counting, distance estimation, and calorie burn calculation.
"""
from dataclasses import dataclass, field
from typing import Optional
import math
import statistics


@dataclass
class SensorReading:
    timestamp: float  # seconds
    accel_x: float  # m/s²
    accel_y: float
    accel_z: float
    gyro_x: float = 0  # rad/s
    gyro_y: float = 0
    gyro_z: float = 0


@dataclass
class UserProfile:
    weight_kg: float
    height_cm: float
    age: int
    sex: str  # "male" or "female"


# Activity detection thresholds (accelerometer magnitude)
ACTIVITY_PROFILES = {
    "stationary":  {"magnitude_range": (0.0, 0.3),  "variance_max": 0.01},
    "walking":     {"magnitude_range": (0.3, 1.5),  "variance_max": 0.5},
    "running":     {"magnitude_range": (1.5, 4.0),  "variance_max": 2.0},
    "cycling":     {"magnitude_range": (0.2, 0.8),  "variance_max": 0.3},
    "swimming":    {"magnitude_range": (0.5, 2.0),  "variance_max": 1.0},
    "weightlifting": {"magnitude_range": (1.0, 5.0), "variance_max": 3.0},
}


def detect_activity(readings: list[SensorReading], window_seconds: float = 5.0) -> dict:
    """
    Detect current activity from sensor data using magnitude + variance analysis.

    ponytail: heuristic thresholds, not ML. Upgrade to a trained model
    (e.g., TensorFlow Lite) for production accuracy.
    """
    if not readings:
        return {"activity": "unknown", "confidence": 0}

    # Compute acceleration magnitude for each reading
    magnitudes = [math.sqrt(r.accel_x**2 + r.accel_y**2 + r.accel_z**2) for r in readings]

    # Gravity-compensated magnitude (remove ~9.81)
    gravity = 9.81
    net_magnitudes = [max(0, m - gravity) for m in magnitudes]

    avg_mag = statistics.mean(net_magnitudes)
    variance = statistics.variance(net_magnitudes) if len(net_magnitudes) > 1 else 0

    # Match against activity profiles
    best_match = "stationary"
    best_confidence = 0.0

    for activity, profile in ACTIVITY_PROFILES.items():
        lo, hi = profile["magnitude_range"]
        if lo <= avg_mag <= hi and variance <= profile["variance_max"]:
            # Confidence based on how centered we are in the range
            mid = (lo + hi) / 2
            range_width = hi - lo
            distance_from_mid = abs(avg_mag - mid) / (range_width / 2) if range_width > 0 else 1
            confidence = max(0.3, 1.0 - distance_from_mid * 0.5)

            if confidence > best_confidence:
                best_match = activity
                best_confidence = confidence

    return {
        "activity": best_match,
        "confidence": round(best_confidence, 2),
        "avg_magnitude": round(avg_mag, 3),
        "variance": round(variance, 4),
        "reading_count": len(readings),
    }


def count_steps(readings: list[SensorReading], sensitivity: float = 1.2) -> dict:
    """
    Count steps from accelerometer data using peak detection.

    ponytail: simple threshold-based peak counting. Upgrade to
    Zero-Crossing orFFT-based counting for better accuracy.
    """
    if not readings:
        return {"steps": 0, "distance_m": 0, "cadence_spm": 0}

    magnitudes = [math.sqrt(r.accel_x**2 + r.accel_y**2 + r.accel_z**2) for r in readings]
    gravity = 9.81
    net = [m - gravity for m in magnitudes]

    # Simple peak detection
    threshold = statistics.mean([abs(n) for n in net]) * sensitivity
    steps = 0
    last_peak_idx = -10  # Minimum 10 samples between steps (~0.4s at 25Hz)

    for i in range(1, len(net) - 1):
        if (net[i] > net[i - 1] and net[i] > net[i + 1] and
            net[i] > threshold and i - last_peak_idx >= 10):
            steps += 1
            last_peak_idx = i

    # Duration
    if len(readings) >= 2:
        duration_s = readings[-1].timestamp - readings[0].timestamp
    else:
        duration_s = 0

    # Distance estimation (average stride length ~0.7m)
    stride_length_m = 0.7
    distance_m = steps * stride_length_m

    # Cadence (steps per minute)
    cadence_spm = (steps / duration_s * 60) if duration_s > 0 else 0

    return {
        "steps": steps,
        "distance_m": round(distance_m, 1),
        "distance_km": round(distance_m / 1000, 3),
        "duration_seconds": round(duration_s, 1),
        "cadence_spm": round(cadence_spm, 1),
        "stride_length_m": stride_length_m,
    }


def estimate_distance(steps: int, height_cm: float, sex: str) -> dict:
    """Estimate distance from step count using anthropometric stride model."""
    # Stride length estimation (National Institute for Occupational Safety)
    if sex == "male":
        stride_m = height_cm * 0.415 / 100
    else:
        stride_m = height_cm * 0.413 / 100

    distance_m = steps * stride_m
    return {
        "steps": steps,
        "stride_length_m": round(stride_m, 3),
        "distance_m": round(distance_m, 1),
        "distance_km": round(distance_m / 1000, 3),
    }


def calculate_calories(
    activity: str,
    duration_minutes: float,
    user: UserProfile,
    heart_rate: Optional[int] = None,
) -> dict:
    """
    Calculate calorie burn for an activity.

    Uses MET (Metabolic Equivalent of Task) values.
    ponytail: MET table, not individual metabolic modeling.
    """
    # MET values by activity
    met_values = {
        "stationary": 1.0,
        "walking": 3.5,
        "running": 8.0,
        "cycling": 6.0,
        "swimming": 7.0,
        "weightlifting": 5.0,
        "hiit": 12.0,
        "yoga": 2.5,
        "stretching": 2.0,
    }

    met = met_values.get(activity, 3.5)

    # Basic calorie calculation: MET × weight(kg) × duration(hours)
    hours = duration_minutes / 60
    calories = met * user.weight_kg * hours

    # Heart rate correction (Keytel et al. formula) if available
    hr_calories = None
    if heart_rate:
        if user.sex == "male":
            hr_calories = ((-55.0969 + (0.6309 * heart_rate) + (0.1988 * user.weight_kg) +
                           (0.2017 * user.age)) / 4.184) * duration_minutes
        else:
            hr_calories = ((-20.4022 + (0.4472 * heart_rate) - (0.1263 * user.weight_kg) +
                           (0.074 * user.age)) / 4.184) * duration_minutes

    # Use HR-based if available (more accurate), otherwise MET-based
    final_calories = round(hr_calories if hr_calories else calories)

    return {
        "calories": final_calories,
        "met": met,
        "activity": activity,
        "duration_minutes": round(duration_minutes, 1),
        "method": "heart_rate" if hr_calories else "met",
    }


def classify_intensity(heart_rate: int, age: int) -> dict:
    """Classify exercise intensity from heart rate."""
    max_hr = 208 - 0.7 * age
    intensity_pct = (heart_rate / max_hr * 100) if max_hr > 0 else 0

    if intensity_pct < 50:
        zone = "very_light"
        label = "Very Light (Warm-up)"
    elif intensity_pct < 60:
        zone = "light"
        label = "Light (Fat Burn)"
    elif intensity_pct < 70:
        zone = "moderate"
        label = "Moderate (Aerobic)"
    elif intensity_pct < 80:
        zone = "hard"
        label = "Hard (Threshold)"
    elif intensity_pct < 90:
        zone = "very_hard"
        label = "Very Hard (Anaerobic)"
    else:
        zone = "maximum"
        label = "Maximum (VO2 Max)"

    return {
        "heart_rate": heart_rate,
        "max_heart_rate": round(max_hr),
        "intensity_pct": round(intensity_pct, 1),
        "zone": zone,
        "label": label,
    }

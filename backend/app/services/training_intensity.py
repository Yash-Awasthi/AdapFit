"""Training Intensity Distribution Analytics.

Extracted from domestique (inspiration).
Polarization index, intensity distribution classification,
and measured capacity capping for endurance training.

All pure functions — no DB, no async.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


# Canonical centroids in (Z1+Z2%, Z3+Z4%, Z5+%) space
CLASSIFICATION_CENTROIDS = {
    "polarized": (80, 5, 15),
    "pyramidal": (80, 15, 5),
    "threshold": (60, 30, 10),
    "hiit": (40, 25, 35),
    "base": (95, 3, 2),
}

_BAND_PI_CENTRES = {
    "polarized": 2.5,
    "pyramidal": 1.5,
    "threshold": 0.75,
    "hiit": 0.25,
}

_BAND_PI_HALFWIDTH = {
    "polarized": 0.5,
    "pyramidal": 0.5,
    "threshold": 0.25,
    "hiit": 0.25,
}

# Capacity cap constants
TAU_S = 26.0  # envelope decay time constant (seconds)
QUAL_RATIO = 1.20  # qualifying rep ratio
QUAL_MAX_ON_S = 120  # max on-duration for qualifying
TOO_HARD = 0.95  # cap trigger threshold
CAP_FRAC = 0.90  # cap target fraction
VO2_FLOOR = 1.06  # minimum ratio for vo2 reps


@dataclass
class IntensityDistribution:
    """Training intensity distribution breakdown."""
    z1z2_pct: float = 0.0  # Easy (recovery + endurance)
    z3z4_pct: float = 0.0  # Moderate (tempo + threshold)
    z5plus_pct: float = 0.0  # Hard (VO2max + anaerobic)
    total_tss: float = 0.0
    total_hours: float = 0.0


@dataclass
class Classification:
    """Intensity distribution classification."""
    label: str = "unknown"
    pi_additive: Optional[float] = None
    pi_multiplicative: Optional[float] = None
    confidence: float = 0.0
    description: str = ""


def polarization_index(
    z1z2_pct: float,
    z3z4_pct: float,
    z5plus_pct: float,
) -> Optional[float]:
    """Additive polarization index.

    PI = log10((Z1+Z2 + Z5+) / Z3+Z4)

    >0 = polarized, ~0 = pyramidal, <0 = inverted

    Args:
        z1z2_pct: Percentage of training in Z1+Z2 (0-100)
        z3z4_pct: Percentage of training in Z3+Z4 (0-100)
        z5plus_pct: Percentage of training in Z5+ (0-100)

    Returns:
        PI value, or None if Z3+Z4 is near zero
    """
    if z3z4_pct < 0.1:
        return None
    try:
        return round(math.log10((z1z2_pct + z5plus_pct) / z3z4_pct), 2)
    except (ValueError, ZeroDivisionError):
        return None


def treff_polarization_index(
    z1z2_pct: float,
    z3z4_pct: float,
    z5plus_pct: float,
) -> Optional[float]:
    """Treff 2019 multiplicative polarization index.

    PI = log10((Z1+Z2 × Z5+) / Z3+Z4)

    Rewards genuine two-pole shape: high easy AND hard with suppressed middle.

    Args:
        z1z2_pct: Percentage in Z1+Z2 (0-100)
        z3z4_pct: Percentage in Z3+Z4 (0-100)
        z5plus_pct: Percentage in Z5+ (0-100)

    Returns:
        Treff PI value, or None if Z3+Z4 is near zero
    """
    if z3z4_pct < 0.1:
        return None
    try:
        return round(math.log10((z1z2_pct * z5plus_pct) / z3z4_pct), 2)
    except (ValueError, ZeroDivisionError):
        return None


def classify_distribution(
    z1z2_pct: float,
    z3z4_pct: float,
    z5plus_pct: float,
) -> Classification:
    """Classify training intensity distribution.

    Uses PI-band cascade (Treff 2019) with centroid confidence scoring.

    Args:
        z1z2_pct: Percentage in Z1+Z2
        z3z4_pct: Percentage in Z3+Z4
        z5plus_pct: Percentage in Z5+

    Returns:
        Classification with label, PI values, and confidence
    """
    pi_add = polarization_index(z1z2_pct, z3z4_pct, z5plus_pct)
    pi_mult = treff_polarization_index(z1z2_pct, z3z4_pct, z5plus_pct)

    # PI-band cascade classification (check base first, then PI thresholds)
    label = "unknown"
    description = ""

    if z1z2_pct > 90 and z3z4_pct < 10:
        label = "base"
        description = "Base building: almost all aerobic training"
    elif pi_mult is not None and pi_mult > 2.0:
        label = "polarized"
        description = "Polarized training: mostly easy + hard, minimal moderate"
    elif z5plus_pct > 30:
        label = "hiit"
        description = "HIIT-heavy: substantial high-intensity work"
    elif pi_add is not None and pi_add >= 0.75:
        label = "pyramidal"
        description = "Pyramidal distribution: decreasing from easy to hard"
    elif pi_add is not None and pi_add > 0.25:
        label = "threshold"
        description = "Threshold-focused: heavy on Z3+Z4 work"
    else:
        label = "pyramidal"
        description = "Mixed distribution"

    # Confidence from centroid distance
    point = (z1z2_pct, z3z4_pct, z5plus_pct)
    min_dist = float("inf")
    closest = label
    for centroid_label, centroid in CLASSIFICATION_CENTROIDS.items():
        dist = math.sqrt(sum((p - c) ** 2 for p, c in zip(point, centroid)))
        if dist < min_dist:
            min_dist = dist
            closest = centroid_label

    # Map PI distance to confidence
    if label in _BAND_PI_CENTRES and pi_add is not None:
        pi_dist = abs(pi_add - _BAND_PI_CENTRES[label])
        halfwidth = _BAND_PI_HALFWIDTH[label]
        confidence = max(0.5, min(1.0, 1.0 - pi_dist / (2 * halfwidth)))
    else:
        confidence = max(0.5, min(1.0, 1.0 - min_dist / 70.0))

    return Classification(
        label=label,
        pi_additive=pi_add,
        pi_multiplicative=pi_mult,
        confidence=round(confidence, 3),
        description=description,
    )


def compute_distribution_from_sessions(
    sessions: list[dict],
) -> IntensityDistribution:
    """Compute intensity distribution from training sessions.

    Each session should have: 'tss', 'z1z2_pct', 'z3z4_pct', 'z5plus_pct',
    'duration_hours'.

    Args:
        sessions: List of session dictionaries

    Returns:
        IntensityDistribution with weighted averages
    """
    if not sessions:
        return IntensityDistribution()

    total_tss = sum(s.get("tss", 0) for s in sessions)
    if total_tss == 0:
        return IntensityDistribution()

    weighted_z1z2 = sum(s.get("z1z2_pct", 0) * s.get("tss", 0) for s in sessions) / total_tss
    weighted_z3z4 = sum(s.get("z3z4_pct", 0) * s.get("tss", 0) for s in sessions) / total_tss
    weighted_z5plus = sum(s.get("z5plus_pct", 0) * s.get("tss", 0) for s in sessions) / total_tss
    total_hours = sum(s.get("duration_hours", 0) for s in sessions)

    return IntensityDistribution(
        z1z2_pct=round(weighted_z1z2, 1),
        z3z4_pct=round(weighted_z3z4, 1),
        z5plus_pct=round(weighted_z5plus, 1),
        total_tss=total_tss,
        total_hours=round(total_hours, 1),
    )


# --- Capacity Capping ---

def pmax_envelope(t: float, cp: float, pmax: float) -> float:
    """Measured max-power envelope at duration t seconds.

    P_env(t) = CP + (Pmax - CP) * exp(-t / TAU_S)

    Args:
        t: Duration in seconds
        cp: Critical Power (watts)
        pmax: Measured maximum power (watts)

    Returns:
        Maximum sustainable power at duration t
    """
    if t < 0:
        t = 0.0
    return cp + (pmax - cp) * math.exp(-t / TAU_S)


def should_cap_rep(
    prescribed_ratio: float,
    duration_s: float,
    cp: float,
    pmax: float,
) -> bool:
    """Determine if a rep should be capped to the rider's envelope.

    Args:
        prescribed_ratio: Prescribed power as ratio of FTP
        duration_s: Rep duration in seconds
        cp: Critical Power (watts)
        pmax: Measured maximum power (watts)
        ftp: Functional Threshold Power (watts)

    Returns:
        True if the rep exceeds the rider's measured envelope
    """
    if duration_s <= 0 or duration_s > QUAL_MAX_ON_S:
        return False
    if prescribed_ratio < QUAL_RATIO:
        return False

    env_power = pmax_envelope(duration_s, cp, pmax)
    ftp = cp  # Assume FTP ≈ CP for ratio calculation
    if ftp <= 0:
        return False

    prescribed_power = prescribed_ratio * ftp
    env_ratio = env_power / ftp

    return prescribed_ratio > TOO_HARD * env_ratio


def cap_rep_power(
    prescribed_ratio: float,
    duration_s: float,
    cp: float,
    pmax: float,
    ftp: float,
) -> Optional[float]:
    """Cap a rep's power to the rider's measured envelope.

    Args:
        prescribed_ratio: Prescribed power ratio
        duration_s: Rep duration in seconds
        cp: Critical Power (watts)
        pmax: Measured maximum power (watts)
        ftp: Functional Threshold Power (watts)

    Returns:
        Capped ratio, or None if no capping needed
    """
    if not should_cap_rep(prescribed_ratio, duration_s, cp, pmax):
        return None

    env_power = pmax_envelope(duration_s, cp, pmax)
    env_ratio = env_power / ftp if ftp > 0 else 0.0

    # Cap at 90% of envelope, but never below VO2 floor
    cap_ratio = CAP_FRAC * env_ratio
    is_vo2 = prescribed_ratio < 1.20 + 1e-9
    floor = VO2_FLOOR if is_vo2 else 1.0
    cap_ratio = max(floor, min(cap_ratio, prescribed_ratio))

    return round(cap_ratio, 3)


def analyze_weekly_distribution(
    weekly_tss: list[float],
    weekly_z1z2: list[float],
    weekly_z3z4: list[float],
    weekly_z5plus: list[float],
) -> dict:
    """Analyze training distribution trends over multiple weeks.

    Args:
        weekly_tss: Weekly TSS values
        weekly_z1z2: Weekly Z1+Z2 percentages
        weekly_z3z4: Weekly Z3+Z4 percentages
        weekly_z5plus: Weekly Z5+ percentages

    Returns:
        Weekly distribution analysis with trends
    """
    if not weekly_tss:
        return {"weeks": 0, "avg_distribution": None, "trend": "insufficient_data"}

    n = len(weekly_tss)

    avg_z1z2 = sum(weekly_z1z2) / n
    avg_z3z4 = sum(weekly_z3z4) / n
    avg_z5plus = sum(weekly_z5plus) / n

    classification = classify_distribution(avg_z1z2, avg_z3z4, avg_z5plus)

    # Trend: compare first half to second half
    if n >= 4:
        mid = n // 2
        first_half_z5 = sum(weekly_z5plus[:mid]) / mid
        second_half_z5 = sum(weekly_z5plus[mid:]) / (n - mid)
        if second_half_z5 > first_half_z5 * 1.1:
            trend = "increasing_intensity"
        elif second_half_z5 < first_half_z5 * 0.9:
            trend = "decreasing_intensity"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"

    return {
        "weeks": n,
        "avg_tss": round(sum(weekly_tss) / n, 0),
        "avg_distribution": {
            "z1z2_pct": round(avg_z1z2, 1),
            "z3z4_pct": round(avg_z3z4, 1),
            "z5plus_pct": round(avg_z5plus, 1),
        },
        "classification": classification.label,
        "pi_additive": classification.pi_additive,
        "pi_multiplicative": classification.pi_multiplicative,
        "confidence": classification.confidence,
        "trend": trend,
    }

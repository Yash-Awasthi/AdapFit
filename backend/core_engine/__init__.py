"""
AdapFit Core Engine — High-Performance Computation Module
Tries to import the Rust PyO3 extension (10-100x faster).
Falls back to pure Python implementations automatically.
"""
import math
from typing import List, Tuple, Optional

try:
    from core_engine import (
        compute_hrv_zscore,
        compute_sleep_score,
        compute_acwr,
        compute_ewma,
        compute_recovery_score,
        detect_anomalies,
        detect_injury_risk,
        compute_subjective_score,
    )
    _RUST_AVAILABLE = True
except ImportError:
    _RUST_AVAILABLE = False

    def compute_hrv_zscore(today_hrv: float, baseline_mean: float = 50.0, baseline_std: float = 10.0) -> Tuple[float, float]:
        std = baseline_std if baseline_std > 0.1 else 10.0
        z_score = (today_hrv - baseline_mean) / std
        hrv_score = max(0.0, min(100.0, 50.0 + z_score * 25.0))
        return round(z_score, 2), round(hrv_score, 1)

    def compute_sleep_score(sleep_hours: float, efficiency: float = 85.0, target_hours: float = 8.0) -> float:
        duration_ratio = min(1.0, sleep_hours / target_hours)
        duration_score = duration_ratio * 100.0
        efficiency_score = max(0.0, min(100.0, efficiency))
        score = 0.70 * duration_score + 0.30 * efficiency_score
        return round(max(0.0, min(100.0, score)), 1)

    def compute_acwr(acute_load: float, chronic_load: float) -> Tuple[float, str, float]:
        if chronic_load <= 0:
            return 1.0, "SWEET_SPOT", 0.0
        acwr = round(acute_load / chronic_load, 2)
        if acwr < 0.80:
            return acwr, "UNDER_TRAINING", 0.0
        elif acwr <= 1.30:
            return acwr, "SWEET_SPOT", 0.0
        elif acwr < 1.50:
            return acwr, "CAUTION", -5.0
        else:
            return acwr, "DANGER_ZONE", -15.0

    def compute_ewma(values: List[float], window: int) -> List[float]:
        if not values:
            return []
        alpha = 2.0 / (window + 1)
        result = [values[0]]
        for i in range(1, len(values)):
            ewma = alpha * values[i] + (1 - alpha) * result[-1]
            result.append(round(ewma, 2))
        return result

    def compute_recovery_score(hrv_score: float, sleep_score: float, subj_score: float, acwr_penalty: float, has_hrv: bool) -> int:
        if has_hrv:
            raw = 0.40 * hrv_score + 0.35 * sleep_score + 0.25 * subj_score + acwr_penalty
        else:
            raw = 0.55 * sleep_score + 0.45 * subj_score + acwr_penalty
        return int(max(0.0, min(100.0, round(raw))))

    def detect_anomalies(values: List[float], threshold: float = 2.0) -> List[bool]:
        if len(values) < 3:
            return [False] * len(values)
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std = math.sqrt(variance)
        if std < 0.001:
            return [False] * len(values)
        return [abs((v - mean) / std) > threshold for v in values]

    def detect_injury_risk(acwr: float, hrv_trend_slope: float, sleep_debt_hours: float, consecutive_high_load_days: int) -> float:
        risk = 0.0
        if acwr > 1.5: risk += 35.0
        elif acwr > 1.3: risk += 20.0
        elif acwr < 0.8: risk += 10.0
        if hrv_trend_slope < -2.0: risk += 25.0
        elif hrv_trend_slope < -1.0: risk += 15.0
        elif hrv_trend_slope < -0.5: risk += 8.0
        if sleep_debt_hours > 4.0: risk += 20.0
        elif sleep_debt_hours > 2.0: risk += 12.0
        elif sleep_debt_hours > 1.0: risk += 6.0
        if consecutive_high_load_days >= 5: risk += 20.0
        elif consecutive_high_load_days >= 3: risk += 12.0
        elif consecutive_high_load_days >= 2: risk += 6.0
        return round(max(0.0, min(100.0, risk)), 1)

    def compute_subjective_score(soreness: int, fatigue: int, stress: int, num_sore_groups: int) -> float:
        sore = max(1, min(10, soreness))
        energy = max(1, min(10, fatigue))
        stress_inv = 11 - max(1, min(10, stress))
        muscle_penalty = 10.0 if num_sore_groups == 0 else max(2.0, 10.0 - num_sore_groups * 2.0)
        total = sore + energy + stress_inv + muscle_penalty
        return round(max(0.0, min(100.0, total / 40.0 * 100.0)), 1)


def is_rust_available() -> bool:
    return _RUST_AVAILABLE

__all__ = [
    "compute_hrv_zscore",
    "compute_sleep_score",
    "compute_acwr",
    "compute_ewma",
    "compute_recovery_score",
    "detect_anomalies",
    "detect_injury_risk",
    "compute_subjective_score",
    "is_rust_available",
]

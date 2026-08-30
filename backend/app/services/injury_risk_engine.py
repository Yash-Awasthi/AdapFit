"""
Injury Risk Detection Engine — Athlete injury risk from training metrics
Inspired by athlete-injury-risk-detection: ACWR, rolling features, risk factor decomposition

Patterns extracted:
- ACWR (Acute:Chronic Workload Ratio) with zone classification
- Rolling window features (7/14/28-day)
- Risk factor decomposition with explainability
- Composite risk score (weighted sum)
- HR delta from baseline
- Workload trend calculation
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class ACWRZone(Enum):
    UNDER = "under"
    OPTIMAL = "optimal"
    ELEVATED = "elevated"
    DANGER = "danger"


@dataclass
class DailyMetrics:
    date: float
    training_load: float
    soreness: float  # 0-10 scale
    sleep_hours: float
    resting_hr: float
    baseline_hr: float = 60.0
    previous_injuries: int = 0
    days_since_injury: float = 365.0
    injury_prone: bool = False


@dataclass
class RiskFactor:
    code: str
    label: str
    detail: str
    contribution: float
    severity: str  # "high", "moderate", "info"


@dataclass
class InjuryRiskResult:
    risk_score: float
    risk_level: RiskLevel
    risk_factors: List[RiskFactor]
    acwr: float
    acwr_zone: ACWRZone
    acute_load: float
    chronic_load: float
    load_trend: float
    hr_delta: float
    recommendations: List[str]


# ── Domain Constants (from athlete-injury-risk-detection config) ────────────

# ACWR windows
ACUTE_WINDOW = 7
CHRONIC_WINDOW = 28
ROLLING_WINDOWS = (7, 14, 28)
LOAD_TREND_WINDOW = 7

# ACWR zone bounds
ACWR_DANGER = 1.5
ACWR_ELEVATED = 1.3
ACWR_UNDER = 0.8

# Risk factor weights
W_ACWR_DANGER = 0.35
W_ACWR_ELEVATED = 0.18
W_ACWR_UNDER = 0.08
W_SORENESS = 0.20
W_SLEEP = 0.15
W_RESTING_HR = 0.12
W_INJURY_PRONE = 0.10
W_PREVIOUS_INJURIES = 0.08
W_RECENT_RETURN = 0.10

# Normalization ranges
SORENESS_ONSET = 4.0
SORENESS_RANGE = 6.0
SLEEP_TARGET = 7.0
SLEEP_RANGE = 4.0
HR_DELTA_RANGE = 20.0
PREVIOUS_INJURIES_RANGE = 5.0
RECENT_RETURN_DAYS = 60

# Risk level thresholds
RISK_LOW_THRESHOLD = 0.16
RISK_HIGH_THRESHOLD = 0.27


class InjuryRiskEngine:
    """Pure function injury risk detection from training metrics."""

    # ── ACWR Calculation ──────────────────────────────────────────────────

    @staticmethod
    def calculate_acwr(loads: List[float]) -> Tuple[float, float, float, ACWRZone]:
        """Calculate Acute:Chronic Workload Ratio.
        
        Returns: (acute_load, chronic_load, acwr, zone)
        """
        if len(loads) < ACUTE_WINDOW:
            acute = sum(loads) / len(loads) if loads else 0
            chronic = acute
            return acute, chronic, 1.0, ACWRZone.OPTIMAL

        # Acute load: 7-day mean
        acute = sum(loads[-ACUTE_WINDOW:]) / ACUTE_WINDOW

        # Chronic load: 28-day mean
        chronic_window = loads[-CHRONIC_WINDOW:] if len(loads) >= CHRONIC_WINDOW else loads
        chronic = sum(chronic_window) / len(chronic_window)

        # ACWR ratio
        if chronic == 0:
            acwr = 1.0
        else:
            acwr = acute / chronic

        # Zone classification
        if acwr >= ACWR_DANGER:
            zone = ACWRZone.DANGER
        elif acwr >= ACWR_ELEVATED:
            zone = ACWRZone.ELEVATED
        elif acwr < ACWR_UNDER:
            zone = ACWRZone.UNDER
        else:
            zone = ACWRZone.OPTIMAL

        return round(acute, 2), round(chronic, 2), round(acwr, 3), zone

    @staticmethod
    def acwr_zone_label(zone: ACWRZone) -> str:
        labels = {
            ACWRZone.UNDER: "Under-training (detraining risk)",
            ACWRZone.OPTIMAL: "Optimal load zone",
            ACWRZone.ELEVATED: "Elevated load (monitor closely)",
            ACWRZone.DANGER: "Danger zone (high injury risk)",
        }
        return labels[zone]

    # ── Rolling Features ──────────────────────────────────────────────────

    @staticmethod
    def calculate_rolling_mean(values: List[float], window: int) -> float:
        if not values:
            return 0.0
        recent = values[-window:] if len(values) >= window else values
        return sum(recent) / len(recent)

    @staticmethod
    def calculate_rolling_features(values: List[float]) -> Dict[str, float]:
        """Calculate 7/14/28-day rolling means."""
        return {
            "7d": InjuryRiskEngine.calculate_rolling_mean(values, 7),
            "14d": InjuryRiskEngine.calculate_rolling_mean(values, 14),
            "28d": InjuryRiskEngine.calculate_rolling_mean(values, 28),
        }

    @staticmethod
    def calculate_load_trend(loads: List[float], window: int = LOAD_TREND_WINDOW) -> float:
        """Calculate workload trend (slope) over window."""
        if len(loads) < 2:
            return 0.0
        recent = loads[-window:] if len(loads) >= window else loads
        n = len(recent)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(recent) / n
        numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, recent))
        denominator = sum((xi - x_mean) ** 2 for xi in x)
        if denominator == 0:
            return 0.0
        return round(numerator / denominator, 4)

    # ── Risk Factor Decomposition ─────────────────────────────────────────

    @staticmethod
    def _acwr_factor(acwr: float) -> RiskFactor:
        """The ACWR factor — the single most important risk factor."""
        if acwr >= ACWR_DANGER:
            return RiskFactor(
                "acwr_danger",
                f"ACWR in danger zone (> {ACWR_DANGER})",
                f"Acute load far above chronic habit (ACWR {acwr:.2f})",
                W_ACWR_DANGER,
                "high",
            )
        if acwr >= ACWR_ELEVATED:
            return RiskFactor(
                "acwr_elevated",
                f"Elevated ACWR ({ACWR_ELEVATED}–{ACWR_DANGER})",
                f"Rising load, worth monitoring (ACWR {acwr:.2f})",
                W_ACWR_ELEVATED,
                "moderate",
            )
        if acwr < ACWR_UNDER:
            return RiskFactor(
                "acwr_under",
                f"Low ACWR (< {ACWR_UNDER})",
                f"Possible under-loading / detraining (ACWR {acwr:.2f})",
                W_ACWR_UNDER,
                "info",
            )
        return RiskFactor("acwr_optimal", "ACWR optimal", f"ACWR {acwr:.2f}", 0.0, "info")

    @staticmethod
    def _soreness_factor(soreness: float) -> RiskFactor:
        contribution = max(0.0, min(1.0, (soreness - SORENESS_ONSET) / SORENESS_RANGE)) * W_SORENESS
        severity = "high" if soreness >= 7 else "moderate" if soreness >= SORENESS_ONSET else "info"
        return RiskFactor(
            "soreness",
            "High soreness",
            f"{soreness:.1f}/10 (counts above {SORENESS_ONSET:.0f})",
            round(contribution, 3),
            severity,
        )

    @staticmethod
    def _sleep_factor(sleep_hours: float) -> RiskFactor:
        contribution = max(0.0, min(1.0, (SLEEP_TARGET - sleep_hours) / SLEEP_RANGE)) * W_SLEEP
        severity = "high" if sleep_hours < 5 else "moderate" if sleep_hours < SLEEP_TARGET else "info"
        return RiskFactor(
            "sleep",
            "Insufficient sleep",
            f"{sleep_hours:.1f} h/night (target {SLEEP_TARGET:.0f} h)",
            round(contribution, 3),
            severity,
        )

    @staticmethod
    def _hr_factor(resting_hr: float, baseline_hr: float) -> RiskFactor:
        hr_delta = resting_hr - baseline_hr
        contribution = max(0.0, min(1.0, hr_delta / HR_DELTA_RANGE)) * W_RESTING_HR
        severity = "high" if hr_delta > 15 else "moderate" if hr_delta > 5 else "info"
        return RiskFactor(
            "resting_hr",
            "Elevated resting heart rate",
            f"+{hr_delta:.0f} bpm above baseline ({baseline_hr:.0f} → {resting_hr:.0f})",
            round(contribution, 3),
            severity,
        )

    @staticmethod
    def _injury_history_factor(previous_injuries: int, days_since_injury: float) -> List[RiskFactor]:
        factors = []
        # Previous injuries
        history_c = max(0.0, min(1.0, previous_injuries / PREVIOUS_INJURIES_RANGE)) * W_PREVIOUS_INJURIES
        if history_c > 0:
            factors.append(RiskFactor(
                "previous_injuries",
                "Injury history",
                f"{previous_injuries} previous injuries",
                round(history_c, 3),
                "moderate",
            ))
        # Recent return
        if days_since_injury < RECENT_RETURN_DAYS:
            recent_c = W_RECENT_RETURN * (1 - days_since_injury / RECENT_RETURN_DAYS)
            factors.append(RiskFactor(
                "recent_return",
                "Recently returned from injury",
                f"{days_since_injury:.0f} days since last injury (within {RECENT_RETURN_DAYS}d window)",
                round(recent_c, 3),
                "high" if days_since_injury < 14 else "moderate",
            ))
        return factors

    @staticmethod
    def _injury_prone_factor(injury_prone: bool) -> Optional[RiskFactor]:
        if injury_prone:
            return RiskFactor(
                "injury_prone",
                "Injury-prone athlete",
                "Flagged as injury-prone based on history",
                W_INJURY_PRONE,
                "moderate",
            )
        return None

    # ── Composite Risk Score ──────────────────────────────────────────────

    @classmethod
    def calculate_risk_factors(cls, metrics: DailyMetrics, acwr: float) -> List[RiskFactor]:
        """Calculate all risk factors for a given day's metrics."""
        factors = [cls._acwr_factor(acwr)]
        factors.append(cls._soreness_factor(metrics.soreness))
        factors.append(cls._sleep_factor(metrics.sleep_hours))
        factors.append(cls._hr_factor(metrics.resting_hr, metrics.baseline_hr))
        factors.extend(cls._injury_history_factor(metrics.previous_injuries, metrics.days_since_injury))
        prone = cls._injury_prone_factor(metrics.injury_prone)
        if prone:
            factors.append(prone)
        return factors

    @staticmethod
    def composite_risk_score(factors: List[RiskFactor]) -> float:
        """Sum of factor contributions (0-1 scale)."""
        return round(sum(f.contribution for f in factors), 3)

    @staticmethod
    def classify_risk(score: float) -> RiskLevel:
        if score >= RISK_HIGH_THRESHOLD:
            return RiskLevel.HIGH
        elif score >= RISK_LOW_THRESHOLD:
            return RiskLevel.MODERATE
        return RiskLevel.LOW

    # ── Recommendations ───────────────────────────────────────────────────

    @staticmethod
    def generate_recommendations(factors: List[RiskFactor], risk_level: RiskLevel) -> List[str]:
        recs = []
        active = [f for f in factors if f.contribution > 0]
        if risk_level == RiskLevel.HIGH:
            recs.append("⚠️ HIGH RISK — Consider reducing training load or taking a rest day")
        for f in active:
            if f.code == "acwr_danger":
                recs.append("Reduce acute training load immediately — ACWR exceeds safe zone")
            elif f.code == "acwr_elevated":
                recs.append("Monitor load closely — ACWR is rising above optimal range")
            elif f.code == "acwr_under":
                recs.append("Consider increasing training load — possible detraining")
            elif f.code == "soreness":
                recs.append("Address muscle soreness — consider recovery protocols (foam rolling, massage)")
            elif f.code == "sleep":
                recs.append("Prioritize sleep — aim for 7+ hours for optimal recovery")
            elif f.code == "resting_hr":
                recs.append("Elevated resting HR detected — may indicate overtraining or illness")
            elif f.code == "recent_return":
                recs.append("Recently returned from injury — progress gradually")
        if not recs:
            recs.append("✅ All metrics within normal range — continue current training")
        return recs

    # ── Main Analysis ─────────────────────────────────────────────────────

    @classmethod
    def analyze(cls, metrics: DailyMetrics, historical_loads: Optional[List[float]] = None) -> InjuryRiskResult:
        """Full injury risk analysis for a single day."""
        loads = historical_loads or [metrics.training_load]
        acute, chronic, acwr, zone = cls.calculate_acwr(loads)
        load_trend = cls.calculate_load_trend(loads)
        hr_delta = metrics.resting_hr - metrics.baseline_hr
        factors = cls.calculate_risk_factors(metrics, acwr)
        score = cls.composite_risk_score(factors)
        risk_level = cls.classify_risk(score)
        recommendations = cls.generate_recommendations(factors, risk_level)
        return InjuryRiskResult(
            risk_score=score,
            risk_level=risk_level,
            risk_factors=factors,
            acwr=acwr,
            acwr_zone=zone,
            acute_load=acute,
            chronic_load=chronic,
            load_trend=load_trend,
            hr_delta=round(hr_delta, 1),
            recommendations=recommendations,
        )

    @classmethod
    def analyze_series(cls, metrics_list: List[DailyMetrics]) -> List[InjuryRiskResult]:
        """Analyze a time series of daily metrics, building up historical context."""
        results = []
        historical_loads = []
        for m in metrics_list:
            historical_loads.append(m.training_load)
            result = cls.analyze(m, historical_loads)
            results.append(result)
        return results

    @staticmethod
    def get_acwr_zone_info() -> Dict:
        return {
            "zones": {
                "under": {"range": "0.0 – 0.8", "meaning": "Under-training / detraining"},
                "optimal": {"range": "0.8 – 1.3", "meaning": "Sweet spot for adaptation"},
                "elevated": {"range": "1.3 – 1.5", "meaning": "Rising load, monitor closely"},
                "danger": {"range": "> 1.5", "meaning": "High injury risk zone"},
            },
            "optimal_range": (0.8, 1.3),
            "danger_threshold": ACWR_DANGER,
        }

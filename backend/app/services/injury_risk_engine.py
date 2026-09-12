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


# ── Body regions ────────────────────────────────────────────────────────────
# Session RPE above `high_risk_rpe` on a session that loads the region is the
# signal the region endpoint reports on.

MUSCLE_VULNERABILITY: Dict[str, Dict] = {
    "lower_back": {
        "high_risk_rpe": 8.0,
        "common_in": ["deadlift", "barbell row", "back squat", "good morning"],
        "baseline_injury_share": 0.22,
    },
    "knee": {
        "high_risk_rpe": 8.5,
        "common_in": ["back squat", "lunge", "leg press", "box jump"],
        "baseline_injury_share": 0.18,
    },
    "shoulder": {
        "high_risk_rpe": 8.0,
        "common_in": ["overhead press", "bench press", "pull-up", "lateral raise"],
        "baseline_injury_share": 0.17,
    },
    "hamstrings": {
        "high_risk_rpe": 8.5,
        "common_in": ["romanian deadlift", "sprint", "leg curl", "kettlebell swing"],
        "baseline_injury_share": 0.12,
    },
    "ankle": {
        "high_risk_rpe": 7.5,
        "common_in": ["box jump", "running", "calf raise", "lateral bound"],
        "baseline_injury_share": 0.11,
    },
    "elbow": {
        "high_risk_rpe": 8.0,
        "common_in": ["bench press", "triceps extension", "pull-up", "skull crusher"],
        "baseline_injury_share": 0.07,
    },
    "wrist": {
        "high_risk_rpe": 7.5,
        "common_in": ["front squat", "push-up", "overhead press", "handstand"],
        "baseline_injury_share": 0.06,
    },
    "groin": {
        "high_risk_rpe": 8.5,
        "common_in": ["lunge", "lateral lunge", "sprint", "sumo deadlift"],
        "baseline_injury_share": 0.07,
    },
}

# Which region an exercise name exercises, checked in order.
REGION_EXERCISE_HINTS: List[tuple] = [
    ("lower_back", ("deadlift", "good morning", "back extension", "barbell row")),
    ("knee", ("squat", "lunge", "leg press", "leg extension", "box jump")),
    ("shoulder", ("overhead press", "ohp", "lateral raise", "pull-up", "chin-up", "bench press")),
    ("hamstrings", ("romanian", "rdl", "leg curl", "nordic", "sprint")),
    ("ankle", ("calf raise", "running", "treadmill", "bound")),
    ("elbow", ("triceps", "skull crusher", "pushdown", "curl")),
    ("wrist", ("push-up", "handstand", "front squat", "wrist")),
    ("groin", ("sumo", "adductor", "lateral lunge", "copenhagen")),
]


def _region_for_exercise(name: str) -> Optional[str]:
    lowered = name.lower()
    for region, hints in REGION_EXERCISE_HINTS:
        if any(hint in lowered for hint in hints):
            return region
    return None


# ── Endpoint-facing facade ──────────────────────────────────────────────────
# Storage returns plain dicts, while the engine analyses DailyMetrics. This
# facade joins the two log streams by calendar day and exposes the analysis as
# JSON-ready dicts, which is the shape the injury-risk endpoints return.

def _log_day(log: Dict) -> Optional[str]:
    raw = log.get("log_date") or log.get("completed_at") or log.get("created_at") or log.get("date")
    if not raw:
        return None
    return str(raw)[:10]


def _as_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _daily_metrics_from(workout_logs: List[Dict], recovery_logs: List[Dict]) -> List[DailyMetrics]:
    """Join workout and recovery logs into one DailyMetrics per calendar day."""
    recovery_by_day = {_log_day(r): r for r in recovery_logs if _log_day(r)}
    loads_by_day: Dict[str, float] = {}
    rpe_by_day: Dict[str, float] = {}

    for log in workout_logs:
        day = _log_day(log)
        if not day:
            continue
        load = _as_float(log.get("session_load"))
        if load is None:
            # Older logs predate the EWMA pipeline and only carry duration and RPE.
            duration = _as_float(log.get("actual_duration_minutes")) or 0.0
            rpe = _as_float(log.get("session_rpe")) or 0.0
            load = duration * rpe
        loads_by_day[day] = loads_by_day.get(day, 0.0) + load
        rpe = _as_float(log.get("session_rpe"))
        if rpe is not None:
            rpe_by_day[day] = max(rpe_by_day.get(day, 0.0), rpe)

    baseline_hr = 60.0
    recorded_hrs = [
        hr for hr in (_as_float(r.get("resting_heart_rate")) for r in recovery_logs) if hr
    ]
    if recorded_hrs:
        baseline_hr = round(sum(recorded_hrs) / len(recorded_hrs), 1)

    days = sorted(set(loads_by_day) | set(recovery_by_day))
    metrics: List[DailyMetrics] = []
    for index, day in enumerate(days):
        recovery = recovery_by_day.get(day, {})
        metrics.append(
            DailyMetrics(
                date=float(index),
                training_load=round(loads_by_day.get(day, 0.0), 1),
                soreness=_as_float(recovery.get("soreness_score")) or 0.0,
                sleep_hours=_as_float(recovery.get("sleep_duration_hours")) or SLEEP_TARGET,
                resting_hr=_as_float(recovery.get("resting_heart_rate")) or baseline_hr,
                baseline_hr=baseline_hr,
            )
        )
    return metrics


def _serialize(result: InjuryRiskResult) -> Dict:
    return {
        "risk_score": result.risk_score,
        "risk_level": result.risk_level.value,
        "risk_factors": [
            {
                "code": f.code,
                "label": f.label,
                "detail": f.detail,
                "contribution": f.contribution,
                "severity": f.severity,
            }
            for f in result.risk_factors
        ],
        "acwr": result.acwr,
        "acwr_zone": result.acwr_zone.value,
        "acute_load": result.acute_load,
        "chronic_load": result.chronic_load,
        "load_trend": result.load_trend,
        "hr_delta": result.hr_delta,
        "recommendations": result.recommendations,
    }


class _InjuryRiskFacade:
    """Dict-in, dict-out entry points for the injury-risk endpoints."""

    def analyze(
        self,
        workout_logs: List[Dict],
        recovery_logs: List[Dict],
        injury_history: Optional[List[Dict]] = None,
    ) -> Dict:
        metrics = _daily_metrics_from(workout_logs, recovery_logs)
        if not metrics:
            return {
                "risk_score": 0.0,
                "risk_level": RiskLevel.LOW.value,
                "risk_factors": [],
                "acwr": 1.0,
                "acwr_zone": ACWRZone.OPTIMAL.value,
                "acute_load": 0.0,
                "chronic_load": 0.0,
                "load_trend": 0.0,
                "hr_delta": 0.0,
                "recommendations": ["Log training and recovery data to see an injury risk estimate."],
                "days_analyzed": 0,
            }

        history = injury_history or []
        current = metrics[-1]
        current.previous_injuries = len(history)
        for injury in history:
            days_ago = _as_float(injury.get("days_ago"))
            if days_ago is not None:
                current.days_since_injury = min(current.days_since_injury, days_ago)
        current.injury_prone = bool(history)

        result = InjuryRiskEngine.analyze(current, [m.training_load for m in metrics])
        payload = _serialize(result)
        payload["days_analyzed"] = len(metrics)
        payload["previous_injuries"] = len(history)
        return payload

    def predict_region_risk(self, workout_logs: List[Dict], region: str) -> Dict:
        key = region.strip().lower().replace("-", "_").replace(" ", "_")
        profile = MUSCLE_VULNERABILITY.get(key)
        if profile is None:
            raise KeyError(region)

        sessions = 0
        high_risk_sessions = 0
        for log in workout_logs:
            exercises = log.get("logged_exercises") or []
            names = []
            for exercise in exercises:
                if isinstance(exercise, dict):
                    names.append(str(exercise.get("name") or exercise.get("exercise_id") or ""))
                elif isinstance(exercise, str):
                    names.append(exercise)
            if not names:
                names = [str(log.get("workout_id") or "")]
            if not any(_region_for_exercise(n) == key for n in names if n):
                continue
            sessions += 1
            rpe = _as_float(log.get("session_rpe")) or 0.0
            if rpe >= profile["high_risk_rpe"]:
                high_risk_sessions += 1

        # Region risk starts from that region's share of injuries and rises with
        # the proportion of hard sessions that load it.
        hard_ratio = high_risk_sessions / sessions if sessions else 0.0
        risk = min(1.0, profile["baseline_injury_share"] + hard_ratio * 0.5)
        if risk >= RISK_HIGH_THRESHOLD:
            level = RiskLevel.HIGH
        elif risk >= RISK_LOW_THRESHOLD:
            level = RiskLevel.MODERATE
        else:
            level = RiskLevel.LOW

        recommendations = []
        if hard_ratio > 0.33:
            recommendations.append(
                f"{high_risk_sessions} of {sessions} sessions loading the {key.replace('_', ' ')} "
                f"were at RPE {profile['high_risk_rpe']:.1f} or above — hold the next one below that."
            )
        if not recommendations:
            recommendations.append("No elevated loading pattern for this region.")

        return {
            "region": key,
            "risk_score": round(risk, 3),
            "risk_level": level.value,
            "sessions_loading_region": sessions,
            "high_risk_sessions": high_risk_sessions,
            "high_risk_rpe": profile["high_risk_rpe"],
            "common_in": profile["common_in"],
            "recommendations": recommendations,
        }

    def get_weekly_risk_trend(
        self,
        workout_logs: List[Dict],
        recovery_logs: List[Dict],
        weeks: int = 4,
    ) -> Dict:
        metrics = _daily_metrics_from(workout_logs, recovery_logs)
        results = InjuryRiskEngine.analyze_series(metrics) if metrics else []

        weekly = []
        for week in range(weeks):
            chunk = results[week * 7:(week + 1) * 7]
            if not chunk:
                continue
            weekly.append({
                "week": week + 1,
                "avg_risk_score": round(sum(r.risk_score for r in chunk) / len(chunk), 3),
                "peak_risk_score": max(r.risk_score for r in chunk),
                "avg_acwr": round(sum(r.acwr for r in chunk) / len(chunk), 3),
                "days": len(chunk),
            })

        if len(weekly) >= 2:
            delta = weekly[-1]["avg_risk_score"] - weekly[0]["avg_risk_score"]
            if delta > 0.02:
                trend = "rising"
            elif delta < -0.02:
                trend = "falling"
            else:
                trend = "stable"
        else:
            delta = 0.0
            trend = "insufficient_data"

        return {
            "weeks_requested": weeks,
            "weekly": weekly,
            "trend": trend,
            "change": round(delta, 3),
        }

    def get_status(self) -> Dict:
        return {
            "available": True,
            "engine": "InjuryRiskEngine",
            "monitored_regions": len(MUSCLE_VULNERABILITY),
            "windows": {
                "acute_days": ACUTE_WINDOW,
                "chronic_days": CHRONIC_WINDOW,
                "rolling": list(ROLLING_WINDOWS),
            },
            "thresholds": {
                "low": RISK_LOW_THRESHOLD,
                "high": RISK_HIGH_THRESHOLD,
                "acwr_danger": ACWR_DANGER,
                "acwr_elevated": ACWR_ELEVATED,
            },
            "acwr_zones": InjuryRiskEngine.get_acwr_zone_info(),
        }


injury_risk_engine = _InjuryRiskFacade()

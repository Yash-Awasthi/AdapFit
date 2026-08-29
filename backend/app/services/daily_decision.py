"""
The daily training decision: Train, Reduce, Recover, or Rest.

Deterministic by design. The quantitative engines produce the signals, these
rules pick the state, and an LLM may only phrase the result afterwards — it
never selects the state, so a recommendation can always be traced to the
numbers that produced it.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from app.core.workout_metrics import session_load


class Decision(str, Enum):
    TRAIN = "TRAIN"
    REDUCE = "REDUCE"
    RECOVER = "RECOVER"
    REST = "REST"


# Recovery score bands. Boundaries are inclusive at the lower end.
BANDS = (
    (75, Decision.TRAIN),
    (55, Decision.REDUCE),
    (30, Decision.RECOVER),
    (0, Decision.REST),
)

HEADLINE = {
    Decision.TRAIN: "Train as planned",
    Decision.REDUCE: "Train, but reduce intensity",
    Decision.RECOVER: "Active recovery today",
    Decision.REST: "Rest today",
}

# Upper bound on ACWR before added load is treated as a spike.
ACWR_SPIKE = 1.5
ACWR_HIGH = 1.3
SEVERE_SORENESS = 8
SEVERE_FATIGUE = 8


@dataclass
class DecisionSignals:
    """Everything the rules are allowed to consider."""
    recovery_score: Optional[float] = None
    acwr: Optional[float] = None
    sleep_hours: Optional[float] = None
    sleep_score: Optional[float] = None
    hrv_z_score: Optional[float] = None
    soreness: Optional[float] = None       # 1-10, higher is worse
    fatigue: Optional[float] = None        # 1-10, higher is worse
    resting_hr_delta: Optional[float] = None
    pain_flagged: bool = False
    illness_flagged: bool = False
    data_completeness: float = 0.0         # 0-1


@dataclass
class DailyDecision:
    decision: Decision
    headline: str
    reasons: list[str] = field(default_factory=list)
    cautions: list[str] = field(default_factory=list)
    confidence: str = "low"
    intensity_ceiling_pct: int = 100
    signals_used: dict[str, Any] = field(default_factory=dict)
    safety_override: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "decision": self.decision.value,
            "headline": self.headline,
            "reasons": self.reasons,
            "cautions": self.cautions,
            "confidence": self.confidence,
            "intensity_ceiling_pct": self.intensity_ceiling_pct,
            "signals_used": self.signals_used,
            "safety_override": self.safety_override,
        }


def _band(score: float) -> Decision:
    for threshold, decision in BANDS:
        if score >= threshold:
            return decision
    return Decision.REST


def _confidence(signals: DecisionSignals) -> str:
    if signals.data_completeness >= 0.7:
        return "high"
    if signals.data_completeness >= 0.4:
        return "medium"
    return "low"


def _downgrade(decision: Decision) -> Decision:
    order = [Decision.TRAIN, Decision.REDUCE, Decision.RECOVER, Decision.REST]
    return order[min(order.index(decision) + 1, len(order) - 1)]


def decide(signals: DecisionSignals) -> DailyDecision:
    """
    Pick today's decision and record why.

    Safety overrides are applied last and can only make the day easier, never
    harder: no combination of good numbers should talk someone into training
    through pain.
    """
    reasons: list[str] = []
    cautions: list[str] = []

    score = signals.recovery_score
    if score is None:
        # With no recovery signal at all, the honest answer is the middle of
        # the range rather than a confident recommendation either way.
        decision = Decision.REDUCE
        reasons.append("No recovery data yet, so today defaults to a moderate session.")
    else:
        decision = _band(score)
        reasons.append(f"Recovery score is {round(score)}/100.")

    if signals.hrv_z_score is not None:
        if signals.hrv_z_score <= -1.0:
            reasons.append(f"HRV is {abs(signals.hrv_z_score):.1f} SD below your baseline.")
            decision = _downgrade(decision)
        elif signals.hrv_z_score >= 1.0:
            reasons.append(f"HRV is {signals.hrv_z_score:.1f} SD above your baseline.")

    if signals.sleep_hours is not None and signals.sleep_hours < 6:
        reasons.append(f"You slept {signals.sleep_hours:.1f}h, below your usual need.")
        decision = _downgrade(decision)
    elif signals.sleep_score is not None and signals.sleep_score < 50:
        reasons.append("Sleep quality was poor last night.")
        decision = _downgrade(decision)

    if signals.acwr is not None:
        if signals.acwr >= ACWR_SPIKE:
            reasons.append(f"Training load spiked (ACWR {signals.acwr:.2f}).")
            decision = _downgrade(decision)
        elif signals.acwr >= ACWR_HIGH:
            reasons.append(f"Recent load is elevated (ACWR {signals.acwr:.2f}).")
            cautions.append("Hold volume flat this week rather than adding to it.")
        elif signals.acwr < 0.8:
            reasons.append(f"Recent load is light (ACWR {signals.acwr:.2f}), leaving room to build.")

    if signals.soreness is not None and signals.soreness >= SEVERE_SORENESS:
        reasons.append(f"Muscle soreness is high ({signals.soreness:.0f}/10).")
        decision = _downgrade(decision)
    if signals.fatigue is not None and signals.fatigue >= SEVERE_FATIGUE:
        reasons.append(f"Perceived fatigue is high ({signals.fatigue:.0f}/10).")
        decision = _downgrade(decision)

    if signals.resting_hr_delta is not None and signals.resting_hr_delta >= 7:
        reasons.append(f"Resting heart rate is {signals.resting_hr_delta:.0f} bpm above baseline.")
        cautions.append("An elevated resting heart rate can precede illness.")

    override = None
    if signals.pain_flagged:
        decision = Decision.REST
        override = "pain"
        cautions.append("You reported pain. Training through it risks injury; see a clinician if it persists.")
    elif signals.illness_flagged:
        decision = Decision.REST
        override = "illness"
        cautions.append("You reported illness. Resting shortens it; training extends it.")

    ceiling = {
        Decision.TRAIN: 100,
        Decision.REDUCE: 70,
        Decision.RECOVER: 40,
        Decision.REST: 0,
    }[decision]

    confidence = _confidence(signals)
    if confidence == "low":
        cautions.append("Based on limited data. Connect a wearable or check in daily to improve this.")

    return DailyDecision(
        decision=decision,
        headline=HEADLINE[decision],
        reasons=reasons,
        cautions=cautions,
        confidence=confidence,
        intensity_ceiling_pct=ceiling,
        signals_used={
            k: v for k, v in {
                "recovery_score": signals.recovery_score,
                "acwr": signals.acwr,
                "sleep_hours": signals.sleep_hours,
                "hrv_z_score": signals.hrv_z_score,
                "soreness": signals.soreness,
                "fatigue": signals.fatigue,
            }.items() if v is not None
        },
        safety_override=override,
    )


def signals_from_logs(
    recovery_log: Optional[dict],
    checkin: Optional[dict],
    workload: Optional[dict],
    workout_logs: Optional[list[dict]] = None,
) -> DecisionSignals:
    """Assemble decision signals from whatever the stores actually hold."""
    recovery_log = recovery_log or {}
    checkin = checkin or {}
    workload = workload or {}
    wearable = recovery_log.get("wearable_data") or {}

    signals = DecisionSignals(
        recovery_score=recovery_log.get("recovery_score"),
        acwr=workload.get("acwr"),
        sleep_hours=wearable.get("sleep_duration_hours") or recovery_log.get("sleep_duration_hours"),
        sleep_score=recovery_log.get("sleep_score"),
        hrv_z_score=recovery_log.get("hrv_z_score"),
        soreness=checkin.get("soreness") or recovery_log.get("soreness_score"),
        fatigue=checkin.get("fatigue") or recovery_log.get("fatigue_score"),
        resting_hr_delta=recovery_log.get("resting_hr_delta"),
        pain_flagged=bool(checkin.get("pain_flagged") or recovery_log.get("pain_flagged")),
        illness_flagged=bool(checkin.get("illness") or recovery_log.get("illness_flagged")),
    )

    # Completeness drives the confidence label, so it counts the signals that
    # actually arrived rather than the ones the schema allows.
    present = sum(
        1 for v in (
            signals.recovery_score, signals.acwr, signals.sleep_hours,
            signals.hrv_z_score, signals.soreness, signals.fatigue,
        ) if v is not None
    )
    signals.data_completeness = present / 6
    if workout_logs:
        # Any recent session confirms the load figures are grounded in real work.
        signals.data_completeness = min(1.0, signals.data_completeness + 0.1)
    return signals

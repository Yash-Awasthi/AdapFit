"""NEWS2 (National Early Warning Score) clinical early warning system.

Extracted from inspiration/ZFIT/news2 and inspiration/ZFIT/early_warning_scores.
NEWS2 is the NHS standard for standardising assessment of acute-illness severity.
Based on 6 physiological parameters: respiration rate, oxygen saturation,
systolic blood pressure, pulse rate, consciousness level, temperature.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

class AlertLevel(IntEnum):
    NONE = 0
    LOW = 1
    MODERATE = 2
    HIGH = 3


@dataclass(frozen=True)
class VitalSigns:
    """Patient vital signs for NEWS2 calculation."""
    respiratory_rate: int          # breaths per minute
    oxygen_saturation: int          # SpO2 percentage
    systolic_bp: int                # mmHg
    pulse_rate: int                 # beats per minute
    consciousness: str = "alert"    # alert, voice, pain, unresponsive (AVPU)
    temperature: float = 37.0       # °C
    supplemental_oxygen: bool = False  # on supplemental O2?
    hypercapnic_scale: bool = False  # use COPD/hypercapnic SpO2 scale 2


@dataclass(frozen=True)
class NEWSScore:
    total: int
    respiratory_score: int
    oxygen_sat_score: int
    systolic_bp_score: int
    pulse_score: int
    consciousness_score: int
    temp_score: int
    supplemental_o2_score: int
    alert_level: AlertLevel
    trigger: str | None  # "low", "medium", "high" or None


def _respiratory_rate_score(rr: int) -> int:
    if rr <= 8 or rr >= 25: return 3
    if rr in (9,): return 1  # 9
    if 9 <= rr <= 11: return 1
    if 12 <= rr <= 20: return 0
    if 21 <= rr <= 24: return 2
    return 3


def _oxygen_sat_score(sat: int, hypercapnic: bool = False) -> int:
    if hypercapnic:
        # Scale 2 for hypercapnic/COPD patients
        if sat <= 83: return 3
        if 84 <= sat <= 85: return 2
        if 86 <= sat <= 87: return 1
        if 88 <= sat <= 92: return 0
        if 93 <= sat <= 94: return 1
        if 95 <= sat <= 96: return 2
        return 0  # 97-99
    else:
        # Scale 1 (standard)
        if sat <= 91: return 3
        if 92 <= sat <= 93: return 2
        if 94 <= sat <= 95: return 1
        return 0  # >= 96


def _systolic_bp_score(sbp: int) -> int:
    if sbp <= 90 or sbp >= 220: return 3
    if 91 <= sbp <= 100: return 2
    if 101 <= sbp <= 110: return 1
    if 111 <= sbp <= 219: return 0
    return 3


def _pulse_rate_score(pr: int) -> int:
    if pr <= 40 or pr >= 131: return 3
    if 41 <= pr <= 50: return 1
    if 51 <= pr <= 90: return 0
    if 91 <= pr <= 110: return 1
    if 111 <= pr <= 130: return 2
    return 3


def _consciousness_score(avpu: str) -> int:
    avpu = avpu.lower().strip()
    if avpu == "alert": return 0
    if avpu == "voice": return 3
    if avpu == "pain": return 3
    if avpu == "unresponsive": return 3
    # New confusion = 3
    if "confusion" in avpu or "new" in avpu: return 3
    return 0


def _temperature_score(temp: float) -> int:
    if temp <= 35.0: return 3
    if 35.1 <= temp <= 36.0: return 1
    if 36.1 <= temp <= 38.0: return 0
    if 38.1 <= temp <= 39.0: return 1
    if temp >= 39.1: return 2
    return 3


def calculate_news2(vitals: VitalSigns) -> NEWSScore:
    """Calculate NEWS2 score from vital signs.

    Score ranges 0-20:
      0:       No trigger
      1-4:    Low — ward-based response
      5-6:    Medium — urgent review
      ≥7:     High — emergency/critical care
    """
    rr_score = _respiratory_rate_score(vitals.respiratory_rate)
    sat_score = _oxygen_sat_score(vitals.oxygen_saturation, vitals.hypercapnic_scale)
    sbp_score = _systolic_bp_score(vitals.systolic_bp)
    pulse_score = _pulse_rate_score(vitals.pulse_rate)
    consci_score = _consciousness_score(vitals.consciousness)
    temp_score = _temperature_score(vitals.temperature)
    o2_score = 2 if vitals.supplemental_oxygen else 0

    total = rr_score + sat_score + sbp_score + pulse_score + consci_score + temp_score + o2_score

    single_red = max(rr_score, sat_score, sbp_score, pulse_score, consci_score, temp_score) == 3
    if total >= 7:
        alert = AlertLevel.HIGH
        trigger = "high"
    elif total >= 5 or single_red:
        # RCP NEWS2: a score of 3 in any one parameter warrants urgent review on its own.
        alert = AlertLevel.MODERATE
        trigger = "medium"
    elif total >= 1:
        alert = AlertLevel.LOW
        trigger = "low"
    else:
        alert = AlertLevel.NONE
        trigger = None

    return NEWSScore(
        total=total,
        respiratory_score=rr_score,
        oxygen_sat_score=sat_score,
        systolic_bp_score=sbp_score,
        pulse_score=pulse_score,
        consciousness_score=consci_score,
        temp_score=temp_score,
        supplemental_o2_score=o2_score,
        alert_level=alert,
        trigger=trigger,
    )


def home_next_step(score: NEWSScore) -> str:
    """What someone measuring at home should do, by NEWS2 band."""
    if score.alert_level == AlertLevel.HIGH:
        return "Call 112 (or 108 for an ambulance) now. These readings together need emergency care."
    if score.alert_level == AlertLevel.MODERATE:
        return "Contact a doctor now, or go to urgent care within the hour. Take these readings with you."
    if score.alert_level == AlertLevel.LOW:
        return "Rest and measure again in 4-6 hours. If the numbers or how you feel get worse, contact a doctor."
    return "Your readings are in the normal range."


def news2_recommendation(score: NEWSScore) -> str:
    """Clinical recommendation based on NEWS2 score."""
    if score.alert_level == AlertLevel.HIGH:
        return ("HIGH risk. Emergency assessment. "
                "Consider critical care admission. "
                "Continuous monitoring required.")
    elif score.alert_level == AlertLevel.MODERATE:
        return ("MODERATE risk. Urgent review needed within 1 hour. "
                "Increase monitoring frequency. "
                "Inform senior clinician.")
    elif score.alert_level == AlertLevel.LOW:
        return ("LOW risk. Monitor at least hourly. "
                "If persistently low (total 1-4), "
                "consider clinical review.")
    else:
        return "No acute concerns. Routine monitoring."

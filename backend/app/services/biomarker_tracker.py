"""
Biomarker Tracker & Anomaly Detection for ZFIT
Extracted from: bloodboy-biomarkers-tracker (blood test analysis)
Patterns: Biomarker extraction, trend analysis, anomaly detection,
          unit conversion, reference range comparison, visualization data
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class BiomarkerStatus(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL_LOW = "critical_low"
    CRITICAL_HIGH = "critical_high"


@dataclass
class ReferenceRange:
    low: float
    high: float
    unit: str
    critical_low: Optional[float] = None
    critical_high: Optional[float] = None


@dataclass
class BiomarkerReading:
    name: str
    value: float
    unit: str
    timestamp: datetime
    test_name: str = ""
    lab_name: str = ""
    notes: str = ""


@dataclass
class BiomarkerTrend:
    name: str
    readings: list[BiomarkerReading]
    current_value: float
    reference_range: ReferenceRange
    status: BiomarkerStatus
    trend_direction: str  # "rising", "falling", "stable"
    change_rate: float  # % change per month
    anomaly_detected: bool
    anomaly_description: str = ""


# ─── Reference Ranges (common blood markers) ──────────────────────────

COMMON_REFERENCE_RANGES = {
    "hemoglobin": ReferenceRange(low=12.0, high=17.5, unit="g/dL", critical_low=7.0, critical_high=20.0),
    "wbc": ReferenceRange(low=4.5, high=11.0, unit="K/uL", critical_low=2.0, critical_high=30.0),
    "platelets": ReferenceRange(low=150, high=400, unit="K/uL", critical_low=50, critical_high=800),
    "glucose_fasting": ReferenceRange(low=70, high=100, unit="mg/dL", critical_low=50, critical_high=400),
    "cholesterol_total": ReferenceRange(low=0, high=200, unit="mg/dL", critical_high=300),
    "ldl": ReferenceRange(low=0, high=100, unit="mg/dL", critical_high=190),
    "hdl": ReferenceRange(low=40, high=80, unit="mg/dL", critical_low=20),
    "triglycerides": ReferenceRange(low=0, high=150, unit="mg/dL", critical_high=500),
    "creatinine": ReferenceRange(low=0.6, high=1.2, unit="mg/dL", critical_low=0.3, critical_high=4.0),
    "bun": ReferenceRange(low=7, high=20, unit="mg/dL", critical_high=80),
    "alt": ReferenceRange(low=7, high=56, unit="U/L", critical_high=500),
    "ast": ReferenceRange(low=10, high=40, unit="U/L", critical_high=500),
    "tsh": ReferenceRange(low=0.4, high=4.0, unit="mIU/L", critical_low=0.1, critical_high=10.0),
    "vitamin_d": ReferenceRange(low=30, high=100, unit="ng/mL", critical_low=10, critical_high=150),
    "iron": ReferenceRange(low=60, high=170, unit="ug/dL", critical_low=20, critical_high=400),
    "ferritin": ReferenceRange(low=12, high=300, unit="ng/mL", critical_low=5, critical_high=1000),
    "hba1c": ReferenceRange(low=4.0, high=5.7, unit="%", critical_high=12.0),
    "crp": ReferenceRange(low=0, high=3.0, unit="mg/L", critical_high=50),
    "esr": ReferenceRange(low=0, high=20, unit="mm/hr", critical_high=100),
}


# ─── Status Classification ─────────────────────────────────────────────

def classify_biomarker(value: float, reference: ReferenceRange) -> BiomarkerStatus:
    """Classify a biomarker reading against its reference range."""
    if reference.critical_low is not None and value <= reference.critical_low:
        return BiomarkerStatus.CRITICAL_LOW
    if reference.critical_high is not None and value >= reference.critical_high:
        return BiomarkerStatus.CRITICAL_HIGH
    if value < reference.low:
        return BiomarkerStatus.LOW
    if value > reference.high:
        return BiomarkerStatus.HIGH
    return BiomarkerStatus.NORMAL


def status_severity(status: BiomarkerStatus) -> int:
    """Return severity score (0=normal, 4=critical)."""
    return {
        BiomarkerStatus.NORMAL: 0,
        BiomarkerStatus.LOW: 1,
        BiomarkerStatus.HIGH: 1,
        BiomarkerStatus.CRITICAL_LOW: 4,
        BiomarkerStatus.CRITICAL_HIGH: 4,
    }[status]


# ─── Trend Analysis ────────────────────────────────────────────────────

def analyze_trend(readings: list[BiomarkerReading], reference: ReferenceRange) -> BiomarkerTrend:
    """Analyze trends in a series of biomarker readings."""
    if not readings:
        raise ValueError("Need at least one reading")

    sorted_readings = sorted(readings, key=lambda r: r.timestamp)
    current = sorted_readings[-1]
    status = classify_biomarker(current.value, reference)

    trend_direction = "stable"
    change_rate = 0.0
    anomaly_detected = False
    anomaly_description = ""

    if len(sorted_readings) >= 2:
        first = sorted_readings[0]
        last = sorted_readings[-1]
        time_diff_months = max(0.1, (last.timestamp - first.timestamp).total_seconds() / (30 * 24 * 3600))

        if first.value != 0:
            change_rate = ((last.value - first.value) / abs(first.value)) * 100 / time_diff_months

        if change_rate > 5:
            trend_direction = "rising"
        elif change_rate < -5:
            trend_direction = "falling"

        # Anomaly detection: check for rapid changes or out-of-range values
        values = [r.value for r in sorted_readings]
        mean_val = sum(values) / len(values)
        if len(values) >= 3:
            variance = sum((v - mean_val) ** 2 for v in values) / len(values)
            std_dev = variance ** 0.5

            if std_dev > 0 and abs(last.value - mean_val) > 2 * std_dev:
                anomaly_detected = True
                anomaly_description = f"Value {last.value} deviates {abs(last.value - mean_val)/std_dev:.1f}σ from mean ({mean_val:.2f})"

        # Check for crossing critical thresholds
        prev_status = classify_biomarker(sorted_readings[-2].value, reference)
        if status_severity(status) > status_severity(prev_status):
            anomaly_detected = True
            anomaly_description = f"Status worsened from {prev_status.value} to {status.value}"

    return BiomarkerTrend(
        name=current.name,
        readings=sorted_readings,
        current_value=current.value,
        reference_range=reference,
        status=status,
        trend_direction=trend_direction,
        change_rate=round(change_rate, 2),
        anomaly_detected=anomaly_detected,
        anomaly_description=anomaly_description,
    )


# ─── Unit Conversion ───────────────────────────────────────────────────

UNIT_CONVERSIONS = {
    ("mg/dL", "mmol/L"): lambda v: v / 18.018,
    ("mmol/L", "mg/dL"): lambda v: v * 18.018,
    ("ng/mL", "nmol/L"): lambda v: v * 2.496,
    ("nmol/L", "ng/mL"): lambda v: v / 2.496,
    ("ug/dL", "umol/L"): lambda v: v / 5.585,
    ("umol/L", "ug/dL"): lambda v: v * 5.585,
}


def convert_unit(value: float, from_unit: str, to_unit: str) -> Optional[float]:
    """Convert between common biomarker units."""
    if from_unit == to_unit:
        return value
    converter = UNIT_CONVERSIONS.get((from_unit, to_unit))
    return round(converter(value), 4) if converter else None


# ─── Dashboard Data ────────────────────────────────────────────────────

def generate_biomarker_dashboard(
    readings: list[BiomarkerReading],
    reference_ranges: dict[str, ReferenceRange] = None,
) -> dict:
    """Generate a comprehensive biomarker dashboard."""
    if reference_ranges is None:
        reference_ranges = COMMON_REFERENCE_RANGES

    # Group readings by biomarker name
    grouped: dict[str, list[BiomarkerReading]] = {}
    for r in readings:
        grouped.setdefault(r.name.lower(), []).append(r)

    trends = []
    alerts = []
    summary = {"total": 0, "normal": 0, "abnormal": 0, "critical": 0}

    for name, marker_readings in grouped.items():
        ref = reference_ranges.get(name)
        if not ref:
            continue

        trend = analyze_trend(marker_readings, ref)
        trends.append(trend)

        summary["total"] += 1
        if trend.status == BiomarkerStatus.NORMAL:
            summary["normal"] += 1
        elif trend.status in (BiomarkerStatus.CRITICAL_LOW, BiomarkerStatus.CRITICAL_HIGH):
            summary["critical"] += 1
            alerts.append({
                "name": name,
                "status": trend.status.value,
                "value": trend.current_value,
                "reference": f"{ref.low}-{ref.high} {ref.unit}",
            })
        else:
            summary["abnormal"] += 1

    return {
        "summary": summary,
        "trends": [
            {
                "name": t.name,
                "value": t.current_value,
                "status": t.status.value,
                "trend": t.trend_direction,
                "change_rate": t.change_rate,
                "anomaly": t.anomaly_detected,
                "anomaly_desc": t.anomaly_description,
                "reference": f"{t.reference_range.low}-{t.reference_range.high} {t.reference_range.unit}",
            }
            for t in trends
        ],
        "alerts": alerts,
    }

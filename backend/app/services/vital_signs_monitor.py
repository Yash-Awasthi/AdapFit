"""
Vital Signs Monitor
Synthesized from openhrv, rppg, and apple-health-grafana patterns

Features:
- Real-time vital signs monitoring
- Trend detection and alerts
- Multi-signal correlation
- Anomaly detection
- Health risk scoring
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
import time
import math
from collections import deque


class VitalSign(Enum):
    HEART_RATE = "heart_rate"
    HRV = "hrv"
    SPO2 = "spo2"
    RESPIRATORY_RATE = "respiratory_rate"
    BLOOD_PRESSURE_SYS = "blood_pressure_systolic"
    BLOOD_PRESSURE_DIA = "blood_pressure_diastolic"
    TEMPERATURE = "temperature"


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class VitalReading:
    """Single vital sign reading"""
    timestamp: float
    vital: VitalSign
    value: float
    unit: str
    quality: float  # 0-1 signal quality
    source: str


@dataclass
class VitalTrend:
    """Trend analysis for a vital sign"""
    vital: VitalSign
    direction: str  # 'increasing', 'decreasing', 'stable'
    slope: float
    confidence: float
    period: float  # seconds
    alerts: List[str]


@dataclass
class HealthAlert:
    """Health alert"""
    timestamp: float
    severity: AlertSeverity
    vital: VitalSign
    message: str
    value: float
    threshold: float
    recommendation: str


@dataclass
class VitalSignsSummary:
    """Summary of all vital signs"""
    timestamp: float
    heart_rate: Optional[float]
    hrv: Optional[float]
    spo2: Optional[float]
    respiratory_rate: Optional[float]
    blood_pressure: Optional[Tuple[float, float]]
    temperature: Optional[float]
    overall_score: float  # 0-100
    alerts: List[HealthAlert]


class VitalSignsMonitor:
    """
    Real-time vital signs monitor
    Synthesized from openhrv, rppg, and apple-health-grafana patterns
    """
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.readings: Dict[VitalSign, deque] = {
            vital: deque(maxlen=window_size) for vital in VitalSign
        }
        self.alerts: List[HealthAlert] = []
        self.baselines: Dict[VitalSign, float] = {}
        self.thresholds: Dict[VitalSign, Dict[str, float]] = {
            VitalSign.HEART_RATE: {'low': 50, 'high': 100, 'critical_low': 40, 'critical_high': 120},
            VitalSign.HRV: {'low': 20, 'high': 100, 'critical_low': 10},
            VitalSign.SPO2: {'low': 95, 'critical_low': 90},
            VitalSign.RESPIRATORY_RATE: {'low': 12, 'high': 20, 'critical_low': 8, 'critical_high': 25},
            VitalSign.BLOOD_PRESSURE_SYS: {'low': 90, 'high': 140, 'critical_low': 80, 'critical_high': 180},
            VitalSign.BLOOD_PRESSURE_DIA: {'low': 60, 'high': 90, 'critical_low': 50, 'critical_high': 110},
            VitalSign.TEMPERATURE: {'low': 36.1, 'high': 37.5, 'critical_low': 35.0, 'critical_high': 39.0}
        }
    
    def add_reading(self, reading: VitalReading):
        """Add a new vital sign reading"""
        self.readings[reading.vital].append(reading)
        
        # Check for alerts
        self._check_thresholds(reading)
        
        # Update baselines periodically
        self._update_baselines()
    
    def _check_thresholds(self, reading: VitalReading):
        """Check if reading triggers any alerts"""
        if reading.vital not in self.thresholds:
            return
        
        thresholds = self.thresholds[reading.vital]
        
        # Check critical thresholds first
        if 'critical_low' in thresholds and reading.value < thresholds['critical_low']:
            self._create_alert(
                reading, AlertSeverity.EMERGENCY,
                f"Critical low {reading.vital.value}: {reading.value} {reading.unit}",
                thresholds['critical_low']
            )
        elif 'critical_high' in thresholds and reading.value > thresholds['critical_high']:
            self._create_alert(
                reading, AlertSeverity.EMERGENCY,
                f"Critical high {reading.vital.value}: {reading.value} {reading.unit}",
                thresholds['critical_high']
            )
        # Check warning thresholds
        elif 'low' in thresholds and reading.value < thresholds['low']:
            self._create_alert(
                reading, AlertSeverity.WARNING,
                f"Low {reading.vital.value}: {reading.value} {reading.unit}",
                thresholds['low']
            )
        elif 'high' in thresholds and reading.value > thresholds['high']:
            self._create_alert(
                reading, AlertSeverity.WARNING,
                f"High {reading.vital.value}: {reading.value} {reading.unit}",
                thresholds['high']
            )
    
    def _create_alert(
        self,
        reading: VitalReading,
        severity: AlertSeverity,
        message: str,
        threshold: float
    ):
        """Create a health alert"""
        alert = HealthAlert(
            timestamp=reading.timestamp,
            severity=severity,
            vital=reading.vital,
            message=message,
            value=reading.value,
            threshold=threshold,
            recommendation=self._get_recommendation(reading.vital, severity)
        )
        self.alerts.append(alert)
    
    def _get_recommendation(self, vital: VitalSign, severity: AlertSeverity) -> str:
        """Get recommendation based on vital and severity"""
        recommendations = {
            (VitalSign.HEART_RATE, AlertSeverity.WARNING): "Rest and monitor. If persistent, consult a doctor.",
            (VitalSign.HEART_RATE, AlertSeverity.CRITICAL): "Seek immediate medical attention.",
            (VitalSign.SPO2, AlertSeverity.WARNING): "Check breathing. If below 94%, seek medical advice.",
            (VitalSign.SPO2, AlertSeverity.CRITICAL): "Seek emergency medical care immediately.",
            (VitalSign.RESPIRATORY_RATE, AlertSeverity.WARNING): "Practice deep breathing exercises.",
            (VitalSign.TEMPERATURE, AlertSeverity.WARNING): "Rest, hydrate, and monitor temperature.",
            (VitalSign.TEMPERATURE, AlertSeverity.CRITICAL): "Seek immediate medical attention.",
        }
        
        return recommendations.get((vital, severity), "Monitor and consult healthcare provider if concerned.")
    
    def _update_baselines(self):
        """Update baseline values from recent readings"""
        for vital, readings in self.readings.items():
            if len(readings) >= 10:
                values = [r.value for r in list(readings)[-10:]]
                self.baselines[vital] = sum(values) / len(values)
    
    def analyze_trend(
        self,
        vital: VitalSign,
        period: float = 3600  # 1 hour
    ) -> VitalTrend:
        """Analyze trend for a vital sign"""
        readings = list(self.readings.get(vital, []))
        
        if len(readings) < 5:
            return VitalTrend(
                vital=vital,
                direction='stable',
                slope=0,
                confidence=0,
                period=period,
                alerts=['Insufficient data for trend analysis']
            )
        
        # Filter readings within period
        cutoff_time = time.time() - period
        recent = [r for r in readings if r.timestamp >= cutoff_time]
        
        if len(recent) < 3:
            return VitalTrend(
                vital=vital,
                direction='stable',
                slope=0,
                confidence=0,
                period=period,
                alerts=['Insufficient recent data']
            )
        
        # Calculate linear regression
        n = len(recent)
        x = [(r.timestamp - recent[0].timestamp) for r in recent]
        y = [r.value for r in recent]
        
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator > 0 else 0
        intercept = y_mean - slope * x_mean
        
        # Calculate R²
        y_pred = [slope * x[i] + intercept for i in range(n)]
        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Determine direction
        if abs(slope) < 0.1:
            direction = 'stable'
        elif slope > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'
        
        # Check for concerning trends
        alerts = []
        baseline = self.baselines.get(vital)
        if baseline:
            current = y[-1]
            deviation = abs(current - baseline) / baseline * 100
            if deviation > 20:
                alerts.append(f"Significant deviation from baseline: {deviation:.1f}%")
        
        return VitalTrend(
            vital=vital,
            direction=direction,
            slope=slope,
            confidence=r_squared,
            period=period,
            alerts=alerts
        )
    
    def calculate_health_score(self) -> float:
        """Calculate overall health score (0-100)"""
        scores = []
        
        # HR score
        if VitalSign.HEART_RATE in self.baselines:
            hr = self.baselines[VitalSign.HEART_RATE]
            if 60 <= hr <= 80:
                hr_score = 100
            elif 50 <= hr < 60 or 80 < hr <= 100:
                hr_score = 70
            else:
                hr_score = 40
            scores.append(hr_score)
        
        # HRV score
        if VitalSign.HRV in self.baselines:
            hrv = self.baselines[VitalSign.HRV]
            if hrv >= 50:
                hrv_score = 100
            elif hrv >= 30:
                hrv_score = 70
            else:
                hrv_score = 40
            scores.append(hrv_score)
        
        # SpO2 score
        if VitalSign.SPO2 in self.baselines:
            spo2 = self.baselines[VitalSign.SPO2]
            if spo2 >= 98:
                spo2_score = 100
            elif spo2 >= 95:
                spo2_score = 70
            else:
                spo2_score = 30
            scores.append(spo2_score)
        
        # Respiratory rate score
        if VitalSign.RESPIRATORY_RATE in self.baselines:
            rr = self.baselines[VitalSign.RESPIRATORY_RATE]
            if 12 <= rr <= 18:
                rr_score = 100
            elif 10 <= rr <= 20:
                rr_score = 70
            else:
                rr_score = 40
            scores.append(rr_score)
        
        # Calculate weighted average
        if scores:
            return sum(scores) / len(scores)
        return 50  # Default score
    
    def get_summary(self) -> VitalSignsSummary:
        """Get current vital signs summary"""
        summary = VitalSignsSummary(
            timestamp=time.time(),
            heart_rate=self.baselines.get(VitalSign.HEART_RATE),
            hrv=self.baselines.get(VitalSign.HRV),
            spo2=self.baselines.get(VitalSign.SPO2),
            respiratory_rate=self.baselines.get(VitalSign.RESPIRATORY_RATE),
            blood_pressure=None,
            temperature=self.baselines.get(VitalSign.TEMPERATURE),
            overall_score=self.calculate_health_score(),
            alerts=[a for a in self.alerts if time.time() - a.timestamp < 3600]
        )
        
        # Get blood pressure if available
        if VitalSign.BLOOD_PRESSURE_SYS in self.baselines and VitalSign.BLOOD_PRESSURE_DIA in self.baselines:
            summary.blood_pressure = (
                self.baselines[VitalSign.BLOOD_PRESSURE_SYS],
                self.baselines[VitalSign.BLOOD_PRESSURE_DIA]
            )
        
        return summary
    
    def correlate_vitals(
        self,
        vital1: VitalSign,
        vital2: VitalSign,
        period: float = 3600
    ) -> Dict[str, any]:
        """Correlate two vital signs"""
        readings1 = list(self.readings.get(vital1, []))
        readings2 = list(self.readings.get(vital2, []))
        
        # Filter to same time period
        cutoff_time = time.time() - period
        readings1 = [r for r in readings1 if r.timestamp >= cutoff_time]
        readings2 = [r for r in readings2 if r.timestamp >= cutoff_time]
        
        if len(readings1) < 5 or len(readings2) < 5:
            return {'correlation': 0, 'significance': 'insufficient_data'}
        
        # Match readings by timestamp (simplified)
        values1 = [r.value for r in readings1[:min(len(readings1), len(readings2))]]
        values2 = [r.value for r in readings2[:min(len(readings1), len(readings2))]]
        
        # Calculate Pearson correlation
        n = len(values1)
        if n < 3:
            return {'correlation': 0, 'significance': 'insufficient_data'}
        
        mean1 = sum(values1) / n
        mean2 = sum(values2) / n
        
        numerator = sum((values1[i] - mean1) * (values2[i] - mean2) for i in range(n))
        denom1 = math.sqrt(sum((x - mean1) ** 2 for x in values1))
        denom2 = math.sqrt(sum((x - mean2) ** 2 for x in values2))
        
        if denom1 == 0 or denom2 == 0:
            return {'correlation': 0, 'significance': 'no_variance'}
        
        correlation = numerator / (denom1 * denom2)
        
        # Determine significance
        if abs(correlation) > 0.7:
            significance = 'strong'
        elif abs(correlation) > 0.4:
            significance = 'moderate'
        else:
            significance = 'weak'
        
        return {
            'correlation': correlation,
            'significance': significance,
            'vital1': vital1.value,
            'vital2': vital2.value,
            'sample_size': n
        }


def create_vital_signs_monitor(window_size: int = 100) -> VitalSignsMonitor:
    """Create a vital signs monitor"""
    return VitalSignsMonitor(window_size)
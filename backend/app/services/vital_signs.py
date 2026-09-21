"""
Vital Signs Service — SpO2 estimation, body temperature, recorded ECG.

A phone has no ECG electrode, so there is no measurement to return for one.
This service used to answer the ECG endpoints with a random heart rate and
invented PR, QRS and QT intervals labelled "Normal Sinus Rhythm"; a reading
that looks clinical and is not measured is worse than no reading, because it
is indistinguishable from a real one once it reaches the screen. ECG readings
are now only ever stored when a device supplies them.

Camera-derived heart rate belongs to the rPPG service, which computes it from
real frames (app/api/v1/endpoints/rppg_api.py).

Features:
- Blood oxygen (SpO2) estimated from supplied red/infrared PPG averages
- Body temperature tracking with fever alerts
- ECG readings recorded from a connected device
"""
import time
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class ECGReading:
    timestamp: float
    heart_rate: int
    rhythm: str  # normal, atrial_fibrillation, bradycardia, tachycardia
    # None when the recording device did not report the interval. Never filled
    # in with a plausible value: an absent interval must stay visibly absent.
    pr_interval_ms: Optional[float]
    qrs_duration_ms: Optional[float]
    qt_interval_ms: Optional[float]
    abnormalities: list[str]


@dataclass
class SpO2Reading:
    timestamp: float
    spo2_percent: int
    confidence: str  # high, medium, low
    # From the pulse source that supplied it, if any. The R-ratio yields
    # saturation only, so this is None unless a device reported a pulse.
    pulse_rate: Optional[int]
    classification: str  # normal, mild_hypoxemia, moderate_hypoxemia, severe


@dataclass
class TemperatureReading:
    timestamp: float
    temperature_celsius: float
    measurement_site: str  # oral, temporal, axillary, rectal
    classification: str  # hypothermia, normal, fever, high_fever
    fever_alert: bool


class VitalSignsService:
    """Comprehensive vital signs monitoring and analysis."""

    def __init__(self):
        self._ecg_readings: list[ECGReading] = []
        self._spo2_readings: list[SpO2Reading] = []
        self._temperature_readings: list[TemperatureReading] = []
        self._measurement_session: dict = {}

    # === ECG ===

    ECG_UNAVAILABLE = {
        "status": "unsupported",
        "supported": False,
        "reason": "no_ecg_hardware",
        "message": (
            "This device has no ECG sensor. Record an ECG on a device that has one, "
            "or use the camera heart-rate measurement for pulse only."
        ),
    }

    def start_ecg_measurement(self, user_id: str = "default") -> dict:
        """No phone camera measures an ECG, so there is nothing to start."""
        return dict(self.ECG_UNAVAILABLE)

    def process_ecg_frame(self, user_id: str = "default") -> dict:
        return dict(self.ECG_UNAVAILABLE)

    def record_ecg(
        self,
        heart_rate: int,
        rhythm: str = "normal",
        pr_interval_ms: Optional[float] = None,
        qrs_duration_ms: Optional[float] = None,
        qt_interval_ms: Optional[float] = None,
        abnormalities: Optional[list[str]] = None,
    ) -> dict:
        """
        Store an ECG a device actually measured.

        Intervals stay None when the device did not report them rather than
        being filled in, so a downstream reader can tell absent from measured.
        """
        reading = ECGReading(
            timestamp=time.time(), heart_rate=heart_rate, rhythm=rhythm,
            pr_interval_ms=pr_interval_ms, qrs_duration_ms=qrs_duration_ms,
            qt_interval_ms=qt_interval_ms, abnormalities=abnormalities or [],
        )
        self._ecg_readings.append(reading)
        return {
            "recorded": True, "heart_rate": heart_rate, "rhythm": rhythm,
            "pr_interval": pr_interval_ms, "qrs_duration": qrs_duration_ms,
            "qt_interval": qt_interval_ms, "abnormalities": reading.abnormalities,
        }

    def get_ecg_history(self, user_id: str = "default", limit: int = 10) -> list[dict]:
        return [
            {
                "timestamp": r.timestamp, "heart_rate": r.heart_rate, "rhythm": r.rhythm,
                "pr_interval": r.pr_interval_ms, "qrs_duration": r.qrs_duration_ms,
                "qt_interval": r.qt_interval_ms, "abnormalities": r.abnormalities,
                "classification": "Normal Sinus Rhythm" if r.rhythm == "normal" else r.rhythm.replace("_", " ").title(),
            }
            for r in self._ecg_readings[-limit:]
        ]

    def analyze_rhythm(self, readings: list[dict]) -> dict:
        if not readings:
            return {"status": "no_data"}
        hrs = [r.get("heart_rate", 70) for r in readings[-10:]]
        avg_hr = sum(hrs) / len(hrs)
        variability = max(hrs) - min(hrs)
        if avg_hr < 60:
            return {"rhythm": "bradycardia", "avg_hr": round(avg_hr), "message": "Heart rate below 60 bpm. Consult a doctor if symptomatic."}
        elif avg_hr > 100:
            return {"rhythm": "tachycardia", "avg_hr": round(avg_hr), "message": "Heart rate above 100 bpm. Monitor and reduce stress."}
        elif variability > 30:
            return {"rhythm": "variable", "avg_hr": round(avg_hr), "message": "High heart rate variability detected. Generally healthy."}
        return {"rhythm": "normal", "avg_hr": round(avg_hr), "message": "Normal sinus rhythm detected."}

    # === SpO2 ===

    def estimate_spo2(self, red_avg: float, infrared_avg: float, pulse_rate: Optional[int] = None) -> dict:
        """
        Estimate blood oxygen from a PPG signal by the R-value method.

        Both channel averages are required: defaulting them would turn a
        request carrying no signal into a confident saturation reading.
        """
        if infrared_avg == 0:
            return {"error": "Invalid signal"}
        r_ratio = red_avg / infrared_avg
        spo2 = max(70, min(100, int(110 - 25 * r_ratio)))
        confidence = "high" if 0.4 < r_ratio < 1.2 else "medium" if 0.3 < r_ratio < 1.4 else "low"

        if spo2 >= 95:
            classification = "normal"
        elif spo2 >= 90:
            classification = "mild_hypoxemia"
        elif spo2 >= 85:
            classification = "moderate_hypoxemia"
        else:
            classification = "severe"

        reading = SpO2Reading(
            timestamp=time.time(), spo2_percent=spo2, confidence=confidence,
            pulse_rate=pulse_rate, classification=classification,
        )
        self._spo2_readings.append(reading)
        return {
            "spo2_percent": spo2, "confidence": confidence, "pulse_rate": reading.pulse_rate,
            "classification": classification.replace("_", " ").title(),
            "message": "Normal" if spo2 >= 95 else "Below normal - consult doctor" if spo2 >= 90 else "Low - seek medical attention",
        }

    def get_spo2_history(self, limit: int = 10) -> list[dict]:
        return [{"timestamp": r.timestamp, "spo2": r.spo2_percent, "classification": r.classification} for r in self._spo2_readings[-limit:]]

    # === Body Temperature ===

    def log_temperature(self, temp_celsius: float, site: str = "oral") -> dict:
        if temp_celsius < 30 or temp_celsius > 45:
            return {"error": "Invalid temperature reading"}
        if temp_celsius < 35:
            classification = "hypothermia"
            fever_alert = True
        elif temp_celsius < 37.5:
            classification = "normal"
            fever_alert = False
        elif temp_celsius < 38.5:
            classification = "fever"
            fever_alert = True
        else:
            classification = "high_fever"
            fever_alert = True

        reading = TemperatureReading(
            timestamp=time.time(), temperature_celsius=temp_celsius,
            measurement_site=site, classification=classification, fever_alert=fever_alert,
        )
        self._temperature_readings.append(reading)
        return {
            "temperature": temp_celsius, "site": site, "classification": classification.replace("_", " ").title(),
            "fever_alert": fever_alert, "fahrenheit": round(temp_celsius * 9/5 + 32, 1),
            "message": "Normal temperature" if classification == "normal" else f"{classification.replace('_', ' ').title()} detected. {'Seek medical attention.' if classification == 'high_fever' else 'Monitor closely.'}",
        }

    def get_temperature_history(self, limit: int = 10) -> list[dict]:
        return [{"timestamp": r.timestamp, "temp_c": r.temperature_celsius, "temp_f": round(r.temperature_celsius * 9/5 + 32, 1), "classification": r.classification, "site": r.measurement_site} for r in self._temperature_readings[-limit:]]

    def get_vitals_summary(self) -> dict:
        latest_ecg = self._ecg_readings[-1] if self._ecg_readings else None
        latest_spo2 = self._spo2_readings[-1] if self._spo2_readings else None
        latest_temp = self._temperature_readings[-1] if self._temperature_readings else None
        return {
            "heart_rate": {"value": latest_ecg.heart_rate if latest_ecg else None, "rhythm": latest_ecg.rhythm if latest_ecg else "unknown"},
            "spo2": {"value": latest_spo2.spo2_percent if latest_spo2 else None, "classification": latest_spo2.classification if latest_spo2 else "unknown"},
            "temperature": {"value": latest_temp.temperature_celsius if latest_temp else None, "classification": latest_temp.classification if latest_temp else "unknown"},
            "total_readings": len(self._ecg_readings) + len(self._spo2_readings) + len(self._temperature_readings),
        }


from app.core.per_user import per_user, register

vital_signs_service = register("vital_signs.vital_signs_service", per_user(VitalSignsService))
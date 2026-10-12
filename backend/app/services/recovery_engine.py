from typing import Optional, Tuple
from app.models.schemas import (
    WearableBiometrics,
    SubjectiveCheckin,
    UserBaseline,
    ReadinessState,
    ACWRStatus,
    RecoveryMetricsBreakdown,
    RecoveryCalculationResponse
)
from app.core.config import settings
from app.services.daily_decision import BANDS, Decision

class RecoveryEngine:
    """
    Scientific recovery, fatigue and workload calculation engine.
    Implements HRV Z-Score baseline tracking, Hooper-Mackinnon subjective matrix,
    Foster's Session-RPE internal load, and Acute:Chronic Workload Ratio (ACWR).
    """

    @staticmethod
    def calculate_hrv_z_score(
        today_hrv: Optional[float],
        baseline_mean: float = settings.DEFAULT_BASELINE_HRV_RMSSD,
        baseline_std: float = settings.DEFAULT_BASELINE_HRV_STD
    ) -> Tuple[Optional[float], float]:
        """
        Computes the Z-Score of RMSSD HRV relative to personal 28-day baseline.
        Returns: (z_score, normalized_hrv_score_0_to_100)
        """
        if today_hrv is None or today_hrv <= 0:
            return None, 70.0  # Default neutral score when wearable is absent
        
        std = baseline_std if baseline_std > 0.1 else 10.0
        z_score = (today_hrv - baseline_mean) / std
        return round(z_score, 2), RecoveryEngine.hrv_score_from_z(z_score)

    @staticmethod
    def hrv_score_from_z(z_score: float) -> float:
        """Z-score -2..+2 mapped linearly onto 0..100, centred at 50."""
        return round(max(0.0, min(100.0, 50.0 + z_score * 25.0)), 1)

    @staticmethod
    def readiness_for(recovery_score: float) -> ReadinessState:
        """Readiness on the same bands as the daily decision, so the two never disagree."""
        floors = {decision: floor for floor, decision in BANDS}
        if recovery_score >= 85:
            return ReadinessState.OPTIMAL
        if recovery_score >= floors[Decision.TRAIN]:
            return ReadinessState.MODERATE
        if recovery_score >= floors[Decision.REDUCE]:
            return ReadinessState.REDUCED
        return ReadinessState.DEPLETED

    @staticmethod
    def calculate_sleep_score(
        sleep_hours: Optional[float],
        sleep_efficiency: Optional[float] = None,
        target_hours: float = settings.DEFAULT_BASELINE_SLEEP_HOURS
    ) -> float:
        """
        Computes Sleep Quality Index (0-100).
        """
        if sleep_hours is None or sleep_hours <= 0:
            return 70.0  # Default neutral score
        
        duration_ratio = min(1.0, sleep_hours / target_hours)
        duration_score = duration_ratio * 100.0
        
        if sleep_efficiency is not None and sleep_efficiency > 0:
            # 70% weight on duration, 30% on sleep efficiency
            efficiency_score = max(0.0, min(100.0, sleep_efficiency))
            sleep_score = (0.70 * duration_score) + (0.30 * efficiency_score)
        else:
            sleep_score = duration_score
            
        return round(max(0.0, min(100.0, sleep_score)), 1)

    @staticmethod
    def calculate_subjective_score(checkin: Optional[SubjectiveCheckin]) -> float:
        """
        Computes subjective recovery rating from 1-10 Hooper-Mackinnon questionnaire.
        Formula: (Soreness + Energy + (11-Stress) + sore-area points) / 40 * 100, where no sore areas is 10.
        """
        if checkin is None:
            return 75.0  # Default neutral/good
        
        # Scales: soreness 1 sore-10 fresh, fatigue 1 exhausted-10 energized, stress 1 relaxed-10 stressed.
        soreness = checkin.soreness
        energy_rating = checkin.fatigue
        stress_inverted = 11 - checkin.stress

        total_points = soreness + energy_rating + stress_inverted + (10 if len(checkin.sore_muscle_groups) == 0 else max(2, 10 - len(checkin.sore_muscle_groups)*2))
        score = (total_points / 40.0) * 100.0
        return round(max(0.0, min(100.0, score)), 1)

    @staticmethod
    def evaluate_acwr(
        acute_load: Optional[float],
        chronic_load: Optional[float]
    ) -> Tuple[Optional[float], ACWRStatus, float]:
        """
        Evaluates Acute:Chronic Workload Ratio.
        Returns: (acwr_value, acwr_status, penalty_modifier)
        """
        if acute_load is None or chronic_load is None or chronic_load <= 0:
            return None, ACWRStatus.SWEET_SPOT, 0.0
        
        acwr = round(acute_load / chronic_load, 2)
        
        if acwr < 0.80:
            return acwr, ACWRStatus.UNDER_TRAINING, 0.0
        elif acwr <= 1.30:
            return acwr, ACWRStatus.SWEET_SPOT, 0.0
        elif acwr < 1.50:
            return acwr, ACWRStatus.CAUTION, -5.0
        else:
            # Danger zone: high spike in acute load
            return acwr, ACWRStatus.DANGER_ZONE, -15.0

    @classmethod
    def compute_daily_recovery(
        cls,
        wearable_data: Optional[WearableBiometrics],
        subjective_checkin: Optional[SubjectiveCheckin],
        baseline: Optional[UserBaseline] = None,
        acute_load: Optional[float] = None,
        chronic_load: Optional[float] = None
    ) -> RecoveryCalculationResponse:
        """
        Full recovery score calculation pipeline.
        Combines biometric HRV Z-Score, Sleep Index, Subjective Check-in and ACWR.
        """
        base_hrv_mean = baseline.hrv_mean_rmssd if baseline else settings.DEFAULT_BASELINE_HRV_RMSSD
        base_hrv_std = baseline.hrv_std_rmssd if baseline else settings.DEFAULT_BASELINE_HRV_STD
        base_sleep = baseline.sleep_target_hours if baseline else settings.DEFAULT_BASELINE_SLEEP_HOURS

        # 1. HRV Processing
        hrv_val = wearable_data.hrv_rmssd if wearable_data else None
        z_score, hrv_score = cls.calculate_hrv_z_score(hrv_val, base_hrv_mean, base_hrv_std)

        # 2. Sleep Processing
        sleep_hours = wearable_data.sleep_duration_hours if wearable_data else None
        sleep_eff = wearable_data.sleep_efficiency_pct if wearable_data else None
        sleep_score = cls.calculate_sleep_score(sleep_hours, sleep_eff, base_sleep)

        # 3. Subjective Ratings
        subj_score = cls.calculate_subjective_score(subjective_checkin)

        # 4. ACWR Evaluation
        acwr_val, acwr_status, acwr_penalty = cls.evaluate_acwr(acute_load, chronic_load)

        # 5. Composite Weighted Recovery Score
        if hrv_val is not None:
            # Full Wearable Mode: 40% HRV, 35% Sleep, 25% Subjective
            raw_score = (0.40 * hrv_score) + (0.35 * sleep_score) + (0.25 * subj_score) + acwr_penalty
        else:
            # Manual / No HRV Mode: 55% Sleep, 45% Subjective
            raw_score = (0.55 * sleep_score) + (0.45 * subj_score) + acwr_penalty

        recovery_score = int(round(max(0.0, min(100.0, raw_score))))

        # 6. State Machine Classification
        state = cls.readiness_for(recovery_score)
        directive = {
            ReadinessState.OPTIMAL: "High readiness detected. Progressive overload, heavy compound movements, or high intensity recommended.",
            ReadinessState.MODERATE: "Normal baseline readiness. Standard hypertrophy/endurance session with moderate volume (RPE 7-8).",
            ReadinessState.REDUCED: "Mild fatigue or suppressed recovery. Scaled-back volume and lower axial load recommended.",
            ReadinessState.DEPLETED: "Recovery is low. Gentle mobility, foam rolling, or a Zone 1 walk instead of training.",
        }[state]

        if acwr_status == ACWRStatus.DANGER_ZONE:
            directive += " [ALERT: ACWR > 1.5 indicates high acute fatigue spike; deload recommended.]"

        breakdown = RecoveryMetricsBreakdown(
            hrv_z_score=z_score,
            sleep_score=sleep_score,
            subjective_score=subj_score,
            acwr=acwr_val,
            acwr_status=acwr_status
        )

        return RecoveryCalculationResponse(
            recovery_score=recovery_score,
            readiness_state=state,
            metrics_breakdown=breakdown,
            recommendation_directive=directive
        )

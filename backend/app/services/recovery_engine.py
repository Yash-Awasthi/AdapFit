from typing import Optional, Tuple
import math
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
        
        # Map Z-Score (-2.0 to +2.0) linearly to (0 to 100), centered at 50 for z=0
        hrv_score = 50.0 + (z_score * 25.0)
        hrv_score = max(0.0, min(100.0, hrv_score))
        
        return round(z_score, 2), round(hrv_score, 1)

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
        Formula: (Soreness + Energy + (11-Stress) + (11-Fatigue)) / 40 * 100
        """
        if checkin is None:
            return 75.0  # Default neutral/good
        
        # Energy is derived as (11 - fatigue) or direct ratings
        soreness = checkin.soreness          # 1 (sore) to 10 (fresh)
        fatigue_inverted = 11 - checkin.fatigue # 1 (exhausted -> inv 10) to 10 (energized -> inv 1) wait:
        # If checkin.fatigue is 1 (exhausted), 11-fatigue = 10, but we want 1=exhausted (bad) so let's use direct score:
        # In schemas: soreness: 1(sore)-10(fresh), fatigue: 1(exhausted)-10(energized), stress: 1(relaxed)-10(extreme stress)
        energy_rating = checkin.fatigue     # 1 (exhausted) to 10 (energized)
        stress_inverted = 11 - checkin.stress # 1 (relaxed -> 10) to 10 (stressed -> 1)
        
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
        if recovery_score >= 85:
            state = ReadinessState.OPTIMAL
            directive = "High readiness detected. Progressive overload, heavy compound movements, or high intensity recommended."
        elif recovery_score >= 65:
            state = ReadinessState.MODERATE
            directive = "Normal baseline readiness. Standard hypertrophy/endurance session with moderate volume (RPE 7-8)."
        elif recovery_score >= 45:
            state = ReadinessState.REDUCED
            directive = "Mild fatigue or suppressed recovery. Scaled-back volume, lower axial load, or active recovery recommended."
        else:
            state = ReadinessState.DEPLETED
            directive = "Systemic exhaustion or severe workload spike. Prescribed full rest, gentle mobility, foam rolling, or Zone 1 walk."

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

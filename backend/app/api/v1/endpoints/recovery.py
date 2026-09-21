from fastapi import APIRouter, HTTPException, status
from app.models.schemas import RecoveryCalculationRequest, RecoveryCalculationResponse
from app.services.recovery_engine import RecoveryEngine
from app.services import personal_baseline
from app.core.storage import storage

router = APIRouter()


async def _loads(user_id: str, acute: float | None, chronic: float | None) -> tuple[float | None, float | None]:
    """
    Training load for the ACWR term.

    The client may send its own figures, but when it does not the stored
    workload history is the answer — asking the phone for a number the server
    already has is how two devices end up disagreeing about the same day.
    """
    if acute is not None and chronic is not None:
        return acute, chronic
    history = await storage.get_workload_history(user_id, 28)
    latest = history[-1] if history else {}
    return (
        acute if acute is not None else latest.get("acute_load"),
        chronic if chronic is not None else latest.get("chronic_load"),
    )


@router.post("", response_model=RecoveryCalculationResponse, status_code=status.HTTP_201_CREATED)
async def create_recovery_log(req: RecoveryCalculationRequest):
    """Log daily recovery data and compute recovery score with ML insights."""
    try:
        # The whole point of the score is that it is relative to this user's
        # own normal; without the baseline every account is measured against
        # the same population defaults.
        baseline = await personal_baseline.load(req.user_id)
        acute_load, chronic_load = await _loads(req.user_id, req.current_acute_load, req.current_chronic_load)

        response = RecoveryEngine.compute_daily_recovery(
            wearable_data=req.wearable_data,
            subjective_checkin=req.subjective_checkin,
            baseline=baseline,
            acute_load=acute_load,
            chronic_load=chronic_load,
        )

        from app.services.ml_engine import ml_engine
        recovery_logs = await storage.get_recovery_logs(req.user_id, 28)
        workout_logs = await storage.get_workout_logs(req.user_id, 28)
        features = ml_engine.extract_features(recovery_logs, workout_logs)
        ml_insights = ml_engine.predict_readiness(features)

        acwr = response.metrics_breakdown.acwr or 1.0
        injury_risk = ml_engine.compute_injury_risk(acwr, 0.0, 0.0, 0)

        wd = req.wearable_data
        sc = req.subjective_checkin
        resting_hr = wd.resting_heart_rate if wd else None
        await storage.add_recovery_log(req.user_id, {
            "recovery_score": response.recovery_score,
            "readiness_state": response.readiness_state.value,
            "hrv_rmssd": wd.hrv_rmssd if wd else None,
            "sleep_duration_hours": wd.sleep_duration_hours if wd else None,
            "sleep_efficiency_pct": wd.sleep_efficiency_pct if wd else None,
            "hrv_z_score": response.metrics_breakdown.hrv_z_score,
            "sleep_score": response.metrics_breakdown.sleep_score,
            "subjective_score": response.metrics_breakdown.subjective_score,
            "resting_heart_rate": resting_hr,
            # Stored rather than recomputed downstream: the decision rules read
            # this field, and the baseline it was measured against moves.
            "resting_hr_delta": (resting_hr - baseline.rhr_baseline) if resting_hr is not None else None,
            "steps": wd.steps if wd else None,
            "active_calories": wd.active_calories if wd else None,
            "soreness_score": sc.soreness if sc else None,
            "fatigue_score": sc.fatigue if sc else None,
            "stress_score": sc.stress if sc else None,
            "sore_muscle_groups": sc.sore_muscle_groups if sc else [],
            "pain_flagged": getattr(sc, "pain_flagged", False) if sc else False,
            "illness_flagged": getattr(sc, "illness_flagged", False) if sc else False,
            "log_date": req.log_date,
        })

        # Today's reading is part of tomorrow's normal.
        await personal_baseline.refresh(req.user_id)

        return RecoveryCalculationResponse(
            recovery_score=response.recovery_score,
            readiness_state=response.readiness_state,
            metrics_breakdown=response.metrics_breakdown,
            recommendation_directive=response.recommendation_directive,
            ml_insights=ml_insights,
            injury_risk=injury_risk,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Recovery calculation failed") from e


@router.get("")
async def list_recovery_logs(user_id: str, days: int = 28):
    """List recovery log history."""
    logs = await storage.get_recovery_logs(user_id, days)
    return {"user_id": user_id, "items": logs, "count": len(logs)}

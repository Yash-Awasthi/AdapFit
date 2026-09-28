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

        acwr = response.metrics_breakdown.acwr
        injury_risk = ml_engine.compute_injury_risk(acwr, 0.0, 0.0, 0) if acwr is not None else None

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


def _domain(name: str, score, insight: str) -> dict:
    available = score is not None
    return {"name": name, "score": round(score) if available else 0, "weight": 0, "weighted_score": 0,
            "status": ("good" if score >= 70 else "moderate" if score >= 40 else "low") if available else "no_data",
            "insight": insight, "data_available": available}


@router.get("/today")
async def recovery_today(user_id: str):
    """
    Today's check-in explained: each domain against the user's own baseline,
    and the training decision with its reasons. Same score as the check-in.
    """
    from app.services.daily_decision import decide, signals_from_logs

    logs = await storage.get_recovery_logs(user_id, 1)
    if not logs:
        return {"overall_score": None, "recovery_level": "no_data", "domains": [], "cross_domain_insights": [],
                "recommendations": [], "training_recommendation": "Complete a morning check-in to get today's recovery.",
                "confidence": "low", "data_completeness": 0, "calculated_at": None}
    log = logs[-1]
    history = await storage.get_recovery_logs(user_id, personal_baseline.WINDOW_DAYS)
    workload = await storage.get_workload_history(user_id, 28)
    base = personal_baseline.compute(history, workload)
    latest_load = workload[-1] if workload else None
    result = decide(signals_from_logs(log, None, latest_load, await storage.get_workout_logs(user_id, 7)))

    hrv, z = log.get("hrv_rmssd"), log.get("hrv_z_score")
    rhr, rhr_delta = log.get("resting_heart_rate"), log.get("resting_hr_delta")
    acwr = latest_load.get("acwr") if latest_load else None
    domains = [
        _domain("hrv", None if z is None else max(0, min(100, 60 + z * 20)),
                f"HRV {hrv:.0f} ms, {z:+.1f} SD from your normal of {base['hrv_mean_rmssd']:.0f} ms."
                if hrv is not None and z is not None else "No HRV in today's check-in."),
        _domain("sleep", log.get("sleep_score"),
                f"{log['sleep_duration_hours']}h against your usual {base['sleep_target_hours']}h."
                if log.get("sleep_duration_hours") is not None else "No sleep in today's check-in."),
        _domain("subjective", log.get("subjective_score"),
                "From your soreness, fatigue and stress ratings." if log.get("subjective_score") is not None
                else "No soreness, fatigue or stress ratings today."),
        _domain("heart_rate", None if rhr_delta is None else max(0, min(100, 70 - rhr_delta * 6)),
                f"Resting HR {rhr:.0f} bpm, {rhr_delta:+.0f} from your normal." if rhr_delta is not None and rhr is not None
                else "No resting heart rate today."),
        _domain("training_load", None if acwr is None else max(0, 100 - abs(acwr - 1.05) * 120),
                f"This week's load is {acwr:.2f}x your 4-week average." if acwr is not None
                else "No training logged in the last 4 weeks."),
    ]
    priority = {"REST": "high", "RECOVER": "high", "REDUCE": "medium", "TRAIN": "low"}[result.decision.value]
    recommendations = [{"priority": priority, "category": "training", "message": result.headline,
                        "rationale": "; ".join(result.reasons)}]
    recommendations += [{"priority": "high", "category": "caution", "message": c, "rationale": ""} for c in result.cautions]
    if base["confidence"] < 1:
        recommendations.append({
            "priority": "low", "category": "baseline",
            "message": f"Your personal baseline is {round(base['confidence'] * 100)}% built.",
            "rationale": f"It uses {base['sample_counts']['hrv']} HRV readings so far; 14 make it fully yours.",
        })
    score = log.get("recovery_score")
    return {
        "overall_score": score,
        "recovery_level": (log.get("readiness_state") or "").lower(),
        "domains": domains,
        "cross_domain_insights": result.reasons + result.cautions,
        "recommendations": recommendations,
        "training_recommendation": result.headline,
        "confidence": result.confidence,
        "data_completeness": round(sum(d["data_available"] for d in domains) / len(domains) * 100),
        "calculated_at": log.get("log_date") or log.get("created_at"),
        "baseline": base,
    }

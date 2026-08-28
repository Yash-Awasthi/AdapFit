"""
AdapFit Supervisor Agent
Routes between specialized agents, resolves conflicts, synthesizes final recommendations.
"""
from typing import Dict, List, Any, Optional


class SupervisorAgent:
    """Central orchestrator that coordinates specialized agents."""

    def synthesize_recommendation(self, recovery_assessment, workout_plan, acwr_status, ml_predictions, nlp_insights=None, agent_memory=None):
        readiness_state = recovery_assessment.get("readiness_state", "MODERATE")
        recovery_score = recovery_assessment.get("recovery_score", 70)
        acwr_status_val = acwr_status.get("acwr_status", "SWEET_SPOT")
        
        recommendation = {
            "readiness_state": readiness_state,
            "recovery_score": recovery_score,
            "acwr_status": acwr_status_val,
            "actions": [],
            "warnings": [],
            "insights": [],
        }
        
        if acwr_status_val == "DANGER_ZONE":
            recommendation["warnings"].append("ACWR > 1.5: Mandatory deload recommended.")
            recommendation["actions"].append("Deload: Cap volume at 50%, RPE <= 5")
        elif acwr_status_val == "CAUTION":
            recommendation["warnings"].append("ACWR between 1.3-1.5. Fatigue accumulating.")
            recommendation["actions"].append("Reduce high-intensity finishers")
        
        if readiness_state == "OPTIMAL":
            recommendation["actions"].append("Full progressive overload permitted. RPE 8-9.")
        elif readiness_state == "MODERATE":
            recommendation["actions"].append("Standard training. RPE 7-8.")
        elif readiness_state == "REDUCED":
            recommendation["actions"].append("Scaled-back volume (-40%). Mobility focus.")
        else:
            recommendation["actions"].append("Active recovery only. Rest or gentle mobility.")
        
        if ml_predictions and ml_predictions.get("is_trained"):
            predicted = ml_predictions.get("predicted_state", "UNKNOWN")
            confidence = ml_predictions.get("confidence", 0)
            recommendation["insights"].append(f"ML predicts tomorrow: {predicted} ({confidence:.0%})")
        
        if agent_memory:
            accepted = agent_memory.get("accepted_workouts", 0)
            rejected = agent_memory.get("rejected_workouts", 0)
            rate = accepted / max(accepted + rejected, 1)
            if rate < 0.5:
                recommendation["insights"].append(f"Low adherence ({rate:.0%}). Simplify plans.")
            elif rate > 0.8:
                recommendation["insights"].append(f"High adherence ({rate:.0%}). Great engagement.")
        
        return recommendation

    def resolve_conflict(self, workout_suggestion, acwr_warning, injury_risk):
        if acwr_warning or injury_risk.get("risk_level") in ["CRITICAL", "ELEVATED"]:
            return {"resolution": "safety_override", "reason": injury_risk.get("recommendation", "High risk")}
        return {"resolution": "approved"}

    def get_status(self):
        return {"agent_type": "supervisor", "version": "2.0"}


supervisor_agent = SupervisorAgent()

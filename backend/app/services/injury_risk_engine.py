"""
AdapFit Injury Risk Prediction Engine
Multi-factor analysis combining training load patterns, recovery scores,
biomechanical indicators, and historical data to predict and prevent injuries.
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
import math


# Injury risk factor weights (evidence-based)
RISK_WEIGHTS = {
    "acwr": 0.25,
    "load_spike": 0.15,
    "fatigue_accumulation": 0.20,
    "sleep_deficit": 0.10,
    "hrv_decline": 0.10,
    "consecutive_high_rpe": 0.10,
    "muscle_imbalance": 0.05,
    "previous_injury": 0.05,
}

# Body region vulnerability mapping
MUSCLE_VULNERABILITY = {
    "hamstrings": {"high_risk_rpe": 8, "fatigue_multiplier": 1.3, "common_in": ["sprinting", "deadlift"]},
    "lower_back": {"high_risk_rpe": 7, "fatigue_multiplier": 1.4, "common_in": ["deadlift", "squat", "row"]},
    "shoulders": {"high_risk_rpe": 7, "fatigue_multiplier": 1.2, "common_in": ["bench", "ohp", "pull_up"]},
    "knees": {"high_risk_rpe": 7, "fatigue_multiplier": 1.25, "common_in": ["squat", "leg_press", "lunges"]},
    "hips": {"high_risk_rpe": 6, "fatigue_multiplier": 1.15, "common_in": ["deadlift", "squat", "hip_thrust"]},
    "elbows": {"high_risk_rpe": 6, "fatigue_multiplier": 1.1, "common_in": ["curl", "tricep_extension", "row"]},
    "ankles": {"high_risk_rpe": 5, "fatigue_multiplier": 1.1, "common_in": ["calf_raise", "squat", "running"]},
}

# Weekly load distribution — sudden spikes in specific patterns
DANGEROUS_PATTERNS = {
    "same_day_double": {
        "description": "Two high-intensity sessions in one day",
        "risk_add": 20,
    },
    "3_consecutive_high": {
        "description": "3+ consecutive days of high RPE (>=7)",
        "risk_add": 15,
    },
    "volume_doubling": {
        "description": "Weekly volume doubled compared to previous week",
        "risk_add": 25,
    },
    "novel_movement_spike": {
        "description": "High volume of unfamiliar exercises",
        "risk_add": 10,
    },
    "return_from_break": {
        "description": "Returning after 7+ day gap",
        "risk_add": 20,
    },
}


class InjuryRiskEngine:
    """
    Predicts injury risk by analyzing multiple training and recovery factors.
    Generates risk scores, identifies vulnerable body regions, and provides
    actionable prevention recommendations.
    """

    def analyze(
        self,
        workout_logs: List[dict],
        recovery_logs: List[dict],
        injury_history: Optional[List[dict]] = None,
    ) -> Dict[str, Any]:
        """
        Full injury risk analysis.
        Returns risk score, contributing factors, vulnerable regions, and recommendations.
        """
        if not workout_logs:
            return self._empty_result("No training data available for analysis")

        # Calculate individual risk factors
        factors = {}

        # 1. ACWR risk
        factors["acwr"] = self._assess_acwr_risk(workout_logs)

        # 2. Load spike detection
        factors["load_spike"] = self._assess_load_spike(workout_logs)

        # 3. Fatigue accumulation
        factors["fatigue_accumulation"] = self._assess_fatigue(workout_logs, recovery_logs)

        # 4. Sleep deficit
        factors["sleep_deficit"] = self._assess_sleep_deficit(recovery_logs)

        # 5. HRV decline
        factors["hrv_decline"] = self._assess_hrv_decline(recovery_logs)

        # 6. Consecutive high RPE
        factors["consecutive_high_rpe"] = self._assess_consecutive_high_rpe(workout_logs)

        # 7. Muscle imbalance
        factors["muscle_imbalance"] = self._assess_muscle_imbalance(workout_logs)

        # 8. Previous injury
        factors["previous_injury"] = self._assess_injury_history(injury_history or [])

        # Weighted composite risk score
        composite_risk = sum(
            factors[key]["score"] * RISK_WEIGHTS.get(key, 0.1)
            for key in factors
        )
        composite_risk = min(100, max(0, composite_risk))

        # Risk level
        if composite_risk >= 70:
            risk_level = "CRITICAL"
        elif composite_risk >= 50:
            risk_level = "HIGH"
        elif composite_risk >= 30:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        # Identify vulnerable body regions
        vulnerable_regions = self._identify_vulnerable_regions(workout_logs, recovery_logs, factors)

        # Detect dangerous training patterns
        patterns = self._detect_patterns(workout_logs)

        # Generate recommendations
        recommendations = self._generate_recommendations(factors, risk_level, vulnerable_regions, patterns)

        return {
            "risk_score": round(composite_risk, 1),
            "risk_level": risk_level,
            "factors": factors,
            "vulnerable_regions": vulnerable_regions,
            "dangerous_patterns": patterns,
            "recommendations": recommendations,
            "analysis_date": datetime.now(timezone.utc).isoformat(),
            "data_points": {
                "workouts_analyzed": len(workout_logs),
                "recovery_logs_analyzed": len(recovery_logs),
                "days_covered": self._days_covered(workout_logs),
            },
        }

    def predict_region_risk(
        self, workout_logs: List[dict], region: str
    ) -> Dict[str, Any]:
        """Predict risk for a specific body region."""
        if region not in MUSCLE_VULNERABILITY:
            return {"error": f"Unknown region: {region}"}

        vuln = MUSCLE_VULNERABILITY[region]

        # Count recent exercises targeting this region
        recent_count = 0
        total_volume = 0
        for wl in workout_logs[-14:]:
            exercises = wl.get("exercises", [])
            for ex in exercises:
                ex_id = ex.get("exercise_id", "")
                ex_name = ex.get("name", "").lower()
                if any(t in ex_id or t in ex_name for t in vuln["common_in"]):
                    recent_count += 1
                    total_volume += ex.get("sets", 0) * ex.get("reps", 0)

        # Calculate risk based on exposure
        if recent_count == 0:
            exposure_risk = 5  # Low but not zero
        elif recent_count <= 4:
            exposure_risk = 20
        elif recent_count <= 8:
            exposure_risk = 45
        elif recent_count <= 12:
            exposure_risk = 65
        else:
            exposure_risk = 85

        # Factor in recovery quality
        avg_recovery = 70
        if workout_logs:
            # Use recovery logs if available in the workout log
            recovery_scores = [wl.get("recovery_score", 70) for wl in workout_logs[-7:] if wl.get("recovery_score")]
            if recovery_scores:
                avg_recovery = sum(recovery_scores) / len(recovery_scores)

        recovery_factor = 1.0 - (avg_recovery / 200)  # Lower recovery = higher risk
        final_risk = min(100, exposure_risk * (1 + recovery_factor))

        return {
            "region": region,
            "risk_score": round(final_risk, 1),
            "risk_level": "HIGH" if final_risk >= 60 else ("MODERATE" if final_risk >= 30 else "LOW"),
            "recent_sessions": recent_count,
            "total_volume_14d": total_volume,
            "exposure_risk": round(exposure_risk, 1),
            "recovery_factor": round(recovery_factor, 2),
            "prevention_tips": self._region_prevention_tips(region, final_risk),
        }

    def get_weekly_risk_trend(
        self, workout_logs: List[dict], recovery_logs: List[dict], weeks: int = 4
    ) -> Dict[str, Any]:
        """Get risk score trend over recent weeks."""
        if not workout_logs:
            return {"trend": "no_data", "weekly_scores": []}

        weekly_scores = []
        now = datetime.now(timezone.utc)

        for w in range(weeks):
            week_end = now - timedelta(weeks=w)
            week_start = week_end - timedelta(days=7)

            # Filter logs for this week
            week_workouts = [
                wl for wl in workout_logs
                if self._parse_date(wl.get("log_date", "")) and
                week_start <= self._parse_date(wl.get("log_date", "")) <= week_end
            ]
            week_recoveries = [
                rl for rl in recovery_logs
                if self._parse_date(rl.get("log_date", "")) and
                week_start <= self._parse_date(rl.get("log_date", "")) <= week_end
            ]

            if week_workouts:
                result = self.analyze(week_workouts, week_recoveries)
                weekly_scores.append({
                    "week": f"Week {weeks - w}",
                    "risk_score": result["risk_score"],
                    "risk_level": result["risk_level"],
                })
            else:
                weekly_scores.append({
                    "week": f"Week {weeks - w}",
                    "risk_score": 0,
                    "risk_level": "NO_DATA",
                })

        # Trend direction
        scores = [ws["risk_score"] for ws in weekly_scores if ws["risk_level"] != "NO_DATA"]
        if len(scores) >= 2:
            trend = "increasing" if scores[0] > scores[-1] + 5 else ("decreasing" if scores[0] < scores[-1] - 5 else "stable")
        else:
            trend = "insufficient_data"

        return {
            "trend": trend,
            "weekly_scores": weekly_scores,
            "current_risk": scores[0] if scores else 0,
        }

    # --- Internal risk factor assessments ---

    def _assess_acwr_risk(self, workout_logs: List[dict]) -> Dict[str, Any]:
        """Assess risk from ACWR values."""
        acwr_values = [wl.get("acwr", 1.0) for wl in workout_logs[-28:] if wl.get("acwr")]
        if not acwr_values:
            return {"score": 10, "detail": "No ACWR data available", "level": "UNKNOWN"}

        latest = acwr_values[-1]
        if latest > 1.5:
            score = 90
            level = "DANGER"
            detail = f"ACWR {latest:.2f} exceeds danger zone (>1.5)"
        elif latest > 1.3:
            score = 60
            level = "CAUTION"
            detail = f"ACWR {latest:.2f} in caution zone (1.3-1.5)"
        elif latest < 0.7:
            score = 30
            level = "UNDERTRAINING"
            detail = f"ACWR {latest:.2f} indicates undertraining (<0.7)"
        elif 0.8 <= latest <= 1.3:
            score = 10
            level = "OPTIMAL"
            detail = f"ACWR {latest:.2f} in optimal zone (0.8-1.3)"
        else:
            score = 20
            level = "ACCEPTABLE"
            detail = f"ACWR {latest:.2f}"

        return {"score": score, "detail": detail, "level": level, "latest_acwr": latest}

    def _assess_load_spike(self, workout_logs: List[dict]) -> Dict[str, Any]:
        """Detect sudden load spikes."""
        loads = [wl.get("session_load", 0) for wl in workout_logs[-14:]]
        if len(loads) < 4:
            return {"score": 10, "detail": "Insufficient data for spike detection"}

        # Compare recent sessions to rolling average
        recent_3 = sum(loads[-3:]) / 3 if loads[-3:] else 0
        avg_all = sum(loads[:-3]) / max(len(loads[:-3]), 1) if loads[:-3] else recent_3

        if avg_all > 0:
            spike_ratio = recent_3 / avg_all
        else:
            spike_ratio = 1.0

        if spike_ratio > 1.8:
            score = 80
            detail = f"Load spike: recent avg is {spike_ratio:.1f}x the baseline"
        elif spike_ratio > 1.4:
            score = 50
            detail = f"Moderate load increase: {spike_ratio:.1f}x baseline"
        elif spike_ratio < 0.5:
            score = 15
            detail = f"Load drop: {spike_ratio:.1f}x baseline (detraining risk)"
        else:
            score = 10
            detail = f"Stable load: {spike_ratio:.1f}x baseline"

        return {"score": score, "detail": detail, "spike_ratio": round(spike_ratio, 2)}

    def _assess_fatigue(self, workout_logs: List[dict], recovery_logs: List[dict]) -> Dict[str, Any]:
        """Assess fatigue accumulation from training patterns."""
        rpe_values = [wl.get("session_rpe", 5) for wl in workout_logs[-14:]]

        if not rpe_values:
            return {"score": 10, "detail": "No RPE data"}

        # Average RPE
        avg_rpe = sum(rpe_values) / len(rpe_values)

        # High RPE ratio
        high_rpe_count = sum(1 for r in rpe_values if r >= 7)
        high_rpe_ratio = high_rpe_count / len(rpe_values)

        # Recovery trend if available
        recovery_trend = 0
        if recovery_logs and len(recovery_logs) >= 7:
            early = sum(r.get("recovery_score", 70) for r in recovery_logs[:7]) / 7
            late = sum(r.get("recovery_score", 70) for r in recovery_logs[-7:]) / 7
            recovery_trend = late - early  # Negative = declining

        # Composite fatigue score
        score = 0
        score += min(30, avg_rpe * 4)  # Higher avg RPE = more fatigue
        score += min(30, high_rpe_ratio * 50)  # More high RPE sessions
        if recovery_trend < -10:
            score += 25
        elif recovery_trend < -5:
            score += 15

        score = min(100, max(0, score))

        return {
            "score": round(score, 1),
            "detail": f"Avg RPE: {avg_rpe:.1f}, High RPE ratio: {high_rpe_ratio:.0%}, Recovery trend: {recovery_trend:+.1f}",
            "avg_rpe": round(avg_rpe, 1),
            "high_rpe_ratio": round(high_rpe_ratio, 2),
            "recovery_trend": round(recovery_trend, 1),
        }

    def _assess_sleep_deficit(self, recovery_logs: List[dict]) -> Dict[str, Any]:
        """Assess sleep debt risk."""
        sleep_data = [r.get("sleep_duration_hours", 7) for r in recovery_logs[-7:] if r.get("sleep_duration_hours")]
        if not sleep_data:
            return {"score": 10, "detail": "No sleep data"}

        avg_sleep = sum(sleep_data) / len(sleep_data)
        deficit = max(0, 7.5 - avg_sleep)  # Target 7.5h
        consecutive_bad = 0
        for s in reversed(sleep_data):
            if s < 6.5:
                consecutive_bad += 1
            else:
                break

        if deficit > 2.0 or consecutive_bad >= 3:
            score = 75
            detail = f"Severe sleep debt: {deficit:.1f}h deficit, {consecutive_bad} consecutive bad nights"
        elif deficit > 1.0 or consecutive_bad >= 2:
            score = 45
            detail = f"Moderate sleep debt: {deficit:.1f}h deficit"
        elif deficit > 0.5:
            score = 25
            detail = f"Mild sleep deficit: {deficit:.1f}h"
        else:
            score = 5
            detail = f"Adequate sleep: {avg_sleep:.1f}h avg"

        return {
            "score": score, "detail": detail,
            "avg_sleep_hours": round(avg_sleep, 1),
            "deficit_hours": round(deficit, 1),
            "consecutive_bad_nights": consecutive_bad,
        }

    def _assess_hrv_decline(self, recovery_logs: List[dict]) -> Dict[str, Any]:
        """Assess HRV decline as injury precursor."""
        hrv_values = [r.get("hrv_rmssd") for r in recovery_logs[-14:] if r.get("hrv_rmssd")]
        if len(hrv_values) < 5:
            return {"score": 10, "detail": "Insufficient HRV data"}

        # Linear trend
        n = len(hrv_values)
        x_mean = (n - 1) / 2
        y_mean = sum(hrv_values) / n
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(hrv_values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator > 0 else 0

        # Recent vs baseline
        baseline = sum(hrv_values[:n//2]) / max(n//2, 1)
        recent = sum(hrv_values[n//2:]) / max(n - n//2, 1)
        pct_change = ((recent - baseline) / max(baseline, 1)) * 100

        if slope < -3.0 or pct_change < -20:
            score = 80
            detail = f"Rapid HRV decline: slope {slope:.2f}/day, {pct_change:+.1f}% change"
        elif slope < -1.0 or pct_change < -10:
            score = 50
            detail = f"Moderate HRV decline: slope {slope:.2f}/day, {pct_change:+.1f}% change"
        elif slope < -0.5:
            score = 25
            detail = f"Mild HRV decline: slope {slope:.2f}/day"
        else:
            score = 5
            detail = f"HRV stable/improving: slope {slope:.2f}/day"

        return {
            "score": score, "detail": detail,
            "slope": round(slope, 3),
            "pct_change": round(pct_change, 1),
            "current_mean": round(recent, 1),
            "baseline_mean": round(baseline, 1),
        }

    def _assess_consecutive_high_rpe(self, workout_logs: List[dict]) -> Dict[str, Any]:
        """Check for dangerous consecutive high-intensity patterns."""
        consecutive = 0
        for wl in reversed(workout_logs):
            if wl.get("session_rpe", 0) >= 7:
                consecutive += 1
            else:
                break

        if consecutive >= 5:
            score = 85
            detail = f"Dangerous: {consecutive} consecutive high-RPE sessions (>=7)"
        elif consecutive >= 3:
            score = 50
            detail = f"Warning: {consecutive} consecutive high-RPE sessions"
        elif consecutive >= 1:
            score = 15
            detail = f"{consecutive} high-RPE session(s) — monitor fatigue"
        else:
            score = 5
            detail = "No consecutive high-RPE sessions"

        return {"score": score, "detail": detail, "consecutive_count": consecutive}

    def _assess_muscle_imbalance(self, workout_logs: List[dict]) -> Dict[str, Any]:
        """Detect muscle group imbalances from training volume."""
        # Map exercises to muscle groups
        muscle_volume = {}
        for wl in workout_logs[-28:]:
            for ex in wl.get("exercises", []):
                muscles = ex.get("target_muscles", [])
                if isinstance(muscles, str):
                    muscles = [muscles]
                volume = ex.get("sets", 0) * ex.get("reps", 0)
                for m in muscles:
                    m_lower = m.lower() if isinstance(m, str) else str(m).lower()
                    muscle_volume[m_lower] = muscle_volume.get(m_lower, 0) + volume

        if not muscle_volume:
            return {"score": 10, "detail": "No muscle group data available"}

        # Check push/pull balance
        push_muscles = ["chest", "shoulders", "triceps"]
        pull_muscles = ["back", "biceps", "lats"]
        push_volume = sum(muscle_volume.get(m, 0) for m in push_muscles)
        pull_volume = sum(muscle_volume.get(m, 0) for m in pull_muscles)

        if push_volume > 0 and pull_volume > 0:
            ratio = push_volume / pull_volume
        else:
            ratio = 1.0

        if ratio > 2.0:
            score = 60
            detail = f"Significant push/pull imbalance: {ratio:.1f}:1 (ideal ~1:1)"
        elif ratio > 1.5:
            score = 35
            detail = f"Moderate push/pull imbalance: {ratio:.1f}:1"
        elif ratio < 0.5:
            score = 35
            detail = f"Reverse imbalance (pull dominant): {ratio:.1f}:1"
        else:
            score = 5
            detail = f"Good push/pull balance: {ratio:.1f}:1"

        return {"score": score, "detail": detail, "push_pull_ratio": round(ratio, 2)}

    def _assess_injury_history(self, injury_history: List[dict]) -> Dict[str, Any]:
        """Factor in previous injuries for re-injury risk."""
        if not injury_history:
            return {"score": 5, "detail": "No injury history recorded"}

        recent_injuries = [
            inj for inj in injury_history
            if self._parse_date(inj.get("date", "")) and
            self._parse_date(inj.get("date", "")) > datetime.now(timezone.utc) - timedelta(days=90)
        ]

        if recent_injuries:
            regions = [inj.get("region", "unknown") for inj in recent_injuries]
            score = min(60, 20 + len(recent_injuries) * 15)
            detail = f"{len(recent_injuries)} injury(s) in last 90 days: {', '.join(set(regions))}"
        else:
            score = 5
            detail = f"{len(injury_history)} historical injury(ies), none recent"

        return {"score": score, "detail": detail, "recent_count": len(recent_injuries)}

    def _identify_vulnerable_regions(
        self, workout_logs: List[dict], recovery_logs: List[dict],
        factors: Dict
    ) -> List[Dict[str, Any]]:
        """Identify body regions at elevated risk."""
        regions = []
        fatigue_score = factors.get("fatigue_accumulation", {}).get("score", 0)
        sleep_score = factors.get("sleep_deficit", {}).get("score", 0)

        for region, vuln in MUSCLE_VULNERABILITY.items():
            # Count exercises targeting this region
            count = 0
            for wl in workout_logs[-14:]:
                for ex in wl.get("exercises", []):
                    ex_id = ex.get("exercise_id", "").lower()
                    if any(t in ex_id for t in vuln["common_in"]):
                        count += 1

            if count > 0:
                base_risk = min(60, count * 8)
                # Amplify by fatigue and sleep deficit
                amplified = base_risk * vuln["fatigue_multiplier"]
                if fatigue_score > 50:
                    amplified *= 1.2
                if sleep_score > 40:
                    amplified *= 1.1

                amplified = min(100, amplified)
                if amplified >= 30:
                    regions.append({
                        "region": region,
                        "risk_score": round(amplified, 1),
                        "exposure_sessions": count,
                        "risk_factors": [
                            f"{count} sessions targeting {region} in 14d",
                            f"Fatigue level: {fatigue_score:.0f}/100",
                        ],
                    })

        regions.sort(key=lambda x: -x["risk_score"])
        return regions[:5]

    def _detect_patterns(self, workout_logs: List[dict]) -> List[Dict[str, Any]]:
        """Detect dangerous training patterns."""
        patterns = []

        # 3+ consecutive high RPE
        consecutive = 0
        for wl in reversed(workout_logs):
            if wl.get("session_rpe", 0) >= 7:
                consecutive += 1
            else:
                break
        if consecutive >= 3:
            patterns.append({
                "pattern": "3_consecutive_high",
                "description": DANGEROUS_PATTERNS["3_consecutive_high"]["description"],
                "severity": "high" if consecutive >= 5 else "moderate",
                "days": consecutive,
            })

        # Volume doubling
        if len(workout_logs) >= 14:
            week1_load = sum(wl.get("session_load", 0) for wl in workout_logs[-7:])
            week2_load = sum(wl.get("session_load", 0) for wl in workout_logs[-14:-7])
            if week2_load > 0 and week1_load > week2_load * 1.8:
                patterns.append({
                    "pattern": "volume_doubling",
                    "description": DANGEROUS_PATTERNS["volume_doubling"]["description"],
                    "severity": "high",
                    "ratio": round(week1_load / week2_load, 2),
                })

        # Return from break (>7 day gap)
        if len(workout_logs) >= 2:
            last_date = self._parse_date(workout_logs[-1].get("log_date", ""))
            prev_date = self._parse_date(workout_logs[-2].get("log_date", ""))
            if last_date and prev_date:
                gap = (last_date - prev_date).days
                if gap > 7:
                    patterns.append({
                        "pattern": "return_from_break",
                        "description": DANGEROUS_PATTERNS["return_from_break"]["description"],
                        "severity": "moderate",
                        "gap_days": gap,
                    })

        return patterns

    def _generate_recommendations(
        self, factors: Dict, risk_level: str,
        vulnerable_regions: List, patterns: List
    ) -> List[Dict[str, Any]]:
        """Generate actionable prevention recommendations."""
        recs = []

        if risk_level == "CRITICAL":
            recs.append({
                "priority": "urgent",
                "action": "Consider 2-3 days complete rest or very light mobility work",
                "reason": "Injury risk is critical — recovery is the priority",
            })

        # ACWR-based
        acwr = factors.get("acwr", {})
        if acwr.get("level") == "DANGER":
            recs.append({
                "priority": "high",
                "action": "Reduce training volume by 40-50% this week (deload)",
                "reason": f"ACWR {acwr.get('latest_acwr', 0):.2f} is dangerously high",
            })
        elif acwr.get("level") == "CAUTION":
            recs.append({
                "priority": "medium",
                "action": "Maintain current volume but avoid adding new exercises",
                "reason": f"ACWR {acwr.get('latest_acwr', 0):.2f} approaching danger zone",
            })

        # Sleep
        sleep = factors.get("sleep_deficit", {})
        if sleep.get("score", 0) > 40:
            recs.append({
                "priority": "high",
                "action": "Prioritize 7.5+ hours of sleep tonight",
                "reason": f"Sleep deficit of {sleep.get('deficit_hours', 0):.1f}h impairs recovery",
            })

        # HRV
        hrv = factors.get("hrv_decline", {})
        if hrv.get("score", 0) > 40:
            recs.append({
                "priority": "high",
                "action": "Reduce intensity — HRV is declining, autonomic stress is high",
                "reason": f"HRV trend: {hrv.get('slope', 0):.2f}/day",
            })

        # Muscle-specific
        for region in vulnerable_regions[:2]:
            recs.append({
                "priority": "medium",
                "action": f"Reduce {region['region']} volume — high exposure detected",
                "reason": f"{region['exposure_sessions']} sessions in 14 days",
            })

        # Patterns
        for pattern in patterns:
            if pattern["severity"] == "high":
                recs.append({
                    "priority": "high",
                    "action": f"Address pattern: {pattern['description']}",
                    "reason": "Detected dangerous training pattern",
                })

        # Fatigue
        fatigue = factors.get("fatigue_accumulation", {})
        if fatigue.get("score", 0) > 50:
            recs.append({
                "priority": "medium",
                "action": "Schedule a deload week — fatigue is accumulating",
                "reason": f"Average RPE: {fatigue.get('avg_rpe', 0):.1f}",
            })

        if not recs:
            recs.append({
                "priority": "info",
                "action": "Training load is manageable — continue current approach",
                "reason": "All risk factors within acceptable range",
            })

        return recs

    def _region_prevention_tips(self, region: str, risk: float) -> List[str]:
        """Get region-specific prevention tips."""
        tips = {
            "hamstrings": [
                "Include Nordic hamstring curls 2x/week",
                "Warm up with dynamic leg swings before heavy deadlifts",
                "Monitor RDL volume carefully",
            ],
            "lower_back": [
                "Brace core before every lift (valsalva maneuver)",
                "Limit axial loading when fatigued",
                "Include anti-extension exercises (dead bugs, planks)",
            ],
            "shoulders": [
                "Warm up with band pull-aparts and face pulls",
                "Limit overhead pressing when fatigued",
                "Maintain 2:1 pull-to-push ratio",
            ],
            "knees": [
                "Warm up with bodyweight squats before loading",
                "Avoid deep squats when fatigued",
                "Include VMO strengthening (terminal knee extensions)",
            ],
            "hips": [
                "Dynamic hip circles before training",
                "Include hip flexor stretching in warm-up",
                "Monitor squat depth when hip soreness is present",
            ],
            "elbows": [
                "Limit direct arm work volume when fatigued",
                "Use wrist wraps for heavy pressing",
                "Include forearm/wrist warm-up",
            ],
            "ankles": [
                "Ankle mobility work before squatting",
                "Wear stable footwear for heavy lifts",
                "Include calf raises for ankle stability",
            ],
        }
        base_tips = tips.get(region, ["Monitor volume and intensity", "Include adequate warm-up"])
        if risk >= 60:
            base_tips = [f"REDUCE {region} training volume by 30-50%"] + base_tips
        return base_tips

    def _empty_result(self, reason: str) -> Dict[str, Any]:
        return {
            "risk_score": 0,
            "risk_level": "NO_DATA",
            "factors": {},
            "vulnerable_regions": [],
            "dangerous_patterns": [],
            "recommendations": [{"priority": "info", "action": reason, "reason": reason}],
            "analysis_date": datetime.now(timezone.utc).isoformat(),
            "data_points": {"workouts_analyzed": 0, "recovery_logs_analyzed": 0, "days_covered": 0},
        }

    def _days_covered(self, workout_logs: List[dict]) -> int:
        dates = set()
        for wl in workout_logs:
            d = wl.get("log_date", "")
            if d:
                dates.add(d)
        return len(dates)

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            # Ensure timezone-aware for safe comparisons
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            return None

    def get_status(self) -> Dict[str, Any]:
        return {
            "regions_monitored": len(MUSCLE_VULNERABILITY),
            "risk_factors": len(RISK_WEIGHTS),
            "dangerous_patterns": len(DANGEROUS_PATTERNS),
        }


# Singleton
injury_risk_engine = InjuryRiskEngine()

"""
Sleep journal: each user's logged nights and everything derived from them.

A night records what was measured and nothing else. Stage minutes come from a
wearable or not at all; a manual log carries bedtime, wake time, how it felt
and, optionally, awakenings. Scores use only the measured parts
(SleepAnalyzer rescales weights over what is present).
"""
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.services.sleep_analyzer import (
    SleepAnalyzer, bedtime_consistency_std, grade_for,
)

RECOMMENDED_SLEEP = {
    "teenager": (8, 10),
    "young_adult": (7, 9),
    "adult": (7, 9),
    "older_adult": (7, 8),
}
CYCLE_MINUTES = 90
STAGES = ("deep", "rem", "light", "awake")


def _clock_minutes(value: str) -> int:
    hour, minute = (int(part) for part in value.split(":")[:2])
    if not (0 <= hour < 24 and 0 <= minute < 60):
        raise ValueError(f"Not a clock time: {value}")
    return hour * 60 + minute


def minutes_between(bedtime: str, wake_time: str) -> int:
    """Minutes from bedtime to wake time, across midnight when needed."""
    return (_clock_minutes(wake_time) - _clock_minutes(bedtime)) % 1440


def _fmt_clock(total_minutes: float) -> str:
    m = int(round(total_minutes)) % 1440
    return f"{m // 60:02d}:{m % 60:02d}"


@dataclass
class SleepNight:
    id: str
    date: str
    bedtime: str
    wake_time: str
    total_minutes: int
    source: str = "manual"
    efficiency_pct: Optional[float] = None
    deep_minutes: Optional[float] = None
    rem_minutes: Optional[float] = None
    light_minutes: Optional[float] = None
    awake_minutes: Optional[float] = None
    interruptions: Optional[int] = None
    minutes_to_fall_asleep: Optional[float] = None
    quality_rating: Optional[int] = None
    heart_rate_avg: Optional[float] = None
    hrv_avg: Optional[float] = None
    notes: Optional[str] = None
    logged_at: str = ""

    @property
    def has_stages(self) -> bool:
        return self.deep_minutes is not None and self.rem_minutes is not None


class SleepJournal:
    def __init__(self):
        self._nights: list[SleepNight] = []
        self.age_group = "adult"
        self.target_bedtime: Optional[str] = None
        self.target_wake: Optional[str] = None
        self._analyzer = SleepAnalyzer()

    # --- profile ---
    def set_profile(self, age_group: str = "adult", target_bedtime: Optional[str] = None,
                    target_wake: Optional[str] = None) -> dict:
        if age_group not in RECOMMENDED_SLEEP:
            raise ValueError(f"age_group must be one of {sorted(RECOMMENDED_SLEEP)}")
        for value in (target_bedtime, target_wake):
            if value is not None:
                _clock_minutes(value)
        self.age_group, self.target_bedtime, self.target_wake = age_group, target_bedtime, target_wake
        return self.profile()

    def profile(self) -> dict:
        low, high = RECOMMENDED_SLEEP[self.age_group]
        return {"age_group": self.age_group, "target_bedtime": self.target_bedtime,
                "target_wake": self.target_wake, "recommended_hours": [low, high]}

    # --- nights ---
    def log(self, bedtime: str, wake_time: str, date: Optional[str] = None,
            total_minutes: Optional[int] = None, **measured) -> dict:
        in_bed = minutes_between(bedtime, wake_time)
        night = SleepNight(
            id=uuid.uuid4().hex[:8],
            date=date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            bedtime=bedtime, wake_time=wake_time,
            total_minutes=total_minutes if total_minutes is not None else in_bed,
            logged_at=datetime.now(timezone.utc).isoformat(),
            **{k: v for k, v in measured.items() if v is not None},
        )
        if night.total_minutes <= 0:
            raise ValueError("Wake time must differ from bedtime")
        self._nights.append(night)
        self._nights.sort(key=lambda n: (n.date, n.logged_at))
        return self._public(night)

    def nights(self, days: int = 7) -> list[dict]:
        return [self._public(n) for n in self._recent(days)]

    def delete(self, night_id: str) -> bool:
        before = len(self._nights)
        self._nights = [n for n in self._nights if n.id != night_id]
        return len(self._nights) < before

    def _recent(self, days: int) -> list[SleepNight]:
        return self._nights[-days:]

    def _public(self, night: SleepNight) -> dict:
        data = asdict(night)
        data["score"] = self._score_night(night)["sleep_score"]
        return data

    def _score_night(self, night: SleepNight, consistency_std: Optional[float] = None) -> dict:
        return self._analyzer.calculate_sleep_score(
            duration_hours=night.total_minutes / 60,
            deep_minutes=night.deep_minutes,
            rem_minutes=night.rem_minutes,
            awake_minutes=night.awake_minutes,
            interruptions=night.interruptions,
            bedtime_consistency_std=consistency_std,
            efficiency_pct=night.efficiency_pct,
        )

    # --- derived views ---
    def analysis(self, days: int = 7) -> dict:
        nights = self._recent(days)
        if not nights:
            return {
                "score": 0, "grade": None, "quality_label": "insufficient_data", "nights_analyzed": 0,
                "avg_duration_hours": None, "avg_efficiency_pct": None, "bedtime_consistency_min": None,
                "stage_breakdown": [], "measured": [], "debt": self.debt(), "trend": self.trend(days),
                "recommendations": [{
                    "category": "general", "priority": "low", "title": "Log last night",
                    "description": "Nothing is logged yet, so there is nothing to score.",
                    "tips": ["Add your bedtime and wake time. A wearable adds sleep stages."],
                }],
                "bedtime_plan": self.bedtime_plan(),
            }

        n = len(nights)
        avg_minutes = sum(x.total_minutes for x in nights) / n
        effs = [x.efficiency_pct for x in nights if x.efficiency_pct is not None]
        interrupts = [x.interruptions for x in nights if x.interruptions is not None]
        staged = [x for x in nights if x.has_stages]
        consistency = bedtime_consistency_std([x.bedtime for x in nights]) if n >= 2 else None

        def avg_stage(stage: str) -> Optional[float]:
            vals = [getattr(x, f"{stage}_minutes") for x in staged if getattr(x, f"{stage}_minutes") is not None]
            return sum(vals) / len(vals) if vals else None

        stage_avgs = {st: avg_stage(st) for st in STAGES}
        staged_minutes = sum(x.total_minutes for x in staged) / len(staged) if staged else 0
        breakdown = [
            {"name": st, "minutes": round(v, 1), "percentage": round(v / max(staged_minutes, 1) * 100, 1)}
            for st, v in stage_avgs.items() if v is not None
        ]

        scored = self._analyzer.calculate_sleep_score(
            duration_hours=avg_minutes / 60,
            deep_minutes=stage_avgs["deep"] * avg_minutes / staged_minutes if staged and stage_avgs["deep"] is not None else None,
            rem_minutes=stage_avgs["rem"] * avg_minutes / staged_minutes if staged and stage_avgs["rem"] is not None else None,
            interruptions=round(sum(interrupts) / len(interrupts)) if interrupts else None,
            bedtime_consistency_std=consistency,
            efficiency_pct=sum(effs) / len(effs) if effs else None,
        )
        return {
            "score": scored["sleep_score"],
            "grade": grade_for(scored["sleep_score"]),
            "quality_label": scored["quality_label"],
            "nights_analyzed": n,
            "avg_duration_hours": round(avg_minutes / 60, 2),
            "avg_efficiency_pct": round(sum(effs) / len(effs), 1) if effs else None,
            "bedtime_consistency_min": round(consistency, 1) if consistency is not None else None,
            "stage_breakdown": breakdown,
            "measured": scored["measured"],
            "breakdown": scored["breakdown"],
            "debt": self.debt(),
            "trend": self.trend(days),
            "recommendations": self._analyzer.get_recommendations(scored),
            "bedtime_plan": self.bedtime_plan(),
        }

    def debt(self, days: int = 7) -> dict:
        """Accumulated shortfall against the lower end of the recommended range."""
        low, high = RECOMMENDED_SLEEP[self.age_group]
        nights = self._recent(days)
        if not nights:
            return {"debt_hours": None, "nights_counted": 0, "target_hours": low}
        shortfall = sum(max(0.0, low - x.total_minutes / 60) for x in nights)
        short_nights = sum(1 for x in nights if x.total_minutes / 60 < low)
        if shortfall > 5:
            plan = "Large sleep debt. Protect 8+ hours for the next few nights and keep caffeine before noon."
        elif shortfall > 2:
            plan = "Some sleep debt. Add 30-60 minutes a night this week rather than one long lie-in."
        elif shortfall > 0:
            plan = "A small shortfall. A consistent schedule will close it."
        else:
            plan = "No sleep debt over the nights logged."
        return {"debt_hours": round(shortfall, 1), "nights_counted": len(nights),
                "short_nights": short_nights, "target_hours": low, "recovery_plan": plan}

    def trend(self, days: int = 14) -> dict:
        nights = self._recent(days)
        scored = [self._score_night(x) for x in nights]
        return self._analyzer.detect_trends(scored)

    def bedtime_plan(self) -> Optional[dict]:
        """Bedtimes that end on a full 90-minute cycle at the target wake time."""
        if not self.target_wake:
            return None
        onsets = [x.minutes_to_fall_asleep for x in self._nights[-14:] if x.minutes_to_fall_asleep is not None]
        onset = round(sum(onsets) / len(onsets)) if onsets else 15
        wake = _clock_minutes(self.target_wake)
        low, high = RECOMMENDED_SLEEP[self.age_group]
        options = []
        for cycles in (6, 5, 4):
            sleep_minutes = cycles * CYCLE_MINUTES
            options.append({
                "bedtime": _fmt_clock(wake - sleep_minutes - onset),
                "cycles": cycles,
                "sleep_hours": sleep_minutes / 60,
                "within_recommended": low <= sleep_minutes / 60 <= high,
            })
        return {"target_wake": self.target_wake, "minutes_to_fall_asleep": onset,
                "onset_source": "your logs" if onsets else "typical 15 minutes", "options": options}

    def latest_summary(self) -> dict:
        """Last night in brief, for the health summary card."""
        if not self._nights:
            return {"score": None, "quality": "no_data"}
        night = self._nights[-1]
        scored = self._score_night(night)
        return {"score": scored["sleep_score"], "quality": scored["quality_label"],
                "total_sleep_hours": round(night.total_minutes / 60, 1),
                "deep_sleep_minutes": night.deep_minutes, "rem_sleep_minutes": night.rem_minutes}


from app.core.per_user import per_user, register

sleep_journal = register("sleep_tracker.sleep_journal", per_user(SleepJournal))

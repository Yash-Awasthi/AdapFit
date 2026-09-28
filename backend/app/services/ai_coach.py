"""
Coach briefing and weekly report, built from the user's own records.

Every insight cites the numbers it came from. When a source has too little
data the briefing says what to log instead of filling the gap with a typical
user's week.
"""
import random
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Optional

from app.core.storage import storage
from app.services.sleep_tracker import sleep_journal

MOTIVATIONAL = [
    "Every workout counts. Even 10 minutes is better than none.",
    "Progress isn't linear. Consistency beats intensity.",
    "Your body adapts to what you do often. Keep showing up.",
    "Small daily improvements add up to big results.",
    "Rest days are part of training, not a break from it.",
    "The hardest part of any session is starting. You already know how to do that.",
]


def _date(record: dict, *keys: str) -> Optional[datetime]:
    for key in keys:
        raw = record.get(key)
        if raw:
            try:
                parsed = datetime.fromisoformat(str(raw)[:19])
                return parsed.replace(tzinfo=None)
            except ValueError:
                continue
    return None


def _within(records: list[dict], start: datetime, end: datetime, *keys: str) -> list[dict]:
    out = []
    for r in records:
        d = _date(r, *keys)
        if d is not None and start <= d < end:
            out.append(r)
    return out


def _values(records: list[dict], key: str) -> list[float]:
    return [float(r[key]) for r in records if isinstance(r.get(key), (int, float))]


async def _sources(user_id: str) -> dict:
    return {
        "recovery": await storage.get_recovery_logs(user_id, 60),
        "workouts": await storage.get_workout_logs(user_id, 60),
        "workload": await storage.get_workload_history(user_id, 28),
        "moods": (await storage.get_agent_memory(user_id)).get("mood_logs", []),
        "sleep": sleep_journal.instance_for(user_id),
    }


def _insight(category: str, title: str, message: str, action: str, priority: str, evidence: dict) -> dict:
    return {"category": category, "title": title, "message": message, "action": action,
            "priority": priority, "evidence": evidence}


async def briefing(user_id: str) -> dict:
    """Today's readiness call plus whatever the data supports saying."""
    src = await _sources(user_id)
    insights: list[dict] = []
    missing: list[str] = []
    now = datetime.now()

    recovery = src["recovery"]
    today_call = None
    if recovery:
        last = recovery[-1]
        state, score = last.get("readiness_state"), last.get("recovery_score")
        plans = {
            "OPTIMAL": ("Train hard today", "You are recovered. A heavy or high-intensity session fits today.", "high"),
            "MODERATE": ("Train normally", "Recovery is fine. Keep today's planned session at normal intensity.", "medium"),
            "REDUCED": ("Go lighter today", "Recovery is below your normal. Cut volume by a third or swap to technique work.", "medium"),
            "DEPLETED": ("Rest or walk today", "Recovery is well below your normal. Rest, walk, or do mobility only.", "high"),
        }
        if state in plans:
            title, message, priority = plans[state]
            today_call = _insight("recovery", title, f"{message} Score {score}/100.", title, priority,
                                  {"recovery_score": score, "readiness_state": state, "date": last.get("log_date")})
        if last.get("pain_flagged") or last.get("illness_flagged"):
            insights.append(_insight(
                "safety", "You flagged pain or illness",
                "Skip hard training until it settles. If it lasts more than a few days or gets worse, see a doctor or physiotherapist.",
                "Log how it feels tomorrow", "high",
                {"pain_flagged": bool(last.get("pain_flagged")), "illness_flagged": bool(last.get("illness_flagged"))}))

        hrv = _values(recovery, "hrv_rmssd")
        if len(hrv) >= 10:
            recent, prior = mean(hrv[-7:]), mean(hrv[:-7])
            change = (recent - prior) / prior * 100 if prior else 0
            if abs(change) >= 8:
                up = change > 0
                insights.append(_insight(
                    "hrv", "HRV trending up" if up else "HRV trending down",
                    f"Your 7-day HRV average is {recent:.0f} ms against {prior:.0f} ms before, {change:+.0f}%. "
                    + ("Your body is handling the load well." if up else "Sleep, stress, illness or hard training can each do this."),
                    "Keep the current plan" if up else "Add an easy day this week and protect sleep",
                    "low" if up else "medium", {"hrv_7d_ms": round(recent, 1), "hrv_prior_ms": round(prior, 1)}))
        else:
            missing.append(f"HRV on {10 - len(hrv)} more check-ins to see your HRV trend")
    else:
        missing.append("a daily check-in to get today's readiness")

    journal = src["sleep"]
    debt = journal.debt()
    if debt["nights_counted"] >= 3 and debt["debt_hours"] and debt["debt_hours"] >= 2:
        insights.append(_insight(
            "sleep", "Sleep debt building",
            f"You are {debt['debt_hours']}h short of {debt['target_hours']}h a night over your last {debt['nights_counted']} logged nights.",
            debt.get("recovery_plan", "Go to bed 30 minutes earlier"), "high" if debt["debt_hours"] > 5 else "medium",
            {"debt_hours": debt["debt_hours"], "nights": debt["nights_counted"]}))
    elif debt["nights_counted"] < 3:
        missing.append("3 nights of sleep to track sleep debt")

    workload = src["workload"]
    acwr_values = _values(workload, "acwr")
    if acwr_values:
        acwr = acwr_values[-1]
        if acwr > 1.5:
            insights.append(_insight(
                "load", "Training load jumped",
                f"This week's load is {acwr:.2f} times your 4-week average. Jumps above 1.5 are when overuse injuries cluster.",
                "Hold load steady for the next week", "high", {"acwr": round(acwr, 2)}))
        elif acwr < 0.8 and len(workload) >= 7:
            insights.append(_insight(
                "load", "Load has dropped",
                f"This week's load is {acwr:.2f} times your 4-week average. Fitness fades if this lasts.",
                "Add one session this week", "low", {"acwr": round(acwr, 2)}))

    workouts = src["workouts"]
    this_week = _within(workouts, now - timedelta(days=7), now + timedelta(days=1), "completed_at", "created_at")
    last_week = _within(workouts, now - timedelta(days=14), now - timedelta(days=7), "completed_at", "created_at")
    if this_week or last_week:
        insights.append(_insight(
            "consistency", "Training this week",
            f"{len(this_week)} workout{'s' if len(this_week) != 1 else ''} in the last 7 days, {len(last_week)} the week before.",
            "Plan your next session now" if len(this_week) < len(last_week) else "Keep the rhythm going",
            "low", {"this_week": len(this_week), "last_week": len(last_week)}))
    else:
        missing.append("a workout to start tracking consistency")

    moods = src["moods"]
    mood_vals = [m["mood"] for m in moods if isinstance(m.get("mood"), (int, float))]
    if len(mood_vals) >= 6:
        recent, prior = mean(mood_vals[-3:]), mean(mood_vals[:-3])
        if recent <= prior - 1.5:
            insights.append(_insight(
                "mind", "Mood lower lately",
                f"Your last three mood logs average {recent:.1f}/10 against {prior:.1f} before. "
                "If low mood lasts two weeks or more, talking to someone helps. Tele-MANAS is free on 14416.",
                "Try a 10-minute walk outside and a short breathing session", "medium",
                {"mood_recent": round(recent, 1), "mood_prior": round(prior, 1)}))

    priority_rank = {"high": 0, "medium": 1, "low": 2}
    insights.sort(key=lambda i: priority_rank[i["priority"]])
    return {
        "date": now.strftime("%Y-%m-%d"),
        "today": today_call,
        "insights": insights,
        "to_unlock": missing,
        "motivation": random.choice(MOTIVATIONAL),
    }


async def weekly_report(user_id: str) -> dict:
    """The last 7 days against the 7 before, in figures and plain sentences."""
    src = await _sources(user_id)
    now = datetime.now()
    week = (now - timedelta(days=7), now + timedelta(days=1))
    prev = (now - timedelta(days=14), now - timedelta(days=7))

    def window(records: list[dict], span, *keys):
        return _within(records, span[0], span[1], *keys)

    rec_now = window(src["recovery"], week, "log_date", "created_at")
    rec_prev = window(src["recovery"], prev, "log_date", "created_at")
    wk_now = window(src["workouts"], week, "completed_at", "created_at")
    wk_prev = window(src["workouts"], prev, "completed_at", "created_at")
    nights = src["sleep"].nights(7)

    def avg(vals: list[float]) -> Optional[float]:
        return round(mean(vals), 1) if vals else None

    figures = {
        "workouts": len(wk_now),
        "workouts_prev": len(wk_prev),
        "checkins": len(rec_now),
        "avg_recovery": avg(_values(rec_now, "recovery_score")),
        "avg_recovery_prev": avg(_values(rec_prev, "recovery_score")),
        "avg_hrv_ms": avg(_values(rec_now, "hrv_rmssd")),
        "avg_sleep_hours": avg([n["total_minutes"] / 60 for n in nights]) or avg(_values(rec_now, "sleep_duration_hours")),
        "nights_logged": len(nights),
    }
    if not (figures["workouts"] or figures["checkins"] or figures["nights_logged"]):
        return {"status": "insufficient_data", "figures": figures,
                "message": "Nothing logged in the last 7 days yet. Check in, log sleep or finish a workout to get a report."}

    lines = [f"{figures['workouts']} workout{'s' if figures['workouts'] != 1 else ''} this week"
             + (f" ({figures['workouts_prev']} the week before)." if figures["workouts_prev"] else ".")]
    if figures["avg_recovery"] is not None:
        line = f"Average recovery {figures['avg_recovery']}/100"
        if figures["avg_recovery_prev"] is not None:
            delta = figures["avg_recovery"] - figures["avg_recovery_prev"]
            line += f", {'up' if delta >= 0 else 'down'} {abs(delta):.1f} on last week"
        lines.append(line + ".")
    if figures["avg_sleep_hours"] is not None:
        lines.append(f"You slept {figures['avg_sleep_hours']}h a night on average.")
    if figures["avg_hrv_ms"] is not None:
        lines.append(f"HRV averaged {figures['avg_hrv_ms']} ms.")

    focus = "Keep the same routine next week."
    if figures["avg_sleep_hours"] is not None and figures["avg_sleep_hours"] < 7:
        focus = "Next week, protect sleep first: aim for 7+ hours before adding training."
    elif figures["workouts"] < figures["workouts_prev"]:
        focus = "Next week, book your sessions in the calendar to get back to last week's count."
    elif figures["avg_recovery"] is not None and figures["avg_recovery"] >= 75 and figures["workouts"] >= 3:
        focus = "Recovery is holding up; next week can take a small increase in load."

    return {
        "status": "ok",
        "period": f"{(now - timedelta(days=6)).strftime('%d %b')} – {now.strftime('%d %b %Y')}",
        "summary": " ".join(lines),
        "focus": focus,
        "figures": figures,
    }


_feedback: dict[str, list[dict]] = {}


def log_feedback(user_id: str, insight_category: str, helpful: bool, comment: str = "") -> dict:
    _feedback.setdefault(user_id, []).append({
        "category": insight_category, "helpful": helpful, "comment": comment,
        "at": datetime.now(timezone.utc).isoformat(),
    })
    return {"recorded": True}

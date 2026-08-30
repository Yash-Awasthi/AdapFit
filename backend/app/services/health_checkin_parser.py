"""Health Check-in Parser Service.

Extracted from health-skill (inspiration).
Natural language daily health check-in parsing,
mood scoring, pain detection, and symptom extraction.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


MOOD_ADJECTIVES = {
    "awful": 2, "terrible": 2, "horrible": 2,
    "bad": 3, "low": 3, "down": 3, "sad": 3,
    "tired": 4, "meh": 4, "stressed": 4,
    "ok": 5, "okay": 5, "fine": 5, "alright": 5,
    "decent": 6,
    "good": 7, "happy": 7, "positive": 7,
    "great": 9, "excellent": 9, "amazing": 9, "wonderful": 9, "fantastic": 9,
}

PAIN_WORDS = {
    "knee": "knee", "back": "back", "lower back": "back",
    "head": "head", "headache": "head", "migraine": "head",
    "neck": "neck", "shoulder": "shoulder", "shoulders": "shoulder",
    "stomach": "stomach", "belly": "stomach",
}

SLEEP_QUALITY_WORDS = {
    "good sleep": "good", "slept well": "good", "great sleep": "good",
    "poor sleep": "poor", "bad sleep": "poor", "slept badly": "poor",
    "restless": "poor", "ok sleep": "ok",
}

APPETITE_WORDS = {
    "no appetite": "low", "low appetite": "low", "not hungry": "low",
    "high appetite": "high", "hungry": "high", "normal appetite": "normal",
}

ENERGY_WORDS = {
    "exhausted": 2, "drained": 2, "no energy": 2,
    "low energy": 3, "sluggish": 3, "tired": 4,
    "ok energy": 5, "fine": 5,
    "good energy": 7, "energetic": 8, "full of energy": 9,
}


@dataclass
class HealthCheckin:
    mood_score: int | None = None
    mood_label: str | None = None
    sleep_hours: float | None = None
    sleep_quality: str | None = None
    energy_level: int | None = None
    pain_locations: list[str] = field(default_factory=list)
    pain_level: int | None = None
    weight_kg: float | None = None
    hydration_glasses: int | None = None
    calories_estimate: int | None = None
    steps: int | None = None
    medication_taken: bool | None = None
    notes: str = ""
    raw_text: str = ""


def parse_checkin(text: str) -> HealthCheckin:
    """Parse a natural-language daily check-in string."""
    if not text:
        return HealthCheckin(raw_text=text)
    t = text.lower()
    result = HealthCheckin(raw_text=text)
    mood_match = re.search(r':(\d+)', t)
    if mood_match:
        result.mood_score = max(1, min(10, int(mood_match.group(1))))
    else:
        for word, score in MOOD_ADJECTIVES.items():
            if word in t:
                result.mood_score = score
                result.mood_label = word
                break
    sleep_match = re.search(r's(?:leep)?[\s:]*(\d+\.?\d*)', t)
    if sleep_match:
        result.sleep_hours = float(sleep_match.group(1))
    for phrase, quality in SLEEP_QUALITY_WORDS.items():
        if phrase in t:
            result.sleep_quality = quality
            break
    energy_match = re.search(r'e(?:nergy)?[\s:]*(\d+)', t)
    if energy_match:
        result.energy_level = max(1, min(10, int(energy_match.group(1))))
    else:
        for phrase, level in ENERGY_WORDS.items():
            if phrase in t:
                result.energy_level = level
                break
    for word, location in PAIN_WORDS.items():
        if word in t:
            if location not in result.pain_locations:
                result.pain_locations.append(location)
    pain_match = re.search(r'pain[\s:]*(\d+)', t)
    if pain_match:
        result.pain_level = max(1, min(10, int(pain_match.group(1))))
    weight_match = re.search(r'w(?:eight)?[\s:]*(\d+\.?\d*)', t)
    if weight_match:
        result.weight_kg = float(weight_match.group(1))
    water_match = re.search(r'(\d+)\s*(?:glass|water|hydrat)', t)
    if water_match:
        result.hydration_glasses = int(water_match.group(1))
    for phrase, level in APPETITE_WORDS.items():
        if phrase in t:
            break
    if any(word in t for word in ["took med", "took medication", "meds taken", "medication done"]):
        result.medication_taken = True
    elif any(word in t for word in ["forgot med", "missed med", "no med"]):
        result.medication_taken = False
    return result


def calculate_wellness_score(checkin: HealthCheckin) -> int:
    """Calculate a 0-100 wellness score from check-in data."""
    score = 50.0
    components = 0
    if checkin.mood_score:
        score += (checkin.mood_score - 5) * 3
        components += 1
    if checkin.sleep_hours:
        if 7 <= checkin.sleep_hours <= 9:
            score += 10
        elif 6 <= checkin.sleep_hours < 7:
            score += 5
        elif checkin.sleep_hours < 5:
            score -= 10
        components += 1
    if checkin.sleep_quality == "good":
        score += 8
    elif checkin.sleep_quality == "poor":
        score -= 8
    if checkin.energy_level:
        score += (checkin.energy_level - 5) * 2
        components += 1
    if checkin.pain_level:
        score -= checkin.pain_level * 2
        components += 1
    if checkin.pain_locations:
        score -= len(checkin.pain_locations) * 3
    if checkin.medication_taken is True:
        score += 5
    elif checkin.medication_taken is False:
        score -= 5
    return max(0, min(100, int(score)))


def extract_symptoms(checkin: HealthCheckin) -> list[dict[str, Any]]:
    """Extract structured symptoms from check-in."""
    symptoms = []
    if checkin.pain_locations:
        for loc in checkin.pain_locations:
            symptoms.append({
                "type": "pain",
                "location": loc,
                "severity": checkin.pain_level or 5,
            })
    if checkin.mood_score and checkin.mood_score <= 4:
        symptoms.append({
            "type": "mood",
            "description": checkin.mood_label or "low mood",
            "severity": 10 - checkin.mood_score,
        })
    if checkin.energy_level and checkin.energy_level <= 3:
        symptoms.append({
            "type": "fatigue",
            "severity": 10 - checkin.energy_level,
        })
    if checkin.sleep_quality == "poor":
        symptoms.append({
            "type": "sleep",
            "description": "poor sleep quality",
            "severity": 6,
        })
    return symptoms


def generate_checkin_summary(checkins: list[HealthCheckin]) -> dict[str, Any]:
    """Generate summary from multiple check-ins."""
    if not checkins:
        return {"count": 0}
    mood_scores = [c.mood_score for c in checkins if c.mood_score]
    sleep_hours = [c.sleep_hours for c in checkins if c.sleep_hours]
    energy_levels = [c.energy_level for c in checkins if c.energy_level]
    pain_counts = sum(len(c.pain_locations) for c in checkins)
    wellness_scores = [calculate_wellness_score(c) for c in checkins]
    return {
        "count": len(checkins),
        "avg_mood": round(sum(mood_scores) / len(mood_scores), 1) if mood_scores else None,
        "avg_sleep_hours": round(sum(sleep_hours) / len(sleep_hours), 1) if sleep_hours else None,
        "avg_energy": round(sum(energy_levels) / len(energy_levels), 1) if energy_levels else None,
        "avg_wellness_score": round(sum(wellness_scores) / len(wellness_scores), 1),
        "total_pain_reports": pain_counts,
        "medication_adherence": sum(1 for c in checkins if c.medication_taken) / len(checkins) if checkins else 0,
    }

"""
AdapFit Natural Language Workout Logger
Parses free-text workout descriptions into structured data.
"I did 3x10 bench at 80kg RPE 8" → structured workout log.
"""
import re
from typing import Dict, List, Any, Optional, Tuple
from app.services.intent_classifier import entity_extractor


class NLWorkoutLogger:
    """
    Parses natural language workout descriptions into structured workout entries.
    Supports common patterns like:
    - "3x10 bench press at 80kg"
    - "bench 4x8 100kg RPE 9"
    - "did 3 sets of 12 squats at 60kg"
    - "5k run in 25 minutes"
    - "30 min jog"
    """

    # Exercise names stop at these boundaries ("at 80kg", "with dumbbells", "for 4x8", "rpe 8", end)
    # Exercise names: letters/words, stopping before at/with/for/rpe/numbers
    NAME_PATTERN = r'[a-zA-Z]+(?:\s+(?!at\b|with\b|for\b|rpe\b|\d)[a-zA-Z]+)*'

    # Pattern: [sets]x[reps] [exercise] [at/with] [weight] [rpe X]
    SETS_X_REPS = re.compile(
        r'(\d+)\s*[x×]\s*(\d+)\s+'
        r'((?!at\b|with\b|for\b|rpe\b)[a-zA-Z]+(?:\s+(?!at\b|with\b|for\b|rpe\b|\d)[a-zA-Z]+)*)'
        r'(?:\s+(?:(?:at|with|w/?)\s+)?(\d+(?:\.\d+)?)\s*(?:kg|lbs?|pounds?|kilos?))?',
        re.IGNORECASE
    )

    # Pattern: [exercise] [sets]x[reps] [weight]
    EXERCISE_FIRST = re.compile(
        r'((?!at\b|with\b|for\b|rpe\b)[a-zA-Z]+(?:\s+(?!at\b|with\b|for\b|rpe\b|\d)[a-zA-Z]+)*)'
        r'\s+(\d+)\s*[x×]\s*(\d+)',
        re.IGNORECASE
    )

    # Pattern: [sets] sets of [reps] [exercise] [at weight]
    SETS_OF_REPS = re.compile(
        r'(\d+)\s+sets?\s+(?:of\s+)?(\d+)\s+'
        r'((?!at\b|with\b|for\b|rpe\b)[a-zA-Z]+(?:\s+(?!at\b|with\b|for\b|rpe\b|\d)[a-zA-Z]+)*)'
        r'(?:\s+(?:at|with)\s+(\d+(?:\.\d+)?)\s*(?:kg|lbs?|pounds?|kilos?))?',
        re.IGNORECASE
    )

    # Pattern: [reps] reps [exercise] [at weight]  -> single set
    REPS_FIRST = re.compile(
        r'(\d+)\s+reps?\s+(?:of\s+)?'
        r'((?!at\b|with\b|for\b|rpe\b)[a-zA-Z]+(?:\s+(?!at\b|with\b|for\b|rpe\b|\d)[a-zA-Z]+)*)'
        r'(?:\s+(?:at|with)\s+(\d+(?:\.\d+)?)\s*(?:kg|lbs?|pounds?|kilos?))?',
        re.IGNORECASE
    )

    # Pattern: ran/did X km/miles in Y minutes
    CARDIO_PATTERN = re.compile(
        r'(?:ran|run|jog|jogged|cycled|cycled|biked|walked?|walk)\s+'
        r'(\d+(?:\.\d+)?)\s*(km|mi(?:les?)?|miles?)\s*'
        r'(?:in\s+(\d+)\s*(?:min(?:utes?)?|mins?))?',
        re.IGNORECASE
    )

    # Pattern: [duration] min [activity]
    DURATION_ACTIVITY = re.compile(
        r'(\d+)\s*(?:min(?:utes?)?|mins?)\s+'
        r'([a-zA-Z][a-zA-Z\s\-\'\"]+)',
        re.IGNORECASE
    )

    # Pattern: [exercise] for [sets] x [reps]
    EXERCISE_FOR = re.compile(
        r'((?!at\b|with\b|for\b|rpe\b)[a-zA-Z]+(?:\s+(?!at\b|with\b|for\b|rpe\b|\d)[a-zA-Z]+)*)'
        r'\s+for\s+(\d+)\s*[x×]\s*(\d+)',
        re.IGNORECASE
    )

    # Pattern: [distance] km/miles [activity] [in N minutes]  ("5k run in 25 minutes")
    CARDIO_NUMBER_FIRST = re.compile(
        r'(\d+(?:\.\d+)?)\s*(km|mi(?:les?)?)\s+'
        r'(?:ran|run|jog|jogged|cycled|biked|walked?|walk)'
        r'(?:\s+in\s+(\d+)\s*(?:min(?:utes?)?|mins?))?',
        re.IGNORECASE
    )
    RPE_EMBED = re.compile(r'(?:rpe|rpe\s*[:=]?)\s*(\d+(?:\.\d+)?)', re.IGNORECASE)

    def parse(self, text: str, timestamp: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse a natural language workout description into structured data.
        Returns a workout log entry with exercises, cardio, and metadata.
        """
        entities = entity_extractor.extract_all(text)
        exercises = self._extract_exercises_structured(text)
        cardio = self._extract_cardio(text)
        global_rpe = entities.get("rpe")

        # Build the structured log
        log_entry = {
            "exercises": exercises,
            "cardio": cardio,
            "duration_minutes": self._extract_total_duration(text, entities),
            "global_rpe": global_rpe,
            "notes": text.strip(),
            "total_sets": sum(e.get("sets", 0) for e in exercises),
            "total_reps": sum(e.get("sets", 0) * e.get("reps", 0) for e in exercises),
            "total_volume_kg": sum(
                e.get("sets", 0) * e.get("reps", 0) * e.get("weight_kg", 0)
                for e in exercises
            ),
            "timestamp": timestamp,
            "parse_confidence": self._compute_confidence(exercises, cardio, entities),
        }

        return log_entry

    def _extract_exercises_structured(self, text: str) -> List[Dict[str, Any]]:
        """Extract exercise entries with sets, reps, weight."""
        exercises = []
        seen = set()

        # Pattern 1: 3x10 bench press at 80kg
        for m in self.SETS_X_REPS.finditer(text):
            name = m.group(3).strip()
            eid = self._resolve_exercise_id(name)
            if eid and eid not in seen:
                seen.add(eid)
                exercises.append(self._build_entry(
                    name=name, exercise_id=eid,
                    sets=int(m.group(1)), reps=int(m.group(2)),
                    weight_str=m.group(4), text=text
                ))

        # Pattern 2: bench 4x8 100kg
        for m in self.EXERCISE_FIRST.finditer(text):
            name = m.group(1).strip()
            eid = self._resolve_exercise_id(name)
            if eid and eid not in seen:
                seen.add(eid)
                exercises.append(self._build_entry(
                    name=name, exercise_id=eid,
                    sets=int(m.group(2)), reps=int(m.group(3)),
                    weight_str=None, text=text
                ))

        # Pattern 3: 3 sets of 12 squats [at 60kg]
        for m in self.SETS_OF_REPS.finditer(text):
            name = m.group(3).strip()
            eid = self._resolve_exercise_id(name)
            if eid and eid not in seen:
                seen.add(eid)
                exercises.append(self._build_entry(
                    name=name, exercise_id=eid,
                    sets=int(m.group(1)), reps=int(m.group(2)),
                    weight_str=m.group(4), text=text
                ))

        # Pattern 3b: 12 reps of bench press at 80kg (single set)
        for m in self.REPS_FIRST.finditer(text):
            name = m.group(2).strip()
            eid = self._resolve_exercise_id(name)
            if eid and eid not in seen:
                seen.add(eid)
                exercises.append(self._build_entry(
                    name=name, exercise_id=eid,
                    sets=1, reps=int(m.group(1)),
                    weight_str=m.group(3), text=text
                ))

        # Pattern 4: bench press for 4x8
        for m in self.EXERCISE_FOR.finditer(text):
            name = m.group(1).strip()
            eid = self._resolve_exercise_id(name)
            if eid and eid not in seen:
                seen.add(eid)
                exercises.append(self._build_entry(
                    name=name, exercise_id=eid,
                    sets=int(m.group(2)), reps=int(m.group(3)),
                    weight_str=None, text=text
                ))

        # If no structured patterns matched, try entity extraction
        if not exercises:
            ent_exercises = entity_extractor.extract_exercises(text)
            weights = entities.get("weights", []) if (entities := entity_extractor.extract_all(text)) else []
            reps_list = entities.get("reps", [])
            sets_list = entities.get("sets", [])

            for i, ex in enumerate(ent_exercises[:6]):
                if ex["exercise_id"] not in seen:
                    seen.add(ex["exercise_id"])
                    exercises.append(self._build_entry(
                        name=ex["alias"], exercise_id=ex["exercise_id"],
                        sets=sets_list[i] if i < len(sets_list) else (reps_list[i] if i < len(reps_list) else 3),
                        reps=reps_list[i] if i < len(reps_list) else 10,
                        weight_str=None, text=text
                    ))

        return exercises

    def _build_entry(
        self, name: str, exercise_id: str, sets: int, reps: int,
        weight_str: Optional[str], text: str
    ) -> Dict[str, Any]:
        """Build a single exercise log entry."""
        weight_kg = 0.0
        if weight_str:
            try:
                weight_kg = float(weight_str)
            except ValueError:
                pass

        # Also check for weight in text near the exercise name
        if weight_kg == 0:
            weight_match = re.search(
                rf'{re.escape(name)}.*?(\d+(?:\.\d+)?)\s*(?:kg|lbs?|pounds?|kilos?)',
                text, re.IGNORECASE
            )
            if weight_match:
                val = float(weight_match.group(1))
                unit = weight_match.group(0).lower()
                if "lb" in unit or "pound" in unit:
                    val *= 0.453592
                weight_kg = val

        rpe_match = re.search(r'(?:rpe|rpe\s*[:=]?)\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
        rpe = float(rpe_match.group(1)) if rpe_match else None

        return {
            "exercise_id": exercise_id,
            "name": name.title(),
            "sets": sets,
            "reps": reps,
            "weight_kg": round(weight_kg, 1),
            "rpe": rpe,
            "volume_kg": round(sets * reps * weight_kg, 1),
        }

    def _extract_cardio(self, text: str) -> List[Dict[str, Any]]:
        """Extract cardio entries."""
        entries = []

        for m in self.CARDIO_PATTERN.finditer(text):
            distance = float(m.group(1))
            unit = "km" if m.group(2).lower().startswith("k") else "miles"
            duration = int(m.group(3)) if m.group(3) else None
            entries.append({
                "type": "cardio",
                "distance": distance,
                "distance_unit": unit,
                "duration_minutes": duration,
                "pace_min_per_km": round(duration / distance, 1) if duration and distance else None,
            })

        # Number-first: "5k run in 25 minutes"
        for m in self.CARDIO_NUMBER_FIRST.finditer(text):
            distance = float(m.group(1))
            unit = "km" if m.group(2).lower().startswith("k") else "miles"
            duration = int(m.group(3)) if m.group(3) else None
            entries.append({
                "type": "cardio",
                "distance": distance,
                "distance_unit": unit,
                "duration_minutes": duration,
                "pace_min_per_km": round(duration / distance, 1) if duration and distance else None,
            })

        # Duration-only: "30 min jog"
        for m in self.DURATION_ACTIVITY.finditer(text):
            activity = m.group(2).strip().lower()
            if any(w in activity for w in ["jog", "run", "bike", "cycle", "walk", "swim", "row"]):
                entries.append({
                    "type": "cardio",
                    "activity": activity,
                    "duration_minutes": int(m.group(1)),
                })

        return entries

    def _extract_total_duration(self, text: str, entities: dict) -> Optional[int]:
        """Extract total workout duration."""
        durations = entities.get("duration", [])
        if durations:
            # Return the largest duration (likely total)
            return max(d["value"] for d in durations if d["unit"] == "minutes")
        return None

    def _resolve_exercise_id(self, name: str) -> Optional[str]:
        """Resolve exercise name to ID via aliases."""
        from app.services.intent_classifier import entity_extractor as _ee
        aliases = _ee.EXERCISE_ALIASES
        name_lower = name.lower().strip()
        # Direct match
        if name_lower in aliases:
            return aliases[name_lower]
        # Partial match
        for alias, eid in aliases.items():
            if alias in name_lower or name_lower in alias:
                return eid
        # Generate slug as fallback
        slug = re.sub(r'[^a-z0-9]+', '-', name_lower).strip('-')
        return slug if slug else None

    def _compute_confidence(
        self, exercises: list, cardio: list, entities: dict
    ) -> float:
        """Compute parse confidence score (0-1)."""
        if not exercises and not cardio:
            return 0.0
        score = 0.3  # Base for any parse
        if exercises:
            score += 0.3
            # Higher if we have structured data
            if any(e.get("weight_kg", 0) > 0 for e in exercises):
                score += 0.15
            if any(e.get("reps", 0) > 0 for e in exercises):
                score += 0.1
            if any(e.get("sets", 0) > 0 for e in exercises):
                score += 0.1
        if cardio:
            score += 0.2
        return min(1.0, round(score, 2))


nl_workout_logger = NLWorkoutLogger()

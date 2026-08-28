"""
AdapFit Intent Classifier & Entity Extractor
Domain-specific NLP for fitness conversations.
Classifies user intents and extracts structured entities from natural language.
"""
import re
from typing import Dict, List, Any, Optional, Tuple


class IntentClassifier:
    """
    Multi-label intent classifier for fitness coaching conversations.
    Uses keyword patterns, regex rules, and contextual heuristics.
    No external model dependencies — pure Python for zero-latency inference.
    """

    INTENTS = {
        "recovery_query": {
            "patterns": [
                r"\b(how\s+(am\s+i|is\s+my|are\s+my)\b.*\b(recovery|readiness|feel|doing))",
                r"\b(recovery\s+score|readiness\s+state|hrv|am\s+ready)",
                r"\b(can|i\s+can)\b.*\b(train|lift|workout|exercise|push)",
                r"\b(should)\b.*\b(rest|train|workout|skip)",
            ],
            "keywords": ["how am i", "my recovery", "recovery score", "readiness",
                         "am i ready", "can i train", "should i rest", "feel today"],
        },
        "workout_advice": {
            "patterns": [
                r"\b(workout|train|exercise|lift|squat|bench|deadlift)\b.*\b(what|which|how|suggest|plan|recommend|today)",
                r"\b(what\s+(should|do)\s+(i|we))\b.*\b(do|train|workout|exercise)",
                r"\b(give|create|generate|build|make)\b.*\b(workout|routine|program|plan)",
                r"\b(push|pull|leg|upper|lower|full\s+body)\s*(day|workout|session)",
            ],
            "keywords": ["what should i do", "workout plan", "training plan", "suggest a workout",
                         "generate workout", "create routine", "what to train"],
        },
        "exercise_info": {
            "patterns": [
                r"\b(how\s+(do|to)|show|explain|describe)\b.*\b(do|perform|execut)",
                r"\b(proper|correct)\s+(form|technique|way|technique)",
                r"\b(equipment|muscle|target|focus)\b.*\b(for|of|worked|hit)",
                r"\b(alternative|substitut|replace|instead)\s*(for|of)",
            ],
            "keywords": ["how to do", "proper form", "technique", "exercise form",
                         "alternative for", "substitute", "what muscles", "equipment for"],
        },
        "sleep_advice": {
            "patterns": [
                r"\b(sleep|tired|exhaust|rest|nap|insomnia|can'?t\s+sleep)\b",
                r"\b(sleep\s+(quality|duration|hours|score|debt|hygiene))",
            ],
            "keywords": ["sleep", "tired", "exhausted", "fatigue", "can't sleep",
                         "insomnia", "rest day", "sleep quality"],
        },
        "pain_injury": {
            "patterns": [
                r"\b(pain|ache|hurt|injur|sore|strain|pull|tear|snap|sharp)\b",
                r"\b(doesn'?t\s+feel\s+(right|good|normal))",
                r"\b(should\s+I\s+(see|go\s+to)\s+a\s+(doctor|pt|physio))",
            ],
            "keywords": ["pain", "hurt", "injury", "sore", "strain", "hurts",
                         "doesn't feel right", "see a doctor", "physical therapy"],
        },
        "acwr_workload": {
            "patterns": [
                r"\b(acwr|workload|overtrain|undertrain|volume|too\s+much|deload)\b",
                r"\b(am\s+i\s+(doing\s+)?(too\s+much|overtraining|undertraining))",
            ],
            "keywords": ["acwr", "workload", "overtraining", "too much volume",
                         "deload", "undertraining", "workload ratio"],
        },
        "hrv_basics": {
            "patterns": [
                r"\b(hrv|heart\s+rate\s+variab)\b",
                r"\b(rmssd|lf[\s/]hf|autonomic|nervous\s+system)\b",
            ],
            "keywords": ["hrv", "heart rate variability", "rmssd", "nervous system"],
        },
        "nutrition": {
            "patterns": [
                r"\b(eat|diet|calori|protein|carb|fat|macros?|meal|food|nutrition)\b",
                r"\b(bulk|cut|deficit|surplus|tdee|bmr)\b",
            ],
            "keywords": ["eat", "diet", "calories", "protein", "carbs", "macros",
                         "meal plan", "nutrition", "bulk", "cut", "deficit"],
        },
        "motivation": {
            "patterns": [
                r"\b(motivat|inspir|drive|lazy|don'?t\s+want|can'?t\s+be\s+bothered)\b",
                r"\b(give\s+up|quit|struggling|mental|mindset)\b",
            ],
            "keywords": ["motivation", "inspired", "lazy", "don't want to",
                         "give up", "struggling", "mindset"],
        },
        "progress": {
            "patterns": [
                r"\b(progress|improv|getting\s+(stronger|bigger|fitter|leaner)|pr|personal\s+record)\b",
                r"\b(am\s+i\s+improving|results|transformation|before\s+and\s+after)\b",
            ],
            "keywords": ["progress", "improving", "getting stronger", "PR",
                         "personal record", "results", "transformation"],
        },
        "greeting": {
            "patterns": [
                r"^(hi|hello|hey|yo|sup|what'?s\s+up|greetings|good\s+(morning|afternoon|evening))",
            ],
            "keywords": ["hi", "hello", "hey", "what's up", "good morning",
                         "good afternoon", "good evening"],
        },
        "workout_log": {
            "patterns": [
                r"\b(i\s+(did|just\s+did|completed|finished|ran|ran)\b.*\b(set|rep|km|mile|minute))",
                r"\b(log|logged|record|recorded)\b.*\b(workout|exercise|run|session)\b",
                r"\b(\d+)\s*(sets?|reps?|x)\s*\d+.*\b(of|at|on)\b",
                r"\b(bench|squat|dead|press|curl|row|pull|push)\b.*\d+\s*(kg|lbs?|lb|kg|reps?)",
            ],
            "keywords": ["just did", "completed", "logged", "finished workout"],
        },
        "rest_timer": {
            "patterns": [
                r"\b(rest\s*timer|timer|set\s+timer|how\s+long\s+(left|remaining|rest))\b",
            ],
            "keywords": ["rest timer", "timer", "how long left"],
        },
        "body_metrics": {
            "patterns": [
                r"\b(weigh|weight|body\s*fat|bf%|bmi|measure|circumference)\b",
                r"\b(scale| weigh(ed)? |(gained|lost)\s+\d+\s*(kg|lbs?|pounds?))\b",
            ],
            "keywords": ["weight", "body fat", "bmi", "measurements", "weigh in"],
        },
    }

    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify intent(s) from user message.
        Returns primary intent + confidence + all matched intents.
        """
        text_lower = text.lower().strip()
        if not text_lower:
            return {"primary_intent": "empty", "confidence": 0.0, "all_intents": []}

        scores: Dict[str, float] = {}
        matched_details: Dict[str, List[str]] = {}

        for intent, config in self.INTENTS.items():
            score = 0.0
            matches = []

            # Pattern matching (weighted higher)
            for pattern in config.get("patterns", []):
                if re.search(pattern, text_lower):
                    score += 0.6
                    matches.append(f"pattern:{pattern[:30]}")

            # Keyword matching
            for kw in config.get("keywords", []):
                if kw in text_lower:
                    score += 0.3
                    matches.append(f"kw:{kw}")

            if score > 0:
                scores[intent] = min(score, 1.0)
                matched_details[intent] = matches

        if not scores:
            return {"primary_intent": "default", "confidence": 0.5, "all_intents": []}

        sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_intents[0]

        all_intents = [
            {"intent": intent, "confidence": round(conf, 2)}
            for intent, conf in sorted_intents
        ]

        return {
            "primary_intent": primary[0],
            "confidence": round(primary[1], 2),
            "all_intents": all_intents,
        }


class EntityExtractor:
    """
    Domain-specific entity extraction for fitness conversations.
    Extracts exercise names, weights, reps, sets, durations, muscle groups, etc.
    """

    # Unit patterns
    WEIGHT_PATTERN = re.compile(
        r'(\d+(?:\.\d+)?)\s*(kg|kgs|lbs?|pounds?|kilos?)',
        re.IGNORECASE
    )
    REPS_PATTERN = re.compile(
        r'(\d+)\s*(?:reps?|repetitions?|x)',
        re.IGNORECASE
    )
    SETS_PATTERN = re.compile(
        r'(\d+)\s*(?:sets?|sets?\s+of)',
        re.IGNORECASE
    )
    DURATION_PATTERN = re.compile(
        r'(\d+)\s*(?:min(?:utes?)?|hrs?|hours?|seconds?|sec|mins?)',
        re.IGNORECASE
    )
    DISTANCE_PATTERN = re.compile(
        r'(\d+(?:\.\d+)?)\s*(km|kilometers?|mi(?:les?)?|meters?|m)',
        re.IGNORECASE
    )
    RPE_PATTERN = re.compile(
        r'(?:rpe|rpe\s*[:=]?)\s*(\d+(?:\.\d+)?)',
        re.IGNORECASE
    )
    TEMPO_PATTERN = re.compile(
        r'(\d)-(\d)-(\d)(?:-(\d))?',
        re.IGNORECASE
    )
    HEART_RATE_PATTERN = re.compile(
        r'(\d+)\s*(?:bpm|hr|heart\s*rate)',
        re.IGNORECASE
    )

    # Exercise name aliases
    EXERCISE_ALIASES = {
        "bench": "barbell-bench-press",
        "bench press": "barbell-bench-press",
        "bp": "barbell-bench-press",
        "db bench": "dumbbell-bench-press",
        "dumbbell bench": "dumbbell-bench-press",
        "squat": "barbell-squat",
        "barbell squat": "barbell-squat",
        "back squat": "barbell-squat",
        "front squat": "front-squat",
        "goblet squat": "goblet-squat",
        "dead": "conventional-deadlift",
        "deadlift": "conventional-deadlift",
        "dl": "conventional-deadlift",
        "conventional deadlift": "conventional-deadlift",
        "sumo deadlift": "sumo-deadlift",
        "ohp": "overhead-press",
        "overhead press": "overhead-press",
        "military press": "overhead-press",
        "barbell row": "bent-over-barbell-row",
        "row": "bent-over-barbell-row",
        "pull up": "pull-ups",
        "pullup": "pull-ups",
        "pull-ups": "pull-ups",
        "chin up": "chin-ups",
        "chinup": "chin-ups",
        "curl": "barbell-bicep-curl",
        "bicep curl": "barbell-bicep-curl",
        "hammer curl": "hammer-curls",
        "lateral raise": "dumbbell-lateral-raise",
        "lat raise": "dumbbell-lateral-raise",
        "leg press": "leg-press",
        "leg extension": "leg-extensions",
        "leg curl": "lying-leg-curl",
        "calf raise": "standing-calf-raise",
        "tricep pushdown": "tricep-rope-pushdown",
        "pushdown": "tricep-rope-pushdown",
        "dip": "dips",
        "dips": "dips",
        "push up": "pushups",
        "pushup": "pushups",
        "plank": "plank",
        "russian twist": "russian-twist",
        "hip thrust": "barbell-hip-thrust",
        "face pull": "face-pulls",
        "cable fly": "cable-chest-fly",
        "incline bench": "incline-barbell-bench-press",
        "incline press": "incline-barbell-bench-press",
        "romanian deadlift": "romanian-deadlift",
        "rdl": "romanian-deadlift",
        "bulgarian split squat": "bulgarian-split-squat",
        "hack squat": "hack-squat",
        "cable row": "seated-cable-row",
        "lat pulldown": "lat-pulldown",
        "shrugs": "barbell-shrugs",
        "shrug": "barbell-shrugs",
        "hang clean": "hang-clean",
        "power clean": "power-clean",
        "push press": "push-press",
        "arnold press": "arnold-press",
        "preacher curl": "preacher-curl",
        "skull crusher": "skullcrushers",
        "close grip bench": "close-grip-bench-press",
    }

    MUSCLE_GROUP_PATTERNS = {
        "chest": [r"\bchest\b", r"\bpecs?\b"],
        "back": [r"\bback\b", r"\blats?\b", r"\bupper\s+back\b", r"\btraps?\b"],
        "shoulders": [r"\bshoulders?\b", r"\bdelts?\b", r"\bdeltoids?\b"],
        "biceps": [r"\bbiceps?\b", r"\bbicep\b"],
        "triceps": [r"\btriceps?\b", r"\btricep\b"],
        "quads": [r"\bquads?\b", r"\bquadriceps?\b", r"\bthighs?\b"],
        "hamstrings": [r"\bhamstrings?\b", r"\bhamstring\b"],
        "glutes": [r"\bglutes?\b", r"\bglute\b", r"\bbutt\b"],
        "core": [r"\bcore\b", r"\babs?\b", r"\babdominal\b", r"\bstomach\b"],
        "calves": [r"\bcalves?\b", r"\bcalf\b"],
        "forearms": [r"\bforearms?\b", r"\bforearm\b", r"\bgrip\b"],
    }

    # Tempo descriptors
    TEMPO_MAP = {
        "slow": "4-1-2-0",
        "fast": "1-0-1-0",
        "explosive": "0-0-1-0",
        "controlled": "3-1-2-0",
        "pause": "3-2-2-0",
    }

    def extract_all(self, text: str) -> Dict[str, Any]:
        """Extract all entities from text."""
        return {
            "weights": self.extract_weights(text),
            "reps": self.extract_reps(text),
            "sets": self.extract_sets(text),
            "duration": self.extract_duration(text),
            "distance": self.extract_distance(text),
            "rpe": self.extract_rpe(text),
            "heart_rate": self.extract_heart_rate(text),
            "exercises": self.extract_exercises(text),
            "muscles_mentioned": self.extract_muscle_groups(text),
            "tempo": self.extract_tempo(text),
        }

    def extract_weights(self, text: str) -> List[Dict[str, Any]]:
        results = []
        for m in self.WEIGHT_PATTERN.finditer(text):
            val = float(m.group(1))
            unit = m.group(2).lower()
            # Normalize to kg
            if unit.startswith("lb") or unit.startswith("pound"):
                val = val * 0.453592
            results.append({"value": round(val, 1), "unit": "kg", "raw": m.group(0)})
        return results

    def extract_reps(self, text: str) -> List[int]:
        return [int(m.group(1)) for m in self.REPS_PATTERN.finditer(text)]

    def extract_sets(self, text: str) -> List[int]:
        return [int(m.group(1)) for m in self.SETS_PATTERN.finditer(text)]

    def extract_duration(self, text: str) -> List[Dict[str, Any]]:
        results = []
        for m in self.DURATION_PATTERN.finditer(text):
            val = int(m.group(1))
            unit_raw = m.group(0).lower()
            if "hr" in unit_raw or "hour" in unit_raw:
                unit = "hours"
            elif "sec" in unit_raw:
                unit = "seconds"
            else:
                unit = "minutes"
            results.append({"value": val, "unit": unit})
        return results

    def extract_distance(self, text: str) -> List[Dict[str, Any]]:
        results = []
        for m in self.DISTANCE_PATTERN.finditer(text):
            val = float(m.group(1))
            unit_raw = m.group(2).lower()
            if unit_raw.startswith("mi"):
                unit = "miles"
            elif unit_raw.startswith("k"):
                unit = "km"
            elif unit_raw.startswith("m"):
                unit = "meters"
            else:
                unit = "km"
            results.append({"value": val, "unit": unit})
        return results

    def extract_rpe(self, text: str) -> Optional[float]:
        m = self.RPE_PATTERN.search(text)
        return float(m.group(1)) if m else None

    def extract_heart_rate(self, text: str) -> Optional[int]:
        m = self.HEART_RATE_PATTERN.search(text)
        return int(m.group(1)) if m else None

    def extract_exercises(self, text: str) -> List[Dict[str, str]]:
        text_lower = text.lower()
        found = []
        for alias, exercise_id in sorted(
            self.EXERCISE_ALIASES.items(), key=lambda x: -len(x[0])
        ):
            if alias in text_lower:
                found.append({"alias": alias, "exercise_id": exercise_id})
        return found

    def extract_muscle_groups(self, text: str) -> List[str]:
        text_lower = text.lower()
        found = []
        for muscle, patterns in self.MUSCLE_GROUP_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, text_lower):
                    if muscle not in found:
                        found.append(muscle)
                    break
        return found

    def extract_tempo(self, text: str) -> Optional[str]:
        m = self.TEMPO_PATTERN.search(text)
        if m:
            return m.group(0)
        text_lower = text.lower()
        for keyword, tempo in self.TEMPO_MAP.items():
            if keyword in text_lower:
                return tempo
        return None


intent_classifier = IntentClassifier()
entity_extractor = EntityExtractor()

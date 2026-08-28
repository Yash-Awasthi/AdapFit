"""
AdapFit Voice Workout Logger
Speech-to-text → NL parser → structured workout data.
Supports real-time transcription with incremental parsing.
"""
import re
from typing import Dict, List, Any, Optional
from app.services.nl_workout_logger import nl_workout_logger
from app.services.intent_classifier import entity_extractor


# Common speech-to-text corrections for fitness context
SPEECH_CORRECTIONS = {
    # Exercise name corrections
    "bench press": "bench press",
    "bench preload": "bench press",
    "bed press": "bench press",
    "bent preload": "bent over row",
    "dead lift": "deadlift",
    "deadlip": "deadlift",
    "front squat": "front squat",
    "frost squat": "front squat",
    "goblet squat": "goblet squat",
    "oblique squat": "goblet squat",
    "overhead press": "overhead press",
    "overhead preload": "overhead press",
    "ohp": "ohp",
    "pull up": "pull up",
    "pull ups": "pull ups",
    "pull-up": "pull up",
    "chin up": "chin up",
    "chin ups": "chin ups",
    "barbell row": "barbell row",
    "barrel row": "barbell row",
    "lat pull down": "lat pulldown",
    "lat pulldown": "lat pulldown",
    "latte pull down": "lat pulldown",
    "lateral raise": "lateral raise",
    "ladle raise": "lateral raise",
    "bicep curl": "bicep curl",
    "by sub curl": "bicep curl",
    "tricep push down": "tricep pushdown",
    "tricep dip": "dips",
    "cable fly": "cable fly",
    "table fly": "cable fly",
    "hip thrust": "hip thrust",
    "high trust": "hip thrust",
    "leg press": "leg press",
    "leg extension": "leg extension",
    "leg curl": "leg curl",
    "calf raise": "calf raise",
    "calf raiser": "calf raise",
    "face pull": "face pull",
    "face Paul": "face pull",
    "shrug": "shrugs",
    "Russian twist": "russian twist",
    "russian list": "russian twist",
    "plank": "plank",
    "blank": "plank",
    "push up": "push ups",
    "push ups": "push ups",
    "pushups": "push ups",
    "sit up": "sit ups",
    "sit ups": "sit ups",

    # Unit corrections
    "kgs": "kg",
    "kay gee": "kg",
    "pounds": "lbs",
    "reps": "reps",
    "rep": "reps",
    "sets": "sets",
    "set": "sets",
    "minutes": "min",
    "mins": "min",

    # Common number confusions
    "twenty": "20",
    "thirty": "30",
    "forty": "40",
    "fifty": "50",
    "sixty": "60",
    "seventy": "70",
    "eighty": "80",
    "ninety": "90",
    "hundred": "100",
    "one twenty": "120",
    "one thirty": "130",
    "one fifty": "150",
}

# Number word to digit mapping
NUMBER_WORDS = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "eleven": "11", "twelve": "12", "thirteen": "13", "fourteen": "14",
    "fifteen": "15", "sixteen": "16", "seventeen": "17", "eighteen": "18",
    "nineteen": "19", "twenty": "20", "twenty five": "25",
    "thirty": "30", "thirty five": "35", "forty": "40", "forty five": "45",
    "fifty": "50", "sixty": "60", "seventy": "70", "eighty": "80",
    "ninety": "90", "one hundred": "100", "one hundred ten": "110",
    "one twenty": "120", "one thirty": "130", "one forty": "140",
    "one fifty": "150", "two hundred": "200",
}


class VoiceWorkoutLogger:
    """
    Processes voice input for workout logging.
    Handles speech-to-text normalization, exercise name correction,
    and integrates with the NL parser for structured output.
    """

    def __init__(self):
        self._corrections = SPEECH_CORRECTIONS
        self._number_words = NUMBER_WORDS

    def normalize_transcript(self, raw_transcript: str) -> str:
        """
        Clean and normalize a speech-to-text transcript
        for workout context.
        """
        text = raw_transcript.strip()

        # Lowercase for matching but preserve some structure
        text_lower = text.lower()

        # Apply number word corrections (longest match first)
        for word, digit in sorted(self._number_words.items(), key=lambda x: -len(x[0])):
            text_lower = text_lower.replace(word, digit)

        # Apply speech corrections
        for wrong, correct in sorted(self._corrections.items(), key=lambda x: -len(x[0])):
            text_lower = text_lower.replace(wrong, correct)

        # Fix common patterns
        # "three by ten" → "3x10"
        text_lower = re.sub(r'(\d+)\s*by\s*(\d+)', r'\1x\2', text_lower)

        # "sets of" → just spaces
        text_lower = re.sub(r'(\d+)\s+sets?\s+of\s+(\d+)', r'\1x\2', text_lower)

        # "times" as multiplication
        text_lower = re.sub(r'(\d+)\s*times\s*(\d+)', r'\1x\2', text_lower)

        # Clean up extra spaces
        text_lower = re.sub(r'\s+', ' ', text_lower).strip()

        return text_lower

    def parse_voice_input(
        self, transcript: str, confidence: float = 0.0
    ) -> Dict[str, Any]:
        """
        Process a voice transcript into structured workout data.
        Returns parsed data with voice-specific metadata.
        """
        normalized = self.normalize_transcript(transcript)

        # Parse using the NL workout logger
        parsed = nl_workout_logger.parse(normalized)

        # Voice-specific quality checks
        quality_issues = self._check_quality(transcript, normalized, parsed)

        # Estimate transcription accuracy
        accuracy_estimate = self._estimate_accuracy(transcript, normalized, parsed)

        return {
            "raw_transcript": transcript,
            "normalized": normalized,
            "parsed": {
                "exercises": parsed["exercises"],
                "cardio": parsed["cardio"],
                "duration_minutes": parsed["duration_minutes"],
                "global_rpe": parsed["global_rpe"],
                "total_sets": parsed["total_sets"],
                "total_reps": parsed["total_reps"],
                "total_volume_kg": parsed["total_volume_kg"],
            },
            "parse_confidence": parsed["parse_confidence"],
            "voice_confidence": confidence,
            "accuracy_estimate": accuracy_estimate,
            "quality_issues": quality_issues,
            "needs_confirmation": parsed["parse_confidence"] < 0.7 or accuracy_estimate < 0.6,
        }

    def process_incremental(self, partial_transcript: str) -> Dict[str, Any]:
        """
        Process a partial/incremental transcript during live recording.
        Returns current parse state and what's still ambiguous.
        """
        normalized = self.normalize_transcript(partial_transcript)
        entities = entity_extractor.extract_all(normalized)

        # What do we know so far?
        known = {}
        ambiguous = []

        if entities["exercises"]:
            known["exercises"] = entities["exercises"]
        else:
            ambiguous.append("exercise_name")

        if entities["sets"]:
            known["sets"] = entities["sets"]
        else:
            ambiguous.append("sets")

        if entities["reps"]:
            known["reps"] = entities["reps"]
        else:
            ambiguous.append("reps")

        if entities["weights"]:
            known["weights"] = entities["weights"]
        else:
            ambiguous.append("weight")

        if entities["rpe"]:
            known["rpe"] = entities["rpe"]

        return {
            "normalized": normalized,
            "known": known,
            "ambiguous": ambiguous,
            "completeness": len(known) / 4,  # 4 core fields
        }

    def generate_voice_prompts(self, partial_parse: Dict) -> List[str]:
        """
        Generate follow-up voice prompts to fill in missing data.
        E.g., "How many sets?" or "What weight?"
        """
        prompts = []
        ambiguous = partial_parse.get("ambiguous", [])

        if "exercise_name" in ambiguous:
            prompts.append("What exercise did you do?")
        if "sets" in ambiguous and "reps" in ambiguous:
            prompts.append("How many sets and reps?")
        elif "sets" in ambiguous:
            prompts.append("How many sets?")
        elif "reps" in ambiguous:
            prompts.append("How many reps?")
        if "weight" in ambiguous:
            prompts.append("What weight did you use?")

        return prompts[:3]

    def format_confirmation(self, parsed_data: Dict) -> str:
        """Format parsed data as a spoken confirmation message."""
        exercises = parsed_data.get("exercises", [])
        if not exercises:
            return "I didn't catch any exercises. Could you repeat that?"

        parts = []
        for ex in exercises[:4]:
            desc = f"{ex['sets']} sets of {ex['reps']} {ex['name']}"
            if ex.get("weight_kg", 0) > 0:
                desc += f" at {ex['weight_kg']} kilograms"
            if ex.get("rpe"):
                desc += f", RPE {ex['rpe']}"
            parts.append(desc)

        total_vol = parsed_data.get("total_volume_kg", 0)
        rpe = parsed_data.get("global_rpe")
        cardio = parsed_data.get("cardio", [])

        confirmation = "Got it! " + ". ".join(parts) + "."
        if total_vol > 0:
            confirmation += f" Total volume: {total_vol:.0f} kilograms."
        if rpe:
            confirmation += f" RPE {rpe}."
        if cardio:
            for c in cardio[:2]:
                if c.get("distance"):
                    confirmation += f" {c['distance']} {c.get('distance_unit', 'km')} {c.get('activity', 'cardio')}."
                elif c.get("duration_minutes"):
                    confirmation += f" {c['duration_minutes']} minutes of {c.get('activity', 'cardio')}."

        confirmation += " Want me to log this?"
        return confirmation

    def _check_quality(
        self, raw: str, normalized: str, parsed: Dict
    ) -> List[str]:
        """Check transcript quality and flag issues."""
        issues = []

        if len(raw.strip()) < 5:
            issues.append("Transcript too short")

        if parsed["parse_confidence"] < 0.3:
            issues.append("Low parse confidence — could not identify exercises")

        if parsed["parse_confidence"] < 0.6 and parsed["parse_confidence"] >= 0.3:
            issues.append("Partial parse — some details may be missing")

        # Check for likely misheard numbers
        numbers_in_raw = re.findall(r'\b\d+\b', raw)
        numbers_in_norm = re.findall(r'\b\d+\b', normalized)
        if len(numbers_in_raw) != len(numbers_in_norm):
            issues.append("Some numbers may have been corrected from speech recognition")

        # Check for very high weights (likely misheard)
        for ex in parsed.get("exercises", []):
            if ex.get("weight_kg", 0) > 300:
                issues.append(f"Very high weight detected ({ex['weight_kg']}kg) — please verify")

        return issues

    def _estimate_accuracy(
        self, raw: str, normalized: str, parsed: Dict
    ) -> float:
        """Estimate transcription accuracy based on heuristics."""
        score = 0.5  # base

        # More exercises found = likely more accurate
        if parsed.get("exercises"):
            score += 0.2

        # If parse confidence is high
        if parsed["parse_confidence"] >= 0.7:
            score += 0.15

        # Corrections were applied (might indicate lower raw accuracy)
        corrections = sum(1 for k in self._corrections if k in raw.lower())
        if corrections == 0:
            score += 0.1  # no corrections needed = likely cleaner audio

        return min(1.0, round(score, 2))

    def get_status(self) -> Dict[str, Any]:
        return {
            "correction_rules": len(self._corrections),
            "number_words": len(self._number_words),
            "supported_exercises": len(entity_extractor.EXERCISE_ALIASES),
        }


voice_workout_logger = VoiceWorkoutLogger()

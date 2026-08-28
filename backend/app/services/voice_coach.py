"""AI Voice Coach — real-time audio coaching during workouts.

Generates contextual voice cues based on:
- Workout phase (warmup, working sets, rest, cooldown)
- Performance data (RPE, tempo, form grade)
- Time-based cues (rest timer countdown, set transitions)
- Motivational cues based on user profile

Uses TTS-ready text generation (actual TTS is handled by mobile expo-speech).
"""

from __future__ import annotations
import random
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class CueType(str, Enum):
    ENCOURAGEMENT = "encouragement"
    FORM_CORRECTION = "form_correction"
    REST_REMINDER = "rest_reminder"
    SET_START = "set_start"
    SET_COMPLETE = "set_complete"
    EXERCISE_TRANSITION = "exercise_transition"
    TEMPO_CUE = "tempo_cue"
    SAFETY_ALERT = "safety_alert"
    PROGRESS_UPDATE = "progress_update"
    WORKOUT_COMPLETE = "workout_complete"


@dataclass
class VoiceCue:
    cue_type: CueType
    text: str
    priority: int  # 1 = low, 5 = critical
    timestamp_seconds: float = 0
    tts_config: dict = None

    def __post_init__(self):
        if self.tts_config is None:
            self.tts_config = {"rate": 1.0, "pitch": 1.0}


# Cue templates organized by context
ENCOURAGEMENT_CUES = [
    "Great form! Keep pushing!",
    "You've got this! Stay strong!",
    "Perfect rep! Let's keep going!",
    "Nice work! One more set to go!",
    "That's the way! Consistent power!",
    "Excellent depth! Feel the burn!",
    "Strong performance! Your body is adapting!",
    "Beautiful technique! You're getting stronger!",
]

FORM_CORRECTION_CUES = {
    "elbow_flare": "Tuck your elbows in. Protect those shoulders.",
    "rounded_back": "Brace your core! Keep that spine neutral.",
    "knee_cave": "Push your knees out. Track over your toes.",
    "insufficient_depth": "Go deeper! Range of motion matters.",
    "too_fast": "Slow it down. Control the negative.",
    "forward_lean": "Chest up! Drive through your heels.",
    "swinging": "Stay strict. No momentum.",
    "sagging_hips": "Engage your core! Straight body line.",
}

REST_CUES = [
    "Rest now. Take deep breaths.",
    "Good set! Rest for {seconds} seconds.",
    "Recover. Hydrate. Next set coming up.",
    "Breathe in through your nose, out through your mouth.",
    "Shake it out. {seconds} seconds until next set.",
]

SET_START_CUES = [
    "Set {set_number} of {total_sets}. Let's go!",
    "Ready? Set {set_number}. Focus on form.",
    "Here we go — set {set_number}. {target_reps} reps at {weight}.",
    "Time to work! Set {set_number}. Give it everything.",
]

SAFETY_CUES = {
    "high_rpe": "That looked heavy! Consider reducing weight if form breaks down.",
    "fatigue_detected": "I'm seeing fatigue in your movement. Maybe drop the weight a bit.",
    "heart_rate_high": "Your heart rate is elevated. Take an extra 30 seconds.",
    "pain_reported": "Stop the exercise. Let's find a safer alternative.",
}

TEMPO_CUES = {
    "slow_down": "Slow... 2... 3... control the weight.",
    "explode": "Drive it up! Explode through the concentric!",
    "pause": "Pause at the top! Hold it!",
    "stretch": "Feel the stretch at the bottom. Full range.",
}


class VoiceCoach:
    """Generates contextual voice cues for workout coaching."""

    def __init__(self):
        self.cue_history: list[VoiceCue] = []
        self.user_preferences: dict = {}
        self._motivation_level = 0.5  # 0 = chill, 1 = intense

    def set_user_preference(self, style: str = "balanced"):
        """Set coaching style: chill, balanced, intense."""
        styles = {
            "chill": 0.2,
            "balanced": 0.5,
            "intense": 0.8,
            "military": 1.0,
        }
        self._motivation_level = styles.get(style, 0.5)

    def get_encouragement(self) -> VoiceCue:
        if self._motivation_level > 0.7:
            text = random.choice([
                "PUSH IT! You're not done yet!",
                "COME ON! Maximum effort right now!",
                "NO LIMITS! Give me everything!",
                "CRUSH IT! This is where champions are made!",
            ])
        elif self._motivation_level > 0.3:
            text = random.choice(ENCOURAGEMENT_CUES)
        else:
            text = random.choice([
                "Nice work. Steady progress.",
                "Good rhythm. Keep it up.",
                "That's it. Consistent effort.",
            ])
        return VoiceCue(cue_type=CueType.ENCOURAGEMENT, text=text, priority=2)

    def get_form_correction(self, fault: str) -> VoiceCue:
        text = FORM_CORRECTION_CUES.get(fault, "Watch your form on this rep.")
        return VoiceCue(cue_type=CueType.FORM_CORRECTION, text=text, priority=4)

    def get_rest_cue(self, seconds: int, set_number: int = 0, total_sets: int = 0) -> VoiceCue:
        if set_number > 0 and total_sets > 0:
            remaining = total_sets - set_number
            text = f"Rest now. {remaining} {'set' if remaining == 1 else 'sets'} remaining. {seconds} seconds."
        else:
            text = random.choice(REST_CUES).replace("{seconds}", str(seconds))
        return VoiceCue(cue_type=CueType.REST_REMINDER, text=text, priority=2)

    def get_set_start_cue(
        self, set_number: int, total_sets: int,
        target_reps: str = "", weight: str = "",
    ) -> VoiceCue:
        template = random.choice(SET_START_CUES)
        text = template.format(
            set_number=set_number, total_sets=total_sets,
            target_reps=target_reps, weight=weight,
        )
        return VoiceCue(cue_type=CueType.SET_START, text=text, priority=3)

    def get_set_complete_cue(self, set_number: int, total_sets: int, form_grade: str = "") -> VoiceCue:
        if form_grade in ("A", "B"):
            text = f"Set {set_number} done! {form_grade} form. "
        else:
            text = f"Set {set_number} complete. "
        remaining = total_sets - set_number
        if remaining > 0:
            text += f"{remaining} {'set' if remaining == 1 else 'sets'} left."
        else:
            text += "Last set done! Moving on."
        return VoiceCue(cue_type=CueType.SET_COMPLETE, text=text, priority=2)

    def get_exercise_transition(self, current: str, next_exercise: str, rest_seconds: int = 60) -> VoiceCue:
        text = f"Done with {current}! {rest_seconds} seconds rest, then we move to {next_exercise}."
        return VoiceCue(cue_type=CueType.EXERCISE_TRANSITION, text=text, priority=3)

    def get_tempo_cue(self, tempo_type: str) -> VoiceCue:
        text = TEMPO_CUES.get(tempo_type, "Maintain your tempo.")
        return VoiceCue(cue_type=CueType.TEMPO_CUE, text=text, priority=3)

    def get_safety_alert(self, alert_type: str) -> VoiceCue:
        text = SAFETY_CUES.get(alert_type, "Please check your form and safety.")
        return VoiceCue(cue_type=CueType.SAFETY_ALERT, text=text, priority=5)

    def get_progress_update(self, completed: int, total: int) -> VoiceCue:
        pct = completed / total * 100 if total > 0 else 0
        if pct < 25:
            text = f"Getting warmed up! {completed} of {total} exercises done."
        elif pct < 50:
            text = f"Quarter way through! {completed} of {total} done."
        elif pct < 75:
            text = f"Past halfway! {completed} of {total} done. Strong work."
        else:
            text = f"Almost there! {completed} of {total} done. Finish strong!"
        return VoiceCue(cue_type=CueType.PROGRESS_UPDATE, text=text, priority=2)

    def get_workout_complete(self, duration_minutes: int, exercises_done: int) -> VoiceCue:
        if self._motivation_level > 0.7:
            text = f"WORKOUT COMPLETE! {exercises_done} exercises in {duration_minutes} minutes. You're a BEAST!"
        elif self._motivation_level > 0.3:
            text = f"Great workout! {exercises_done} exercises, {duration_minutes} minutes. You should feel proud."
        else:
            text = f"Session complete. {exercises_done} exercises in {duration_minutes} minutes. Good work today."
        return VoiceCue(cue_type=CueType.WORKOUT_COMPLETE, text=text, priority=2)

    def get_countdown_cue(self, seconds_remaining: int) -> Optional[VoiceCue]:
        """Generate countdown cues at specific intervals."""
        if seconds_remaining in (10, 5, 3, 2, 1):
            if seconds_remaining <= 3:
                text = str(seconds_remaining)
            elif seconds_remaining == 5:
                text = "5 seconds! Get ready!"
            else:
                text = "10 seconds. Let's go soon!"
            return VoiceCue(
                cue_type=CueType.REST_REMINDER, text=text,
                priority=3, tts_config={"rate": 1.2 if seconds_remaining <= 3 else 1.0}
            )
        return None

    def get_cue_log(self) -> list[dict]:
        return [
            {"type": c.cue_type.value, "text": c.text, "priority": c.priority}
            for c in self.cue_history[-50:]
        ]


voice_coach = VoiceCoach()

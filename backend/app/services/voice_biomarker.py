"""Voice Biomarker Analysis Service - AI-powered disease detection from voice patterns.

Based on 2025 research (Nature, Medsi AI, Sonaphi):
- Depression detection via speech patterns
- Heart disease risk from voice quality
- Cognitive decline screening
- Respiratory health assessment
- Stress and anxiety detection
- Parkinson's disease early detection
"""

import time
import math
from typing import Dict, List, Optional, Any


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


class VoiceBiomarkerService:
    """AI-powered voice analysis for health biomarker detection."""

    def __init__(self):
        self._sequence = 0
        self.analyses: Dict[str, Dict] = {}
        self.user_baselines: Dict[str, Dict] = {}

    # The acoustic measurements a recording must supply. They previously
    # defaulted to random values, so a request carrying no audio at all came
    # back with a depression, cardiovascular and cognitive-decline screening.
    REQUIRED_FEATURES = (
        "speech_rate", "pitch_variability", "energy", "pause_rate", "articulation",
        "tremor", "breath_support", "spectral", "jitter", "shimmer",
    )

    def analyze_voice(self, user_id: str, audio_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record this sample's acoustic features and how they compare to the
        user's own previous samples.

        It deliberately does not screen for disease. The per-condition risk
        percentages this used to return came from thresholds invented in this
        file, presented beside correlations quoted from published instruments
        the code does not implement. Changes against a personal baseline are
        what the measurements support, and are worth showing on their own.
        """
        missing = [f for f in self.REQUIRED_FEATURES if not _is_number(audio_features.get(f))]
        if missing:
            return {
                "status": "insufficient_data",
                "missing_features": missing,
                "message": (
                    "No acoustic measurements were supplied, so there is nothing to report. "
                    "Record a sample with the voice analyser first."
                ),
            }

        # Counter, not a second-resolution timestamp: two recordings analysed
        # in the same second shared an id and the first was overwritten.
        self._sequence += 1
        analysis_id = f"vb_{user_id}_{int(time.time())}_{self._sequence}"
        features = self._extract_features(audio_features)
        comparison = self._compare_to_baseline(user_id, features)

        analysis = {
            "analysis_id": analysis_id,
            "user_id": user_id,
            "status": "measured",
            "timestamp": time.time(),
            "voice_features": features,
            "duration_seconds": audio_features.get("duration", 30),
            "comparison_to_baseline": comparison,
            "notable_changes": self._notable_changes(comparison),
            "disclaimer": (
                "Acoustic measurements of one recording, compared with your own previous "
                "recordings. They do not screen for any medical condition."
            ),
        }

        self.analyses[analysis_id] = analysis
        self._update_baseline(user_id, features)
        return analysis

    # A feature has to move by more than this against the personal baseline
    # before it is worth pointing out, rather than being ordinary variation.
    NOTABLE_CHANGE = 0.15

    def _notable_changes(self, comparison: Dict[str, Any]) -> List[Dict[str, Any]]:
        if comparison.get("status") != "compared":
            return []
        return [
            {"feature": key, "change": entry["change"], "direction": entry["direction"]}
            for key, entry in comparison["changes"].items()
            if abs(entry["change"]) >= self.NOTABLE_CHANGE
        ]

    def get_feature_history(self, user_id: str, feature: str, limit: int = 30) -> Dict[str, Any]:
        """One acoustic feature across this user's recordings, oldest first."""
        points = [
            {"timestamp": a["timestamp"], "value": a["voice_features"][feature]}
            for a in self.analyses.values()
            if a["user_id"] == user_id
            and a.get("status") == "measured"
            and feature in a.get("voice_features", {})
        ]
        points.sort(key=lambda p: p["timestamp"])
        points = points[-limit:]

        if len(points) < 2:
            return {
                "feature": feature,
                "status": "insufficient_data",
                "data_points": len(points),
                "message": "Need at least two recordings to show a trend.",
            }

        latest, previous = points[-1]["value"], points[-2]["value"]
        change = latest - previous
        return {
            "feature": feature,
            "status": "ok",
            "data_points": len(points),
            "latest": round(latest, 3),
            "change": round(change, 3),
            "direction": "increased" if change > 0 else "decreased" if change < 0 else "unchanged",
            "average": round(sum(p["value"] for p in points) / len(points), 3),
            "history": points,
        }

    def get_voice_exercises(self, target: str) -> List[Dict]:
        """Get voice exercises to improve specific biomarkers."""
        exercises = {
            "depression": [
                {"name": "Humming Meditation", "duration": "5 min", "description": "Hum at comfortable pitch for 30s, rest 10s. Repeat 10x.", "benefit": "Increases vocal energy and pitch variability"},
                {"name": "Emotional Reading", "duration": "10 min", "description": "Read a passage expressing different emotions (joy, sadness, anger).", "benefit": "Expands emotional vocal range"},
                {"name": "Singing Practice", "duration": "15 min", "description": "Sing along to uplifting songs, focusing on projection.", "benefit": "Boosts energy, increases speech rate"},
            ],
            "cognitive_decline": [
                {"name": "Word Association Sprint", "duration": "5 min", "description": "Name as many items in a category in 60s. Repeat with different categories.", "benefit": "Improves word-finding speed"},
                {"name": "Story Retelling", "duration": "10 min", "description": "Read a short story, then retell it from memory in your own words.", "benefit": "Enhances semantic coherence and working memory"},
                {"name": "Complex Sentence Practice", "duration": "10 min", "description": "Construct and speak increasingly complex sentences.", "benefit": "Improves executive function and language complexity"},
            ],
            "respiratory": [
                {"name": "Sustained Phonation", "duration": "5 min", "description": "Say 'ah' for as long as possible. Rest 30s between attempts.", "benefit": "Increases breath support and phonation time"},
                {"name": "Pursed Lip Speaking", "duration": "10 min", "description": "Speak while maintaining pursed lip position for controlled exhale.", "benefit": "Improves expiratory control"},
                {"name": "Diaphragmatic Breathing + Speech", "duration": "10 min", "description": "Practice deep belly breathing, then speak a paragraph using diaphragmatic support.", "benefit": "Strengthens breath support for speech"},
            ],
        }

        return exercises.get(target, exercises["depression"])

    def _extract_features(self, audio_features: Dict[str, Any]) -> Dict[str, float]:
        """Name the supplied measurements consistently. Callers check them first."""
        return {
            "speech_rate": float(audio_features["speech_rate"]),
            "pitch_variability": float(audio_features["pitch_variability"]),
            "energy_level": float(audio_features["energy"]),
            "pause_frequency": float(audio_features["pause_rate"]),
            "articulation_rate": float(audio_features["articulation"]),
            "voice_tremor": float(audio_features["tremor"]),
            "breath_support": float(audio_features["breath_support"]),
            "spectral_centroid": float(audio_features["spectral"]),
            "jitter": float(audio_features["jitter"]),
            "shimmer": float(audio_features["shimmer"]),
        }

    def _compare_to_baseline(self, user_id: str, features: Dict[str, float]) -> Dict[str, Any]:
        baseline = self.user_baselines.get(user_id)
        if not baseline:
            return {"status": "no_baseline", "message": "First analysis - baseline being established"}

        changes = {}
        for key in features:
            if key in baseline:
                diff = features[key] - baseline[key]
                changes[key] = {"change": round(diff, 3), "direction": "increased" if diff > 0 else "decreased"}

        return {"status": "compared", "changes": changes}

    def _update_baseline(self, user_id: str, features: Dict[str, float]):
        if user_id not in self.user_baselines:
            self.user_baselines[user_id] = features.copy()
        else:
            for key in features:
                self.user_baselines[user_id][key] = (
                    self.user_baselines[user_id][key] * 0.7 + features[key] * 0.3
                )


from app.core.durable import shared  # noqa: E402

voice_biomarker_service = shared("app.services.voice_biomarker.voice_biomarker_service", VoiceBiomarkerService())
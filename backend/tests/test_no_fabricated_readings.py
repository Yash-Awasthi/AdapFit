"""
Services that report health data report what was measured, or nothing.

Each service here used to fill in its own inputs with random values, so a
request carrying no measurements still produced a confident result — a night
of "frequent breathing pauses", a voice screening
for depression. The rule these tests hold is the same one the health bridge
in the mobile app already follows: never return a fabricated reading.
"""
import pytest

from app.services.sleep_audio_analyzer import SleepAudioAnalyzerService
from app.services.voice_biomarker import VoiceBiomarkerService

FEATURES = {
    "speech_rate": 0.5, "pitch_variability": 0.5, "energy": 0.5, "pause_rate": 0.5,
    "articulation": 0.5, "tremor": 0.1, "breath_support": 0.6, "spectral": 0.5,
    "jitter": 0.1, "shimmer": 0.1,
}


class TestVoiceAnalysis:
    def test_no_audio_features_gives_no_analysis(self):
        result = VoiceBiomarkerService().analyze_voice("u", {})
        assert result["status"] == "insufficient_data"
        assert "voice_features" not in result

    def test_partial_features_are_refused(self):
        result = VoiceBiomarkerService().analyze_voice("u", {"speech_rate": 0.5})
        assert result["status"] == "insufficient_data"
        assert "speech_rate" not in result["missing_features"]

    def test_supplied_features_are_reported_unchanged(self):
        result = VoiceBiomarkerService().analyze_voice("u", {**FEATURES, "energy": 0.77})
        assert result["status"] == "measured"
        assert result["voice_features"]["energy_level"] == pytest.approx(0.77)

    def test_no_disease_screening_is_produced(self):
        """Risk percentages per condition came from thresholds invented in the file."""
        result = VoiceBiomarkerService().analyze_voice("u", FEATURES)
        assert "disease_screenings" not in result
        assert "do not screen" in result["disclaimer"]

    def test_the_second_recording_is_compared_with_the_first(self):
        service = VoiceBiomarkerService()
        assert service.analyze_voice("u", FEATURES)["comparison_to_baseline"]["status"] == "no_baseline"
        second = service.analyze_voice("u", {**FEATURES, "tremor": 0.9})
        assert second["comparison_to_baseline"]["status"] == "compared"
        assert any(c["feature"] == "voice_tremor" for c in second["notable_changes"])

    def test_a_feature_trend_needs_two_recordings(self):
        service = VoiceBiomarkerService()
        service.analyze_voice("u", FEATURES)
        assert service.get_feature_history("u", "voice_tremor")["status"] == "insufficient_data"
        service.analyze_voice("u", {**FEATURES, "tremor": 0.4})
        trend = service.get_feature_history("u", "voice_tremor")
        assert trend["status"] == "ok"
        assert trend["direction"] == "increased"


class TestSleepAudio:
    def test_a_night_with_no_detected_events_is_not_scored(self):
        result = SleepAudioAnalyzerService().analyze_night_audio("u", {"duration_minutes": 480})
        assert result["status"] == "insufficient_data"
        assert "apnea_risk" not in result

    def test_a_night_with_no_duration_is_not_scored(self):
        result = SleepAudioAnalyzerService().analyze_night_audio("u", {"snoring_events": []})
        assert result["status"] == "insufficient_data"

    def test_a_reported_quiet_night_scores_as_quiet(self):
        """An empty list is a measurement: nothing was detected."""
        result = SleepAudioAnalyzerService().analyze_night_audio("u", {
            "duration_minutes": 480, "snoring_events": [], "breathing_pauses": [],
        })
        assert result["status"] == "scored"
        assert result["snoring"]["severity"] == "none"
        assert result["apnea_risk"]["risk_level"] == "low"

    def test_the_score_follows_the_events_reported(self):
        service = SleepAudioAnalyzerService()
        result = service.analyze_night_audio("u", {
            "duration_minutes": 480,
            "snoring_events": [{"start_minute": i, "duration_min": 2} for i in range(20)],
            "breathing_pauses": [{"start_minute": i, "duration_seconds": 20, "gasping": True} for i in range(8)],
        })
        assert result["apnea_risk"]["risk_level"] == "high"
        assert "Gasping during sleep" in result["apnea_risk"]["risk_factors"]

    def test_the_same_night_always_scores_the_same(self):
        service = SleepAudioAnalyzerService()
        night = {"duration_minutes": 480, "snoring_events": [{"start_minute": 4, "duration_min": 1}]}
        first = service.analyze_night_audio("u", night)
        second = service.analyze_night_audio("u", night)
        assert first["sleep_quality_score"] == second["sleep_quality_score"]
        assert first["apnea_risk"] == second["apnea_risk"]

    def test_an_unmeasured_noise_floor_stays_absent(self):
        result = SleepAudioAnalyzerService().analyze_night_audio("u", {
            "duration_minutes": 480, "noise_events": [],
        })
        assert result["environment"]["avg_noise_db"] is None

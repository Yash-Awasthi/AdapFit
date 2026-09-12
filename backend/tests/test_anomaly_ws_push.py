"""
Tests for the anomaly detection → WebSocket alert push integration.

Verifies that when an anomaly is detected via the /detect endpoint,
ws_manager.push_alert() is called with the correct parameters.

The src.anomaly.detector module is stubbed so no real detector is needed.
"""
import asyncio
import sys
import types
from unittest.mock import patch, AsyncMock, MagicMock

# ── Stub the src.anomaly.detector module ───────────────────────────────────
# The real module lives outside backend/app and may not be importable in the
# test environment. The endpoint imports it lazily inside the function body.
_fake_src = types.ModuleType("src")
_fake_anomaly = types.ModuleType("src.anomaly")
_fake_detector = types.ModuleType("src.anomaly.detector")
_fake_detector.HealthAnomalyDetector = MagicMock
_fake_detector.MetricType = MagicMock
_fake_src.anomaly = _fake_anomaly
_fake_anomaly.detector = _fake_detector
sys.modules["src"] = _fake_src
sys.modules["src.anomaly"] = _fake_anomaly
sys.modules["src.anomaly.detector"] = _fake_detector


class FakeWebSocket:
    def __init__(self):
        self.sent = []
        self.closed = False

    async def accept(self):
        pass

    async def send_text(self, text):
        self.sent.append(text)

    async def close(self, code=1000, reason=""):
        self.closed = True


def test_anomaly_detect_pushes_ws_alert_for_high_heart_rate():
    """When an anomaly is detected, push_alert should be called."""
    from app.api.v1.endpoints.anomaly_detection_api import detect_anomaly, AnomalyDetectRequest

    req = AnomalyDetectRequest(metric="heart_rate", current_value=250.0)
    user = {"id": "test-user-123"}

    with patch("app.api.v1.endpoints.anomaly_detection_api.ws_manager") as mock_ws:
        mock_ws.push_alert = AsyncMock()
        # The detector's real behavior depends on src.anomaly.detector;
        # we just need to verify push_alert is called if anomaly is truthy.
        # If no anomaly is detected (value within range), push_alert is NOT called.
        # We mock the detector to force an anomaly.
        with patch("app.api.v1.endpoints.anomaly_detection_api._get_detector") as mock_det:
            mock_detector = MagicMock()
            fake_anomaly = MagicMock()
            fake_anomaly.severity.value = "critical"
            fake_anomaly.message = "Heart rate critically high"
            fake_anomaly.expected_range = (50, 120)
            mock_detector.detect.return_value = fake_anomaly
            mock_det.return_value = mock_detector

            asyncio.run(detect_anomaly(req, user))

            mock_ws.push_alert.assert_called_once()
            call_kwargs = mock_ws.push_alert.call_args
            assert call_kwargs.kwargs["user_id"] == "test-user-123"
            assert call_kwargs.kwargs["alert_type"] == "health_anomaly"
            assert "Heart rate" in call_kwargs.kwargs["message"]
            assert call_kwargs.kwargs["severity"] == "critical"


def test_anomaly_detect_does_not_push_when_no_anomaly():
    """When no anomaly is detected, push_alert should NOT be called."""
    from app.api.v1.endpoints.anomaly_detection_api import detect_anomaly, AnomalyDetectRequest

    req = AnomalyDetectRequest(metric="heart_rate", current_value=72.0)
    user = {"id": "test-user-456"}

    with patch("app.api.v1.endpoints.anomaly_detection_api.ws_manager") as mock_ws:
        mock_ws.push_alert = AsyncMock()
        with patch("app.api.v1.endpoints.anomaly_detection_api._get_detector") as mock_det:
            mock_detector = MagicMock()
            mock_detector.detect.return_value = None  # No anomaly
            mock_det.return_value = mock_detector

            asyncio.run(detect_anomaly(req, user))

            mock_ws.push_alert.assert_not_called()


def test_emergency_check_pushes_critical_alert():
    """Emergency check should push critical-severity alerts."""
    from app.api.v1.endpoints.anomaly_detection_api import check_emergencies, EmergencyCheckRequest

    req = EmergencyCheckRequest(metrics={"heart_rate": 300.0, "spo2": 70.0})
    user = {"id": "emergency-user"}

    with patch("app.api.v1.endpoints.anomaly_detection_api.ws_manager") as mock_ws:
        mock_ws.push_alert = AsyncMock()
        with patch("app.api.v1.endpoints.anomaly_detection_api._get_detector") as mock_det:
            mock_detector = MagicMock()
            e1 = MagicMock()
            e1.metric.value = "heart_rate"
            e1.severity.value = "critical"
            e1.message = "Heart rate emergency"
            e2 = MagicMock()
            e2.metric.value = "spo2"
            e2.severity.value = "critical"
            e2.message = "SpO2 critically low"
            mock_detector.detect_health_emergencies.return_value = [e1, e2]
            mock_det.return_value = mock_detector

            result = asyncio.run(check_emergencies(req, user))

            assert mock_ws.push_alert.call_count == 2
            assert result["emergencies"] == 2
            # Both calls should use critical severity
            for call in mock_ws.push_alert.call_args_list:
                assert call.kwargs["severity"] == "critical"
                assert call.kwargs["alert_type"] == "health_emergency"


def test_batch_detect_pushes_alert_for_each_anomaly():
    """Batch detect should push one alert per anomaly found."""
    from app.api.v1.endpoints.anomaly_detection_api import detect_batch_anomalies, BatchAnomalyRequest

    req = BatchAnomalyRequest(
        metric="heart_rate",
        values=[["2024-01-01T00:00:00", 250], ["2024-01-01T01:00:00", 60], ["2024-01-01T02:00:00", 180]],
    )
    user = {"id": "batch-user"}

    with patch("app.api.v1.endpoints.anomaly_detection_api.ws_manager") as mock_ws:
        mock_ws.push_alert = AsyncMock()
        with patch("app.api.v1.endpoints.anomaly_detection_api._get_detector") as mock_det:
            mock_detector = MagicMock()
            a1 = MagicMock()
            a1.timestamp = MagicMock()
            a1.timestamp.isoformat.return_value = "2024-01-01T00:00:00"
            a1.value = 250.0
            a1.severity.value = "warning"
            a1.message = "Heart rate too high"
            a2 = MagicMock()
            a2.timestamp = MagicMock()
            a2.timestamp.isoformat.return_value = "2024-01-01T02:00:00"
            a2.value = 180.0
            a2.severity.value = "warning"
            a2.message = "Heart rate elevated"
            mock_detector.detect_batch.return_value = [a1, a2]
            mock_det.return_value = mock_detector

            result = asyncio.run(detect_batch_anomalies(req, user))

            assert mock_ws.push_alert.call_count == 2
            assert result["anomalies_found"] == 2

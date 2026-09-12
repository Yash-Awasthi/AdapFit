"""
Tests for the hardened WebSocketManager:
  - push_health_update broadcasts to connected clients
  - sweep_stale closes idle connections
  - connect enforces the per-user connection cap

Uses asyncio.run() directly so no pytest-asyncio plugin is needed
(matching the rest of the ZFIT test suite, which is fully synchronous).
"""
import asyncio
import json


class FakeWebSocket:
    """Minimal async websocket stub for testing the manager."""
    def __init__(self):
        self.sent = []
        self.closed = False
        self.close_code = None

    async def accept(self):
        pass

    async def send_text(self, text):
        self.sent.append(text)

    async def close(self, code=1000, reason=""):
        self.closed = True
        self.close_code = code


def _fresh_manager():
    """Fresh WebSocketManager with a controllable time source."""
    from app.services.websocket_manager import WebSocketManager
    mgr = WebSocketManager()
    mgr._time = type("fake_time", (), {"time": staticmethod(lambda: 1000.0)})()
    return mgr


def test_push_health_update_sends_to_connected_user():
    mgr = _fresh_manager()
    ws = FakeWebSocket()

    async def run():
        await mgr.connect(ws, "user-1")
        await mgr.push_health_update(
            user_id="user-1",
            measurement_type="heart_rate",
            value=72.0,
            source="garmin",
            confidence="high",
        )
    asyncio.run(run())

    # First message is the connected greeting; second is the health update.
    assert len(ws.sent) == 2
    msg = json.loads(ws.sent[1])
    assert msg["type"] == "health_update"
    assert msg["measurement_type"] == "heart_rate"
    assert msg["value"] == 72.0
    assert msg["source"] == "garmin"


def test_push_health_update_noop_when_user_not_connected():
    mgr = _fresh_manager()

    async def run():
        await mgr.push_health_update("nope", "heart_rate", 72.0)
    asyncio.run(run())

    assert mgr.get_status()["total_connections"] == 0


def test_sweep_stale_closes_idle_connections():
    mgr = _fresh_manager()
    ws1 = FakeWebSocket()
    ws2 = FakeWebSocket()

    async def run():
        await mgr.connect(ws1, "user-1")
        await mgr.connect(ws2, "user-1")
        # Advance fake clock so both connections are idle > 120s.
        mgr._time = type("t", (), {"time": staticmethod(lambda: 1000.0 + 200.0)})()
        swept = await mgr.sweep_stale(max_idle_seconds=120)
        return swept
    swept = asyncio.run(run())

    assert swept == 2
    assert ws1.closed and ws2.closed
    assert mgr.get_status()["total_connections"] == 0


def test_sweep_stale_keeps_active_connections():
    mgr = _fresh_manager()
    ws = FakeWebSocket()

    async def run():
        await mgr.connect(ws, "user-1")
        # simulate a recent message (updates _last_seen via send_to_user)
        await mgr.send_to_user("user-1", {"type": "ping"})
        mgr._time = type("t", (), {"time": staticmethod(lambda: 1000.0 + 30.0)})()
        swept = await mgr.sweep_stale(max_idle_seconds=120)
        return swept
    swept = asyncio.run(run())

    assert swept == 0
    assert not ws.closed


def test_connection_cap_evicts_oldest():
    mgr = _fresh_manager()
    # MAX_CONNECTIONS_PER_USER is 5 — opening a 6th should evict the oldest.
    sockets = [FakeWebSocket() for _ in range(6)]

    async def run():
        for ws in sockets:
            await mgr.connect(ws, "user-1")
    asyncio.run(run())

    assert mgr.get_status()["total_connections"] == 5
    # The newest socket survived; one of the earlier ones was evicted.
    assert not sockets[5].closed
    assert sum(1 for s in sockets[:5] if s.closed) == 1

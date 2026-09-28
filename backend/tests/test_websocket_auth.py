"""WebSocket handshake authentication.

WebSocket routes never pass through AuthMiddleware, because
BaseHTTPMiddleware only sees HTTP scope, so each route has to authenticate on
its own. These tests drive every WebSocket route the app exposes and check
that an anonymous handshake is refused, that the user named in the path can
connect, and that another user cannot connect to their socket.

Tokens are only accepted for accounts that exist, so the users here are
registered for real rather than having a token minted for a made-up id.
"""
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.auth import create_access_token
from tests.conftest import register_user
from app.core.config import settings
from app.main import app

c = TestClient(app)

# (path template, whether the path names the connecting user)
WS_ROUTES = [
    ("/ws/bpm/{uid}", True),
    ("/ws/{uid}", True),
    ("/api/v1/chat/ws/{uid}", True),
    ("/api/v1/sensors/ws/{uid}", True),
    ("/api/v1/camera-ws/ws/bpm", False),
    # The declared prefix (/challenges) is applied on top of a route path that
    # already carries /ws/challenges/, so the public URL repeats the segment.
    ("/api/v1/challenges/ws/challenges/demo-challenge", False),
]

_ROUTE_IDS = [row[0] for row in WS_ROUTES]


@pytest.fixture(autouse=True)
def _auth_enforced(monkeypatch):
    """Turn the local development bypass off for these tests.

    A development .env may set AUTH_DISABLED to skip JWT checks locally. That
    flag makes every handshake succeed, so it has to be off before the refusal
    cases below mean anything.
    """
    monkeypatch.setattr(settings, "AUTH_DISABLED", False)


@pytest.fixture(scope="module")
def owner():
    """A registered account, whose id the WebSocket paths name."""
    result = register_user("ws-owner@example.com", "ws-owner")
    return result["user"]["id"]


@pytest.fixture(scope="module")
def stranger():
    result = register_user("ws-stranger@example.com", "ws-stranger")
    return result["user"]["id"]


def _connect(path, token=None):
    """Attempt a handshake; returns the refusal close code, or None when accepted.

    The handshake is entered and left by hand rather than with a `with` block,
    because leaving the block closes the socket from the client side and
    surfaces a normal 1000 close, which would be indistinguishable from a
    refusal.
    """
    if token:
        separator = "&" if "?" in path else "?"
        path = f"{path}{separator}token={token}"
    session = c.websocket_connect(path)
    try:
        session.__enter__()
    except WebSocketDisconnect as exc:
        return exc.code
    except Exception as exc:  # refused in a shape the client surfaces differently
        return type(exc).__name__

    try:
        session.__exit__(None, None, None)
    except Exception:
        pass
    return None


@pytest.mark.parametrize("template,named", WS_ROUTES, ids=_ROUTE_IDS)
def test_anonymous_handshake_is_refused(template, named, owner):
    code = _connect(template.format(uid=owner))
    assert code == 1008, f"anonymous client on {template} closed with {code}, expected 1008"


@pytest.mark.parametrize("template,named", WS_ROUTES, ids=_ROUTE_IDS)
def test_own_token_is_accepted(template, named, owner):
    token = create_access_token(owner)
    code = _connect(template.format(uid=owner), token)
    assert code is None, f"owner refused on {template} with close code {code}"


@pytest.mark.parametrize(
    "template,named",
    [row for row in WS_ROUTES if row[1]],
    ids=[row[0] for row in WS_ROUTES if row[1]],
)
def test_another_users_token_is_refused(template, named, owner, stranger):
    token = create_access_token(stranger)
    code = _connect(template.format(uid=owner), token)
    assert code == 1008, f"{template} let a different user in (close code {code})"


def test_invalid_token_is_refused(owner):
    assert _connect(f"/api/v1/chat/ws/{owner}", "not-a-jwt") == 1008

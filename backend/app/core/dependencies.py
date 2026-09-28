"""
FastAPI Dependencies — Authentication & Authorization

Provides route-level dependencies for protecting endpoints:
- get_current_user: Extract user from Authorization header (optional)
- require_user: Require valid authentication
- require_admin: Require admin role
- require_owner_or_admin: Require resource owner or admin
"""
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from app.core.auth import decode_access_token, user_manager
from app.core.config import settings
from app.middleware.auth import auth_bypass_active


def _extract_bearer_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extract JWT token from Authorization header."""
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None
    return authorization[7:]


async def _decode_user_from_token(token: Optional[str]) -> Optional[dict]:
    """Decode and validate JWT, return user dict or None."""
    if not token:
        return None
    await user_manager._ensure_loaded()
    payload = decode_access_token(token)
    if not payload:
        return None
    return await user_manager.get_user(payload["sub"])


async def _dev_user() -> dict:
    """
    Stand-in for the authenticated user while the dev bypass is on.

    Must carry the same keys as a real record, `id` above all: endpoints index
    `user["id"]` directly and a differently shaped dict turns the bypass into
    a KeyError instead of a 401.
    """
    existing = await user_manager.get_user(settings.DEV_USER_ID)
    if existing:
        return existing
    return {
        "id": settings.DEV_USER_ID,
        "sub": settings.DEV_USER_ID,
        "user_id": settings.DEV_USER_ID,
        "email": f"{settings.DEV_USER_ID}@localhost",
        "auth": "bypass",
    }


async def get_current_user(
    authorization: Optional[str] = Header(None),
) -> Optional[dict]:
    """
    Dependency: Extract authenticated user from request.
    Returns None if not authenticated (does NOT raise).
    Use this when auth is optional (e.g. public endpoints with optional personalization).
    """
    token = _extract_bearer_token(authorization)
    user = await _decode_user_from_token(token)
    if user is None and auth_bypass_active():
        return await _dev_user()
    return user


async def require_user(
    authorization: Optional[str] = Header(None),
) -> dict:
    """
    Dependency: Require valid authentication.
    Raises 401 if not authenticated.
    Use this as the default for any endpoint that needs a logged-in user.
    """
    token = _extract_bearer_token(authorization)
    user = await _decode_user_from_token(token)
    # The middleware bypass does not reach route-level dependencies, so the
    # flag has to be honoured here too for a guarded endpoint to open.
    if not user and auth_bypass_active():
        return await _dev_user()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def require_admin(
    authorization: Optional[str] = Header(None),
) -> dict:
    """
    Dependency: Require admin or superadmin role.
    Raises 401 if not authenticated, 403 if not admin.
    """
    user = await require_user(authorization)
    if user.get("role") not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


def require_owner_or_owner_id(user_id: str):
    """
    Factory: Returns a dependency that checks if the authenticated user
    matches the given user_id or is an admin.

    Usage:
        @router.get("/items/{item_id}")
        async def get_item(item_id: str, user: dict = Depends(require_owner_or_owner_id("me"))):
            ...
    """
    async def _check(authorization: Optional[str] = Header(None)) -> dict:
        user = await require_user(authorization)
        if user["id"] == user_id or user.get("role") in ("admin", "superadmin"):
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: not resource owner",
        )
    return _check


# Default dependency for most endpoints — extracts user_id from query or body
async def get_user_id(
    user_id: Optional[str] = None,
    authorization: Optional[str] = Header(None),
) -> str:
    """
    Extract user_id from query parameter or authenticated token.
    Falls back to 'default' for backward compatibility with unauthenticated endpoints.
    """
    if user_id:
        return user_id
    token = _extract_bearer_token(authorization)
    user = await _decode_user_from_token(token)
    if user:
        return user["id"]
    return "default"


def ensure_owner(caller: dict, user_id: Optional[str]) -> None:
    """
    Raise 403 unless the caller is the named user or an admin.

    Use this for handlers that take the subject's user_id from the path or
    query string. `require_owner_or_owner_id` cannot guard those: its argument
    is evaluated where the dependency is declared, so it only ever compares
    against a fixed literal, not a value that arrives per request.

        async def get_record(user_id: str, caller: dict = Depends(require_user)):
            ensure_owner(caller, user_id)
    """
    # The development bypass stands in as whoever the request names, so
    # comparing ids would refuse everything it exists to allow. The bypass can
    # never be active in production.
    if auth_bypass_active():
        return
    if user_id is None or caller.get("id") == user_id:
        return
    if caller.get("role") in ("admin", "superadmin"):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: not resource owner",
    )


# === WebSocket Authentication ===

# 1008 is the RFC 6455 "policy violation" close code: the handshake was
# understood but refused, which is what a missing or wrong token is.
WS_POLICY_VIOLATION = 1008


async def authenticate_websocket(websocket, expected_user_id: Optional[str] = None) -> Optional[dict]:
    """
    Authenticate a WebSocket handshake and return the caller's user record.

    WebSocket routes never pass through AuthMiddleware, because
    BaseHTTPMiddleware only receives HTTP scope, so every route has to validate
    on its own. Call this before accepting the connection:

        user = await authenticate_websocket(websocket, expected_user_id=user_id)
        if user is None:
            return

    The token is read from the `token` query parameter, falling back to an
    Authorization header when a client can send one. An admin may connect to
    another user's socket; anyone else may only reach their own.
    """
    if auth_bypass_active():
        return await _dev_user()

    token = websocket.query_params.get("token")
    if not token:
        token = _extract_bearer_token(websocket.headers.get("Authorization"))

    user = await _decode_user_from_token(token)
    if user is None:
        await websocket.close(code=WS_POLICY_VIOLATION, reason="Authentication required")
        return None

    if expected_user_id and user["id"] != expected_user_id:
        if user.get("role") not in ("admin", "superadmin"):
            await websocket.close(code=WS_POLICY_VIOLATION, reason="Not the owner of this connection")
            return None

    from app.core import privacy
    from app.core.per_user import CURRENT_USER

    reason = privacy.blocked(user["id"])
    if reason:
        await websocket.close(code=WS_POLICY_VIOLATION, reason=reason)
        return None
    # IdentityMiddleware only sees HTTP, so per-user state and consent checks read the caller from here.
    CURRENT_USER.set(user["id"])
    return user

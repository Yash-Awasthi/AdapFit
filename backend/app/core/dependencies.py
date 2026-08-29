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
from app.core.auth import decode_token, user_manager
from app.core.config import settings
from app.middleware.auth import auth_bypass_active


def _extract_bearer_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extract JWT token from Authorization header."""
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None
    return authorization[7:]


def _decode_user_from_token(token: Optional[str]) -> Optional[dict]:
    """Decode and validate JWT, return user dict or None."""
    if not token:
        return None
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None
    return user_manager.get_user(payload["sub"])


def _dev_user() -> dict:
    """
    Stand-in for the authenticated user while the dev bypass is on.

    Must carry the same keys as a real record, `id` above all: endpoints index
    `user["id"]` directly and a differently shaped dict turns the bypass into
    a KeyError instead of a 401.
    """
    existing = user_manager.get_user(settings.DEV_USER_ID)
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
    user = _decode_user_from_token(token)
    if user is None and auth_bypass_active():
        return _dev_user()
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
    user = _decode_user_from_token(token)
    # The middleware bypass does not reach route-level dependencies, so the
    # flag has to be honoured here too for a guarded endpoint to open.
    if not user and auth_bypass_active():
        return _dev_user()
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
    user = _decode_user_from_token(token)
    if user:
        return user["id"]
    return "default"

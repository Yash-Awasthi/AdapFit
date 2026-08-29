"""
Authentication Middleware

Validates JWT tokens on all /api/v1/* routes.
Public endpoints are explicitly allowlisted.
Injects authenticated user into request.state.user.
"""
import time
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.auth import decode_token
from app.core.config import settings


def auth_bypass_active() -> bool:
    """
    True when JWT validation is switched off for local development.

    Production never honours the flag: an open API is only ever a local
    convenience, and a stray AUTH_DISABLED in a deployed environment would
    otherwise expose every user's records.
    """
    return settings.AUTH_DISABLED and settings.ENVIRONMENT.lower() != "production"


# Public endpoints that don't require authentication
# These are the only endpoints accessible without a valid JWT
PUBLIC_ENDPOINTS = {
    # Auth
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/api/v1/auth-v2/login",
    "/api/v1/auth-v2/register",
    "/api/v1/auth-v2/refresh",
    # User signup (no token exists yet at account creation)
    "/api/v1/users",
    # Health checks
    "/",
    "/health",
    "/ready",
    # API docs
    "/docs",
    "/openapi.json",
    "/redoc",
    # Static files
    "/static",
    "/admin",
    # WebSocket (handled separately)
    "/ws",
    # Metrics
    "/metrics",
}

# Public path prefixes (endpoints starting with these are public)
PUBLIC_PREFIXES = (
    "/docs",
    "/openapi",
    "/redoc",
    "/static",
    "/admin",
    "/ws/",
)


def is_public_endpoint(path: str) -> bool:
    """Check if an endpoint is public (doesn't require auth)."""
    # Exact match
    if path in PUBLIC_ENDPOINTS:
        return True
    # Prefix match
    for prefix in PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that validates JWT on all /api/v1/* routes.
    
    - Extracts Bearer token from Authorization header
    - Validates JWT and decodes user payload
    - Injects user into request.state.user
    - Returns 401 for missing/invalid tokens on protected routes
    - Skips public endpoints (login, register, docs, etc.)
    """
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Only apply to API routes
        if not path.startswith("/api/v1/"):
            return await call_next(request)
        
        # Skip public endpoints
        if is_public_endpoint(path):
            return await call_next(request)

        if auth_bypass_active():
            request.state.user = {"sub": settings.DEV_USER_ID, "auth": "bypass"}
            request.state.user_id = settings.DEV_USER_ID
            return await call_next(request)

        # Extract Authorization header
        auth_header = request.headers.get("Authorization", "")
        
        if not auth_header.startswith("Bearer "):
            return Response(
                content='{"detail":"Missing or invalid Authorization header. Use: Bearer <token>"}',
                status_code=401,
                media_type="application/json",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        # Decode and validate JWT
        payload = decode_token(token)
        
        if payload is None:
            return Response(
                content='{"detail":"Invalid or expired token"}',
                status_code=401,
                media_type="application/json",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Inject user into request state
        request.state.user = payload
        request.state.user_id = payload.get("sub", "")
        
        # Continue to endpoint
        response = await call_next(request)
        return response

"""
Security Middleware — CSP headers, input sanitization, request logging, IP blocking

Features:
- Content Security Policy headers
- X-Frame-Options, X-Content-Type-Options, X-XSS-Protection
- Input sanitization (strip HTML, validate email)
- Request logging with timing
- IP blocking for abuse
"""
import time
import re
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


# IP blocklist (in production, use Redis)
blocked_ips: set[str] = set()

# Rate limit tracking
request_counts: dict[str, list[float]] = {}

# Suspicious patterns
SUSPICIOUS_PATTERNS = [
    re.compile(r"<script", re.IGNORECASE),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"<iframe", re.IGNORECASE),
    re.compile(r"eval\(", re.IGNORECASE),
    re.compile(r"union\s+select", re.IGNORECASE),
    re.compile(r";\s*drop\s+table", re.IGNORECASE),
    re.compile(r"<img[^>]+onerror", re.IGNORECASE),
]


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable):
        # Check blocked IPs
        client_ip = request.client.host if request.client else "unknown"
        if client_ip in blocked_ips:
            return JSONResponse(status_code=403, content={"error": "Access denied"})

        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(self)"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # CSP header
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' https://fonts.gstatic.com",
            "connect-src 'self' http://localhost:8000",
            "frame-ancestors 'none'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        return response


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Sanitize request inputs and detect suspicious patterns."""

    async def dispatch(self, request: Request, call_next: Callable):
        # Check for suspicious patterns in URL
        url = str(request.url)
        for pattern in SUSPICIOUS_PATTERNS:
            if pattern.search(url):
                return JSONResponse(
                    status_code=400,
                    content={"error": "Suspicious request detected"},
                )

        # Check query parameters
        for key, value in request.query_params.items():
            for pattern in SUSPICIOUS_PATTERNS:
                if pattern.search(value):
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid query parameter"},
                    )

        response = await call_next(request)
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with timing."""

    async def dispatch(self, request: Request, call_next: Callable):
        start = time.time()
        client_ip = request.client.host if request.client else "unknown"

        response = await call_next(request)

        duration = time.time() - start
        # Store in request state for metrics
        if hasattr(request.app.state, "request_log"):
            request.app.state.request_log.append({
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "ip": client_ip,
                "timestamp": time.time(),
            })
            # Keep only last 1000 entries
            if len(request.app.state.request_log) > 1000:
                request.app.state.request_log = request.app.state.request_log[-500:]

        return response


# === Input Validation Helpers ===

def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Strip HTML tags and dangerous characters."""
    if not isinstance(value, str):
        return str(value)
    # Strip HTML tags
    clean = re.sub(r"<[^>]+>", "", value)
    # Strip null bytes
    clean = clean.replace("\x00", "")
    # Truncate
    return clean[:max_length].strip()


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_username(username: str) -> dict:
    """Validate username format."""
    errors = []
    if len(username) < 3:
        errors.append("Username must be at least 3 characters")
    if len(username) > 50:
        errors.append("Username must be at most 50 characters")
    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        errors.append("Username can only contain letters, numbers, underscores, and hyphens")
    return {"valid": len(errors) == 0, "errors": errors}


# === API Key Authentication ===

def validate_api_key(api_key: str) -> dict:
    """Validate API key from header."""
    from app.core.auth import api_key_manager
    return api_key_manager.validate_key(api_key)


def block_ip(ip: str) -> None:
    """Block an IP address."""
    blocked_ips.add(ip)


def unblock_ip(ip: str) -> None:
    """Unblock an IP address."""
    blocked_ips.discard(ip)

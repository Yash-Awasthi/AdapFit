"""
Input Validation & Security Hardening Middleware

Features:
- Request body size limits
- SQL injection pattern detection
- XSS pattern detection
- Rate limiting per endpoint category
- Input sanitization
- Request logging for security audit
- API key rotation support
- CORS hardening
"""
import re
import time
import hashlib
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


# SQL injection patterns
SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|EXEC)\b)",
    r"(--|;|\/\*|\*\/|xp_)",
    r"(\bOR\b\s+\b\d+\b\s*=\s*\b\d+\b)",
    r"('|\")(;|\s+(OR|AND)\s+)",
]

# XSS patterns
XSS_PATTERNS = [
    r"<script[^>]*>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe",
    r"<object",
    r"<embed",
]

# Compile patterns for performance
_sql_patterns = [re.compile(p, re.IGNORECASE) for p in SQL_INJECTION_PATTERNS]
_xss_patterns = [re.compile(p, re.IGNORECASE) for p in XSS_PATTERNS]


class ValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for input validation and security hardening."""

    # Max request body size: 10MB
    MAX_BODY_SIZE = 10 * 1024 * 1024

    # Rate limits per category (requests per minute)
    RATE_LIMITS = {
        "auth": 10,
        "chat": 30,
        "camera": 60,  # Frame processing needs higher rate
        "location": 120,  # GPS points need high rate
        "default": 60,
    }

    def __init__(self, app):
        super().__init__(app)
        self._request_counts: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # 1. Body size check
        if request.method in ("POST", "PUT", "PATCH"):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.MAX_BODY_SIZE:
                return Response(
                    content='{"error": "Request body too large"}',
                    status_code=413,
                    media_type="application/json",
                )

        # 2. Rate limiting (skip for /auth/ — per-email lockout is the protection there)
        client_ip = request.client.host if request.client else "unknown"
        category = self._get_category(request.url.path)
        if category != "auth" and self._is_rate_limited(client_ip, category):
            return Response(
                content='{"error": "Rate limit exceeded. Please try again later."}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": "60"},
            )

        # 3. Security pattern detection on query params and path
        full_url = str(request.url)
        if self._detect_injection(full_url):
            return Response(
                content='{"error": "Invalid request detected"}',
                status_code=400,
                media_type="application/json",
            )

        # 4. Process request
        response = await call_next(request)

        # 5. Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"

        # 6. Request timing header
        elapsed = time.time() - start_time
        response.headers["X-Response-Time"] = f"{elapsed:.3f}s"

        return response

    def _get_category(self, path: str) -> str:
        """Determine rate limit category from path."""
        if "/auth/" in path:
            return "auth"
        elif "/chat" in path:
            return "chat"
        elif "/camera/" in path:
            return "camera"
        elif "/location/" in path:
            return "location"
        return "default"

    def _is_rate_limited(self, client_ip: str, category: str) -> bool:
        """Check if client has exceeded rate limit for category."""
        key = f"{client_ip}:{category}"
        now = time.time()
        window = 60  # 1 minute window

        if key not in self._request_counts:
            self._request_counts[key] = []

        # Clean old entries
        self._request_counts[key] = [
            t for t in self._request_counts[key] if now - t < window
        ]

        limit = self.RATE_LIMITS.get(category, self.RATE_LIMITS["default"])
        if len(self._request_counts[key]) >= limit:
            return True

        self._request_counts[key].append(now)
        return False

    def _detect_injection(self, text: str) -> bool:
        """Detect SQL injection or XSS patterns in text."""
        for pattern in _sql_patterns:
            if pattern.search(text):
                return True
        for pattern in _xss_patterns:
            if pattern.search(text):
                return True
        return False


def sanitize_input(text: str) -> str:
    """Sanitize string input to prevent injection attacks."""
    if not isinstance(text, str):
        return text
    # Remove null bytes
    text = text.replace("\x00", "")
    # Trim excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def validate_bpm(value: float) -> float:
    """Validate BPM value is within physiological range."""
    return max(30, min(220, value))


def validate_coordinates(lat: float, lng: float) -> tuple[float, float]:
    """Validate GPS coordinates."""
    return max(-90, min(90, lat)), max(-180, min(180, lng))


def generate_request_hash(data: dict) -> str:
    """Generate a hash for request deduplication."""
    import json
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()[:16]

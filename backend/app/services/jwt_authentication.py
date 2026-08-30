"""JWT Authentication Service.

Extracted from authx (inspiration).
Handles JWT token creation, validation, and refresh with multiple
token location support (headers, cookies, query, JSON).

All pure functions — no DB, no async.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class JWTConfig:
    """JWT configuration."""
    secret_key: str = "default-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    jwt_header_name: str = "Authorization"
    jwt_header_type: str = "Bearer"
    jwt_cookie_csrf_protect: bool = True


@dataclass
class TokenPayload:
    """JWT token payload."""
    sub: str
    exp: float
    iat: float
    type: str = "access"  # "access" or "refresh"
    jti: str = ""
    extra: dict = field(default_factory=dict)


@dataclass
class RequestToken:
    """Token extracted from request."""
    token: str
    type: str = "access"
    location: str = "headers"  # "headers", "cookies", "query", "json"
    csrf: Optional[str] = None


@dataclass
class TokenPair:
    """Access and refresh token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 1800


# --- Base64 Helpers ---

def base64url_encode(data: bytes) -> str:
    """URL-safe base64 encode."""
    return urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


def base64url_decode(s: str) -> bytes:
    """URL-safe base64 decode."""
    padding = 4 - len(s) % 4
    if padding != 4:
        s += '=' * padding
    return urlsafe_b64decode(s)


# --- HMAC Signing ---

def sign_data(data: str, secret: str, algorithm: str = "HS256") -> str:
    """Sign data with HMAC.

    Args:
        data: Data to sign
        secret: Secret key
        algorithm: Signing algorithm

    Returns:
        Signature string
    """
    if algorithm == "HS256":
        return base64url_encode(
            hmac.new(secret.encode(), data.encode(), hashlib.sha256).digest()
        )
    elif algorithm == "HS384":
        return base64url_encode(
            hmac.new(secret.encode(), data.encode(), hashlib.sha384).digest()
        )
    elif algorithm == "HS512":
        return base64url_encode(
            hmac.new(secret.encode(), data.encode(), hashlib.sha512).digest()
        )
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")


def verify_signature(data: str, signature: str, secret: str, algorithm: str = "HS256") -> bool:
    """Verify HMAC signature.

    Args:
        data: Signed data
        signature: Expected signature
        secret: Secret key
        algorithm: Signing algorithm

    Returns:
        True if signature is valid
    """
    expected = sign_data(data, secret, algorithm)
    return hmac.compare_digest(expected, signature)


# --- Token Creation ---

def create_jwt_token(
    payload: TokenPayload,
    config: JWTConfig = JWTConfig(),
) -> str:
    """Create a JWT token.

    Args:
        payload: Token payload
        config: JWT configuration

    Returns:
        JWT token string
    """
    header = {"alg": config.algorithm, "typ": "JWT"}
    payload_dict = {
        "sub": payload.sub,
        "exp": payload.exp,
        "iat": payload.iat,
        "type": payload.type,
        "jti": payload.jti,
        **payload.extra,
    }

    header_b64 = base64url_encode(json.dumps(header).encode())
    payload_b64 = base64url_encode(json.dumps(payload_dict).encode())

    signature = sign_data(f"{header_b64}.{payload_b64}", config.secret_key, config.algorithm)

    return f"{header_b64}.{payload_b64}.{signature}"


def create_token_pair(
    user_id: str,
    config: JWTConfig = JWTConfig(),
    extra: dict = None,
) -> TokenPair:
    """Create access and refresh token pair.

    Args:
        user_id: User identifier
        config: JWT configuration
        extra: Additional payload data

    Returns:
        Token pair
    """
    now = time.time()

    access_payload = TokenPayload(
        sub=user_id,
        exp=now + config.access_token_expire_minutes * 60,
        iat=now,
        type="access",
        jti=hashlib.md5(f"{user_id}{now}".encode()).hexdigest(),
        extra=extra or {},
    )

    refresh_payload = TokenPayload(
        sub=user_id,
        exp=now + config.refresh_token_expire_days * 86400,
        iat=now,
        type="refresh",
        jti=hashlib.md5(f"{user_id}{now}refresh".encode()).hexdigest(),
    )

    return TokenPair(
        access_token=create_jwt_token(access_payload, config),
        refresh_token=create_jwt_token(refresh_payload, config),
        expires_in=config.access_token_expire_minutes * 60,
    )


# --- Token Validation ---

def decode_jwt_token(
    token: str,
    config: JWTConfig = JWTConfig(),
) -> Optional[TokenPayload]:
    """Decode and validate a JWT token.

    Args:
        token: JWT token string
        config: JWT configuration

    Returns:
        Token payload or None if invalid
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, signature = parts

        # Verify signature
        if not verify_signature(f"{header_b64}.{payload_b64}", signature, config.secret_key, config.algorithm):
            return None

        # Decode payload
        payload_dict = json.loads(base64url_decode(payload_b64))

        # Check expiration
        if payload_dict.get("exp", 0) < time.time():
            return None

        return TokenPayload(
            sub=payload_dict.get("sub", ""),
            exp=payload_dict.get("exp", 0),
            iat=payload_dict.get("iat", 0),
            type=payload_dict.get("type", "access"),
            jti=payload_dict.get("jti", ""),
            extra={k: v for k, v in payload_dict.items()
                   if k not in ("sub", "exp", "iat", "type", "jti")},
        )

    except Exception:
        return None


def validate_token_type(
    payload: TokenPayload,
    expected_type: str = "access",
) -> bool:
    """Validate token type.

    Args:
        payload: Token payload
        expected_type: Expected token type

    Returns:
        True if token type matches
    """
    return payload.type == expected_type


def is_token_expired(payload: TokenPayload) -> bool:
    """Check if token is expired.

    Args:
        payload: Token payload

    Returns:
        True if expired
    """
    return payload.exp < time.time()


# --- Token Refresh ---

def refresh_access_token(
    refresh_token: str,
    config: JWTConfig = JWTConfig(),
    extra: dict = None,
) -> Optional[TokenPair]:
    """Refresh access token using refresh token.

    Args:
        refresh_token: Refresh JWT token
        config: JWT configuration
        extra: Additional payload data

    Returns:
        New token pair or None if refresh token is invalid
    """
    payload = decode_jwt_token(refresh_token, config)
    if payload is None:
        return None

    if not validate_token_type(payload, "refresh"):
        return None

    if is_token_expired(payload):
        return None

    return create_token_pair(payload.sub, config, extra)


# --- Token Extraction ---

def extract_token_from_header(
    auth_header: str,
    header_type: str = "Bearer",
) -> Optional[str]:
    """Extract token from Authorization header.

    Args:
        auth_header: Authorization header value
        header_type: Expected header type

    Returns:
        Token string or None
    """
    if not auth_header:
        return None

    if header_type and auth_header.startswith(f"{header_type} "):
        return auth_header[len(header_type) + 1:]

    return auth_header if not header_type else None


def extract_token_from_cookie(
    cookies: dict,
    cookie_name: str = "access_token",
) -> Optional[str]:
    """Extract token from cookies.

    Args:
        cookies: Request cookies
        cookie_name: Cookie name

    Returns:
        Token string or None
    """
    return cookies.get(cookie_name)


def extract_token_from_query(
    query_params: dict,
    param_name: str = "token",
) -> Optional[str]:
    """Extract token from query parameters.

    Args:
        query_params: Query parameters
        param_name: Parameter name

    Returns:
        Token string or None
    """
    return query_params.get(param_name)


# --- CSRF Protection ---

def generate_csrf_token(secret: str, session_id: str) -> str:
    """Generate a CSRF token.

    Args:
        secret: Secret key
        session_id: Session identifier

    Returns:
        CSRF token
    """
    timestamp = str(int(time.time()))
    data = f"{session_id}:{timestamp}"
    signature = sign_data(data, secret)
    return f"{timestamp}:{signature}"


def verify_csrf_token(
    csrf_token: str,
    secret: str,
    session_id: str,
    max_age: int = 3600,
) -> bool:
    """Verify a CSRF token.

    Args:
        csrf_token: CSRF token to verify
        secret: Secret key
        session_id: Session identifier
        max_age: Maximum token age in seconds

    Returns:
        True if valid
    """
    try:
        parts = csrf_token.split(":")
        if len(parts) != 2:
            return False

        timestamp_str, signature = parts
        timestamp = int(timestamp_str)

        # Check age
        if time.time() - timestamp > max_age:
            return False

        # Verify signature
        data = f"{session_id}:{timestamp_str}"
        return verify_signature(data, signature, secret)

    except Exception:
        return False

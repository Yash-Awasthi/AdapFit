"""
Authentication System — JWT tokens, password hashing, session management

Features:
- JWT access + refresh tokens
- bcrypt password hashing
- Role-based access control (user, admin, superadmin)
- Session management with token revocation
- Password strength validation
"""
import os
import time
import hashlib
import secrets
from typing import Optional
from dataclasses import dataclass, field

# JWT handling — pure Python implementation (no external deps needed)
import base64
import json
import hmac


_env_key = os.getenv("JWT_SECRET_KEY", "")
if not _env_key:
    if os.getenv("ENVIRONMENT", "development") == "production":
        raise ValueError(
            "JWT_SECRET_KEY environment variable is required in production. "
            "Generate one with: python -c 'import secrets; print(secrets.token_hex(64))'"
        )
    import logging as _logging
    _logging.warning("JWT_SECRET_KEY not set — using random key for this session. Tokens will NOT survive restart.")
    _env_key = secrets.token_hex(64)
SECRET_KEY = _env_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30
API_KEY_PREFIX = "af_"

# Account lockout settings
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

# Audit log (in-memory, rotates on size)
MAX_AUDIT_LOG_SIZE = 5000
_audit_log: list[dict] = []


def _log_audit_event(event_type: str, user_id: str = "", details: dict = None, ip: str = ""):
    """Record a security audit event."""
    import time as _time
    _audit_log.append({
        "event": event_type,
        "user_id": user_id,
        "details": details or {},
        "ip": ip,
        "timestamp": _time.time(),
    })
    if len(_audit_log) > MAX_AUDIT_LOG_SIZE:
        _audit_log[:] = _audit_log[-MAX_AUDIT_LOG_SIZE // 2:]


def get_audit_log(limit: int = 100) -> list[dict]:
    """Get recent audit log entries."""
    return list(reversed(_audit_log[-limit:]))



def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def _sign(payload: dict, secret: str, expires_at: float) -> str:
    header = {"alg": ALGORITHM, "typ": "JWT"}
    payload["exp"] = expires_at
    payload["iat"] = time.time()
    header_b64 = _b64url_encode(json.dumps(header).encode())
    payload_b64 = _b64url_encode(json.dumps(payload).encode())
    message = f"{header_b64}.{payload_b64}"
    signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    signature_b64 = _b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def _verify(token: str, secret: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, signature_b64 = parts
        message = f"{header_b64}.{payload_b64}"
        expected_sig = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
        actual_sig = _b64url_decode(signature_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        payload = json.loads(_b64url_decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


# === Password Hashing (bcrypt-like using PBKDF2) ===

def hash_password(password: str) -> str:
    """Hash password with PBKDF2-HMAC-SHA256."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 310000)
    return f"pbkdf2:sha256:310000${salt}${dk.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    try:
        parts = hashed.split("$")
        if len(parts) != 3:
            return False
        algo_info = parts[0]  # pbkdf2:sha256:310000
        salt = parts[1]
        stored_hash = parts[2]
        iterations = int(algo_info.split(":")[2])
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations)
        return hmac.compare_digest(dk.hex(), stored_hash)
    except Exception:
        return False


def validate_password_strength(password: str) -> dict:
    """Validate password meets strength requirements."""
    errors = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")
    if len(password) > 128:
        errors.append("Password must be at most 128 characters")
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")
    return {"valid": len(errors) == 0, "errors": errors}


# === Token Management ===

def create_access_token(user_id: str, role: str = "user", extra: Optional[dict] = None) -> str:
    """Create JWT access token."""
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
    }
    if extra:
        payload.update(extra)
    return _sign(payload, SECRET_KEY, time.time() + ACCESS_TOKEN_EXPIRE_MINUTES * 60)


def create_refresh_token(user_id: str) -> str:
    """Create JWT refresh token."""
    payload = {
        "sub": user_id,
        "type": "refresh",
    }
    return _sign(payload, SECRET_KEY, time.time() + REFRESH_TOKEN_EXPIRE_DAYS * 86400)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token."""
    return _verify(token, SECRET_KEY)


def create_token_pair(user_id: str, role: str = "user") -> dict:
    """Create access + refresh token pair."""
    return {
        "access_token": create_access_token(user_id, role),
        "refresh_token": create_refresh_token(user_id),
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


# === API Key Management ===

@dataclass
class ApiKey:
    key_hash: str
    name: str
    tier: str
    rate_limit: int
    created_at: float
    last_used: float = 0
    is_active: bool = True


class ApiKeyManager:
    """Manage API keys for external integrations."""

    def __init__(self):
        self._keys: dict[str, ApiKey] = {}
        self._revoked: set[str] = set()

    def create_key(self, name: str, tier: str = "free", rate_limit: int = 100) -> str:
        raw_key = f"{API_KEY_PREFIX}{secrets.token_hex(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        self._keys[key_hash] = ApiKey(
            key_hash=key_hash, name=name, tier=tier,
            rate_limit=rate_limit, created_at=time.time(),
        )
        return raw_key

    def validate_key(self, raw_key: str) -> Optional[dict]:
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        if key_hash in self._revoked:
            return None
        key = self._keys.get(key_hash)
        if not key or not key.is_active:
            return None
        key.last_used = time.time()
        return {"name": key.name, "tier": key.tier, "rate_limit": key.rate_limit}

    def revoke_key(self, raw_key: str) -> bool:
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        if key_hash in self._keys:
            self._revoked.add(key_hash)
            self._keys[key_hash].is_active = False
            return True
        return False

    def list_keys(self) -> list[dict]:
        return [{"name": k.name, "tier": k.tier, "rate_limit": k.rate_limit, "active": k.is_active, "created_at": k.created_at} for k in self._keys.values()]


api_key_manager = ApiKeyManager()


# === In-Memory User Store (replaced by DB in Stage B) ===

@dataclass
class User:
    id: str
    email: str
    username: str
    password_hash: str
    display_name: str = ""
    avatar_url: str = ""
    date_of_birth: str = ""
    gender: str = ""
    height: float = 0
    weight: float = 0
    units: str = "metric"
    role: str = "user"
    is_active: bool = True
    created_at: float = field(default_factory=time.time)
    last_login: float = 0


class UserManager:
    """User registration, authentication, and profile management."""

    def __init__(self):
        self._users: dict[str, User] = {}
        self._email_index: dict[str, str] = {}
        self._username_index: dict[str, str] = {}
        self._refresh_tokens: dict[str, float] = {}  # token -> expiry
        self._failed_attempts: dict[str, list[float]] = {}  # email -> [timestamps]
        self._lockouts: dict[str, float] = {}  # email -> lockout_expiry

    def register(self, email: str, username: str, password: str, display_name: str = "") -> dict:
        if email.lower() in self._email_index:
            return {"error": "Email already registered"}
        if username.lower() in self._username_index:
            return {"error": "Username already taken"}
        pw_check = validate_password_strength(password)
        if not pw_check["valid"]:
            return {"error": "Weak password", "details": pw_check["errors"]}
        user_id = f"user_{secrets.token_hex(12)}"
        user = User(
            id=user_id, email=email.lower(), username=username.lower(),
            password_hash=hash_password(password),
            display_name=display_name or username,
        )
        self._users[user_id] = user
        self._email_index[email.lower()] = user_id
        self._username_index[username.lower()] = user_id
        tokens = create_token_pair(user_id, user.role)
        self._refresh_tokens[tokens["refresh_token"]] = time.time() + REFRESH_TOKEN_EXPIRE_DAYS * 86400
        return {
            "user": {"id": user_id, "email": user.email, "username": user.username, "display_name": user.display_name, "role": user.role},
            "tokens": tokens,
        }

    def login(self, email: str, password: str, ip: str = "") -> dict:
        email_lower = email.lower()
        
        # Check account lockout
        lockout_until = self._lockouts.get(email_lower, 0)
        if lockout_until > time.time():
            remaining = int((lockout_until - time.time()) / 60) + 1
            _log_audit_event("login_locked", email=email_lower, details={"minutes_remaining": remaining}, ip=ip)
            return {"error": f"Account locked. Try again in {remaining} minutes."}
        
        # Clear expired lockouts
        if lockout_until and lockout_until < time.time():
            self._lockouts.pop(email_lower, None)
            self._failed_attempts.pop(email_lower, None)
        
        user_id = self._email_index.get(email_lower)
        if not user_id:
            _log_audit_event("login_failed_unknown_email", email=email_lower, ip=ip)
            # Perform a dummy password hash to prevent timing attacks
            verify_password(password, hash_password(password))
            return {"error": "Invalid credentials"}
        user = self._users.get(user_id)
        if not user or not verify_password(password, user.password_hash):
            # Track failed attempt
            now = time.time()
            if email_lower not in self._failed_attempts:
                self._failed_attempts[email_lower] = []
            self._failed_attempts[email_lower].append(now)
            # Clean old attempts (> lockout window)
            cutoff = now - LOCKOUT_DURATION_MINUTES * 60
            self._failed_attempts[email_lower] = [t for t in self._failed_attempts[email_lower] if t > cutoff]
            
            _log_audit_event("login_failed_bad_password", user_id=user_id, ip=ip, 
                           details={"attempts": len(self._failed_attempts[email_lower])})
            
            # Lock account if too many failures
            if len(self._failed_attempts[email_lower]) >= MAX_FAILED_ATTEMPTS:
                self._lockouts[email_lower] = now + LOCKOUT_DURATION_MINUTES * 60
                _log_audit_event("account_locked", user_id=user_id, ip=ip,
                               details={"attempts": len(self._failed_attempts[email_lower])})
            
            return {"error": "Invalid credentials"}
        if not user.is_active:
            _log_audit_event("login_disabled_account", user_id=user_id, ip=ip)
            return {"error": "Account disabled"}
        
        # Successful login — clear failures
        self._failed_attempts.pop(email_lower, None)
        self._lockouts.pop(email_lower, None)
        
        user.last_login = time.time()
        tokens = create_token_pair(user_id, user.role)
        self._refresh_tokens[tokens["refresh_token"]] = time.time() + REFRESH_TOKEN_EXPIRE_DAYS * 86400
        
        _log_audit_event("login_success", user_id=user_id, ip=ip)
        
        return {
            "user": {"id": user_id, "email": user.email, "username": user.username, "display_name": user.display_name, "role": user.role},
            "tokens": tokens,
        }

    def refresh(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return {"error": "Invalid refresh token"}
        if refresh_token not in self._refresh_tokens:
            return {"error": "Refresh token revoked"}
        if self._refresh_tokens[refresh_token] < time.time():
            del self._refresh_tokens[refresh_token]
            return {"error": "Refresh token expired"}
        user = self._users.get(payload["sub"])
        if not user or not user.is_active:
            return {"error": "User not found or inactive"}
        del self._refresh_tokens[refresh_token]
        tokens = create_token_pair(user.id, user.role)
        self._refresh_tokens[tokens["refresh_token"]] = time.time() + REFRESH_TOKEN_EXPIRE_DAYS * 86400
        return {"tokens": tokens}

    def logout(self, refresh_token: str) -> dict:
        self._refresh_tokens.pop(refresh_token, None)
        return {"logged_out": True}

    def get_user(self, user_id: str) -> Optional[dict]:
        user = self._users.get(user_id)
        if not user:
            return None
        return {
            "id": user.id, "email": user.email, "username": user.username,
            "display_name": user.display_name, "avatar_url": user.avatar_url,
            "date_of_birth": user.date_of_birth, "gender": user.gender,
            "height": user.height, "weight": user.weight, "units": user.units,
            "role": user.role, "is_active": user.is_active,
            "created_at": user.created_at, "last_login": user.last_login,
        }

    def update_profile(self, user_id: str, updates: dict) -> dict:
        user = self._users.get(user_id)
        if not user:
            return {"error": "User not found"}
        allowed_fields = {"display_name", "avatar_url", "date_of_birth", "gender", "height", "weight", "units"}
        for key, value in updates.items():
            if key in allowed_fields:
                setattr(user, key, value)
        return {"updated": True, "user": self.get_user(user_id)}

    def list_users(self, limit: int = 50) -> list[dict]:
        return [{"id": u.id, "email": u.email, "username": u.username, "display_name": u.display_name, "role": u.role, "is_active": u.is_active, "created_at": u.created_at} for u in list(self._users.values())[:limit]]

    def suspend_user(self, user_id: str) -> dict:
        user = self._users.get(user_id)
        if not user:
            return {"error": "User not found"}
        user.is_active = False
        return {"suspended": True}

    def delete_user(self, user_id: str) -> dict:
        user = self._users.get(user_id)
        if not user:
            return {"error": "User not found"}
        self._email_index.pop(user.email, None)
        self._username_index.pop(user.username, None)
        del self._users[user_id]
        return {"deleted": True}


user_manager = UserManager()


# === FastAPI Dependencies ===

def get_current_user_from_token(token: str) -> Optional[dict]:
    """Extract user from JWT token."""
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None
    return user_manager.get_user(payload["sub"])


def require_auth(token: str) -> dict:
    """Require valid authentication. Returns user or raises error."""
    user = get_current_user_from_token(token)
    if not user:
        raise Exception("Authentication required")
    return user


def require_admin(token: str) -> dict:
    """Require admin role."""
    user = get_current_user_from_token(token)
    if not user:
        raise Exception("Authentication required")
    if user.get("role") not in ("admin", "superadmin"):
        raise Exception("Admin access required")
    return user

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
import uuid
from typing import Optional
from dataclasses import dataclass, field

# JWT handling — pure Python implementation (no external deps needed)
import base64
import json
import hmac


from app.core.config import settings as _settings
_env_key = os.getenv("JWT_SECRET_KEY", "") or _settings.JWT_SECRET_KEY
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


def _log_audit_event(event_type: str, user_id: str = "", details: dict = None, ip: str = "", email: str = ""):
    """Record a security audit event."""
    import time as _time
    _audit_log.append({
        "event": event_type,
        "user_id": user_id,
        "email": email,
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

    def get_key_info(self, raw_key: str) -> Optional[dict]:
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key = self._keys.get(key_hash)
        if not key:
            return None
        return {"name": key.name, "tier": key.tier, "rate_limit": key.rate_limit, "is_active": key.is_active, "created_at": key.created_at}

    def list_keys(self) -> list[dict]:
        return [{"name": k.name, "tier": k.tier, "rate_limit": k.rate_limit, "is_active": k.is_active, "created_at": k.created_at} for k in self._keys.values()]


api_key_manager = ApiKeyManager()


# === Accounts ===

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

    def to_dict(self) -> dict:
        return {
            "id": self.id, "email": self.email, "username": self.username,
            "password_hash": self.password_hash, "display_name": self.display_name,
            "avatar_url": self.avatar_url, "date_of_birth": self.date_of_birth,
            "gender": self.gender, "height": self.height, "weight": self.weight,
            "units": self.units, "role": self.role, "is_active": self.is_active,
            "created_at": self.created_at, "last_login": self.last_login,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        known = set(cls.__dataclass_fields__)
        return cls(**{k: v for k, v in data.items() if k in known})


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _public(user: "User") -> dict:
    return {
        "id": user.id, "email": user.email, "username": user.username,
        "display_name": user.display_name, "role": user.role,
    }


class UserManager:
    """
    User registration, authentication, and profile management.

    The dicts here cache the durable store in app.core.accounts; they are not
    the system of record. Every mutation is written through before it is
    reported as done, so a restart or a second process sees the same accounts.
    """

    def __init__(self):
        self._users: dict[str, User] = {}
        self._email_index: dict[str, str] = {}
        self._username_index: dict[str, str] = {}
        self._refresh_tokens: dict[str, float] = {}  # token hash -> expiry
        self._failed_attempts: dict[str, list[float]] = {}  # email -> [timestamps]
        self._lockouts: dict[str, float] = {}  # email -> lockout_expiry
        self._loaded = False

    async def load(self) -> None:
        """Populate the cache from the durable store. Safe to call repeatedly."""
        from app.core.accounts import account_store, session_store

        self._users.clear()
        self._email_index.clear()
        self._username_index.clear()
        for record in await account_store.load_all():
            self._index(User.from_dict(record))
        self._refresh_tokens = await session_store.load_all()
        self._loaded = True

    async def _ensure_loaded(self) -> None:
        if not self._loaded:
            await self.load()

    def _index(self, user: "User") -> None:
        self._users[user.id] = user
        self._email_index[user.email.lower()] = user.id
        self._username_index[user.username.lower()] = user.id

    async def _persist(self, user: "User") -> None:
        from app.core.accounts import account_store

        await account_store.save(user.to_dict())

    async def _remember_refresh(self, user_id: str, refresh_token: str) -> None:
        from app.core.accounts import session_store

        expiry = time.time() + REFRESH_TOKEN_EXPIRE_DAYS * 86400
        digest = _token_hash(refresh_token)
        self._refresh_tokens[digest] = expiry
        await session_store.add(digest, user_id, expiry)

    async def _forget_refresh(self, refresh_token: str) -> None:
        from app.core.accounts import session_store

        digest = _token_hash(refresh_token)
        self._refresh_tokens.pop(digest, None)
        await session_store.remove(digest)

    async def register(self, email: str, username: str, password: str, display_name: str = "") -> dict:
        await self._ensure_loaded()
        if email.lower() in self._email_index:
            return {"error": "Email already registered"}
        if username.lower() in self._username_index:
            return {"error": "Username already taken"}
        pw_check = validate_password_strength(password)
        if not pw_check["valid"]:
            return {"error": "Weak password", "details": pw_check["errors"]}
        # A UUID rather than an opaque token, so the account id is also the
        # primary key of the profile row every personalization feature reads.
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id, email=email.lower(), username=username.lower(),
            password_hash=hash_password(password),
            display_name=display_name or username,
        )
        self._index(user)
        await self._persist(user)
        tokens = create_token_pair(user_id, user.role)
        await self._remember_refresh(user_id, tokens["refresh_token"])
        _log_audit_event("register", user_id=user_id, email=user.email)
        return {"user": _public(user), "tokens": tokens}

    async def login(self, email: str, password: str, ip: str = "") -> dict:
        await self._ensure_loaded()
        email_lower = email.lower()

        lockout_until = self._lockouts.get(email_lower, 0)
        if lockout_until > time.time():
            remaining = int((lockout_until - time.time()) / 60) + 1
            _log_audit_event("login_locked", email=email_lower, details={"minutes_remaining": remaining}, ip=ip)
            return {"error": f"Account locked. Try again in {remaining} minutes."}

        if lockout_until and lockout_until < time.time():
            self._lockouts.pop(email_lower, None)
            self._failed_attempts.pop(email_lower, None)

        user_id = self._email_index.get(email_lower)
        if not user_id:
            _log_audit_event("login_failed_unknown_email", email=email_lower, ip=ip)
            # Hash anyway: an unknown email must not answer faster than a wrong password.
            verify_password(password, hash_password(password))
            return {"error": "Invalid credentials"}
        user = self._users.get(user_id)
        if not user or not verify_password(password, user.password_hash):
            now = time.time()
            attempts = self._failed_attempts.setdefault(email_lower, [])
            attempts.append(now)
            cutoff = now - LOCKOUT_DURATION_MINUTES * 60
            self._failed_attempts[email_lower] = [t for t in attempts if t > cutoff]

            _log_audit_event("login_failed_bad_password", user_id=user_id, ip=ip,
                             details={"attempts": len(self._failed_attempts[email_lower])})

            if len(self._failed_attempts[email_lower]) >= MAX_FAILED_ATTEMPTS:
                self._lockouts[email_lower] = now + LOCKOUT_DURATION_MINUTES * 60
                _log_audit_event("account_locked", user_id=user_id, ip=ip,
                                 details={"attempts": len(self._failed_attempts[email_lower])})

            return {"error": "Invalid credentials"}
        if not user.is_active:
            _log_audit_event("login_disabled_account", user_id=user_id, ip=ip)
            return {"error": "Account disabled"}

        self._failed_attempts.pop(email_lower, None)
        self._lockouts.pop(email_lower, None)

        user.last_login = time.time()
        await self._persist(user)
        tokens = create_token_pair(user_id, user.role)
        await self._remember_refresh(user_id, tokens["refresh_token"])

        _log_audit_event("login_success", user_id=user_id, ip=ip)
        return {"user": _public(user), "tokens": tokens}

    async def refresh(self, refresh_token: str) -> dict:
        await self._ensure_loaded()
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return {"error": "Invalid refresh token"}
        digest = _token_hash(refresh_token)
        if digest not in self._refresh_tokens:
            return {"error": "Refresh token revoked"}
        if self._refresh_tokens[digest] < time.time():
            await self._forget_refresh(refresh_token)
            return {"error": "Refresh token expired"}
        user = self._users.get(payload["sub"])
        if not user or not user.is_active:
            return {"error": "User not found or inactive"}
        # Rotate on use, so a stolen copy of the token works at most once.
        await self._forget_refresh(refresh_token)
        tokens = create_token_pair(user.id, user.role)
        await self._remember_refresh(user.id, tokens["refresh_token"])
        return {"tokens": tokens}

    async def logout(self, refresh_token: str) -> dict:
        await self._forget_refresh(refresh_token)
        return {"logged_out": True}

    async def get_user(self, user_id: str) -> Optional[dict]:
        await self._ensure_loaded()
        user = self._users.get(user_id)
        if not user:
            return None
        record = user.to_dict()
        record.pop("password_hash")
        return record

    async def update_profile(self, user_id: str, updates: dict) -> dict:
        await self._ensure_loaded()
        user = self._users.get(user_id)
        if not user:
            return {"error": "User not found"}
        allowed_fields = {"display_name", "avatar_url", "date_of_birth", "gender", "height", "weight", "units"}
        for key, value in updates.items():
            if key in allowed_fields:
                setattr(user, key, value)
        await self._persist(user)
        return {"updated": True, "user": await self.get_user(user_id)}

    async def change_password(self, user_id: str, current_password: str, new_password: str) -> dict:
        await self._ensure_loaded()
        user = self._users.get(user_id)
        if not user or not verify_password(current_password, user.password_hash):
            return {"error": "Invalid credentials"}
        pw_check = validate_password_strength(new_password)
        if not pw_check["valid"]:
            return {"error": "Weak password", "details": pw_check["errors"]}
        user.password_hash = hash_password(new_password)
        await self._persist(user)
        _log_audit_event("password_changed", user_id=user_id)
        return {"changed": True}

    async def list_users(self, limit: int = 50) -> list[dict]:
        await self._ensure_loaded()
        return [
            {**_public(u), "is_active": u.is_active, "created_at": u.created_at}
            for u in list(self._users.values())[:limit]
        ]

    async def suspend_user(self, user_id: str) -> dict:
        await self._ensure_loaded()
        user = self._users.get(user_id)
        if not user:
            return {"error": "User not found"}
        user.is_active = False
        await self._persist(user)
        return {"suspended": True}

    async def delete_user(self, user_id: str) -> dict:
        from app.core.accounts import account_store

        await self._ensure_loaded()
        user = self._users.get(user_id)
        if not user:
            return {"error": "User not found"}
        self._email_index.pop(user.email, None)
        self._username_index.pop(user.username, None)
        del self._users[user_id]
        await account_store.delete(user_id)
        from app.core import durable
        await durable.erase_user(user_id)
        return {"deleted": True}


user_manager = UserManager()

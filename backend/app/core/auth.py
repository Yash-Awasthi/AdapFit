"""
Authentication System — JWT tokens, password hashing, session management

Access tokens last 15 minutes; refresh tokens 30 days, single use, rotated on
every refresh. Presenting a refresh token that was already rotated means a copy
was stolen, so every session of that account ends. Changing or resetting the
password, suspension and erasure end every session too.
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
# Verify-only during a JWT key rotation: tokens signed with the old key keep
# working until they expire (at most REFRESH_TOKEN_EXPIRE_DAYS).
PREVIOUS_SECRET_KEY = os.getenv("JWT_SECRET_KEY_PREVIOUS", "")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30
RESET_TOKEN_MINUTES = 30

# Account lockout settings
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


async def _log_audit_event(event_type: str, user_id: str = "", details: dict = None, ip: str = "", email: str = ""):
    from app.core import audit

    extra = dict(details or {})
    if email and not user_id:
        extra["email_hash"] = audit.email_hash(email)
    await audit.record(event_type, user_id=user_id, ip=ip, **extra)


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
        # Two refreshes in the same second must still produce distinct tokens.
        "jti": secrets.token_hex(8),
    }
    return _sign(payload, SECRET_KEY, time.time() + REFRESH_TOKEN_EXPIRE_DAYS * 86400)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token."""
    payload = _verify(token, SECRET_KEY)
    if payload is None and PREVIOUS_SECRET_KEY:
        payload = _verify(token, PREVIOUS_SECRET_KEY)
    return payload


def decode_access_token(token: str) -> Optional[dict]:
    """An access token that is still valid; a refresh token is not a credential for API calls."""
    payload = decode_token(token)
    if not payload or payload.get("type") != "access" or not payload.get("sub"):
        return None
    if not user_manager.token_current(payload):
        return None
    return payload


def create_token_pair(user_id: str, role: str = "user") -> dict:
    """Create access + refresh token pair."""
    return {
        "access_token": create_access_token(user_id, role),
        "refresh_token": create_refresh_token(user_id),
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


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
        self._refresh_tokens: dict[str, tuple[str, float]] = {}  # token hash -> (user id, expiry)
        # ponytail: rotated-token memory and the revocation cut-off live in process memory; a restart forgets
        # them, bounded by the 15-minute access token. Persist both before running more than one worker.
        self._rotated: dict[str, tuple[str, float]] = {}  # hash of a used refresh token -> (user id, expiry)
        self._revoked_before: dict[str, float] = {}  # user id -> tokens issued before this are void
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

    def token_current(self, payload: dict) -> bool:
        """False once the account is gone, suspended, or its sessions were ended after the token was issued."""
        uid = str(payload.get("sub", ""))
        if self._loaded:
            user = self._users.get(uid)
            if user is None or not user.is_active:
                return False
        return float(payload.get("iat", 0)) >= self._revoked_before.get(uid, 0)

    def _index(self, user: "User") -> None:
        self._users[user.id] = user
        self._email_index[user.email.lower()] = user.id
        self._username_index[user.username.lower()] = user.id

    async def _persist(self, user: "User") -> None:
        from app.core.accounts import account_store

        await account_store.save(user.to_dict())

    async def _issue(self, user: "User") -> dict:
        from app.core.accounts import session_store

        tokens = create_token_pair(user.id, user.role)
        expiry = time.time() + REFRESH_TOKEN_EXPIRE_DAYS * 86400
        digest = _token_hash(tokens["refresh_token"])
        self._refresh_tokens[digest] = (user.id, expiry)
        await session_store.add(digest, user.id, expiry)
        return tokens

    async def _forget_refresh(self, refresh_token: str) -> None:
        from app.core.accounts import session_store

        digest = _token_hash(refresh_token)
        self._refresh_tokens.pop(digest, None)
        await session_store.remove(digest)

    async def revoke_sessions(self, user_id: str, reason: str) -> None:
        """End every session: refresh tokens are deleted and access tokens issued until now stop working."""
        from app.core.accounts import session_store

        self._revoked_before[user_id] = time.time()
        for digest in [d for d, (uid, _) in self._refresh_tokens.items() if uid == user_id]:
            self._refresh_tokens.pop(digest, None)
        await session_store.remove_user(user_id)
        await _log_audit_event("sessions_revoked", user_id=user_id, details={"reason": reason})

    async def register(self, email: str, username: str, password: str, display_name: str = "",
                       birth_date: str = "", consent: Optional[dict] = None, guardian_email: str = "",
                       ip: str = "") -> dict:
        from app.core import privacy

        await self._ensure_loaded()
        if email.lower() in self._email_index:
            return {"error": "Email already registered"}
        if username.lower() in self._username_index:
            return {"error": "Username already taken"}
        pw_check = validate_password_strength(password)
        if not pw_check["valid"]:
            return {"error": "Weak password", "details": pw_check["errors"]}
        try:
            privacy.validate_signup(birth_date, consent or {}, guardian_email, email)
        except ValueError as exc:
            return {"error": str(exc)}
        # A UUID rather than an opaque token, so the account id is also the
        # primary key of the profile row every personalization feature reads.
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id, email=email.lower(), username=username.lower(),
            password_hash=hash_password(password),
            display_name=display_name or username, date_of_birth=birth_date,
        )
        self._index(user)
        await self._persist(user)
        consent_state = privacy.start(user_id, birth_date, consent or {}, guardian_email)
        if consent_state["guardian_pending"]:
            consent_state["guardian_email_sent"] = await privacy.send_guardian_link(user_id)
        tokens = await self._issue(user)
        await _log_audit_event("register", user_id=user_id, ip=ip)
        return {"user": _public(user), "tokens": tokens, "privacy": consent_state}

    async def login(self, email: str, password: str, ip: str = "") -> dict:
        await self._ensure_loaded()
        email_lower = email.lower()

        lockout_until = self._lockouts.get(email_lower, 0)
        if lockout_until > time.time():
            remaining = int((lockout_until - time.time()) / 60) + 1
            await _log_audit_event("login_locked", user_id=self._email_index.get(email_lower, ""),
                                   email=email_lower, details={"minutes_remaining": remaining}, ip=ip)
            return {"error": f"Account locked. Try again in {remaining} minutes."}

        if lockout_until and lockout_until < time.time():
            self._lockouts.pop(email_lower, None)
            self._failed_attempts.pop(email_lower, None)

        user_id = self._email_index.get(email_lower)
        if not user_id:
            await _log_audit_event("login_failed_unknown_email", email=email_lower, ip=ip)
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

            await _log_audit_event("login_failed_bad_password", user_id=user_id, ip=ip,
                                   details={"attempts": len(self._failed_attempts[email_lower])})

            if len(self._failed_attempts[email_lower]) >= MAX_FAILED_ATTEMPTS:
                self._lockouts[email_lower] = now + LOCKOUT_DURATION_MINUTES * 60
                await _log_audit_event("account_locked", user_id=user_id, ip=ip,
                                       details={"attempts": len(self._failed_attempts[email_lower])})

            return {"error": "Invalid credentials"}
        if not user.is_active:
            await _log_audit_event("login_disabled_account", user_id=user_id, ip=ip)
            return {"error": "Account disabled"}

        self._failed_attempts.pop(email_lower, None)
        self._lockouts.pop(email_lower, None)

        user.last_login = time.time()
        await self._persist(user)
        from app.core import privacy
        privacy.on_login(user_id)
        tokens = await self._issue(user)

        await _log_audit_event("login_success", user_id=user_id, ip=ip)
        return {"user": _public(user), "tokens": tokens}

    async def refresh(self, refresh_token: str, ip: str = "") -> dict:
        await self._ensure_loaded()
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return {"error": "Invalid refresh token"}
        digest = _token_hash(refresh_token)
        now = time.time()
        self._rotated = {d: v for d, v in self._rotated.items() if v[1] > now}
        if digest in self._rotated:
            owner = self._rotated[digest][0]
            await _log_audit_event("refresh_token_reuse", user_id=owner, ip=ip)
            await self.revoke_sessions(owner, "refresh_token_reuse")
            return {"error": "Refresh token revoked"}
        if digest not in self._refresh_tokens:
            return {"error": "Refresh token revoked"}
        expiry = self._refresh_tokens[digest][1]
        if expiry < now:
            await self._forget_refresh(refresh_token)
            return {"error": "Refresh token expired"}
        user = self._users.get(payload["sub"])
        if not user or not user.is_active:
            return {"error": "User not found or inactive"}
        # Rotate on use, so a stolen copy of the token works at most once.
        await self._forget_refresh(refresh_token)
        self._rotated[digest] = (user.id, expiry)
        return {"tokens": await self._issue(user)}

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
        """Other devices are signed out; this one gets a fresh token pair."""
        await self._ensure_loaded()
        user = self._users.get(user_id)
        if not user or not verify_password(current_password, user.password_hash):
            return {"error": "Invalid credentials"}
        pw_check = validate_password_strength(new_password)
        if not pw_check["valid"]:
            return {"error": "Weak password", "details": pw_check["errors"]}
        user.password_hash = hash_password(new_password)
        await self._persist(user)
        await _log_audit_event("password_changed", user_id=user_id)
        await self.revoke_sessions(user_id, "password_changed")
        return {"changed": True, "tokens": await self._issue(user)}

    async def request_password_reset(self, email: str, ip: str = "") -> bool:
        """Email a single-use link. The route answers the same whether or not the email has an account."""
        from app.core.config import settings
        from app.core.mailer import send_mail

        await self._ensure_loaded()
        user = self._users.get(self._email_index.get(email.strip().lower(), ""))
        if not user or not user.is_active:
            await _log_audit_event("password_reset_unknown_email", email=email, ip=ip)
            return False
        for key in [k for k, v in dict.items(_reset_tokens) if v["user_id"] == user.id]:
            del _reset_tokens[key]
        token = secrets.token_urlsafe(32)
        _reset_tokens[_token_hash(token)] = {"user_id": user.id,
                                             "expires_at": time.time() + RESET_TOKEN_MINUTES * 60}
        link = f"{settings.PUBLIC_BASE_URL.rstrip('/')}{settings.API_V1_STR}/auth/reset-password/{token}"
        await _log_audit_event("password_reset_requested", user_id=user.id, ip=ip)
        return await send_mail(user.email, "Reset your AdapFit password", (
            "Someone asked to reset the password of your AdapFit account. If it was you, open this link within "
            f"{RESET_TOKEN_MINUTES} minutes:\n\n{link}\n\nIf it was not you, ignore this email; your password "
            "has not changed."))

    def reset_link_valid(self, token: str) -> bool:
        link = dict.get(_reset_tokens, _token_hash(token))
        return bool(link) and link["expires_at"] > time.time()

    async def reset_password(self, token: str, new_password: str, ip: str = "") -> dict:
        await self._ensure_loaded()
        digest = _token_hash(token)
        if not self.reset_link_valid(token):
            return {"error": "This link has expired or was already used"}
        pw_check = validate_password_strength(new_password)
        if not pw_check["valid"]:
            return {"error": "Weak password", "details": pw_check["errors"]}
        user = self._users.get(_reset_tokens.pop(digest)["user_id"])
        if not user or not user.is_active:
            return {"error": "This link has expired or was already used"}
        user.password_hash = hash_password(new_password)
        self._failed_attempts.pop(user.email, None)
        self._lockouts.pop(user.email, None)
        await self._persist(user)
        await _log_audit_event("password_reset", user_id=user.id, ip=ip)
        await self.revoke_sessions(user.id, "password_reset")
        return {"reset": True}

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
        await self.revoke_sessions(user_id, "suspended")
        return {"suspended": True}

    async def delete_user(self, user_id: str) -> dict:
        from app.core.accounts import account_store

        await self._ensure_loaded()
        user = self._users.get(user_id)
        if not user:
            return {"error": "User not found"}
        await self.revoke_sessions(user_id, "erased")
        self._email_index.pop(user.email, None)
        self._username_index.pop(user.username, None)
        del self._users[user_id]
        await account_store.delete(user_id)
        from app.core import durable
        from app.core.storage import storage
        await storage.erase_user(user_id)
        await durable.erase_user(user_id)
        await _log_audit_event("account_erased", user_id=user_id)
        return {"deleted": True}

    async def request_deletion(self, user_id: str, password: str) -> dict:
        """Erase after a grace period; the password proves it is the owner, not someone holding the phone."""
        from app.core import privacy

        await self._ensure_loaded()
        user = self._users.get(user_id)
        if not user or not verify_password(password, user.password_hash):
            return {"error": "Invalid credentials"}
        due = privacy.request_deletion(user_id)
        await _log_audit_event("deletion_requested", user_id=user_id)
        return {"deletion_due_at": due, "grace_minutes": privacy.DELETION_GRACE_SECONDS // 60}


def _durable_reset_tokens():
    from app.core.durable import durable_dict
    return durable_dict("app.core.auth.reset_tokens")


# sha256(token) -> {"user_id", "expires_at"}
_reset_tokens = _durable_reset_tokens()
user_manager = UserManager()

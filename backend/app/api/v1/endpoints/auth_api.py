"""User Authentication API — Register, Login, Profile, Token Management"""
from fastapi import APIRouter, Header, HTTPException, Request, Depends
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from app.core.auth import user_manager, decode_token, validate_password_strength, create_token_pair, get_audit_log
from app.core.dependencies import require_admin

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    display_name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    units: Optional[str] = None


class PasswordResetRequest(BaseModel):
    email: str


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=128)


def _extract_user(authorization: Optional[str] = None) -> Optional[dict]:
    """Extract user from Authorization header."""
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None
    return user_manager.get_user(payload["sub"])


@router.post("/register")
async def register(request: RegisterRequest):
    """Register a new user account."""
    result = user_manager.register(request.email, request.username, request.password, request.display_name)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/login")
async def login(request: LoginRequest, req: Request):
    """Authenticate and get access tokens."""
    client_ip = req.client.host if req.client else "unknown"
    result = user_manager.login(request.email, request.password, ip=client_ip)
    if "error" in result:
        # Use 401 for credential errors, 423 for locked accounts
        status_code = 423 if "locked" in result["error"].lower() else 401
        raise HTTPException(status_code=status_code, detail=result["error"])
    return result


@router.post("/refresh")
async def refresh_token(request: RefreshRequest):
    """Refresh access token using refresh token."""
    result = user_manager.refresh(request.refresh_token)
    if "error" in result:
        raise HTTPException(status_code=401, detail=result["error"])
    return result


@router.post("/logout")
async def logout(request: RefreshRequest):
    """Revoke refresh token (logout)."""
    return user_manager.logout(request.refresh_token)


@router.get("/me")
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Get current authenticated user profile."""
    user = _extract_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"user": user}


@router.put("/me")
async def update_profile(request: ProfileUpdateRequest, authorization: Optional[str] = Header(None)):
    """Update current user profile."""
    user = _extract_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    updates = request.model_dump(exclude_none=True)
    return user_manager.update_profile(user["id"], updates)


@router.post("/change-password")
async def change_password(request: PasswordChangeRequest, authorization: Optional[str] = Header(None)):
    """Change password for authenticated user."""
    user = _extract_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    from app.core.auth import verify_password, hash_password
    user_obj = user_manager._users.get(user["id"])
    if not user_obj or not verify_password(request.old_password, user_obj.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    pw_check = validate_password_strength(request.new_password)
    if not pw_check["valid"]:
        raise HTTPException(status_code=400, detail=pw_check["errors"])
    user_obj.password_hash = hash_password(request.new_password)
    return {"changed": True}


@router.post("/forgot-password")
async def forgot_password(request: PasswordResetRequest):
    """Request password reset (sends email in production)."""
    # In production: send reset email with token
    return {"message": "If the email exists, a reset link has been sent", "email": request.email}


@router.get("/validate")
async def validate_token(authorization: Optional[str] = Header(None)):
    """Validate current token and return user info."""
    user = _extract_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"valid": True, "user": user}


@router.get("/audit-log")
async def audit_log(limit: int = 50, admin: dict = Depends(require_admin)):
    """Get security audit log (admin only)."""
    return {"entries": get_audit_log(limit=limit), "admin": admin["id"]}

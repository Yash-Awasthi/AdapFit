"""User Authentication API — Register, Login, Profile, Token Management"""
import html

from fastapi import APIRouter, Form, Header, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional
from app.core import audit
from app.core.auth import user_manager, decode_access_token
from app.core.dependencies import require_admin, require_user

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    display_name: str = ""
    birth_date: str = Field(default="", description="YYYY-MM-DD")
    consent: dict[str, bool] = Field(default_factory=dict, description="Purpose id to choice; see /privacy/consent/purposes")
    guardian_email: str = Field(default="", max_length=255, description="Required under 18")


class DeleteAccountRequest(BaseModel):
    password: str


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


async def _extract_user(authorization: Optional[str] = None) -> Optional[dict]:
    """Extract user from Authorization header."""
    if not authorization:
        return None
    await user_manager._ensure_loaded()
    payload = decode_access_token(authorization.replace("Bearer ", ""))
    if not payload:
        return None
    return await user_manager.get_user(payload["sub"])


def _ip(req: Request) -> str:
    return req.client.host if req.client else "unknown"


@router.post("/register")
async def register(request: RegisterRequest, req: Request):
    """Register a new user account."""
    result = await user_manager.register(request.email, request.username, request.password, request.display_name,
                                         request.birth_date, request.consent, request.guardian_email, ip=_ip(req))
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/login")
async def login(request: LoginRequest, req: Request):
    """Authenticate and get access tokens."""
    result = await user_manager.login(request.email, request.password, ip=_ip(req))
    if "error" in result:
        # Use 401 for credential errors, 423 for locked accounts
        status_code = 423 if "locked" in result["error"].lower() else 401
        raise HTTPException(status_code=status_code, detail=result["error"])
    return result


@router.post("/refresh")
async def refresh_token(request: RefreshRequest, req: Request):
    """Exchange a refresh token for a new pair; the old one stops working."""
    result = await user_manager.refresh(request.refresh_token, ip=_ip(req))
    if "error" in result:
        raise HTTPException(status_code=401, detail=result["error"])
    return result


@router.post("/logout")
async def logout(request: RefreshRequest):
    """Revoke refresh token (logout)."""
    return await user_manager.logout(request.refresh_token)


@router.get("/me")
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Get current authenticated user profile."""
    user = await _extract_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"user": user}


@router.put("/me")
async def update_profile(request: ProfileUpdateRequest, authorization: Optional[str] = Header(None)):
    """Update current user profile."""
    user = await _extract_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    updates = request.model_dump(exclude_none=True)
    return await user_manager.update_profile(user["id"], updates)


@router.post("/change-password")
async def change_password(request: PasswordChangeRequest, authorization: Optional[str] = Header(None)):
    """Change password for authenticated user."""
    user = await _extract_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = await user_manager.change_password(user["id"], request.old_password, request.new_password)
    if "error" in result:
        detail = result.get("details") or result["error"]
        raise HTTPException(status_code=400, detail=detail)
    return result


@router.post("/delete-account")
async def delete_account(request: DeleteAccountRequest, authorization: Optional[str] = Header(None)):
    """Schedule erasure of the account and everything held for it, after a short grace period."""
    user = await _extract_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = await user_manager.request_deletion(user["id"], request.password)
    if "error" in result:
        raise HTTPException(status_code=403, detail=result["error"])
    return result


@router.post("/delete-account/cancel")
async def cancel_delete_account(authorization: Optional[str] = Header(None)):
    from app.core import privacy

    user = await _extract_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    cancelled = privacy.cancel_deletion(user["id"])
    if cancelled:
        # A restore replays erasure requests from the log, so it must also see the cancellation.
        await audit.record("deletion_cancelled", user_id=user["id"])
    return {"cancelled": cancelled}


@router.post("/forgot-password")
async def forgot_password(request: PasswordResetRequest, req: Request):
    """Email a reset link. The answer is the same whether or not the address has an account."""
    await user_manager.request_password_reset(request.email, ip=_ip(req))
    return {"message": "If the email has an account, a reset link has been sent"}


def _page(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(
        f"<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,"
        f"initial-scale=1'><meta name=referrer content=no-referrer><title>{html.escape(title)}</title><style>"
        f"body{{font:16px/1.5 system-ui,sans-serif;max-width:32rem;margin:2rem auto;padding:0 1rem;color:#111;"
        f"background:#fff}}label{{display:block;margin:.75rem 0}}input{{width:100%;padding:.5rem;font:inherit}}"
        f"button{{font:inherit;padding:.6rem 1rem;margin-top:.5rem}}small{{color:#555}}</style></head><body>"
        f"<h1>{html.escape(title)}</h1>{body}</body></html>"
    )


_EXPIRED = "<p>This link has expired or was already used. Ask for a new one from the sign-in screen.</p>"


@router.get("/reset-password/{token}", response_class=HTMLResponse)
async def reset_password_form(token: str):
    if not user_manager.reset_link_valid(token):
        return _page("Link expired", _EXPIRED)
    return _page("Choose a new password", f"""
<form method=post action="{html.escape(token, quote=True)}">
<label>New password <input type=password name=password required minlength=8 maxlength=128
autocomplete=new-password></label>
<label>Repeat it <input type=password name=confirm required minlength=8 maxlength=128 autocomplete=new-password></label>
<small>At least 8 characters with an upper-case letter, a lower-case letter and a digit. Every device signed in to
the account will be signed out.</small><br>
<button>Save password</button>
</form>""")


@router.post("/reset-password/{token}", response_class=HTMLResponse)
async def reset_password_submit(token: str, req: Request, password: str = Form(...), confirm: str = Form(...)):
    if password != confirm:
        return _page("Not saved", f"<p>The two passwords differ.</p><p><a href='{html.escape(token, quote=True)}'>"
                                  f"Back</a></p>")
    result = await user_manager.reset_password(token, password, ip=_ip(req))
    if "error" in result:
        if "details" not in result:
            return _page("Link expired", _EXPIRED)
        items = "".join(f"<li>{html.escape(e)}</li>" for e in result["details"])
        return _page("Not saved", f"<ul>{items}</ul><p><a href='{html.escape(token, quote=True)}'>Back</a></p>")
    return _page("Password changed", "<p>Sign in to the app with your new password.</p>")


@router.get("/validate")
async def validate_token(authorization: Optional[str] = Header(None)):
    """Validate current token and return user info."""
    user = await _extract_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"valid": True, "user": user}


@router.get("/activity")
async def my_security_activity(limit: int = 50, user: dict = Depends(require_user)):
    """The caller's own security log: sign-ins, failed attempts, password and session changes, exports."""
    return {"entries": await audit.entries(user["id"], limit)}


@router.get("/audit-log")
async def audit_log(limit: int = 50, user_id: Optional[str] = None, admin: dict = Depends(require_admin)):
    """Security audit log across all accounts (admin only). Reading it is itself logged."""
    await audit.record("audit_log_read", user_id=user_id or "", actor_id=admin["id"])
    return {"entries": await audit.entries(user_id, limit), "admin": admin["id"]}

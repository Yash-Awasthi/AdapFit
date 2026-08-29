"""Admin API — User management, system stats, analytics overview"""
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.auth import user_manager, decode_token
from app.core.database import get_database_stats

router = APIRouter()


def _require_admin(authorization: Optional[str] = None) -> dict:
    """Verify admin role from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token")
    user = user_manager.get_user(payload["sub"])
    if not user or user.get("role") not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/stats")
async def get_system_stats(authorization: Optional[str] = Header(None)):
    """Get system-wide statistics."""
    _require_admin(authorization)
    db_stats = get_database_stats()
    users = user_manager.list_users(limit=10000)
    return {
        "total_users": len(users),
        "active_users": sum(1 for u in users if u.get("is_active")),
        "admin_users": sum(1 for u in users if u.get("role") in ("admin", "superadmin")),
        "database": db_stats,
        "api_version": "2.0.0",
    }


@router.get("/users")
async def list_users(limit: int = 50, offset: int = 0, authorization: Optional[str] = Header(None)):
    """List all users (admin only)."""
    _require_admin(authorization)
    users = user_manager.list_users(limit=limit)
    return {"users": users, "total": len(users)}


@router.get("/users/{user_id}")
async def get_user_detail(user_id: str, authorization: Optional[str] = Header(None)):
    """Get user details (admin only)."""
    _require_admin(authorization)
    user = user_manager.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": user}


@router.post("/users/{user_id}/suspend")
async def suspend_user(user_id: str, authorization: Optional[str] = Header(None)):
    """Suspend a user account (admin only)."""
    admin = _require_admin(authorization)
    if admin["id"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot suspend yourself")
    result = user_manager.suspend_user(user_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, authorization: Optional[str] = Header(None)):
    """Delete a user account (admin only)."""
    admin = _require_admin(authorization)
    if admin["id"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    result = user_manager.delete_user(user_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/analytics")
async def get_analytics(authorization: Optional[str] = Header(None)):
    """Get health analytics overview (admin only)."""
    _require_admin(authorization)
    db_stats = get_database_stats()
    users = user_manager.list_users(limit=10000)
    return {
        "users": {
            "total": len(users),
            "active": sum(1 for u in users if u.get("is_active")),
            "new_this_week": sum(1 for u in users if u.get("created_at", 0) > __import__("time").time() - 604800),
        },
        "data": db_stats,
        "feature_usage": {
            "workouts": db_stats.get("workouts", 0),
            "meals": db_stats.get("meals", 0),
            "sleep_sessions": db_stats.get("sleep_sessions", 0),
            "mood_entries": db_stats.get("mood_entries", 0),
            "medications": db_stats.get("medications", 0),
        },
    }


@router.get("/health")
async def admin_health():
    """Admin health check (no auth required)."""
    db_stats = get_database_stats()
    return {"status": "healthy", "database": db_stats, "version": "2.0.0"}

"""
Health API Rate Limiter & Quota Management
Per-user rate limiting, quota tracking, and abuse prevention.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid


class APIRateLimiter:
    RATE_LIMITS = {
        "free": {"requests_per_minute": 30, "requests_per_hour": 500, "requests_per_day": 5000, "concurrent": 5},
        "premium": {"requests_per_minute": 120, "requests_per_hour": 5000, "requests_per_day": 50000, "concurrent": 20},
        "enterprise": {"requests_per_minute": 600, "requests_per_hour": 30000, "requests_per_day": 300000, "concurrent": 100},
    }

    def __init__(self):
        self.user_tiers: Dict[str, str] = {}
        self.request_logs: Dict[str, List[dict]] = {}
        self.quota_usage: Dict[str, dict] = {}

    def set_user_tier(self, user_id: str, tier: str) -> dict:
        if tier not in self.RATE_LIMITS:
            return {"error": f"Invalid tier: {tier}. Valid: {list(self.RATE_LIMITS.keys())}"}
        self.user_tiers[user_id] = tier
        return {"user_id": user_id, "tier": tier, "limits": self.RATE_LIMITS[tier]}

    def check_rate_limit(self, user_id: str) -> dict:
        tier = self.user_tiers.get(user_id, "free")
        limits = self.RATE_LIMITS[tier]
        now = datetime.now()
        
        logs = self.request_logs.get(user_id, [])
        
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        recent_minute = sum(1 for l in logs if datetime.fromisoformat(l["timestamp"]) >= minute_ago)
        recent_hour = sum(1 for l in logs if datetime.fromisoformat(l["timestamp"]) >= hour_ago)
        recent_day = sum(1 for l in logs if datetime.fromisoformat(l["timestamp"]) >= day_ago)
        
        allowed = True
        reason = None
        if recent_minute >= limits["requests_per_minute"]:
            allowed = False
            reason = "Minute limit exceeded"
        elif recent_hour >= limits["requests_per_hour"]:
            allowed = False
            reason = "Hour limit exceeded"
        elif recent_day >= limits["requests_per_day"]:
            allowed = False
            reason = "Daily limit exceeded"
        
        return {
            "allowed": allowed,
            "reason": reason,
            "tier": tier,
            "usage": {
                "minute": f"{recent_minute}/{limits['requests_per_minute']}",
                "hour": f"{recent_hour}/{limits['requests_per_hour']}",
                "day": f"{recent_day}/{limits['requests_per_day']}",
            },
            "remaining": {
                "minute": max(0, limits["requests_per_minute"] - recent_minute),
                "hour": max(0, limits["requests_per_hour"] - recent_hour),
                "day": max(0, limits["requests_per_day"] - recent_day),
            },
        }

    def log_request(self, user_id: str, endpoint: str, method: str, status_code: int = 200, response_time_ms: float = 0) -> dict:
        entry = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "timestamp": datetime.now().isoformat(),
        }
        self.request_logs.setdefault(user_id, []).append(entry)
        
        cutoff = datetime.now() - timedelta(days=1)
        self.request_logs[user_id] = [l for l in self.request_logs[user_id] if datetime.fromisoformat(l["timestamp"]) >= cutoff]
        
        return entry

    def get_usage_stats(self, user_id: str) -> dict:
        tier = self.user_tiers.get(user_id, "free")
        limits = self.RATE_LIMITS[tier]
        logs = self.request_logs.get(user_id, [])
        now = datetime.now()
        
        hour_logs = [l for l in logs if datetime.fromisoformat(l["timestamp"]) >= now - timedelta(hours=1)]
        day_logs = [l for l in logs if datetime.fromisoformat(l["timestamp"]) >= now - timedelta(days=1)]
        
        avg_response = sum(l.get("response_time_ms", 0) for l in hour_logs) / max(len(hour_logs), 1)
        error_count = sum(1 for l in day_logs if l["status_code"] >= 400)
        
        endpoint_counts = {}
        for l in day_logs:
            ep = l["endpoint"]
            endpoint_counts[ep] = endpoint_counts.get(ep, 0) + 1
        
        return {
            "tier": tier,
            "limits": limits,
            "requests_today": len(day_logs),
            "requests_this_hour": len(hour_logs),
            "avg_response_time_ms": round(avg_response, 1),
            "error_rate": round(error_count / max(len(day_logs), 1) * 100, 1),
            "top_endpoints": sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:5],
        }


rate_limiter = APIRateLimiter()

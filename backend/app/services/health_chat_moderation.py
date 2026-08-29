"""
Health Chat Moderation — Content safety and moderation for health discussions
"""
from datetime import datetime
from typing import Dict, List, Optional
import uuid
import re


class ChatModeration:
    RESTRICTED_TOPICS = ["self_harm", "suicide", "eating_disorder_promotion", "substance_abuse_detailed", "medical_advice_dangerous"]
    SAFE_HEALTH_TOPICS = ["exercise", "nutrition", "sleep", "stress_management", "meditation", "general_wellness", "medication_general", "mental_health_support"]
    
    TOXICITY_PATTERNS = [
        (r"(?i)(kill yourself|kys|end your life)", "extremely_harmful", "content_removed"),
        (r"(?i)(buy drugs|illegal substances|fake prescription)", "harmful", "content_flagged"),
        (r"(?i)(miracle cure|guaranteed to cure|secret remedy)", "misinformation", "content_flagged"),
        (r"(?i)(you should stop taking your medication)", "dangerous_advice", "content_flagged"),
    ]

    HELPLINE_NUMBERS = {
        "us": {"name": "988 Suicide & Crisis Lifeline", "number": "988", "text": "Text HOME to 741741"},
        "uk": {"name": "Samaritans", "number": "116 123"},
        "canada": {"name": "Crisis Services Canada", "number": "1-833-456-4566"},
        "australia": {"name": "Lifeline Australia", "number": "13 11 14"},
        "india": {"name": "iCall", "number": "9152987821"},
        "global": {"name": "Befrienders Worldwide", "url": "https://www.befrienders.org"},
    }

    def __init__(self):
        self.flagged_content: Dict[str, List[dict]] = {}
        self.user_reports: Dict[str, List[dict]] = {}
        self.moderation_logs: Dict[str, List[dict]] = []

    def moderate_content(self, content: str, user_id: str) -> dict:
        content_lower = content.lower()
        
        for pattern, category, action in self.TOXICITY_PATTERNS:
            if re.search(pattern, content_lower):
                flag = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "content_preview": content[:100],
                    "category": category,
                    "action": action,
                    "timestamp": datetime.now().isoformat(),
                }
                self.flagged_content.setdefault(user_id, []).append(flag)
                self.moderation_logs.append(flag)
                return {"safe": False, "action": action, "category": category, "message": "Content flagged for safety review"}
        
        if any(topic in content_lower for topic in ["suicid", "self harm", "want to die", "end it all"]):
            return {"safe": True, "warning": True, "helplines": self.HELPLINE_NUMBERS, "message": "We're here for you. If you're in crisis, please reach out."}
        
        return {"safe": True, "action": "allowed"}

    def report_content(self, reporter_id: str, content_id: str, reason: str, details: str = "") -> dict:
        report = {"id": str(uuid.uuid4()), "reporter_id": reporter_id, "content_id": content_id, "reason": reason, "details": details, "status": "pending", "timestamp": datetime.now().isoformat()}
        self.user_reports.setdefault(reporter_id, []).append(report)
        return report

    def get_flagged_content(self, limit: int = 50) -> List[dict]:
        return self.moderation_logs[-limit:]

    def get_helplines(self, country: str = "us") -> dict:
        return self.HELPLINE_NUMBERS.get(country, self.HELPLINE_NUMBERS["us"])


chat_moderation = ChatModeration()

"""
Substance Use Disorder & MAT (Medication-Assisted Treatment) Tracking
Tracks recovery, cravings, support network, and relapse prevention.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid


class SubstanceUseService:
    SUBSTANCE_TYPES = {
        "alcohol": {"color": "#E74C3C", "withdrawal_risk": "high", "days": [1, 3, 7, 14, 30, 90, 180, 365]},
        "opioids": {"color": "#E67E22", "withdrawal_risk": "very_high", "days": [1, 3, 7, 14, 30, 90]},
        "tobacco": {"color": "#8E44AD", "withdrawal_risk": "moderate", "days": [1, 3, 7, 14, 30, 60, 90]},
        "cannabis": {"color": "#27AE60", "withdrawal_risk": "low", "days": [1, 7, 14, 30, 60, 90]},
        "benzodiazepines": {"color": "#C0392B", "withdrawal_risk": "very_high", "days": [7, 14, 30, 60, 90]},
        "stimulants": {"color": "#D35400", "withdrawal_risk": "moderate", "days": [1, 3, 7, 14, 30]},
    }

    MAT_MEDICATIONS = {
        "methadone": {"for": "opioids", "type": "full_agonist", "notes": "Daily supervised dosing initially"},
        "buprenorphine": {"for": "opioids", "type": "partial_agonist", "notes": "Can prescribe in office"},
        "naltrexone": {"for": "opioids,alcohol", "type": "antagonist", "notes": "Must be detoxed first"},
        "acamprosate": {"for": "alcohol", "type": "glutamate_modulator", "notes": "Take with meals"},
        "disulfiram": {"for": "alcohol", "type": "aversion", "notes": "Causes reaction if alcohol consumed"},
        "varenicline": {"for": "tobacco", "type": "partial_agonist", "notes": "Reduce then quit"},
        "bupropion": {"for": "tobacco,depression", "type": "antidepressant", "notes": "Also helps with weight"},
    }

    COPING_STRATEGIES = [
        {"id": "urge_surfing", "name": "Urge Surfing", "duration_min": 10, "description": "Observe the craving without acting on it, like a wave that rises and falls"},
        {"id": "play_the_tape", "name": "Play the Tape Through", "duration_min": 5, "description": "Mentally play out the full consequences of using, not just the initial relief"},
        {"id": "call_support", "name": "Call Support Person", "duration_min": 15, "description": "Reach out to your sponsor, therapist, or trusted friend"},
        {"id": "physical_activity", "name": "Physical Activity", "duration_min": 20, "description": "Exercise releases endorphins naturally and reduces cravings"},
        {"id": "grounding", "name": "5-4-3-2-1 Grounding", "duration_min": 5, "description": "Name 5 things you see, 4 hear, 3 touch, 2 smell, 1 taste"},
        {"id": "journal", "name": "Journaling", "duration_min": 10, "description": "Write down what you're feeling and why you want to use"},
        {"id": "meditation", "name": "Mindfulness Meditation", "duration_min": 10, "description": "Focus on breath and observe thoughts without judgment"},
        {"id": "distract", "name": "Engage in Activity", "duration_min": 30, "description": "Do something absorbing: puzzle, game, hobby, cleaning"},
    ]

    MILESTONES = [
        {"days": 1, "badge": "First Step", "emoji": "🌱"},
        {"days": 3, "badge": "Clear-headed", "emoji": "🧠"},
        {"days": 7, "badge": "One Week Strong", "emoji": "💪"},
        {"days": 14, "badge": "Two Weeks Free", "emoji": "⭐"},
        {"days": 30, "badge": "One Month Warrior", "emoji": "🏆"},
        {"days": 60, "badge": "Two Month Champion", "emoji": "🥇"},
        {"days": 90, "badge": "90-Day Milestone", "emoji": "🎯"},
        {"days": 180, "badge": "Six Month Hero", "emoji": "🦸"},
        {"days": 365, "badge": "One Year Survivor", "emoji": "🌟"},
        {"days": 730, "badge": "Two Year Legend", "emoji": "👑"},
    ]

    def __init__(self):
        self.profiles: Dict[str, dict] = {}
        self.craving_logs: Dict[str, List[dict]] = {}
        self.journal_entries: Dict[str, List[dict]] = {}
        self.mat_logs: Dict[str, List[dict]] = {}
        self.sobriety_dates: Dict[str, dict] = {}
        self.support_contacts: Dict[str, List[dict]] = {}

    def create_recovery_profile(self, user_id: str, substance: str, start_date: str, mat_medication: Optional[str] = None) -> dict:
        profile_id = str(uuid.uuid4())
        sub_info = self.SUBSTANCE_TYPES.get(substance, {})
        profile = {
            "id": profile_id,
            "user_id": user_id,
            "substance": substance,
            "start_date": start_date,
            "sobriety_days": 0,
            "mat_medication": mat_medication,
            "mat_info": self.MAT_MEDICATIONS.get(mat_medication, {}),
            "withdrawal_risk": sub_info.get("withdrawal_risk", "unknown"),
            "triggers": [],
            "goals": [],
            "created_at": datetime.now().isoformat(),
        }
        self.profiles[user_id] = profile
        self.craving_logs[user_id] = []
        self.journal_entries[user_id] = []
        self.mat_logs[user_id] = []
        self.sobriety_dates[user_id] = {"date": start_date, "substance": substance}
        self.support_contacts[user_id] = []
        return profile

    def log_craving(self, user_id: str, intensity: int, trigger: str, location: str, duration_min: int, used_coping: Optional[str] = None) -> dict:
        entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "intensity": min(max(intensity), 10),
            "trigger": trigger,
            "location": location,
            "duration_min": duration_min,
            "coping_strategy_used": used_coping,
            "resisted": used_coping is not None,
            "timestamp": datetime.now().isoformat(),
        }
        self.craving_logs.setdefault(user_id, []).append(entry)
        return entry

    def get_coping_strategies(self, intensity: int) -> List[dict]:
        if intensity >= 8:
            return [s for s in self.COPING_STRATEGIES if s["id"] in ("call_support", "grounding", "physical_activity")]
        elif intensity >= 5:
            return [s for s in self.COPING_STRATEGIES if s["id"] in ("urge_surfing", "journal", "meditation")]
        else:
            return [s for s in self.COPING_STRATEGIES if s["id"] in ("distract", "play_the_tape", "journal")]

    def log_mat_dose(self, user_id: str, medication: str, dosage_mg: float, taken_at: str, side_effects: List[str] = None) -> dict:
        entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "medication": medication,
            "dosage_mg": dosage_mg,
            "taken_at": taken_at or datetime.now().isoformat(),
            "side_effects": side_effects or [],
        }
        self.mat_logs.setdefault(user_id, []).append(entry)
        return entry

    def add_journal_entry(self, user_id: str, mood: int, content: str, gratitude: List[str] = None) -> dict:
        entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "mood": min(max(mood), 10),
            "content": content,
            "gratitude": gratitude or [],
            "timestamp": datetime.now().isoformat(),
        }
        self.journal_entries.setdefault(user_id, []).append(entry)
        return entry

    def get_sobriety_status(self, user_id: str) -> dict:
        profile = self.profiles.get(user_id, {})
        sobriety = self.sobriety_dates.get(user_id, {})
        if not sobriety:
            return {"status": "no_profile", "message": "No recovery profile set up"}
        start = datetime.fromisoformat(sobriety["date"])
        days = (datetime.now() - start).days
        milestones_achieved = [m for m in self.MILESTONES if days >= m["days"]]
        next_milestone = next((m for m in self.MILESTONES if days < m["days"]), None)
        cravings = self.craving_logs.get(user_id, [])
        recent = [c for c in cravings if datetime.fromisoformat(c["timestamp"]) > datetime.now() - timedelta(days=7)]
        resistance_rate = sum(1 for c in recent if c.get("resisted")) / max(len(recent), 1) * 100
        return {
            "days_sober": days,
            "substance": sobriety.get("substance", "unknown"),
            "milestones_achieved": milestones_achieved,
            "next_milestone": next_milestone,
            "resistance_rate_7d": round(resistance_rate, 1),
            "cravings_this_week": len(recent),
            "longest_streak_days": days,
        }

    def add_support_contact(self, user_id: str, name: str, relationship: str, phone: str, is_sponsor: bool = False) -> dict:
        contact = {
            "id": str(uuid.uuid4()),
            "name": name,
            "relationship": relationship,
            "phone": phone,
            "is_sponsor": is_sponsor,
        }
        self.support_contacts.setdefault(user_id, []).append(contact)
        return contact

    def get_craving_analytics(self, user_id: str) -> dict:
        logs = self.craving_logs.get(user_id, [])
        if not logs:
            return {"total": 0, "message": "No cravings logged yet"}
        triggers = {}
        locations = {}
        for log in logs:
            triggers[log["trigger"]] = triggers.get(log["trigger"], 0) + 1
            locations[log["location"]] = locations.get(log["location"], 0) + 1
        top_triggers = sorted(triggers.items(), key=lambda x: x[1], reverse=True)[:5]
        avg_intensity = sum(log["intensity"] for log in logs) / len(logs)
        resistance_rate = sum(1 for log in logs if log.get("resisted")) / len(logs) * 100
        return {
            "total_cravings": len(logs),
            "avg_intensity": round(avg_intensity, 1),
            "resistance_rate": round(resistance_rate, 1),
            "top_triggers": [{"trigger": t, "count": c} for t, c in top_triggers],
            "common_locations": dict(sorted(locations.items(), key=lambda x: x[1], reverse=True)[:5]),
        }


substance_use_service = SubstanceUseService()

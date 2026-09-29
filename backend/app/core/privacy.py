"""
Consent, guardian consent and account erasure under the DPDP Act 2023 and Rules 2025.

Consent is per purpose, tied to a policy version, and every change is appended
to the user's log rather than overwriting it, so the log is the record of what
was agreed and when. A grant under an older policy version counts as not given.

Under 18 the user cannot grant anything; a guardian does, through an emailed
link. The child can still withdraw. Analytics is never available to a child
(section 9(3): no tracking or behavioural monitoring of children).
ponytail: guardian identity is an emailed link plus a declaration of adulthood;
Rule 10 prefers a DigiLocker age token, which is the upgrade path.
"""
import hashlib
import logging
import secrets
import time
from datetime import date, datetime, timezone
from typing import Dict, Optional

from app.core.config import settings
from app.core.durable import durable_dict
from app.core.per_user import SHARED, current_user_id

logger = logging.getLogger(__name__)

POLICY_VERSION = "2026-09-29"
ADULT_AGE = 18
# Under 13 would put the app under Google Play's Families policy and needs a design for children.
MIN_AGE = 13
GUARDIAN_LINK_HOURS = 72
DELETION_GRACE_SECONDS = 30 * 60
# Retention: a child's account nobody consented for, and an account unused for years, are erased.
GUARDIAN_WAIT_DAYS = 7
INACTIVE_DAYS = 3 * 365
INACTIVE_NOTICE_HOURS = 48

PURPOSES: Dict[str, dict] = {
    "health_data": {
        "required": True,
        "title": "Store and use my health and fitness data",
        "detail": "Workouts, check-ins, sleep, meals, cycle, medication, symptoms and the other records you "
                  "enter or sync, used to show your history and personalise plans. Needed for the app to work.",
    },
    "ai": {
        "required": False,
        "title": "AI features",
        "detail": "Your message and the records it needs are sent to an AI provider (Google Gemini, Groq or TokenHarbor) to write coach "
                  "replies, read meal photos and parse goals. Without this the app uses its built-in rules.",
    },
    "sharing": {
        "required": False,
        "title": "Sharing with family and community",
        "detail": "Lets you invite family members, post to the community, join challenges and peer support. "
                  "What each person sees is still chosen per connection.",
    },
    "analytics": {
        "required": False,
        "title": "Product analytics",
        "detail": "Anonymous usage counts that help us fix and improve the app. Never offered under 18.",
    },
}

# uid -> {"events": [...], "birth_date", "minor", "guardian_email", "guardian"}
_records = durable_dict("app.core.privacy.records")
# sha256(token) -> {"user_id", "expires_at"}
_guardian_links = durable_dict("app.core.privacy.guardian_links")
# uid -> {"user_id", "due_at", "requested_at"}
_deletions = durable_dict("app.core.privacy.deletions")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_account(uid: Optional[str]) -> bool:
    from app.core.auth import user_manager
    return bool(uid) and uid != SHARED and uid in user_manager._users


def age_from(birth_date: str, today: Optional[date] = None) -> int:
    """Whole years. Raises ValueError for a malformed, future or implausible date."""
    born = date.fromisoformat(birth_date)
    today = today or date.today()
    years = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    if born > today or years > 120:
        raise ValueError("Enter a real date of birth")
    return years


def validate_signup(birth_date: str, choices: dict, guardian_email: Optional[str], own_email: str) -> bool:
    """Checks a signup's privacy fields before the account exists. Returns whether the user is a minor."""
    try:
        age = age_from(birth_date)
    except (TypeError, ValueError):
        raise ValueError("Enter your date of birth as YYYY-MM-DD")
    if age < MIN_AGE:
        raise ValueError(f"AdapFit is for people aged {MIN_AGE} and over")
    minor = age < ADULT_AGE
    if minor:
        email = (guardian_email or "").strip().lower()
        if "@" not in email or email == own_email.strip().lower():
            raise ValueError("Under 18, a parent or guardian's own email address is needed")
    elif not choices.get("health_data"):
        raise ValueError("The app cannot work without consent to store your health data")
    unknown = set(choices) - set(PURPOSES)
    if unknown:
        raise ValueError(f"Unknown consent purpose: {', '.join(sorted(unknown))}")
    return minor


def _append(uid: str, choices: dict, source: str) -> None:
    record = _records.setdefault(uid, {"events": []})
    at = _now()
    for purpose, granted in choices.items():
        if purpose in PURPOSES:
            record["events"].append({"purpose": purpose, "granted": bool(granted), "version": POLICY_VERSION,
                                     "at": at, "source": source})
    _records[uid] = record


def start(uid: str, birth_date: str, choices: dict, guardian_email: Optional[str]) -> dict:
    """Record a new account's privacy state; for a minor, nothing is granted until the guardian confirms."""
    minor = age_from(birth_date) < ADULT_AGE
    _records[uid] = {"events": [], "birth_date": birth_date, "minor": minor,
                     "guardian_email": (guardian_email or "").strip().lower() if minor else "",
                     "guardian": None, "requested": {k: bool(v) for k, v in choices.items() if k in PURPOSES}}
    if not minor:
        _append(uid, {p: bool(choices.get(p)) for p in PURPOSES}, "signup")
    return state(uid)


def current(uid: str) -> Dict[str, dict]:
    """Latest decision per purpose. A decision under an older policy version is reported but not granted."""
    events = (dict.get(_records, uid) or {}).get("events", [])
    out = {}
    for purpose in PURPOSES:
        last = next((e for e in reversed(events) if e["purpose"] == purpose), None)
        valid = bool(last and last["granted"] and last["version"] == POLICY_VERSION)
        out[purpose] = {"granted": valid, "version": last["version"] if last else None,
                        "at": last["at"] if last else None, "source": last["source"] if last else None}
    return out


def state(uid: str) -> dict:
    record = dict.get(_records, uid) or {}
    purposes = current(uid)
    guardian = record.get("guardian")
    deletion = dict.get(_deletions, uid)
    return {
        "policy_version": POLICY_VERSION,
        "purposes": {p: {**PURPOSES[p], **purposes[p]} for p in PURPOSES},
        "needs_consent": not purposes["health_data"]["granted"],
        "minor": bool(record.get("minor")),
        "guardian_pending": bool(record.get("minor")) and not guardian,
        "guardian": {k: guardian[k] for k in ("name", "relationship", "confirmed_at")} if guardian else None,
        "deletion_due_at": deletion["due_at"] if deletion else None,
    }


def update(uid: str, choices: dict) -> dict:
    """The user's own change. A child can withdraw but cannot grant; analytics never opens for a child."""
    unknown = set(choices) - set(PURPOSES)
    if unknown:
        raise ValueError(f"Unknown consent purpose: {', '.join(sorted(unknown))}")
    record = dict.get(_records, uid) or {}
    if record.get("minor") and any(choices.values()):
        raise PermissionError("Under 18, only a parent or guardian can give consent")
    _append(uid, choices, "user")
    return state(uid)


def allowed(purpose: str, uid: Optional[str] = None) -> bool:
    """Whether a purpose may run for the caller. Requests without an account (dev bypass, jobs) are not gated."""
    uid = uid or current_user_id()
    if not _is_account(uid):
        return True
    return current(uid)[purpose]["granted"] and current(uid)["health_data"]["granted"]


def blocked(uid: str) -> Optional[str]:
    """Why an account may not use its data right now, or None."""
    if not _is_account(uid):
        return None
    if dict.__contains__(_deletions, uid):
        return "deletion_pending"
    record = dict.get(_records, uid) or {}
    if record.get("minor") and not record.get("guardian"):
        return "guardian_pending"
    if not current(uid)["health_data"]["granted"]:
        return "consent_required"
    return None


# ── Guardian consent ────────────────────────────────────────────────────────

def _digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def send_guardian_link(uid: str) -> bool:
    from app.core.mailer import send_mail

    record = dict.get(_records, uid) or {}
    if not record.get("minor") or record.get("guardian"):
        return False
    for key in [k for k, v in dict.items(_guardian_links) if v["user_id"] == uid]:
        del _guardian_links[key]
    token = secrets.token_urlsafe(32)
    _guardian_links[_digest(token)] = {"user_id": uid, "expires_at": time.time() + GUARDIAN_LINK_HOURS * 3600}
    link = f"{settings.PUBLIC_BASE_URL.rstrip('/')}{settings.API_V1_STR}/privacy/guardian/{token}"
    body = (
        "Someone under 18 has signed up for AdapFit, a health and fitness tracking app, and named you as "
        "their parent or guardian.\n\n"
        "Under India's Digital Personal Data Protection Act, their data cannot be used until a parent or "
        "guardian agrees. Open this link to see what the app stores and to agree or decline:\n\n"
        f"{link}\n\nThe link works for {GUARDIAN_LINK_HOURS} hours. If you do not know this person, ignore "
        "this email and the account will stay locked."
    )
    return await send_mail(record["guardian_email"], "Consent needed for a child's AdapFit account", body)


def guardian_link(token: str) -> Optional[dict]:
    link = dict.get(_guardian_links, _digest(token))
    if not link or link["expires_at"] < time.time():
        return None
    return {"user_id": link["user_id"], "record": dict.get(_records, link["user_id"]) or {}}


def guardian_confirm(token: str, name: str, relationship: str, declared_adult: bool, choices: dict) -> dict:
    link = guardian_link(token)
    if not link:
        raise LookupError("This link has expired or was already used")
    if not declared_adult or not name.strip() or not relationship.strip():
        raise ValueError("Give your name and relationship, and confirm you are 18 or over")
    if not choices.get("health_data"):
        raise ValueError("Without consent to store health data the account cannot be used; choose decline instead")
    uid = link["user_id"]
    record = _records[uid]
    record["guardian"] = {"name": name.strip(), "relationship": relationship.strip(), "email": record["guardian_email"],
                          "confirmed_at": _now(), "method": "email link and declaration of adulthood"}
    _records[uid] = record
    _append(uid, {**{p: bool(choices.get(p)) for p in PURPOSES}, "analytics": False}, "guardian")
    del _guardian_links[_digest(token)]
    return state(uid)


async def guardian_decline(token: str) -> None:
    link = guardian_link(token)
    if not link:
        raise LookupError("This link has expired or was already used")
    from app.core.auth import user_manager
    await user_manager.delete_user(link["user_id"])


# ── Account erasure ─────────────────────────────────────────────────────────

def request_deletion(uid: str, seconds: int = DELETION_GRACE_SECONDS, reason: str = "user",
                     now: Optional[float] = None) -> float:
    now = now or time.time()
    due = now + seconds
    _deletions[uid] = {"user_id": uid, "due_at": due, "requested_at": now, "reason": reason}
    return due


def on_login(uid: str) -> None:
    """Coming back cancels an erasure scheduled for inactivity, not one the user asked for."""
    pending = dict.get(_deletions, uid)
    if pending and pending.get("reason") == "inactive":
        _deletions.pop(uid, None)


async def schedule_retention(now: Optional[float] = None) -> int:
    """Schedule erasure for unconfirmed child accounts and long-unused accounts. Returns how many."""
    from app.core.auth import user_manager
    from app.core.mailer import send_mail

    now = now or time.time()
    scheduled = 0
    for user in list(user_manager._users.values()):
        if dict.__contains__(_deletions, user.id) or user.role in ("admin", "superadmin"):
            continue
        record = dict.get(_records, user.id) or {}
        if record.get("minor") and not record.get("guardian") and user.created_at < now - GUARDIAN_WAIT_DAYS * 86400:
            request_deletion(user.id, 0, "guardian_never_confirmed", now)
            scheduled += 1
        elif max(user.created_at, user.last_login) < now - INACTIVE_DAYS * 86400:
            sent = await send_mail(user.email, "Your AdapFit account will be deleted",
                                   f"You have not used AdapFit for {INACTIVE_DAYS // 365} years, so your account and "
                                   f"everything in it will be deleted in {INACTIVE_NOTICE_HOURS} hours. Sign in "
                                   "before then to keep it. You can export your data from Settings after signing in.")
            # No erasure without the notice; the next sweep tries again.
            if sent:
                request_deletion(user.id, INACTIVE_NOTICE_HOURS * 3600, "inactive", now)
                scheduled += 1
    return scheduled


def cancel_deletion(uid: str) -> bool:
    return _deletions.pop(uid, None) is not None


async def run_due_deletions(now: Optional[float] = None) -> int:
    from app.core.auth import user_manager

    now = now or time.time()
    await schedule_retention(now)
    due = [(uid, d.get("reason", "user")) for uid, d in list(dict.items(_deletions)) if d["due_at"] <= now]
    for uid, reason in due:
        await user_manager.delete_user(uid)
        _deletions.pop(uid, None)
        logger.info("Account erased (%s): %s", reason, _digest(uid)[:12])
    return len(due)

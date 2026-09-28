"""
Encrypted vault: records a user keeps under their own passphrase, and time-limited shares of them.

Every vault record is already encrypted at rest with the server keyring, like all
feature state (app/core/crypto.py). A passphrase adds a second layer the server
cannot open on its own: the key is derived with PBKDF2-SHA256 and never stored,
so a forgotten passphrase means the record is unreadable, by design.
"""
import base64
import hashlib
import json
import secrets
import time
import uuid
from typing import Optional

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.durable import durable_dict

PBKDF2_ITERATIONS = 600_000
MAX_SHARE_HOURS = 24 * 30
ALGORITHMS = {
    "at_rest": {"name": "AES-256-GCM", "key": "server keyring (DATA_ENCRYPTION_KEYS)", "scope": "all stored feature data"},
    "passphrase": {"name": "AES-256-GCM", "key_derivation": f"PBKDF2-HMAC-SHA256, {PBKDF2_ITERATIONS} iterations",
                   "scope": "vault records saved with a passphrase"},
    "passwords": {"name": "PBKDF2-HMAC-SHA256", "iterations": 310_000},
    "tokens": {"name": "HMAC-SHA256 (JWT HS256)"},
}

# record id -> {"id", "user_id", "label", "created_at", "protected", "salt", "nonce", "payload"}
_records = durable_dict("app.core.encryption.records")
# share id -> {"id", "record_id", "owner_id", "recipient_id", "expires_at", "max_accesses", "access_count", "status"}
_shares = durable_dict("app.core.encryption.shares")


def _passphrase_key(passphrase: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode(), salt, PBKDF2_ITERATIONS, dklen=32)


def _meta(record: dict) -> dict:
    return {k: record[k] for k in ("id", "label", "created_at", "protected")}


def encrypt(user_id: str, data: dict, label: str = "", passphrase: Optional[str] = None) -> dict:
    record_id = uuid.uuid4().hex
    plain = json.dumps(data, sort_keys=True).encode()
    record = {"id": record_id, "user_id": user_id, "label": label[:120], "created_at": time.time(),
              "protected": bool(passphrase)}
    if passphrase:
        if len(passphrase) < 8:
            raise ValueError("Passphrase must be at least 8 characters")
        salt, nonce = secrets.token_bytes(16), secrets.token_bytes(12)
        cipher = AESGCM(_passphrase_key(passphrase, salt)).encrypt(nonce, plain, record_id.encode())
        record.update(salt=base64.b64encode(salt).decode(), nonce=base64.b64encode(nonce).decode(),
                      payload=base64.b64encode(cipher).decode())
    else:
        record["payload"] = plain.decode()
    _records[record_id] = record
    return _meta(record)


def _open(record: dict, passphrase: Optional[str]) -> dict:
    if not record["protected"]:
        return json.loads(record["payload"])
    if not passphrase:
        raise PermissionError("This record needs its passphrase")
    key = _passphrase_key(passphrase, base64.b64decode(record["salt"]))
    try:
        plain = AESGCM(key).decrypt(base64.b64decode(record["nonce"]), base64.b64decode(record["payload"]),
                                    record["id"].encode())
    except InvalidTag:
        raise PermissionError("Wrong passphrase")
    return json.loads(plain)


def _active_share(share_id: str, record_id: str, caller: str) -> Optional[dict]:
    share = dict.get(_shares, share_id)
    if (not share or share["record_id"] != record_id or share["recipient_id"] != caller
            or share["status"] != "active" or share["expires_at"] < time.time()
            or share["access_count"] >= share["max_accesses"]):
        return None
    return share


def decrypt(caller: str, record_id: str, passphrase: Optional[str] = None, share_id: Optional[str] = None) -> dict:
    record = dict.get(_records, record_id)
    if not record:
        raise LookupError("Record not found")
    share = None
    if record["user_id"] != caller:
        share = _active_share(share_id or "", record_id, caller)
        if share is None:
            raise LookupError("Record not found")
    data = _open(record, passphrase)
    if share is not None:
        share["access_count"] += 1
        _shares[share["id"]] = share
    return {**_meta(record), "data": data, "owner_id": record["user_id"], "via_share": share["id"] if share else None}


def list_records(user_id: str) -> list:
    return [_meta(r) for r in dict.values(_records) if r["user_id"] == user_id]


def delete(user_id: str, record_id: str) -> bool:
    record = dict.get(_records, record_id)
    if not record or record["user_id"] != user_id:
        return False
    del _records[record_id]
    for sid in [s["id"] for s in dict.values(_shares) if s["record_id"] == record_id]:
        del _shares[sid]
    return True


def share(owner_id: str, record_id: str, recipient_id: str, expiry_hours: int = 24, max_accesses: int = 10) -> dict:
    record = dict.get(_records, record_id)
    if not record or record["user_id"] != owner_id:
        raise LookupError("Record not found")
    if recipient_id == owner_id:
        raise ValueError("Share with someone else")
    share_id = uuid.uuid4().hex
    _shares[share_id] = {
        "id": share_id, "record_id": record_id, "owner_id": owner_id, "recipient_id": recipient_id,
        "created_at": time.time(), "expires_at": time.time() + max(1, min(expiry_hours, MAX_SHARE_HOURS)) * 3600,
        "max_accesses": max(1, min(max_accesses, 100)), "access_count": 0, "status": "active",
    }
    return dict(_shares[share_id])


def revoke_share(owner_id: str, share_id: str) -> bool:
    share = dict.get(_shares, share_id)
    if not share or share["owner_id"] != owner_id:
        return False
    share["status"] = "revoked"
    _shares[share_id] = share
    return True


def shares_for(user_id: str) -> dict:
    mine = [dict(s) for s in dict.values(_shares) if s["owner_id"] == user_id]
    received = [dict(s) for s in dict.values(_shares) if s["recipient_id"] == user_id and s["status"] == "active"]
    return {"given": mine, "received": received}

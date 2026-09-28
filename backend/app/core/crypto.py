"""
Encryption at rest: AES-256-GCM under a keyring.

DATA_ENCRYPTION_KEYS holds "id:base64key" pairs separated by commas. The first
key encrypts; every key decrypts. To rotate: put a new key first, restart, call
POST /encryption/key/rotate (re-encrypts every stored row), then drop the old key.

Without the variable, development generates one key into the data directory.
Production refuses to start without it (startup_checks).
"""
import base64
import os
import secrets
import stat
from functools import lru_cache
from pathlib import Path
from typing import List, Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"AFE1"
_NONCE = 12


def new_key() -> str:
    return base64.b64encode(AESGCM.generate_key(bit_length=256)).decode()


def _parse(spec: str) -> List[Tuple[str, bytes]]:
    ring = []
    for part in (p.strip() for p in spec.split(",")):
        if not part:
            continue
        key_id, _, encoded = part.partition(":")
        key = base64.b64decode(encoded)
        if not key_id or len(key_id) > 32 or len(key) != 32:
            raise ValueError("DATA_ENCRYPTION_KEYS entries must be id:base64 of 32 bytes")
        ring.append((key_id, key))
    return ring


def _dev_key_file() -> Path:
    base = os.getenv("ADAPFIT_DATA_DIR") or Path(__file__).resolve().parent.parent / "data"
    return Path(base) / "data_encryption_key"


@lru_cache(maxsize=1)
def keyring() -> List[Tuple[str, bytes]]:
    spec = os.getenv("DATA_ENCRYPTION_KEYS", "").strip()
    if spec:
        return _parse(spec)
    if os.getenv("ENVIRONMENT", "development").lower() == "production":
        raise RuntimeError("DATA_ENCRYPTION_KEYS is required in production")
    path = _dev_key_file()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"dev:{new_key()}", encoding="utf-8")
        try:
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass
    return _parse(path.read_text(encoding="utf-8"))


def active_key_id() -> str:
    return keyring()[0][0]


def seal(plain: bytes, aad: bytes = b"") -> bytes:
    """MAGIC | id length | id | nonce | ciphertext+tag. `aad` binds the blob to where it is stored."""
    key_id, key = keyring()[0]
    nonce = secrets.token_bytes(_NONCE)
    kid = key_id.encode()
    return MAGIC + bytes([len(kid)]) + kid + nonce + AESGCM(key).encrypt(nonce, plain, aad)


def is_sealed(blob: bytes) -> bool:
    return blob[:4] == MAGIC


def key_id_of(blob: bytes) -> str:
    return blob[5:5 + blob[4]].decode() if is_sealed(blob) else ""


def open_sealed(blob: bytes, aad: bytes = b"") -> bytes:
    """Decrypt a sealed blob; a blob written before encryption was enabled is returned as is."""
    if not is_sealed(blob):
        return blob
    kid_len = blob[4]
    key_id = blob[5:5 + kid_len].decode()
    key = dict(keyring()).get(key_id)
    if key is None:
        raise KeyError(f"encryption key {key_id!r} is not in DATA_ENCRYPTION_KEYS")
    start = 5 + kid_len
    return AESGCM(key).decrypt(blob[start:start + _NONCE], blob[start + _NONCE:], aad)

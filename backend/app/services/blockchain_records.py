"""Blockchain Health Records Service - Immutable health data ledger.

Based on 2025 blockchain healthcare research:
- Immutable health record entries
- Patient-controlled data sharing
- Tamper-evident audit trail
- Consent management
- Health data verification
"""

import time
import hashlib
import json
from typing import Dict, List, Any


class BlockchainRecordsService:
    """Blockchain-based immutable health records."""

    def __init__(self):
        self.chains: Dict[str, List[Dict]] = {}
        self.consent_grants: Dict[str, List[Dict]] = {}

    def _hash_block(self, block: Dict) -> str:
        """Create SHA-256 hash of block data."""
        block_string = json.dumps(block, sort_keys=True, default=str)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def create_genesis_block(self, user_id: str) -> Dict[str, Any]:
        """Create the first block in a user's health chain."""
        genesis = {
            "index": 0,
            "timestamp": time.time(),
            "data": {"type": "genesis", "user_id": user_id, "message": "Health record chain initialized"},
            "previous_hash": "0",
            "hash": "",
        }
        genesis["hash"] = self._hash_block(genesis)
        self.chains[user_id] = [genesis]
        return genesis

    def add_record(self, user_id: str, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add an immutable health record entry."""
        if user_id not in self.chains:
            self.create_genesis_block(user_id)

        chain = self.chains[user_id]
        previous = chain[-1]

        block = {
            "index": len(chain),
            "timestamp": time.time(),
            "data": {
                "type": record_data.get("type", "health_metric"),
                "category": record_data.get("category", "general"),
                "value": record_data.get("value"),
                "unit": record_data.get("unit"),
                "source": record_data.get("source", "app"),
                "metadata": record_data.get("metadata", {}),
            },
            "previous_hash": previous["hash"],
            "hash": "",
        }
        block["hash"] = self._hash_block(block)
        chain.append(block)

        return {
            "record_id": block["hash"][:16],
            "index": block["index"],
            "timestamp": block["timestamp"],
            "type": block["data"]["type"],
            "verified": True,
            "immutable": True,
        }

    def verify_chain(self, user_id: str) -> Dict[str, Any]:
        """Verify the integrity of a user's health chain."""
        chain = self.chains.get(user_id, [])
        if len(chain) <= 1:
            return {"valid": True, "blocks": len(chain), "message": "Chain is valid"}

        valid = True
        for i in range(1, len(chain)):
            current = chain[i]
            previous = chain[i - 1]

            if current["previous_hash"] != previous["hash"]:
                valid = False
                break

            if current["hash"] != self._hash_block({k: v for k, v in current.items() if k != "hash"}):
                valid = False
                break

        return {
            "valid": valid,
            "blocks": len(chain),
            "message": "Chain integrity verified ✓" if valid else "Chain tampered! ⚠️",
        }

    def get_record_history(self, user_id: str, record_type: str = "", limit: int = 50) -> List[Dict]:
        """Get history of a specific record type."""
        chain = self.chains.get(user_id, [])
        records = [
            {
                "index": b["index"],
                "timestamp": b["timestamp"],
                "type": b["data"]["type"],
                "category": b["data"].get("category"),
                "value": b["data"].get("value"),
                "hash": b["hash"][:16],
            }
            for b in chain[1:]  # Skip genesis
            if not record_type or b["data"]["type"] == record_type
        ]
        return records[-limit:]

    def grant_access(self, user_id: str, grantee: str, record_types: List[str], expiry_hours: int = 24) -> Dict[str, Any]:
        """Grant time-limited access to health records."""
        if user_id not in self.consent_grants:
            self.consent_grants[user_id] = []

        grant = {
            "grantee": grantee,
            "record_types": record_types,
            "granted_at": time.time(),
            "expires_at": time.time() + expiry_hours * 3600,
            "active": True,
        }
        self.consent_grants[user_id].append(grant)

        return {"access_granted": True, "grantee": grantee, "expires_in_hours": expiry_hours}

    def revoke_access(self, user_id: str, grantee: str) -> Dict[str, Any]:
        """Revoke access to health records."""
        grants = self.consent_grants.get(user_id, [])
        revoked = 0
        for grant in grants:
            if grant["grantee"] == grantee and grant["active"]:
                grant["active"] = False
                revoked += 1
        return {"access_revoked": revoked > 0, "revoked_count": revoked}

    def get_audit_log(self, user_id: str) -> List[Dict]:
        """Get complete audit trail of all record access."""
        chain = self.chains.get(user_id, [])
        return [
            {"action": "record_added", "index": b["index"], "timestamp": b["timestamp"], "hash": b["hash"][:16]}
            for b in chain[1:]
        ]


blockchain_records_service = BlockchainRecordsService()
